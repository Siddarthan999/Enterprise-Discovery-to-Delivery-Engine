import json
import re
import io
import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.llm_router import generate_completion
from app.services.proposal.proposal_extractor import extract_proposal_state
from app.services.proposal.save_proposal import save_generated_proposal
from app.services.proposal.company_profile import COMPANY_PROFILE
from app.services.sow.project_state_service import save_project_state
from fastapi.responses import StreamingResponse
from app.services.sow.template_storage import load_templates, TEMPLATE_DIR
from app.services.proposal.pptx_generator import generate_proposal_pptx
from app.services.proposal.proposal_visuals import generate_solution_diagram, generate_approach_diagram

router = APIRouter(tags=["proposal"])

BULLET = "\u25cf"  # ●


# ---------------------------------------------------------------------------
# Extraction (unchanged endpoint — extractor itself now captures more)
# ---------------------------------------------------------------------------
class ProposalDiscoveryRequest(BaseModel):
    title: str = "Discovery Session"
    transcript: str


class ProposalPptxExportRequest(BaseModel):
    structured_proposal: dict
    template_id: str


@router.post("/proposal/extract")
def proposal_discovery(payload: ProposalDiscoveryRequest):
    transcript = (payload.transcript or "").strip()
    if not transcript:
        return {"error": "Transcript is empty", "state": None}

    state = extract_proposal_state(transcript)
    if not isinstance(state, dict):
        return {"error": "Proposal extraction returned invalid state", "state": None}

    if state.get("error"):
        return {
            "title": payload.title,
            "error": f"Proposal extraction failed: {state['error']}",
            "state": state,
        }

    save_project_state(payload.title, state)
    return {"title": payload.title, "state": state}


# ---------------------------------------------------------------------------
# Generation — significantly deeper structured output
# ---------------------------------------------------------------------------
class ProposalRequest(BaseModel):
    state: dict | None = None
    transcript: str | None = None
    author_id: int | None = None
    title: str | None = None


class ApproachPhase(BaseModel):
    title: str = ""
    objective: str = ""
    narrative: str = ""
    indicative_activities: list[str] = Field(default_factory=list)


class SolutionComponent(BaseModel):
    name: str = ""
    description: str = ""


class RiskItem(BaseModel):
    risk: str = ""
    mitigation: str = ""


class CommercialOption(BaseModel):
    name: str = ""
    description: str = ""


class TeamRole(BaseModel):
    role: str = ""
    description: str = ""


class StructuredProposal(BaseModel):
    proposal_title: str = "Proposal"

    executive_summary: str = ""

    current_landscape_intro: str = ""
    current_landscape_points: list[str] = Field(default_factory=list)

    what_weve_heard_intro: str = ""
    what_weve_heard_themes: list[str] = Field(default_factory=list)

    strategic_goals: list[str] = Field(default_factory=list)
    target_outcomes: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)

    solution_overview: str = ""
    solution_components: list[SolutionComponent] = Field(default_factory=list)

    approach_phases: list[ApproachPhase] = Field(default_factory=list)

    change_management_narrative: str = ""
    risk_items: list[RiskItem] = Field(default_factory=list)

    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)

    commercial_narrative: str = ""
    commercial_options: list[CommercialOption] = Field(default_factory=list)
    team_roles: list[TeamRole] = Field(default_factory=list)

    why_this_approach: str = ""
    next_steps: list[str] = Field(default_factory=list)


def _extract_json_block(response: str) -> str:
    response = (response or "").strip()
    if "```" in response:
        response = re.sub(r"```(?:json)?", "", response).strip()
    if response.startswith("{") and response.endswith("}"):
        return response
    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0) if match else response


def _strip_markdown_artifacts(value: str) -> str:
    if not isinstance(value, str):
        return value
    value = re.sub(r"^#{1,6}\s*.*$", "", value, flags=re.MULTILINE)
    return value.strip()


def _format_state_for_prompt(state: dict) -> str:
    def _list_block(label: str, items: list):
        if not items:
            return f"{label}: (none captured)"
        lines = "\n".join(f"  - {item}" for item in items)
        return f"{label}:\n{lines}"

    def _str_block(label: str, value):
        value = (value or "").strip() if isinstance(value, str) else ""
        return f"{label}:\n{value}" if value else f"{label}: (none captured)"

    parts = [
        _str_block("CLIENT NAME", state.get("client_name")),
        _str_block("INDUSTRY", state.get("industry")),
        _str_block("BUSINESS CONTEXT", state.get("business_context")),
        _list_block("CURRENT LANDSCAPE (AS-IS STATE)", state.get("current_landscape", [])),
        _list_block("BUSINESS CHALLENGES", state.get("business_challenges", [])),
        _list_block("STRATEGIC GOALS", state.get("strategic_goals", [])),
        _list_block("PROJECT OBJECTIVES", state.get("project_objectives", [])),
        _list_block("SUCCESS METRICS", state.get("success_metrics", [])),
        _str_block("PROPOSED SOLUTION", state.get("proposed_solution")),
        _list_block("SOLUTION COMPONENTS", state.get("solution_components", [])),
        _str_block("DELIVERY APPROACH", state.get("delivery_approach")),
        _list_block("TECHNOLOGIES", state.get("technologies", [])),
        _list_block("INTEGRATION REQUIREMENTS", state.get("integration_requirements", [])),
        _list_block("RISKS", state.get("risks", [])),
        _list_block("STAKEHOLDERS", state.get("stakeholders", [])),
        _list_block("IN SCOPE", state.get("in_scope", [])),
        _list_block("OUT OF SCOPE", state.get("out_of_scope", [])),
        _list_block("DELIVERABLES", state.get("deliverables", [])),
        _list_block("TIMELINE", state.get("timeline", [])),
        _str_block("COMMERCIAL INFORMATION", state.get("commercial_information")),
        _list_block("ASSUMPTIONS", state.get("assumptions", [])),
        _list_block("DEPENDENCIES", state.get("dependencies", [])),
        _list_block("NEXT STEPS", state.get("next_steps", [])),
    ]
    return "\n\n".join(parts)


def build_structured_proposal_prompt(state: dict, transcript: str | None) -> str:
    state_text = _format_state_for_prompt(state)
    transcript_block = (
        f"\n\nORIGINAL DISCOVERY TRANSCRIPT (use this to enrich sections where the extracted "
        f"state is thin \u2014 do not invent anything not supported by it):\n{transcript}"
        if transcript
        else ""
    )

    return f"""
You are a senior consulting proposal writer producing a HIGH-LEVEL SOLUTION PROPOSAL —
the kind of document a consulting firm sends a prospective client: thorough, structured,
and written with the depth of a real solution architecture and delivery plan, not a brief
summary memo. Every section should read like an experienced consultant explaining their
thinking to a client's leadership team, with real elaboration and reasoning — not a bullet
dump of the extracted facts.

IMPORTANT:
- Do NOT write markdown, headings, or section numbers \u2014 the caller renders those.
- Do NOT copy extracted bullets verbatim \u2014 rewrite every point as a full sentence (or a
  short paragraph where useful) that explains the "so what", not just the "what".
- Return ONLY valid JSON matching the requested schema below.
- NEVER invent client facts, numbers, dates, headcounts, tool names, or commercial terms
  that are not present in the extracted state or transcript. Where something isn't captured,
  write in general/qualitative terms instead of a fabricated specific.
- NEVER invent your own company's credentials, certifications, awards, or case studies —
  that content is added separately and is out of scope for you to write.
- Where the extracted state genuinely contains very little for a section, it is fine for
  that section to be shorter, or for a list field to come back empty \u2014 do not pad with
  invented specifics.

EXTRACTED PROJECT STATE (the ONLY source of client-specific facts you may use):
{state_text}{transcript_block}

WRITING GUIDANCE PER SECTION:

- executive_summary: 3\u20135 sentences. Frame the client's situation (business_context,
  industry), the strategic stakes (why this matters now), and at a high level what's being
  proposed (proposed_solution) \u2014 a narrative opening, not a list.

- current_landscape_intro: 1\u20132 sentences introducing the client's as-is operating
  environment, based on current_landscape and business_context.
- current_landscape_points: turn each current_landscape item into a fully-written point
  (1\u20133 sentences) explaining what exists today AND why it matters for this engagement.
  If current_landscape is empty, return an empty list \u2014 do not invent the client's tooling.

- what_weve_heard_intro / what_weve_heard_themes: as before \u2014 turn each
  business_challenge into a fully-written theme with the "why this matters" framing, 1\u20133
  sentences each.

- strategic_goals: rewrite each captured strategic_goal as a full sentence connecting it to
  why it matters to the client's leadership. Empty list if none were captured.
- target_outcomes: turn each project_objective into an outcome statement from the client's
  point of view, 1\u20132 sentences each.
- success_metrics: rewrite each captured success_metric as a clear, concrete statement. Empty
  list if none were captured \u2014 do not invent KPI targets.

- solution_overview: 2\u20133 sentences framing the overall shape of the proposed solution
  (proposed_solution + delivery_approach + technologies), before the component breakdown.
- solution_components: one entry per solution_component captured (or, if none were captured
  as discrete components but proposed_solution/technologies clearly implies a few, you may
  group proposed_solution into 2\u20134 logical components) \u2014 each with a short name and a
  2\u20133 sentence description of what it does and why it's included, grounded only in
  proposed_solution/technologies/integration_requirements.

- approach_phases: derive 3\u20135 logical phases from delivery_approach and timeline. Each
  phase needs: a short title; a one-sentence objective (in the style "To align X with Y,
  defining Z" \u2014 outcome-oriented, not a activity list); a 1\u20132 sentence narrative giving
  additional context; and 3\u20136 indicative_activities as full sentences grounded in
  proposed_solution/technologies/deliverables/integration_requirements. If timeline data is
  sparse, phase the approach logically based on delivery_approach alone.

- change_management_narrative: 2\u20134 sentences on how change/adoption will be managed for
  THIS client specifically, grounded in business_challenges/stakeholders/assumptions. If
  nothing specific was captured, a brief general statement is fine (this is supplemented by
  a standard methodology section added separately) \u2014 do not invent specifics.

- risk_items: one entry per captured risk, each with the risk restated clearly and, only if
  a mitigation was actually discussed or is a direct logical consequence of the proposed
  solution, a mitigation sentence \u2014 otherwise leave mitigation as an empty string. Empty
  list if no risks were captured.

- in_scope / out_of_scope / deliverables: rewrite each captured item as a complete, specific
  sentence. Do not add items that weren't captured.

- commercial_narrative: 2\u20133 sentences framing the commercial approach based on
  commercial_information and dependencies. If commercial_information is empty, say pricing
  will be confirmed once scope is finalised.
- commercial_options / team_roles: only populate if the state clearly supports it; otherwise
  empty list.

- why_this_approach: 2\u20133 sentences explaining why this approach fits this client's
  situation specifically, grounded in business_context/business_challenges/strategic_goals
  \u2014 not generic marketing copy, and without naming any consulting firm/brand.

- next_steps: rewrite each captured next_step as a clear, actionable full sentence, folding
  in any unreflected dependencies as next steps where relevant.

- proposal_title: "{state.get('client_name') or 'Client'} \u2014 Proposal" unless a more
  specific project/engagement name is implied by the state.

Return ONLY valid JSON with this structure:
{{
  "proposal_title": "",
  "executive_summary": "",
  "current_landscape_intro": "",
  "current_landscape_points": [""],
  "what_weve_heard_intro": "",
  "what_weve_heard_themes": [""],
  "strategic_goals": [""],
  "target_outcomes": [""],
  "success_metrics": [""],
  "solution_overview": "",
  "solution_components": [
    {{"name": "", "description": ""}}
  ],
  "approach_phases": [
    {{"title": "", "objective": "", "narrative": "", "indicative_activities": [""]}}
  ],
  "change_management_narrative": "",
  "risk_items": [
    {{"risk": "", "mitigation": ""}}
  ],
  "in_scope": [""],
  "out_of_scope": [""],
  "deliverables": [""],
  "commercial_narrative": "",
  "commercial_options": [
    {{"name": "", "description": ""}}
  ],
  "team_roles": [
    {{"role": "", "description": ""}}
  ],
  "why_this_approach": "",
  "next_steps": [""]
}}
"""


def generate_structured_proposal(state: dict, transcript: str | None) -> StructuredProposal:
    prompt = build_structured_proposal_prompt(state, transcript)
    raw = generate_completion(prompt)
    parsed = json.loads(_extract_json_block(raw))
    proposal = StructuredProposal(**parsed)

    proposal.executive_summary = _strip_markdown_artifacts(proposal.executive_summary)
    proposal.current_landscape_intro = _strip_markdown_artifacts(proposal.current_landscape_intro)
    proposal.what_weve_heard_intro = _strip_markdown_artifacts(proposal.what_weve_heard_intro)
    proposal.solution_overview = _strip_markdown_artifacts(proposal.solution_overview)
    proposal.change_management_narrative = _strip_markdown_artifacts(proposal.change_management_narrative)
    proposal.commercial_narrative = _strip_markdown_artifacts(proposal.commercial_narrative)
    proposal.why_this_approach = _strip_markdown_artifacts(proposal.why_this_approach)
    for phase in proposal.approach_phases:
        phase.title = _strip_markdown_artifacts(phase.title)
        phase.objective = _strip_markdown_artifacts(phase.objective)
        phase.narrative = _strip_markdown_artifacts(phase.narrative)
        phase.indicative_activities = [_strip_markdown_artifacts(a) for a in phase.indicative_activities]

    return proposal


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"{BULLET} {item}" for item in items]


def _structured_proposal_to_markdown(proposal, solution_diagram_path=None, approach_diagram_path=None):
    lines: list[str] = [
        "## EXECUTIVE SUMMARY",
        "",
        proposal.executive_summary or "Executive summary to be confirmed during discovery.",
        "",
    ]

    # --- About Us (static company profile) ---
    lines.extend(["## ABOUT " + COMPANY_PROFILE["company_name"].upper(), ""])
    lines.append(COMPANY_PROFILE["about_us"])
    if COMPANY_PROFILE.get("key_differentiators"):
        lines.extend(["", "**Key differentiators:**", ""])
        lines.extend(_bullets(COMPANY_PROFILE["key_differentiators"]))
    if COMPANY_PROFILE.get("credentials"):
        lines.extend(["", "**Credentials and recognition:**", ""])
        lines.extend(_bullets(COMPANY_PROFILE["credentials"]))

    # --- Our Understanding ---
    lines.extend(["", "## OUR UNDERSTANDING", ""])
    if proposal.current_landscape_intro or proposal.current_landscape_points:
        lines.append("### Current Landscape")
        lines.append("")
        if proposal.current_landscape_intro:
            lines.append(proposal.current_landscape_intro)
            lines.append("")
        lines.extend(_bullets(proposal.current_landscape_points) or [
            f"{BULLET} Current landscape to be confirmed during discovery."
        ])
        lines.append("")

    lines.append("### What We've Heard")
    lines.append("")
    if proposal.what_weve_heard_intro:
        lines.append(proposal.what_weve_heard_intro)
        lines.append("")
    lines.extend(_bullets(proposal.what_weve_heard_themes) or [
        f"{BULLET} Key themes to be confirmed during discovery."
    ])

    if proposal.strategic_goals:
        lines.extend(["", "### Strategic Goals", ""])
        lines.extend(_bullets(proposal.strategic_goals))

    lines.extend(["", "## TARGET OUTCOMES", ""])
    lines.extend(_bullets(proposal.target_outcomes) or [
        f"{BULLET} Target outcomes to be confirmed during discovery."
    ])
    if proposal.success_metrics:
        lines.extend(["", "**How we'll measure success:**", ""])
        lines.extend(_bullets(proposal.success_metrics))

    # --- Proposed Solution ---
    lines.extend(["", "## PROPOSED SOLUTION", ""])
    lines.append(proposal.solution_overview or "Solution overview to be confirmed during discovery.")
    if solution_diagram_path:
        lines.extend(["", f"![Solution Overview Diagram]({solution_diagram_path})", ""])
    if proposal.solution_components:
        lines.extend(["", "### Core Solution Components", ""])
        for comp in proposal.solution_components:
            name = comp.name or "Component"
            desc = comp.description or ""
            lines.append(f"{BULLET} **{name}** \u2014 {desc}" if desc else f"{BULLET} **{name}**")

    # --- Delivery Approach ---
    lines.extend(["", "## DELIVERY APPROACH", ""])
    if COMPANY_PROFILE.get("delivery_methodology_summary"):
        lines.append(
            f"Delivered using our {COMPANY_PROFILE.get('delivery_methodology_name', 'delivery')} "
            f"methodology: {COMPANY_PROFILE['delivery_methodology_summary']}"
        )
        lines.append("")
    if approach_diagram_path:
        lines.extend(["", f"![Delivery Approach Roadmap]({approach_diagram_path})", ""])
    if proposal.approach_phases:
        for i, phase in enumerate(proposal.approach_phases, start=1):
            title = phase.title or f"Phase {i}"
            lines.append(f"### Phase {i} \u2014 {title}")
            lines.append("")
            if phase.objective:
                lines.append(f"**Objective:** {phase.objective}")
                lines.append("")
            if phase.narrative:
                lines.append(phase.narrative)
                lines.append("")
            if phase.indicative_activities:
                lines.append("**Key activities:**")
                lines.append("")
                lines.extend(_bullets(phase.indicative_activities))
            lines.append("")
    else:
        lines.append("The phased approach will be confirmed during discovery.")
        lines.append("")

    # --- Change Management ---
    lines.extend(["## CHANGE MANAGEMENT APPROACH", ""])
    if proposal.change_management_narrative:
        lines.append(proposal.change_management_narrative)
        lines.append("")
    if COMPANY_PROFILE.get("change_management_principles"):
        lines.append("**Our approach is built around:**")
        lines.append("")
        lines.extend(_bullets(COMPANY_PROFILE["change_management_principles"]))

    # --- Risk Management ---
    lines.extend(["", "## RISK MANAGEMENT APPROACH", ""])
    if COMPANY_PROFILE.get("risk_management_principles"):
        lines.append("Risk is managed systematically across the engagement, including:")
        lines.append("")
        lines.extend(_bullets(COMPANY_PROFILE["risk_management_principles"]))
    if proposal.risk_items:
        lines.extend(["", "**Risks identified for this engagement:**", ""])
        for item in proposal.risk_items:
            risk = item.risk or ""
            mitigation = item.mitigation or ""
            if not risk:
                continue
            lines.append(f"{BULLET} {risk}" + (f" \u2014 *Mitigation:* {mitigation}" if mitigation else ""))

    # --- Scope ---
    lines.extend(["", "## SCOPE SUMMARY", "", "### In Scope", ""])
    lines.extend(_bullets(proposal.in_scope) or [f"{BULLET} To be confirmed during discovery."])
    lines.extend(["", "### Out of Scope", ""])
    lines.extend(_bullets(proposal.out_of_scope) or [f"{BULLET} To be confirmed during discovery."])

    lines.extend(["", "## DELIVERABLES", ""])
    lines.extend(_bullets(proposal.deliverables) or [f"{BULLET} To be confirmed during discovery."])

    # --- Team and Commercial ---
    lines.extend(["", "## TEAM AND COMMERCIAL APPROACH", ""])
    lines.append(proposal.commercial_narrative or "Commercial terms to be confirmed once scope is finalised.")
    if proposal.commercial_options:
        lines.append("")
        for opt in proposal.commercial_options:
            name = opt.name or "Option"
            desc = opt.description or ""
            lines.append(f"{BULLET} **{name}** \u2014 {desc}" if desc else f"{BULLET} **{name}**")
    if proposal.team_roles:
        lines.append("")
        lines.append("**Indicative roles:**")
        lines.append("")
        for role in proposal.team_roles:
            r = role.role or "Role"
            d = role.description or ""
            lines.append(f"{BULLET} **{r}** \u2014 {d}" if d else f"{BULLET} **{r}**")

    lines.extend(["", "## WHY THIS APPROACH", ""])
    lines.append(proposal.why_this_approach or "Rationale to be confirmed during discovery.")

    def _section_content(label, content):
        if isinstance(content, list):
            lines.append(f"**{label}:**")
            lines.append("")
            lines.extend(_bullets(content))
        elif content:
            # Convert concatenated sentences into bullets when multiple points exist
            points = [p.strip() for p in content.split(".") if p.strip()]

            if len(points) > 1:
                lines.append(f"**{label}:**")
                lines.append("")
                lines.extend(_bullets([f"{p}." for p in points]))
            else:
                lines.append(f"**{label}:** {content}")

    # --- Case studies (static) ---
    if COMPANY_PROFILE.get("case_studies"):
        lines.extend(["", "## REFERENCES AND CASE STUDIES", ""])
        for idx, cs in enumerate(COMPANY_PROFILE["case_studies"], start=1):
            client = cs.get("client", "Client")
            lines.append(f"### Client {idx}: {client}")
            lines.append("")

            if cs.get("challenge"):
                _section_content("Key Challenges", cs["challenge"])

            if cs.get("solution"):
                _section_content("Solutions", cs["solution"])

            if cs.get("outcome"):
                _section_content("Key Outcomes", cs["outcome"])

            if cs.get("testimonial"):
                lines.append(f"**Client Testimonial:** {cs['testimonial']}")

            lines.append("")

    lines.extend(["## RECOMMENDED NEXT STEPS", ""])
    lines.extend(_bullets(proposal.next_steps) or [f"{BULLET} Next steps to be confirmed."])

    # --- Contact details (static) ---
    contact = COMPANY_PROFILE.get("contact_details") or {}
    if contact:
        lines.extend(["", "## CONTACT DETAILS", ""])
        lines.append("| | |")
        lines.append("|---|---|")

        if contact.get("name"):
            lines.append(f"| **Name of Offeror's Organisation** | {contact['name']} |")
        if contact.get("address"):
            lines.append(f"| **Address** | {contact['address']} |")
        if contact.get("phone"):
            lines.append(f"| **Telephone Number** | {contact['phone']} |")
        if contact.get("email"):
            lines.append(f"| **Email Address** | {contact['email']} |")
        if contact.get("website"):
            lines.append(f"| **Website** | {contact['website']} |")
        if contact.get("date"):
            lines.append(f"| **Date of Submission** | {contact['date']} |")

    return "\n".join(lines).strip()


@router.post("/proposal/generate")
def generate_proposal(payload: ProposalRequest):
    state = payload.state
    if not state or not isinstance(state, dict):
        return {"error": "No proposal state found"}
    if state.get("error"):
        return {
            "error": f"Cannot generate Proposal because discovery extraction failed: {state['error']}",
            "state": state,
        }
    client_name = state.get("client_name") or "the client"
    try:
        structured_proposal = generate_structured_proposal(state, payload.transcript)
    except Exception as e:
        return {"error": f"Proposal generation failed: {e}"}

    title = payload.title or structured_proposal.proposal_title or f"Proposal - {client_name}"

    # generate diagrams first, using a fresh uuid — no dependency on proposal_id
    gen_uid = uuid.uuid4().hex[:8]
    solution_diagram_path = generate_solution_diagram(
        [c.model_dump() for c in structured_proposal.solution_components],
        filename=f"solution_{gen_uid}.png",
    )
    approach_diagram_path = generate_approach_diagram(
        [p.model_dump() for p in structured_proposal.approach_phases],
        filename=f"approach_{gen_uid}.png",
    )

    proposal_markdown = _structured_proposal_to_markdown(
        structured_proposal, solution_diagram_path, approach_diagram_path
    )

    proposal_id = None
    version_id = None
    try:
        save_result = save_generated_proposal(
            title=title,
            markdown=proposal_markdown,
            author_id=payload.author_id,
            state=state,
        )
        proposal_id = save_result["proposal_id"]
        version_id = save_result["version_id"]
    except Exception as e:
        print(f"⚠️ Failed to save generated Proposal to database: {e}")

    return {
        "proposal_id": proposal_id,
        "version_id": version_id,
        "title": title,
        "structured_proposal": structured_proposal.model_dump(),
        "sow": proposal_markdown,
        "state": state,
    }


@router.post("/proposal/export-pptx")
def export_proposal_pptx(payload: ProposalPptxExportRequest):
    templates = load_templates()
    template = next((t for t in templates if t["id"] == payload.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.get("type") != "pptx":
        raise HTTPException(status_code=400, detail="Selected template is not a PPTX/POTX template")

    template_path = os.path.join(TEMPLATE_DIR, template["filename"])
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template file missing on disk")

    try:
        pptx_bytes = generate_proposal_pptx(template_path, payload.structured_proposal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PPTX generation failed: {e}")

    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": 'attachment; filename="proposal.pptx"'},
    )