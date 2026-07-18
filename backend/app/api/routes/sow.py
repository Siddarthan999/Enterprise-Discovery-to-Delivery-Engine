import json
import re

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.postgres import engine
from app.core.llm_router import generate_completion
from app.services.sow_history.sow_history_search import (
    search_similar_historical_risks,
    search_similar_historical_sows,
)
from app.services.sow_agents.sow_review_orchestrator import review_sow_draft
from app.services.sow_agents.sow_confidence import compute_sow_confidence

router = APIRouter()

MANDATORY_SOW_SECTIONS = [
    "Document Control",
    "Parties & Contact Information",
    "Executive Summary",
    "Business Context & Objectives",
    "Scope of Work",
    "Out of Scope",
    "Solution Overview & Delivery Approach",
    "Detailed Requirements",
    "Deliverables",
    "Timeline & Milestones",
    "Roles & Responsibilities",
    "Governance & Communication Model",
    "Assumptions & Dependencies",
    "Risks & Mitigation Strategy",
    "Commercials & Pricing",
    "Payment Terms & Invoicing",
    "Change Control",
    "Acceptance Criteria",
    "Confidentiality, Compliance & Data Handling",
    "Term & Termination",
    "Approvals & Sign-Off",
]


class SOWRequest(BaseModel):
    state: dict | None = None
    template_id: str | None = None
    transcript: str | None = None


class ContactRow(BaseModel):
    role: str = ""
    name: str = ""
    contact_details: str = ""


class PhaseRow(BaseModel):
    phase: str = ""
    description: str = ""


class DeliverableRow(BaseModel):
    identifier: str = ""
    description: str = ""
    due_timing: str = ""


class MeetingRow(BaseModel):
    meeting_type: str = ""
    frequency: str = ""
    attendees: str = ""


class RiskRow(BaseModel):
    risk: str = ""
    business_impact: str = ""
    mitigation_action: str = ""


class ApprovalRow(BaseModel):
    role: str = ""
    name: str = ""


class StructuredSOW(BaseModel):
    project_title: str = "Untitled Project"
    sow_reference: str = "TBD"
    effective_date: str = "TBD"
    template_reference: str = "Default Standard"
    agreement_relationship: str = "Subject to governing agreement between the parties."

    parties_contact_information: list[ContactRow] = Field(default_factory=list)

    executive_summary: str = ""
    business_context_objectives: str = ""
    scope_of_work: list[str] = Field(default_factory=list)
    out_of_scope: str = ""
    solution_overview_delivery_approach: str = ""
    phases: list[PhaseRow] = Field(default_factory=list)

    detailed_requirements: list[str] = Field(default_factory=list)
    preservation_requirement: str = ""

    deliverables: list[DeliverableRow] = Field(default_factory=list)

    client_responsibilities: list[str] = Field(default_factory=list)
    provider_responsibilities: list[str] = Field(default_factory=list)

    governance_communication_model: str = ""
    governance_meetings: list[MeetingRow] = Field(default_factory=list)

    assumptions_dependencies: list[str] = Field(default_factory=list)
    risks_mitigation: list[RiskRow] = Field(default_factory=list)
    historical_risk_note: str = ""

    commercial_model: str = "TBD"
    fee_structure: str = "TBD"

    payment_schedule: str = "TBD"
    invoice_format: str = "TBD"

    change_control_process: str = "TBD"

    acceptance_criteria_summary: str = ""
    acceptance_criteria_detail: str = "TBD"

    confidentiality_summary: str = ""
    data_handling_policies: str = "TBD"
    compliance_requirements: str = "TBD"

    term_termination_summary: str = ""
    commencement_completion_expectations: str = "TBD"

    client_approvals: list[ApprovalRow] = Field(default_factory=list)
    provider_approvals: list[ApprovalRow] = Field(default_factory=list)

    final_note: str = ""
    date_line: str = "TBD"
    location_line: str = "TBD"
    version_line: str = "1.0"


def get_latest_project_state():
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT project_name, state_json
                FROM project_states
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
        ).mappings().first()
        return row


def _extract_json_block(response: str) -> str:
    response = (response or "").strip()
    if "```" in response:
        response = re.sub(r"```(?:json)?", "", response).strip()
    if response.startswith("{") and response.endswith("}"):
        return response
    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0) if match else response


def _string_or_empty(value) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _list_or_empty(value) -> list:
    return value if isinstance(value, list) else []


def format_state_for_prompt(state: dict) -> str:
    def _list_block(label: str, items: list):
        if not items:
            return f"{label}: (none captured)"
        lines = "\n".join(f"  - {item}" for item in items)
        return f"{label}:\n{lines}"

    parts = []

    scalar_fields = [
        ("PROJECT NAME", state.get("project_name")),
        ("CLIENT NAME", state.get("client_name")),
        ("PROVIDER NAME", state.get("provider_name")),
        ("INDUSTRY", state.get("industry")),
        ("ENGAGEMENT TYPE", state.get("engagement_type")),
        ("MSA REFERENCE", state.get("msa_reference")),
        ("CONTEXT SUMMARY", state.get("context_summary")),
        ("TIMELINE", state.get("timeline")),
        ("PRICING", state.get("pricing")),
        ("PAYMENT TERMS", state.get("payment_terms")),
        ("BILLING SCHEDULE", state.get("billing_schedule")),
        ("CHANGE CONTROL", state.get("change_control")),
        ("LEGAL / COMPLIANCE", state.get("legal_terms")),
        ("DATA HANDLING", state.get("data_handling")),
        ("TERM", state.get("term")),
        ("TERMINATION", state.get("termination")),
    ]

    for label, value in scalar_fields:
        if _string_or_empty(value):
            parts.append(f"{label}:\n{value.strip()}")

    parts.append(_list_block("REQUIREMENTS", _list_or_empty(state.get("requirements"))))
    parts.append(_list_block("RISKS", _list_or_empty(state.get("risks"))))
    parts.append(_list_block("ASSUMPTIONS", _list_or_empty(state.get("assumptions"))))
    parts.append(_list_block("STAKEHOLDERS", _list_or_empty(state.get("stakeholders"))))
    parts.append(_list_block("DELIVERABLES", _list_or_empty(state.get("deliverables"))))
    parts.append(_list_block("CLIENT CONTACTS", _list_or_empty(state.get("client_contacts"))))
    parts.append(_list_block("PROVIDER CONTACTS", _list_or_empty(state.get("provider_contacts"))))
    parts.append(_list_block("CLIENT RESPONSIBILITIES", _list_or_empty(state.get("client_responsibilities"))))
    parts.append(_list_block("PROVIDER RESPONSIBILITIES", _list_or_empty(state.get("provider_responsibilities"))))
    parts.append(_list_block("APPROVERS", _list_or_empty(state.get("approvers"))))
    parts.append(_list_block("OUT OF SCOPE", _list_or_empty(state.get("out_of_scope"))))

    return "\n\n".join(parts)


def build_context_summary(state: dict) -> str:
    parts = []

    for key in [
        "project_name",
        "client_name",
        "provider_name",
        "industry",
        "engagement_type",
        "context_summary",
        "timeline",
        "pricing",
        "payment_terms",
        "billing_schedule",
        "change_control",
        "legal_terms",
        "data_handling",
        "term",
        "termination",
    ]:
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())

    for key in [
        "requirements",
        "risks",
        "assumptions",
        "stakeholders",
        "deliverables",
        "client_contacts",
        "provider_contacts",
        "client_responsibilities",
        "provider_responsibilities",
        "approvers",
        "out_of_scope",
    ]:
        value = state.get(key, [])
        if isinstance(value, list):
            parts.extend(str(v).strip() for v in value if str(v).strip())

    return "\n".join(parts).strip()


def format_historical_context(historical_sows: list, historical_risks: list) -> str:
    parts = []

    if historical_sows:
        excerpts = []
        for sow in historical_sows:
            title = sow.get("title", "Unknown")
            content = (sow.get("content") or "")[:800]
            excerpts.append(f"[{title}]\n{content}")
        parts.append(
            "PAST SOW EXCERPTS (use these for structure, tone, and how this organization frames commitments; do not copy text verbatim):\n"
            + "\n\n".join(excerpts)
        )

    if historical_risks:
        risk_lines = []
        for r in historical_risks:
            desc = r.get("risk_description", "")
            mitigation = r.get("mitigation_approach", "")
            category = r.get("category", "")
            line = f"- ({category}) {desc}"
            if mitigation:
                line += f" — historically mitigated by: {mitigation}"
            risk_lines.append(line)
        parts.append(
            "RISKS SEEN IN SIMILAR PAST ENGAGEMENTS (use only where plausibly relevant to this project):\n"
            + "\n".join(risk_lines)
        )

    return "\n\n".join(parts)


def build_structured_sow_prompt(
    project_name: str,
    state: dict,
    transcript: str | None,
    historical_sows: list,
    historical_risks: list,
    template_id: str | None = None,
) -> str:
    template_note = template_id or "default-standard"
    state_text = format_state_for_prompt(state)
    historical_context = format_historical_context(historical_sows, historical_risks)
    transcript_block = (
        f"\n\nORIGINAL DISCOVERY TRANSCRIPT (use this to enrich sections where the compressed state is thin):\n{transcript}"
        if transcript
        else ""
    )
    mandatory_list = "\n".join(f"- {s}" for s in MANDATORY_SOW_SECTIONS)

    return f"""
You are a senior engagement manager at a professional services firm (consulting / technology services).

You must produce rich, contract-ready content for a pre-formatted Statement of Work DOCX template.

IMPORTANT:
- Do NOT write markdown.
- Do NOT write headings or section numbers.
- Do NOT restate section titles.
- Return ONLY valid JSON matching the requested schema.
- The DOCX template already contains headings, numbering, tables, signature blocks, and boilerplate.
- Your job is to fill section content fields only.

PROJECT NAME:
{project_name}

TEMPLATE ID:
{template_note}

MANDATORY SOW SECTIONS:
{mandatory_list}

EXTRACTED PROJECT STATE:
{state_text}{transcript_block}

HISTORICAL CONTEXT:
{historical_context}

CONTENT QUALITY RULES:
- Executive Summary MUST be 2–4 well-developed paragraphs that:
  - explain why the engagement is happening now,
  - describe the business value of migrating from GitHub Enterprise Server to Cloud,
  - summarize the phases, key roles, and success conditions.
- Business Context & Objectives MUST:
  - describe current pain points with the on-prem GitHub Server (e.g., scalability, security, governance, collaboration),
  - explain strategic drivers for moving to GitHub Cloud,
  - define how success will be measured (e.g., stability, security posture, developer productivity).
- Scope of Work MUST:
  - distinguish discovery, planning, migration, validation, and stabilization activities,
  - avoid repeating the same sentence in different bullets,
  - clearly state inclusions and reference that exclusions are managed via change control.
- Out of Scope MUST:
  - explicitly list at least a few example items that are NOT included (e.g., application refactoring, tool replacements) where the input allows,
  - or clearly state that any work beyond the defined scope is subject to formal change control.
- Solution Overview & Delivery Approach MUST:
  - describe the methodology (assessment, wave planning, pilot, production migration, post-cutover support),
  - outline how rollout waves are structured,
  - explain rollback and contingency concepts at a high level.
- Detailed Requirements MUST:
  - organize expectations logically (e.g., inventory validation, integration coverage, access and authentication, compliance and auditability),
  - avoid duplicate statements.
- Deliverables MUST:
  - read like contract-grade statements, each describing what will be delivered and how completion will be recognized,
  - be linked to the phases (assessment, planning, pilot, migration, stabilization).
- Roles & Responsibilities MUST:
  - clearly separate client vs provider responsibilities,
  - assign client responsibilities such as providing access, data, approvals, and stakeholder alignment,
  - assign provider responsibilities such as detailed planning, execution of migrations, and risk management.
- Governance & Communication Model MUST:
  - describe who participates in which forums,
  - state the cadence (weekly, bi-weekly, etc.),
  - explain how decisions, escalations, and scope changes flow through governance.
- Assumptions & Dependencies MUST:
  - list at least 3–5 concrete assumptions and dependencies (e.g., access, stability of source systems, availability of key stakeholders),
  - link assumptions to risks where relevant.
- Risks & Mitigation Strategy MUST:
  - list at least 3–6 meaningful risks tailored to GitHub migration (inventory gaps, access issues, compliance, performance, user adoption),
  - describe the business impact in concrete terms,
  - include specific mitigation actions (e.g., backup and rollback plans, stakeholder engagement, incremental cutover) rather than generic phrases.
- Acceptance Criteria MUST:
  - describe how migrated repositories and integrations will be validated,
  - cover data integrity, access control, performance and compliance checks.

PLACEHOLDER & SAFETY RULES:
- If commercial/legal/admin data is missing, use "TBD" rather than omitting fields.
- Do NOT invent names, monetary amounts, dates, SLAs, or legal clauses not present in the input.
- If out-of-scope items were not explicitly captured, say so and tie changes to formal change control.
- If a governing agreement is referenced or implied but not identified, use: "Subject to governing agreement between the parties."

Return ONLY valid JSON with this structure:
{{
  "project_title": "Untitled Project",
  "sow_reference": "TBD",
  "effective_date": "TBD",
  "template_reference": "Default Standard",
  "agreement_relationship": "Subject to governing agreement between the parties.",
  "parties_contact_information": [
    {{"role": "", "name": "", "contact_details": ""}}
  ],
  "executive_summary": "",
  "business_context_objectives": "",
  "scope_of_work": [""],
  "out_of_scope": "",
  "solution_overview_delivery_approach": "",
  "phases": [
    {{"phase": "", "description": ""}}
  ],
  "detailed_requirements": [""],
  "preservation_requirement": "",
  "deliverables": [
    {{"identifier": "", "description": "", "due_timing": ""}}
  ],
  "client_responsibilities": [""],
  "provider_responsibilities": [""],
  "governance_communication_model": "",
  "governance_meetings": [
    {{"meeting_type": "", "frequency": "", "attendees": ""}}
  ],
  "assumptions_dependencies": [""],
  "risks_mitigation": [
    {{"risk": "", "business_impact": "", "mitigation_action": ""}}
  ],
  "historical_risk_note": "",
  "commercial_model": "TBD",
  "fee_structure": "TBD",
  "payment_schedule": "TBD",
  "invoice_format": "TBD",
  "change_control_process": "TBD",
  "acceptance_criteria_summary": "",
  "acceptance_criteria_detail": "TBD",
  "confidentiality_summary": "",
  "data_handling_policies": "TBD",
  "compliance_requirements": "TBD",
  "term_termination_summary": "",
  "commencement_completion_expectations": "TBD",
  "client_approvals": [
    {{"role": "", "name": ""}}
  ],
  "provider_approvals": [
    {{"role": "", "name": ""}}
  ],
  "final_note": "",
  "date_line": "TBD",
  "location_line": "TBD",
  "version_line": "1.0"
}}
"""


def generate_structured_sow(
    project_name: str,
    state: dict,
    transcript: str | None,
    historical_sows: list,
    historical_risks: list,
    template_id: str | None = None,
) -> StructuredSOW:
    prompt = build_structured_sow_prompt(
        project_name=project_name,
        state=state,
        transcript=transcript,
        historical_sows=historical_sows,
        historical_risks=historical_risks,
        template_id=template_id,
    )
    raw = generate_completion(prompt)
    parsed = json.loads(_extract_json_block(raw))
    return StructuredSOW(**parsed)


def _structured_sow_to_markdown(sow: StructuredSOW) -> str:
    lines = [
        "# Statement of Work",
        "",
        "## 1. Document Control",
        "",
        f"Project Title: {sow.project_title}",
        f"SOW Reference: {sow.sow_reference}",
        f"Effective Date: {sow.effective_date}",
        f"Template / Reference: {sow.template_reference}",
        f"Agreement Relationship: {sow.agreement_relationship}",
        "",
        "## 2. Parties & Contact Information",
        "",
    ]

    if sow.parties_contact_information:
        for row in sow.parties_contact_information:
            lines.append(f"{row.role}: {row.name} ({row.contact_details})")
    else:
        lines.append(
            "Key client and provider contacts will be confirmed and reflected in the final execution copy of this Statement of Work."
        )

    lines.extend(
        [
            "",
            "## 3. Executive Summary",
            "",
            sow.executive_summary,
            "",
            "## 4. Business Context & Objectives",
            "",
            sow.business_context_objectives,
            "",
            "## 5. Scope of Work",
            "",
            "This section describes the services and activities included in the engagement.",
            "",
        ]
    )
    if sow.scope_of_work:
        for item in sow.scope_of_work:
            lines.append(f"- {item}")
    else:
        lines.append(
            "The detailed scope of work will be confirmed through the agreed discovery and planning activities."
        )

    lines.extend(
        [
            "",
            "## 6. Out of Scope",
            "",
            sow.out_of_scope,
            "",
            "## 7. Solution Overview & Delivery Approach",
            "",
            sow.solution_overview_delivery_approach,
            "",
            "## 8. Detailed Requirements",
            "",
        ]
    )
    for item in sow.detailed_requirements:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 9. Deliverables",
            "",
        ]
    )
    for row in sow.deliverables:
        lines.append(f"- {row.identifier}: {row.description} ({row.due_timing})")

    lines.extend(
        [
            "",
            "## 10. Timeline & Milestones",
            "",
        ]
    )
    for row in sow.phases:
        lines.append(f"- {row.phase}: {row.description}")

    lines.extend(
        [
            "",
            "## 11. Roles & Responsibilities",
            "",
            "### Client Responsibilities",
            "",
        ]
    )
    if sow.client_responsibilities:
        for item in sow.client_responsibilities:
            lines.append(f"- {item}")
    else:
        lines.append(
            "Client responsibilities include providing timely access, approvals, and subject matter expertise required to deliver the engagement."
        )

    lines.extend(
        [
            "",
            "### Provider Responsibilities",
            "",
        ]
    )
    if sow.provider_responsibilities:
        for item in sow.provider_responsibilities:
            lines.append(f"- {item}")
    else:
        lines.append(
            "The provider will be responsible for delivering the agreed scope, managing project risks, and maintaining appropriate quality standards."
        )

    lines.extend(
        [
            "",
            "## 12. Governance & Communication Model",
            "",
            sow.governance_communication_model,
            "",
        ]
    )
    if sow.governance_meetings:
        lines.append("Key governance and communication forums include:")
        for row in sow.governance_meetings:
            lines.append(f"- {row.meeting_type}: {row.frequency} ({row.attendees})")

    lines.extend(
        [
            "",
            "## 13. Assumptions & Dependencies",
            "",
        ]
    )
    for item in sow.assumptions_dependencies:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 14. Risks & Mitigation Strategy",
            "",
        ]
    )
    for row in sow.risks_mitigation:
        lines.append(f"- {row.risk}: {row.business_impact}. Mitigation: {row.mitigation_action}")
    if sow.historical_risk_note:
        lines.extend(["", sow.historical_risk_note])

    lines.extend(
        [
            "",
            "## 15. Commercials & Pricing",
            "",
            f"Commercial Model: {sow.commercial_model}",
            f"Fee Structure: {sow.fee_structure}",
            "",
            "## 16. Payment Terms & Invoicing",
            "",
            f"Payment Schedule: {sow.payment_schedule}",
            f"Invoice Format: {sow.invoice_format}",
            "",
            "## 17. Change Control",
            "",
            sow.change_control_process,
            "",
            "## 18. Acceptance Criteria",
            "",
            sow.acceptance_criteria_summary,
            "",
            f"Detailed acceptance criteria: {sow.acceptance_criteria_detail}",
            "",
            "## 19. Confidentiality, Compliance & Data Handling",
            "",
            sow.confidentiality_summary,
            "",
            f"Data Handling Policies: {sow.data_handling_policies}",
            f"Compliance Requirements: {sow.compliance_requirements}",
            "",
            "## 20. Term & Termination",
            "",
            sow.term_termination_summary,
            "",
            f"Commencement / Completion Expectations: {sow.commencement_completion_expectations}",
            "",
            "## 21. Approvals & Sign-Off",
            "",
            "### Client Approvals",
            "",
        ]
    )
    if sow.client_approvals:
        for row in sow.client_approvals:
            lines.append(f"- {row.role}: {row.name}")
    else:
        lines.append("Client signatories will be confirmed prior to execution of this Statement of Work.")

    lines.extend(
        [
            "",
            "### Provider Approvals",
            "",
        ]
    )
    if sow.provider_approvals:
        for row in sow.provider_approvals:
            lines.append(f"- {row.role}: {row.name}")
    else:
        lines.append("Provider signatories will be confirmed prior to execution of this Statement of Work.")

    if sow.final_note:
        lines.extend(["", sow.final_note])

    lines.extend(
        [
            "",
            f"Date: {sow.date_line}",
            f"Location: {sow.location_line}",
            f"Version: {sow.version_line}",
        ]
    )

    return "\n".join(lines).strip()


@router.post("/sow/generate")
def generate_sow(payload: SOWRequest):
    data = payload.state or get_latest_project_state()

    if not data:
        return {"error": "No project state found"}

    project_name = data.get("project_name", "Untitled Project")
    state = data.get("state_json", data)

    if not isinstance(state, dict):
        return {"error": "Invalid project state format"}

    if state.get("error"):
        return {
            "error": f"Cannot generate SOW because discovery extraction failed: {state['error']}",
            "project_name": project_name,
            "state": state,
        }

    state.setdefault("project_name", project_name)

    context_summary = build_context_summary(state)
    historical_sows = search_similar_historical_sows(context_summary, limit=2)
    historical_risks = search_similar_historical_risks(context_summary, limit=4)

    structured_sow = generate_structured_sow(
        project_name=project_name,
        state=state,
        transcript=payload.transcript,
        historical_sows=historical_sows,
        historical_risks=historical_risks,
        template_id=payload.template_id,
    )

    review_markdown = _structured_sow_to_markdown(structured_sow)

    review = review_sow_draft(
        state=state,
        draft_markdown=review_markdown,
        historical_sows=historical_sows,
        historical_risks=historical_risks,
    )

    confidence = compute_sow_confidence(
        review_result=review,
        historical_sows=historical_sows,
        historical_risks=historical_risks,
        state=state,
        draft_markdown=review_markdown,
    )

    return {
        "project_name": project_name,
        "template_id": payload.template_id,
        "structured_sow": structured_sow.model_dump(),
        "sow": review_markdown,
        "historical_sows_used": [
            {
                "doc_id": s.get("doc_id"),
                "title": s.get("title"),
                "score": s.get("score"),
            }
            for s in historical_sows
        ],
        "historical_risks_considered": historical_risks,
        "review": review,
        "confidence": confidence,
    }