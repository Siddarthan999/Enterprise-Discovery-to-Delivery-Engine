import json
import re

from app.core.llm_router import generate_completion

RISK_EXTRACTION_PROMPT = """
You are analyzing a historical Statement of Work to extract its risk
management content for a precedent library. Real SOWs use inconsistent
section names for this (e.g. "Risks", "Risk Management", "Project Risks",
"Known Constraints & Risks") — look at the whole document's meaning, not
just a specific heading.

Extract every distinct risk that was called out, with its mitigation if
one was given.

Return ONLY valid JSON, no markdown fences, no other text:
{
  "risks": [
    {
      "risk_description": "<the risk itself, as a full sentence>",
      "mitigation_approach": "<the mitigation described, or empty string if none was given>",
      "category": "<one of: technical, compliance, timeline, vendor, resourcing, scope, financial, other>"
    }
  ]
}

If the document contains no identifiable risk content, return {"risks": []}.
Do not invent risks that aren't actually in the document.

DOCUMENT:
{content}
"""


def _extract_json_block(response: str) -> str:
    response = response.strip()
    if "```" in response:
        response = re.sub(r"```(?:json)?", "", response).strip()
    if response.startswith("{") and response.endswith("}"):
        return response
    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0) if match else response


def extract_risk_examples(content: str) -> list:
    """Returns a list of {risk_description, mitigation_approach, category}
    dicts. Never raises — a failed extraction just yields an empty list
    rather than blocking the historical SOW upload."""
    if not content or len(content.strip()) < 50:
        return []

    # Cap input size — a very long SOW doesn't need its full text for risk
    # extraction, and keeps this a cheap, fast call.
    truncated = content[:12000]

    prompt = RISK_EXTRACTION_PROMPT.replace("{content}", truncated)

    try:
        raw = generate_completion(prompt)
        parsed = json.loads(_extract_json_block(raw))
        risks = parsed.get("risks", [])
        if not isinstance(risks, list):
            return []

        cleaned = []
        for r in risks:
            if not isinstance(r, dict):
                continue
            desc = str(r.get("risk_description", "")).strip()
            if not desc:
                continue
            cleaned.append({
                "risk_description": desc,
                "mitigation_approach": str(r.get("mitigation_approach", "")).strip(),
                "category": str(r.get("category", "other")).strip().lower() or "other",
            })
        return cleaned

    except Exception:
        return []