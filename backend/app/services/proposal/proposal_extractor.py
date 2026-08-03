import json
import re
from app.core.llm_router import generate_completion

PROPOSAL_SCHEMA = """
You are an enterprise Proposal Discovery Engine.
Your job is to extract structured proposal information from ALL supplied client context.

The input may include one or more of:
- Meeting transcripts
- Email conversations
- Notes
- RFPs / RFIs
- Prior proposals or SOWs
- Other enterprise documents

Treat every uploaded document as equally important.

Your response MUST be ONLY a single valid JSON object.
Do NOT return markdown.
Do NOT return explanations.
Do NOT wrap the JSON inside ```.
The first character MUST be {
The last character MUST be }

Return this JSON:
{
  "client_name": "",
  "industry": "",
  "business_context": "",
  "current_landscape": [],
  "business_challenges": [],
  "strategic_goals": [],
  "project_objectives": [],
  "success_metrics": [],
  "proposed_solution": "",
  "solution_components": [],
  "delivery_approach": "",
  "technologies": [],
  "integration_requirements": [],
  "risks": [],
  "stakeholders": [],
  "in_scope": [],
  "out_of_scope": [],
  "deliverables": [],
  "timeline": [],
  "commercial_information": "",
  "assumptions": [],
  "dependencies": [],
  "next_steps": []
}

Field guidance:
- current_landscape: specific facts about the client's EXISTING tools, systems, processes, or
  ways of working today (e.g. "Incident data is tracked manually in spreadsheets"). This is
  the "as-is" state, distinct from business_challenges (the pain caused by that state).
- strategic_goals: the client's high-level business/organisational priorities this project
  should serve (e.g. "Reduce regulatory risk", "Improve customer trust") — distinct from
  project_objectives, which are the specific outcomes of THIS engagement.
- success_metrics: any KPIs, targets, or measures of success explicitly discussed (e.g.
  "Reduce mean time to resolution by 20%"). Leave empty if none were discussed — do not invent
  targets.
- solution_components: distinct named parts/modules of the proposed solution, each as a short
  phrase (e.g. "Centralised configuration database", "Automated intake workflow") — only
  include what was actually discussed, not a generic breakdown.
- integration_requirements: specific systems, platforms, or data sources the solution needs to
  connect with, if mentioned.
- risks: risks to the PROJECT or engagement itself that were explicitly raised (e.g. "Data
  migration from the legacy system is a known unknown"), distinct from assumptions/dependencies.
- stakeholders: named roles or individuals with a stake in the outcome, if mentioned.

Extraction priority (highest first):
1. Client name
2. Industry
3. Business context
4. Current landscape
5. Business challenges
6. Strategic goals
7. Project objectives
8. Success metrics
9. Proposed solution
10. Solution components
11. Delivery approach
12. Technologies
13. Integration requirements
14. Risks
15. Stakeholders
16. In-scope items
17. Out-of-scope items
18. Deliverables
19. Timeline
20. Commercial information
21. Assumptions
22. Dependencies
23. Next steps

Rules:
- NEVER invent information.
- Use information from ANY uploaded file.
- If a value does not exist, return an empty string.
- If a list has no entries, return [].
- Arrays should contain complete sentences wherever practical.
- "timeline" is an array of short phase/milestone strings (e.g. "Phase 1 - Discovery: 2 weeks"), not a single paragraph.
"""


def _extract_json_block(response: str) -> str:
    response = (response or "").strip()
    if not response:
        return ""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    if response.startswith("{") and response.endswith("}"):
        return response
    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0).strip() if match else ""


def _repair_to_json(raw: str) -> str:
    prompt = f"""
You previously summarized the transcript as follows:

{raw}

This response does NOT follow the required JSON-only format.
You MUST now convert this into a single valid JSON object that matches the schema described below.

{PROPOSAL_SCHEMA}

Return ONLY the JSON object. No headings, no markdown, no bullet points, no extra text.
The first character of your response MUST be "{{" and the last character MUST be "}}".
"""
    return generate_completion(prompt)


def extract_proposal_state(transcript: str):
    empty_state = {
        "client_name": "",
        "industry": "",
        "business_context": "",
        "current_landscape": [],
        "business_challenges": [],
        "strategic_goals": [],
        "project_objectives": [],
        "success_metrics": [],
        "proposed_solution": "",
        "solution_components": [],
        "delivery_approach": "",
        "technologies": [],
        "integration_requirements": [],
        "risks": [],
        "stakeholders": [],
        "in_scope": [],
        "out_of_scope": [],
        "deliverables": [],
        "timeline": [],
        "commercial_information": "",
        "assumptions": [],
        "dependencies": [],
        "next_steps": [],
    }

    if not transcript or len(transcript.strip()) < 10:
        return empty_state

    prompt = f"""
{PROPOSAL_SCHEMA}

TRANSCRIPT:
{transcript}
"""

    response = ""
    try:
        response = generate_completion(prompt)
        if not response or not response.strip():
            raise ValueError("LLM returned empty response")

        cleaned = _extract_json_block(response)
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
            "client_name": as_str("client_name"),
            "industry": as_str("industry"),
            "business_context": as_str("business_context"),
            "current_landscape": as_list("current_landscape"),
            "business_challenges": as_list("business_challenges"),
            "strategic_goals": as_list("strategic_goals"),
            "project_objectives": as_list("project_objectives"),
            "success_metrics": as_list("success_metrics"),
            "proposed_solution": as_str("proposed_solution"),
            "solution_components": as_list("solution_components"),
            "delivery_approach": as_str("delivery_approach"),
            "technologies": as_list("technologies"),
            "integration_requirements": as_list("integration_requirements"),
            "risks": as_list("risks"),
            "stakeholders": as_list("stakeholders"),
            "in_scope": as_list("in_scope"),
            "out_of_scope": as_list("out_of_scope"),
            "deliverables": as_list("deliverables"),
            "timeline": as_list("timeline"),
            "commercial_information": as_str("commercial_information"),
            "assumptions": as_list("assumptions"),
            "dependencies": as_list("dependencies"),
            "next_steps": as_list("next_steps"),
        }
    except Exception as e:
        return {
            **empty_state,
            "error": str(e),
            "raw_response": response[:2000] if response else "",
        }