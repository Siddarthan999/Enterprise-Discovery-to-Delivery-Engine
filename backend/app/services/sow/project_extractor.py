import json
import re

from app.core.llm_router import generate_completion

PROJECT_SCHEMA = """
You are a JSON API for an enterprise discovery engine.

You MUST respond ONLY with a single valid JSON object that matches the schema below.
Do NOT include any explanations, headings, bullet points, markdown, or text outside the JSON.
The first character of your response MUST be "{" and the last character MUST be "}".

Extract structured project information from a meeting transcript for use in writing a professional, standard Statement of Work.

Return ONLY valid JSON in this format:

{
  "context_summary": "",
  "requirements": [],
  "risks": [],
  "assumptions": [],
  "stakeholders": [],
  "deliverables": [],
  "timeline": "",
  "client_name": "",
  "provider_name": "",
  "industry": "",
  "engagement_type": "",
  "client_contacts": [],
  "provider_contacts": [],
  "client_responsibilities": [],
  "provider_responsibilities": [],
  "out_of_scope": [],
  "pricing": "",
  "payment_terms": "",
  "billing_schedule": "",
  "change_control": "",
  "legal_terms": "",
  "data_handling": "",
  "term": "",
  "termination": "",
  "approvers": [],
  "msa_reference": ""
}

Rules for EVERY array item:
- Write each item as a FULL SENTENCE with real context, not a short keyword phrase.
- Include why it matters or what obligation it creates whenever the transcript supports that context.
- Do not duplicate the same fact across multiple items.
- Do not invent names, fees, dates, legal terms, or responsibilities that were not discussed.
- If a category has no support in the transcript, use an empty array.

Rules for EVERY string field:
- Use a short paragraph or complete sentence when substantive detail exists.
- If the transcript does not support the field, return an empty string.
- Do not fabricate payment terms, legal terms, governing agreement references, or contact information.

Field guidance:
- "context_summary": 3-5 sentences summarizing the engagement, why it is happening, and the intended outcome.
- "timeline": capture phases, target windows, milestones, and dependency timing if mentioned.
- "pricing": include any commercial model, budget range, fee discussion, T&M/fixed fee cues, or note that pricing was deferred only if explicitly said.
- "payment_terms": include payment windows, milestone-based billing, acceptance-linked billing, invoice timing, or procurement conditions if stated.
- "billing_schedule": include how and when invoices will be issued if discussed.
- "change_control": include any comments about handling scope changes, revisions, approvals, or change requests.
- "legal_terms": include confidentiality, IP ownership, compliance, security, regulatory, or MSA references if discussed.
- "data_handling": include data privacy, access, environment, residency, or security handling expectations if discussed.
- "term": include project start/end term language if discussed.
- "termination": include termination or cancellation conditions only if discussed.
- "approvers": include the actual approving roles or named decision-makers if discussed.
- "client_contacts" and "provider_contacts": include the role and name if known, otherwise the role and team context.
"""


def _extract_json_block(response: str) -> str:
    response = (response or "").strip()

    if not response:
        return ""

    # Fenced JSON: ```json { ... } ```
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    # Pure JSON string
    if response.startswith("{") and response.endswith("}"):
        return response

    # Inline JSON object somewhere in the text
    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0).strip() if match else ""


def _repair_to_json(raw: str) -> str:
    """
    Second-pass prompt: if the first response was markdown or prose,
    ask the model explicitly to convert it to JSON matching PROJECT_SCHEMA.
    """
    prompt = f"""
You previously summarized the transcript as follows:

{raw}

This response does NOT follow the required JSON-only format.

You MUST now convert this into a single valid JSON object that matches the schema described below.

{PROJECT_SCHEMA}

Return ONLY the JSON object. No headings, no markdown, no bullet points, no extra text.
The first character of your response MUST be "{{" and the last character MUST be "}}".
"""
    return generate_completion(prompt)


def extract_project_state(transcript: str):
    empty_state = {
        "context_summary": "",
        "requirements": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],
        "deliverables": [],
        "timeline": "",
        "client_name": "",
        "provider_name": "",
        "industry": "",
        "engagement_type": "",
        "client_contacts": [],
        "provider_contacts": [],
        "client_responsibilities": [],
        "provider_responsibilities": [],
        "out_of_scope": [],
        "pricing": "",
        "payment_terms": "",
        "billing_schedule": "",
        "change_control": "",
        "legal_terms": "",
        "data_handling": "",
        "term": "",
        "termination": "",
        "approvers": [],
        "msa_reference": "",
    }

    if not transcript or len(transcript.strip()) < 10:
        return empty_state

    prompt = f"""
{PROJECT_SCHEMA}

TRANSCRIPT:
{transcript}
"""

    response = ""
    try:
        response = generate_completion(prompt)

        if not response or not response.strip():
            raise ValueError("LLM returned empty response")

        cleaned = _extract_json_block(response)

        # If the model ignored JSON-only and returned markdown/prose, try a repair pass
        if not cleaned or not cleaned.strip():
            repair_response = _repair_to_json(response)
            cleaned = _extract_json_block(repair_response)
            if not cleaned or not cleaned.strip():
                raise ValueError("No JSON content found in LLM response (even after repair)")

        data = json.loads(cleaned)

        if not isinstance(data, dict):
            raise ValueError("LLM output was not a JSON object")

        def as_str(key: str) -> str:
            value = data.get(key, "")
            return value if isinstance(value, str) else ""

        def as_list(key: str) -> list:
            value = data.get(key, [])
            return value if isinstance(value, list) else []

        return {
            "context_summary": as_str("context_summary"),
            "requirements": as_list("requirements"),
            "risks": as_list("risks"),
            "assumptions": as_list("assumptions"),
            "stakeholders": as_list("stakeholders"),
            "deliverables": as_list("deliverables"),
            "timeline": as_str("timeline"),
            "client_name": as_str("client_name"),
            "provider_name": as_str("provider_name"),
            "industry": as_str("industry"),
            "engagement_type": as_str("engagement_type"),
            "client_contacts": as_list("client_contacts"),
            "provider_contacts": as_list("provider_contacts"),
            "client_responsibilities": as_list("client_responsibilities"),
            "provider_responsibilities": as_list("provider_responsibilities"),
            "out_of_scope": as_list("out_of_scope"),
            "pricing": as_str("pricing"),
            "payment_terms": as_str("payment_terms"),
            "billing_schedule": as_str("billing_schedule"),
            "change_control": as_str("change_control"),
            "legal_terms": as_str("legal_terms"),
            "data_handling": as_str("data_handling"),
            "term": as_str("term"),
            "termination": as_str("termination"),
            "approvers": as_list("approvers"),
            "msa_reference": as_str("msa_reference"),
        }

    except Exception as e:
        return {
            **empty_state,
            "error": str(e),
            "raw_response": response[:2000] if response else "",
        }