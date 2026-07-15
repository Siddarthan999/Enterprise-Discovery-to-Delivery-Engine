import json
import re
from app.core.embedding import get_embedding
from app.core.llm_router import generate_completion


PROJECT_SCHEMA = """
You are an enterprise discovery engine. Extract structured project
information from a meeting transcript for use in writing a formal
Statement of Work.

Return ONLY valid JSON in this format:

{
  "context_summary": "",
  "requirements": [],
  "risks": [],
  "assumptions": [],
  "stakeholders": [],
  "deliverables": [],
  "timeline": ""
}

Rules for EVERY array item:
- Write each item as a FULL SENTENCE with real context, not a short keyword
  phrase. A weak item looks like "SSO integration". A correct item looks
  like "The client needs SSO integration with their existing Okta identity
  provider to reduce login friction for field staff who currently manage
  separate credentials for each internal tool."
- Include WHY it matters or WHAT problem it solves whenever the transcript
  gives you that context — do not strip reasoning out to save space.
- Do not duplicate the same fact across multiple items.
- If the transcript doesn't give enough detail for a full sentence with
  context, still write the fullest sentence the transcript actually
  supports — never pad with generic industry language that isn't grounded
  in what was actually said.
- If a category has no support in the transcript, use an empty array —
  do not invent items to fill it.

"context_summary": 3-5 sentences synthesizing the overall project
narrative — what the engagement is, why it's happening now, and what
outcome the client wants. This should read like the opening of a
briefing document, not a list.

"timeline": if timeline information exists in the transcript, write it as
a short paragraph (phases, target dates, dependencies mentioned) rather
than a single date string. If nothing was discussed, use "".
"""


def _extract_json_block(response: str) -> str:
    """Model may wrap JSON in prose or code fences despite instructions.
    Strip fences, then fall back to grabbing the first balanced {...} block."""
    response = response.strip()

    if "```" in response:
        response = re.sub(r"```(?:json)?", "", response).strip()

    if response.startswith("{") and response.endswith("}"):
        return response

    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0) if match else response


def extract_project_state(transcript: str):

    empty_state = {
        "context_summary": "",
        "requirements": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],
        "deliverables": [],
        "timeline": ""
    }

    if not transcript or len(transcript.strip()) < 10:
        return empty_state

    prompt = f"""
{PROJECT_SCHEMA}

TRANSCRIPT:
{transcript}
"""

    try:
        response = generate_completion(prompt)
        cleaned = _extract_json_block(response)
        data = json.loads(cleaned)

        return {
            "context_summary": data.get("context_summary", ""),
            "requirements": data.get("requirements", []),
            "risks": data.get("risks", []),
            "assumptions": data.get("assumptions", []),
            "stakeholders": data.get("stakeholders", []),
            "deliverables": data.get("deliverables", []),
            "timeline": data.get("timeline", "")
        }

    except Exception as e:
        # NEVER crash pipeline
        return {
            **empty_state,
            "error": str(e)
        }