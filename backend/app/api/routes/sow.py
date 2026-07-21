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

# ---------------------------------------------------------------------------
# Section list now mirrors the target contract-style SOW (7 numbered sections
# + a legal preamble and signature block, which are not numbered sections in
# the source document and are handled separately below).
# ---------------------------------------------------------------------------
MANDATORY_SOW_SECTIONS = [
    "Contact Information",
    "Engagement Objectives & Scope",
    "Customer Obligations and Expectations",
    "Out-of-Scope & Change Orders",
    "Schedule and Fees",
    "Expenses",
    "Invoices",
]

# Bullet glyph used throughout section bodies, matching the source
# contract's bullet character rather than a markdown "-".
BULLET = "\u25cf"  # ●


class SOWRequest(BaseModel):
    state: dict | None = None
    template_id: str | None = None
    transcript: str | None = None


# ---------------------------------------------------------------------------
# Row models matching the new structure
# ---------------------------------------------------------------------------

class WorkstreamRow(BaseModel):
    """One named workstream under Engagement Objectives & Scope,
    e.g. 'Discovery and Alignment' -> its bullet points."""
    title: str = ""
    bullets: list[str] = Field(default_factory=list)


class ResourceRow(BaseModel):
    """One row of the Customer Resources table.

    NOTE: `role` must always hold a generic role/title (e.g. "Executive
    Sponsor"), never a person's name. The field used to be called `name`,
    which was ambiguous enough that the model would sometimes fill it with
    an actual attendee's name pulled from the transcript (e.g. "Michael
    Chen") instead of the role that person occupies. Renaming it removes
    that ambiguity at the schema level; see the explicit instruction in
    build_structured_sow_prompt() as well.
    """
    role: str = ""
    description: str = ""
    allocation_per_week: str = ""  # keep as string: values like "0.25" or "2" or "as required"


class StructuredSOW(BaseModel):
    # --- Legal preamble ---
    provider_legal_name: str = "TBD"
    agreement_reference: str = (
        "the Master Subscription Agreement, including the Professional Services Addendum"
    )

    # --- 1. Contact Information ---
    customer_legal_name: str = "TBD"
    customer_contact_name: str = "TBD"
    customer_contact_title: str = "TBD"
    customer_address: str = "TBD"
    customer_contact_email: str = "TBD"

    # --- 2. Engagement Objectives & Scope ---
    workstreams: list[WorkstreamRow] = Field(default_factory=list)

    # --- 3. Customer Obligations and Expectations ---
    scope_summary_bullets: list[str] = Field(default_factory=list)  # e.g. data volumes / boundaries
    obligation_bullets: list[str] = Field(default_factory=list)
    customer_resources: list[ResourceRow] = Field(default_factory=list)

    # --- 4. Out-of-Scope & Change Orders ---
    out_of_scope_change_control: str = ""

    # --- 5. Schedule and Fees ---
    duration: str = "TBD"
    fee_amount: str = "TBD"
    start_date: str = "TBD"
    end_date: str = "TBD"
    payment_terms: str = "Net 30"

    # --- 6. Expenses ---
    expenses_terms: str = (
        "Customer shall reimburse Provider for reasonable, pre-approved travel, lodging, "
        "communications, shipping, and other out-of-pocket expenses incurred in connection "
        "with providing the Services."
    )

    # --- 7. Invoices ---
    invoicing_terms: str = (
        "All Professional Services fees and applicable taxes will be invoiced upon SOW "
        "signature and are due in accordance with the terms of the Agreement."
    )

    # --- Signature block ---
    provider_signee_name: str = "TBD"
    provider_signee_title: str = "TBD"
    customer_signee_name: str = "TBD"
    customer_signee_title: str = "TBD"


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


def _strip_markdown_artifacts(text_value: str) -> str:
    """Defensive guard: strip any stray markdown headings the LLM may add
    despite instructions not to, so free-text fields can't inject duplicate
    section titles into the template merge step."""
    if not isinstance(text_value, str):
        return text_value
    text_value = re.sub(r"^#{1,6}\s*.*$", "", text_value, flags=re.MULTILINE)
    return text_value.strip()


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
        ("CUSTOMER ADDRESS", state.get("customer_address")),
        ("CUSTOMER CONTACT EMAIL", state.get("customer_contact_email")),
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
                line += f" \u2014 historically mitigated by: {mitigation}"
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
You are drafting a Professional Services Statement of Work in the style of a
legally-framed SaaS vendor SOW (similar in tone to a Notion / enterprise SaaS Professional
Services SOW), written with contract-grade precision \u2014 but each section should be
thorough and fully fleshed out, not a bare-bones skeleton. Write in complete sentences with
concrete detail pulled from the extracted state and transcript; avoid one-line filler
bullets. Where the input supports it, prefer 2\u20133 sentences of substantive detail per
bullet/point over a short phrase, while never inventing specifics the input doesn't support.

IMPORTANT:
- Do NOT write markdown.
- Do NOT write headings or section numbers.
- Do NOT restate section titles.
- Return ONLY valid JSON matching the requested schema.
- The DOCX template already contains the legal preamble, headings, numbering, tables,
  and signature block layout. Your job is to fill content fields only.

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
- Contact Information MUST reflect the actual customer legal entity name, primary contact
  name, title, address, and email as captured in the extracted state or transcript. If any
  of these were not captured, use "TBD" \u2014 do not fabricate a name, title, or address.
- Engagement Objectives & Scope MUST be organized into a small number of named workstreams
  (e.g. "Discovery and Alignment", a workstream for the core technical deliverable such as
  a migration or build, a workspace/governance workstream, a training/enablement workstream,
  and a handover/sustainment workstream) \u2014 mirror however many workstreams are actually
  supported by the extracted state; do not force a fixed count. Each workstream should have
  a short title and 4\u20138 bullets of concrete activity \u2014 each bullet should describe
  the activity, its purpose, and (where the input supports it) how it will be carried out,
  not a generic one-line filler phrase.
- Customer Obligations and Expectations MUST:
  - state any known scope boundaries (data volumes, system counts, environment counts) as
    scope_summary_bullets where the input provides them, elaborated with the concrete
    numbers/context captured rather than a bare label,
  - list concrete obligations (access provisioning, credentials, stakeholder availability,
    sign-off ownership, review of migration/config proposals) as obligation_bullets, with
    enough detail that a customer reading it knows exactly what is expected of them and by
    when, where the input supports that level of detail,
  - populate customer_resources with role-based staffing expectations (e.g. Executive
    Sponsor, Project Manager, IT/Dev resource, Subject Matter Experts, Change &
    Communications Lead). For each row: `role` MUST always be the generic role/title \u2014
    NEVER a specific person's name, even if the transcript names an individual for that
    role. If the transcript or state ties a named individual to a role, that person's name
    may be woven into the `description` (e.g. "Primary escalation point; currently
    [Name]."), but the `role` field itself must stay a title such as "Executive Sponsor" or
    "IT/Dev Resource". Give each row a substantive one-to-two sentence description of what
    the role is responsible for, and an estimated weekly allocation (e.g. "0.25", "2", "as
    required") only where the input supports an estimate \u2014 otherwise use "TBD".
- Out-of-Scope & Change Orders MUST be a fully developed paragraph (4\u20136 sentences)
  stating that work outside this SOW requires a signed Change Order, and explicitly
  enumerating whatever out-of-scope items were captured in state so the boundary is
  unambiguous, not just a boilerplate one-liner.
- Schedule and Fees MUST state duration, fee_amount, start_date, end_date, and
  payment_terms using only values present in the extracted state \u2014 use "TBD" for any
  that are missing. Do NOT invent a dollar amount or date.
- Expenses and Invoices MAY use standard boilerplate language unless the extracted state
  specifies different terms.

- agreement_reference should name the governing agreement only (e.g. "the Master
  Subscription Agreement, including the Professional Services Addendum"). Do NOT append
  "(the \u201cAgreement\u201d)" yourself \u2014 the template already adds that defined-term
  suffix once, and duplicating it here will produce "(the \u201cAgreement\u201d) (the
  \u201cAgreement\u201d)" in the final document.

PLACEHOLDER & SAFETY RULES:
- If commercial/legal/admin data is missing, use "TBD" rather than omitting fields.
- Do NOT invent names, monetary amounts, dates, SLAs, or legal clauses not present in the input.
- Do NOT wrap a missing/empty value in parentheses or any other fixed decorator \u2014 if a
  value is unknown, the field itself should just be "TBD".

Return ONLY valid JSON with this structure:
{{
  "provider_legal_name": "TBD",
  "agreement_reference": "the Master Subscription Agreement, including the Professional Services Addendum",
  "customer_legal_name": "TBD",
  "customer_contact_name": "TBD",
  "customer_contact_title": "TBD",
  "customer_address": "TBD",
  "customer_contact_email": "TBD",
  "workstreams": [
    {{"title": "", "bullets": [""]}}
  ],
  "scope_summary_bullets": [""],
  "obligation_bullets": [""],
  "customer_resources": [
    {{"role": "", "description": "", "allocation_per_week": "TBD"}}
  ],
  "out_of_scope_change_control": "",
  "duration": "TBD",
  "fee_amount": "TBD",
  "start_date": "TBD",
  "end_date": "TBD",
  "payment_terms": "Net 30",
  "expenses_terms": "",
  "invoicing_terms": "",
  "provider_signee_name": "TBD",
  "provider_signee_title": "TBD",
  "customer_signee_name": "TBD",
  "customer_signee_title": "TBD"
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
    sow = StructuredSOW(**parsed)

    # Defensive pass: strip any stray markdown the model injected into free-text
    # fields, so the template-merge step downstream can't end up with duplicated
    # headings sourced from model output.
    sow.out_of_scope_change_control = _strip_markdown_artifacts(sow.out_of_scope_change_control)
    sow.expenses_terms = _strip_markdown_artifacts(sow.expenses_terms)
    sow.invoicing_terms = _strip_markdown_artifacts(sow.invoicing_terms)
    for ws in sow.workstreams:
        ws.title = _strip_markdown_artifacts(ws.title)
        ws.bullets = [_strip_markdown_artifacts(b) for b in ws.bullets]

    return sow


def _fmt_optional(value: str, fallback: str = "TBD") -> str:
    """Render a value, or a clean fallback if empty \u2014 never a bare '()' or similar."""
    value = (value or "").strip()
    return value if value else fallback


def _fmt_cost(value: str, fallback: str = "TBD") -> str:
    """Render a fee amount with a single 'USD ' prefix, without double-prefixing
    if the model already included it, and without inventing a value."""
    value = (value or "").strip()
    if not value or value.upper() == "TBD":
        return fallback
    if value.upper().startswith("USD"):
        return value
    return f"USD {value}"


def _structured_sow_to_markdown(sow: StructuredSOW) -> str:
    lines = [
        f"This Statement of Work (\u201cSOW\u201d) is entered into by and between "
        f"{_fmt_optional(sow.provider_legal_name)} (\u201cProvider\u201d) and "
        f"{_fmt_optional(sow.customer_legal_name)} (\u201cCustomer\u201d), and is governed by "
        f"the terms and conditions of {sow.agreement_reference} (the \u201cAgreement\u201d). "
        "Capitalized terms used but not defined in this SOW will have the meaning assigned "
        "in the Agreement. This SOW will be deemed effective upon the date last signed by a "
        "party hereto (the \u201cEffective Date\u201d). In the event of a conflict between any "
        "terms of this SOW, the Agreement, or any order form for the Services, the terms of "
        "this SOW will control.",
        "",
        # "## " prefix routes this through the styles["h1"] heading branch in
        # template_engine.add_sow_content() instead of the numbered-list
        # branch (re.match(r"^\d+\.\s+", line)).
        "## 1. CONTACT INFORMATION",
        "",
        # Bold field labels ("**Label:** value") so the contact block reads
        # as a scannable form rather than a wall of plain text.
        f"**Customer Legal Name:** {_fmt_optional(sow.customer_legal_name)}",
        f"**Name:** {_fmt_optional(sow.customer_contact_name)}",
        f"**Title:** {_fmt_optional(sow.customer_contact_title)}",
        f"**Address:** {_fmt_optional(sow.customer_address)}",
        f"**Email:** {_fmt_optional(sow.customer_contact_email)}",
        "",
        "## 2. ENGAGEMENT OBJECTIVES & SCOPE",
        "",
    ]

    if sow.workstreams:
        for ws in sow.workstreams:
            # "### " routes this through styles["h2"] in template_engine, so
            # each workstream reads as a real sub-heading (distinct size +
            # spacing) instead of bold text sitting flush against its own
            # bullet list -- which is what made workstreams blend together
            # visually in the rendered document.
            lines.append(f"### {_fmt_optional(ws.title, 'Workstream')}")
            lines.append("")
            if ws.bullets:
                for b in ws.bullets:
                    lines.append(f"{BULLET} {b}")
            else:
                lines.append(f"{BULLET} Details to be confirmed during discovery.")
            lines.append("")
    else:
        lines.append(
            "The detailed engagement scope will be confirmed through discovery and reflected "
            "in the final execution copy of this SOW."
        )
        lines.append("")

    lines.extend(
        [
            "## 3. CUSTOMER OBLIGATIONS AND EXPECTATIONS",
            "",
        ]
    )
    if sow.scope_summary_bullets:
        for item in sow.scope_summary_bullets:
            lines.append(f"{BULLET} {item}")
    if sow.obligation_bullets:
        for item in sow.obligation_bullets:
            lines.append(f"{BULLET} {item}")
    if not sow.scope_summary_bullets and not sow.obligation_bullets:
        lines.append(
            "Customer obligations will be confirmed during discovery and reflected in the "
            "final execution copy of this SOW."
        )

    # "### " promotes this to a genuine sub-heading (styles["h2"]) instead of
    # a plain body line, and drops the stray trailing "/" left over from the
    # source PDF's two-column heading wrap.
    lines.extend(["", "### Customer Resources", ""])
    if sow.customer_resources:
        lines.append("| Role* | Description | Allocation per week |")
        lines.append("|---|---|---|")
        for row in sow.customer_resources:
            role = _fmt_optional(row.role, "TBD")
            desc = _fmt_optional(row.description, "TBD")
            alloc = _fmt_optional(row.allocation_per_week, "TBD")
            lines.append(f"| {role} | {desc} | {alloc} |")
        lines.append("")
        lines.append("*Roles do not need to be mutually exclusive")
    else:
        lines.append("Customer staffing expectations will be confirmed prior to kickoff.")

    lines.extend(
        [
            "",
            "## 4. OUT-OF-SCOPE & CHANGE ORDERS",
            "",
            sow.out_of_scope_change_control
            or "Any work not specifically set forth as Professional Services within this SOW "
            "is out of scope. Changes to the scope of this SOW require a fully executed "
            "Change Order signed by both parties.",
            "",
            "## 5. SCHEDULE AND FEES",
            "",
            "Subject to the terms herein, the Professional Services described in this SOW are "
            "bid on a fixed fee basis set forth below with the estimated duration post "
            "kick-off and engagement planning.",
            "",
            "### SUMMARY OF SCOPE OF SERVICES",
            "",
            f"**Duration:** {_fmt_optional(sow.duration)}",
            f"**Cost:** {_fmt_cost(sow.fee_amount)}",
            "",
            f"This engagement will commence with a scheduled start date of "
            f"{_fmt_optional(sow.start_date)}. The scheduled end date of this SOW is "
            f"{_fmt_optional(sow.end_date)}.",
            "",
            f"All Professional Services fees and taxes, if applicable, will be invoiced upon "
            f"SOW signature and shall be due and payable in accordance with the terms of the "
            f"Agreement ({_fmt_optional(sow.payment_terms, 'Net 30')}).",
            "",
            "## 6. EXPENSES",
            "",
            sow.expenses_terms,
            "",
            "## 7. INVOICES",
            "",
            sow.invoicing_terms,
            "",
            "### IN WITNESS WHEREOF, the parties have executed this SOW as of the Effective Date",
            "",
            f"**{_fmt_optional(sow.provider_legal_name)}**",
            f"**Name:** {_fmt_optional(sow.provider_signee_name)}",
            f"**Title:** {_fmt_optional(sow.provider_signee_title)}",
            "Date Signed:",
            "",
            f"**{_fmt_optional(sow.customer_legal_name)}**",
            f"**Name:** {_fmt_optional(sow.customer_signee_name)}",
            f"**Title:** {_fmt_optional(sow.customer_signee_title)}",
            "Date Signed:",
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