import json
import re

from app.core.llm_router import generate_completion

PROJECT_SCHEMA = """
You are an enterprise Discovery Engine.

Your job is to extract structured project information from ALL supplied client context.

The input may include one or more of:

- Meeting transcripts
- Email conversations
- Statements of Work
- Contracts
- Proposals
- PDFs
- Word documents
- PowerPoint files
- Excel sheets
- Notes
- Other enterprise documents

Treat every uploaded document as equally important.

Information found in emails, contracts, or supporting documents is just as valuable as information found in the meeting transcript.

Your response MUST be ONLY a single valid JSON object.

Do NOT return markdown.
Do NOT return explanations.
Do NOT wrap the JSON inside ```.

The first character MUST be {
The last character MUST be }

Return this JSON:

{
    "context_summary":"",
    "project_name":"",
    "client_name":"",
    "provider_name":"",
    "industry":"",
    "engagement_type":"",

    "client_address":"",
    "provider_address":"",

    "client_email":"",
    "provider_email":"",

    "client_phone":"",
    "provider_phone":"",

    "effective_date":"",
    "project_start":"",
    "project_end":"",

    "msa_reference":"",

    "requirements":[],
    "deliverables":[],
    "risks":[],
    "assumptions":[],
    "stakeholders":[],

    "timeline":"",

    "client_contacts":[],
    "provider_contacts":[],

    "client_responsibilities":[],
    "provider_responsibilities":[],

    "out_of_scope":[],

    "pricing":"",
    "payment_terms":"",
    "billing_schedule":"",

    "change_control":"",
    "legal_terms":"",
    "data_handling":"",
    "term":"",
    "termination":"",

    "approvers":[]
}

Extraction priority (highest first):

1. Client legal entity
2. Provider legal entity
3. Contact names
4. Contact titles
5. Email addresses
6. Physical addresses
7. Pricing
8. Billing schedule
9. Payment terms
10. Dates
11. Deliverables
12. Requirements
13. Responsibilities
14. Risks
15. MSA references
16. Timeline
17. Approvers

Rules:

- NEVER invent information.
- Use information from ANY uploaded file.
- If a value does not exist, return an empty string.
- If a list has no entries, return [].
- Arrays should contain complete sentences wherever practical.
- Contact arrays should use this format:

Client contacts:

[
    {
        "name":"",
        "title":"",
        "email":"",
        "phone":""
    }
]

Provider contacts:

[
    {
        "name":"",
        "title":"",
        "email":"",
        "phone":""
    }
]
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
        "project_name": "",
        "client_name": "",
        "provider_name": "",
        "industry": "",
        "engagement_type": "",

        "client_address": "",
        "provider_address": "",

        "client_email": "",
        "provider_email": "",

        "client_phone": "",
        "provider_phone": "",

        "effective_date": "",
        "project_start": "",
        "project_end": "",

        "msa_reference": "",

        "requirements": [],
        "deliverables": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],

        "timeline": "",

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
            "project_name": as_str("project_name"),
            "client_name": as_str("client_name"),
            "provider_name": as_str("provider_name"),
            "industry": as_str("industry"),
            "engagement_type": as_str("engagement_type"),

            "client_address": as_str("client_address"),
            "provider_address": as_str("provider_address"),

            "client_email": as_str("client_email"),
            "provider_email": as_str("provider_email"),

            "client_phone": as_str("client_phone"),
            "provider_phone": as_str("provider_phone"),

            "effective_date": as_str("effective_date"),
            "project_start": as_str("project_start"),
            "project_end": as_str("project_end"),

            "msa_reference": as_str("msa_reference"),

            "requirements": as_list("requirements"),
            "deliverables": as_list("deliverables"),
            "risks": as_list("risks"),
            "assumptions": as_list("assumptions"),
            "stakeholders": as_list("stakeholders"),

            "timeline": as_str("timeline"),

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
        }

    except Exception as e:
        return {
            **empty_state,
            "error": str(e),
            "raw_response": response[:2000] if response else "",
        }