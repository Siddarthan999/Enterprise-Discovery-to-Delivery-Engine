from app.services.hybrid_search import hybrid_search
from app.core.llm_router import generate_completion


def build_context(results, max_chunks=5):

    context_parts = []

    for r in results[:max_chunks]:

        title = r.get("title", "Unknown")

        content = r.get("content", "")

        context_parts.append(
            f"""
DOCUMENT: {title}

CONTENT:
{content}
"""
        )

    return "\n\n".join(context_parts)


def generate_answer(question: str):

    results = hybrid_search(question, limit=5)

    context = build_context(results)

    prompt = f"""
You are an Enterprise Knowledge Assistant.

Answer ONLY from the provided context.

If the answer is not present,
say:
"I could not find that information in the uploaded documents."

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    answer = generate_completion(prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "doc_id": r.get("doc_id"),
                "title": r.get("title")
            }
            for r in results
        ]
    }