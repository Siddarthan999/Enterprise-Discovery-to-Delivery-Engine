from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.postgres import engine
from app.core.llm_router import generate_completion

router = APIRouter()


class SOWRequest(BaseModel):
    state: dict | None = None
    template_id: str | None = None


def get_latest_project_state():
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT project_name, state_json
                FROM project_states
                ORDER BY created_at DESC
                LIMIT 1
            """)
        ).mappings().first()

        return row


def build_sow_prompt(project_name: str, state: dict, template_id: str | None = None):

    return f"""
You are a senior management consultant from McKinsey & Company.

You are writing a CLIENT-READY, BOARDROOM-GRADE Statement of Work (SOW).

Your writing style MUST be:
- Narrative-driven (NOT bullet-heavy)
- Structured like a consulting deliverable
- Rich in explanation, reasoning, and context
- Formal, precise, and authoritative
- Designed for executive approval

DO NOT write like a checklist generator.

DO NOT produce short bullet points under every heading.

Instead:
- Use paragraphs as the primary format
- Use bullets ONLY when listing concrete items (max 1–2 per section)
- Each section should read like a mini-report

---

PROJECT NAME:
{project_name}

TEMPLATE ID (if any):
{template_id}

PROJECT STATE (discovery context):
{state}

---

OUTPUT RULES:

- Output MUST be valid Markdown
- Use headings (#, ##, ###)
- Each section MUST contain at least 2–5 well-formed paragraphs
- Avoid fragment sentences
- Avoid bullet points unless absolutely necessary
- No JSON
- No meta commentary

---

SOW STRUCTURE (MANDATORY):

# Statement of Work

## 1. Executive Summary
Write a compelling 2–3 paragraph executive narrative:
- Context of the engagement
- Why this project matters now
- Strategic value and expected transformation

## 2. Business Context & Problem Statement
Write a deep analytical narrative:
- Current challenges
- Business pain points
- Operational or technical gaps
- Impact on stakeholders

## 3. Scope of Work
Describe scope as a structured narrative:
- What is included (in flowing paragraphs)
- What is explicitly out of scope
Only use bullets if absolutely necessary.

## 4. Solution Overview
Explain the proposed solution like a consulting recommendation:
- Approach and methodology
- High-level architecture or delivery approach
- Key design principles

## 5. Detailed Requirements
Convert requirements into structured explanation:
- Functional expectations
- Technical expectations
- Integration considerations

## 6. Deliverables
Describe deliverables as outcomes, not items:
Example style:
"This engagement will produce a fully operational..."

## 7. Assumptions & Dependencies
Write in narrative form explaining constraints and dependencies.

## 8. Risks & Mitigation Strategy
Explain risks analytically:
- Risk description
- Business impact
- Mitigation approach

## 9. Timeline & Milestones
Describe phases as a story of execution:
- Phase-based delivery approach
- Do NOT use simple bullet lists of dates

## 10. Governance Model
Explain operating model:
- Stakeholders
- Communication cadence
- Decision-making framework

## 11. Acceptance Criteria
Define success criteria clearly in structured paragraphs.

---

FINAL QUALITY BAR:
- Must read like a McKinsey / BCG consulting document
- Must NOT feel like AI-generated bullet points
- Must be suitable for C-level stakeholders
"""


@router.post("/sow/generate")
def generate_sow(payload: SOWRequest):

    data = payload.state or get_latest_project_state()

    if not data:
        return {"error": "No project state found"}

    project_name = data.get("project_name", "Untitled Project")
    state = data.get("state_json", data)

    prompt = build_sow_prompt(project_name, state, payload.template_id)

    sow_text = generate_completion(prompt)

    return {
        "project_name": project_name,
        "sow": sow_text,
        "template_id": payload.template_id
    }