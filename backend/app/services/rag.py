import json
import re

from app.services.hybrid_search import hybrid_search
from app.core.llm_router import generate_completion
from app.services.conversation_store import conversation_store

RELEVANCE_THRESHOLD = 0.35  # tune against your hybrid_search score scale

FALLBACK_MESSAGE = "I could not find that information in the uploaded documents."


def format_history(history):
    if not history:
        return ""
    lines = []
    for turn in history:
        lines.append(f"User: {turn['question']}")
        lines.append(f"Assistant: {turn['answer']}")
    return "\n".join(lines)


def condense_question(question: str, history: list) -> str:
    """Rewrite a follow-up into a standalone question using chat history,
    so retrieval works even when the user says 'likewise', 'that one', etc."""
    if not history:
        return question

    prompt = f"""Given the conversation history and a follow-up question, rewrite the
follow-up as a standalone question that contains all necessary context.
Do not answer it. Return ONLY the rewritten question, nothing else.

CONVERSATION HISTORY:
{format_history(history)}

FOLLOW-UP QUESTION:
{question}

STANDALONE QUESTION:"""

    rewritten = generate_completion(prompt).strip()
    return rewritten or question


def build_context(results, max_chunks=5):
    """Tags each chunk with its doc_id so the model can cite precisely
    which document(s) it actually used, instead of us returning every
    retrieved doc as a 'source'."""
    context_parts = []
    for r in results[:max_chunks]:
        doc_id = r.get("doc_id")
        title = r.get("title", "Unknown")
        content = r.get("content", "")
        context_parts.append(
            f"DOCUMENT_ID: {doc_id}\nDOCUMENT_TITLE: {title}\n\nCONTENT:\n{content}"
        )
    return "\n\n---\n\n".join(context_parts)


def _strip_code_fences(text: str) -> str:
    """Some models wrap JSON in ```json ... ``` even when told not to."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _coerce_answer_to_text(answer_field) -> str:
    """The model is asked for a string but sometimes returns a list
    (e.g. when the answer is naturally a set of names). Normalize instead
    of crashing, so we never fall back to dumping raw JSON at the user."""
    if isinstance(answer_field, str):
        return answer_field.strip()

    if isinstance(answer_field, list):
        items = [str(item).strip() for item in answer_field if str(item).strip()]
        return ", ".join(items)

    if isinstance(answer_field, dict):
        items = [f"{k}: {v}" for k, v in answer_field.items()]
        return "; ".join(items)

    if answer_field is None:
        return ""

    return str(answer_field).strip()


def _coerce_cited_ids(cited_field) -> list:
    if not isinstance(cited_field, list):
        return []

    ids = []
    for item in cited_field:
        try:
            ids.append(int(item))
        except (TypeError, ValueError):
            continue
    return ids


def _parse_llm_response(raw: str):
    """Always returns (answer_text, suggested_questions, cited_doc_ids, found_answer)
    — never raw JSON, even if the model deviates from the requested schema."""
    cleaned = _strip_code_fences(raw)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # No JSON at all — can't trust a found_answer flag that isn't there,
        # so treat conservatively as "found" and show the raw text; this
        # only happens if the model badly misbehaves.
        return cleaned.strip(), [], [], True

    if not isinstance(parsed, dict):
        return _coerce_answer_to_text(parsed), [], [], True

    answer_text = _coerce_answer_to_text(parsed.get("answer"))

    suggested = parsed.get("suggested_questions", [])
    if not isinstance(suggested, list):
        suggested = []
    suggested = [str(q).strip() for q in suggested if str(q).strip()]

    cited_doc_ids = _coerce_cited_ids(parsed.get("cited_doc_ids"))

    found_answer = parsed.get("found_answer")
    if not isinstance(found_answer, bool):
        # Model omitted the flag — infer from whether it cited anything,
        # rather than trusting exact-string matching against FALLBACK_MESSAGE.
        found_answer = len(cited_doc_ids) > 0

    if not answer_text:
        answer_text = FALLBACK_MESSAGE
        found_answer = False

    return answer_text, suggested, cited_doc_ids, found_answer


def generate_answer(question: str, session_id: str):
    history = conversation_store.get_history(session_id)

    standalone_question = condense_question(question, history)

    results = hybrid_search(standalone_question, limit=5)

    relevant_results = [
        r for r in results if r.get("score", 0) >= RELEVANCE_THRESHOLD
    ]

    if not relevant_results:
        conversation_store.add_turn(session_id, question, FALLBACK_MESSAGE)
        return {
            "answer": FALLBACK_MESSAGE,
            "sources": [],
            "suggested_questions": [],
        }

    context = build_context(relevant_results)

    prompt = f"""You are an Enterprise Knowledge Assistant. You answer STRICTLY using
the CONTEXT below. You have no general knowledge to fall back on.

Rules:
- If the answer is not explicitly present in the CONTEXT, respond exactly:
  "{FALLBACK_MESSAGE}"
- Never use outside knowledge, even if you're confident it's correct.
- Never give generic instructions (e.g. generic MariaDB/Docker commands) unless
  they are copied from the CONTEXT for the specific entity/user/system asked about.
- If the question is ambiguous given the conversation, ask a clarifying question
  instead of guessing.
- Keep answers concise.

CONVERSATION HISTORY:
{format_history(history)}

CONTEXT (each block tagged with DOCUMENT_ID):
{context}

CURRENT QUESTION (standalone form): {standalone_question}
ORIGINAL USER MESSAGE: {question}

Respond ONLY with valid JSON in this exact shape, no markdown fences, no other text:
{{
  "found_answer": <true if the CONTEXT actually contains the answer, false if it does not>,
  "answer": "<if found_answer is true: a single plain-text string, never an
             array or object — if the answer has multiple items, join them
             into one readable sentence.
             if found_answer is false: exactly this text:
             '{FALLBACK_MESSAGE}'>",
  "cited_doc_ids": [<the DOCUMENT_ID(s) you actually drew the answer from —
                     usually just one. MUST be an empty list if
                     found_answer is false.>],
  "suggested_questions": ["<follow-up 1>", "<follow-up 2>", "<follow-up 3>"]
}}

The "answer" value MUST be a plain string, never a JSON array or object.
"cited_doc_ids" must only contain DOCUMENT_IDs that genuinely support the
answer — do not list every document in the context, only the ones used.
If found_answer is false, cited_doc_ids MUST be empty — do not cite a
document just because it was retrieved if it doesn't actually contain
the answer.
"""

    raw = generate_completion(prompt)
    answer_text, suggested, cited_doc_ids, found_answer = _parse_llm_response(raw)

    # found_answer is the single source of truth for whether we show sources —
    # we don't infer this from string-matching the answer text, since the
    # model doesn't always reproduce FALLBACK_MESSAGE verbatim.
    if not found_answer:
        cited_doc_ids = []

    by_doc_id = {r["doc_id"]: r for r in relevant_results}
    cited_sources = [
        {"doc_id": doc_id, "title": by_doc_id[doc_id].get("title")}
        for doc_id in cited_doc_ids
        if doc_id in by_doc_id
    ]

    # Only backfill a top-doc source when the model DID find an answer but
    # forgot to cite it — never when it said it found nothing.
    if found_answer and not cited_sources:
        top = max(relevant_results, key=lambda r: r.get("score", 0))
        cited_sources = [{"doc_id": top["doc_id"], "title": top.get("title")}]

    conversation_store.add_turn(session_id, question, answer_text)

    return {
        "answer": answer_text,
        "sources": cited_sources,
        "suggested_questions": suggested,
    }