import json
import re
import io
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.llm_router import generate_completion
from app.services.proposal.proposal_extractor import extract_proposal_state
from app.services.proposal.save_proposal import save_generated_proposal
from app.services.sow.project_state_service import save_project_state
from fastapi.responses import StreamingResponse
from app.services.sow.template_storage import load_templates, TEMPLATE_DIR
from app.services.proposal.pptx_generator import generate_proposal_pptx

router = APIRouter(tags=["proposal"])

BULLET = "\u25cf"  # ●


# ---------------------------------------------------------------------------
# Extraction  (unchanged from before)
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
        return {
            "error": "Transcript is empty",
            "state": None,
        }

    state = extract_proposal_state(transcript)
    if not isinstance(state, dict):
        return {
            "error": "Proposal extraction returned invalid state",
            "state": None,
        }

    if state.get("error"):
        return {
            "title": payload.title,
            "error": f"Proposal extraction failed: {state['error']}",
            "state": state,
        }

    save_project_state(payload.title, state)

    return {
        "title": payload.title,
        "state": state,
    }


# ---------------------------------------------------------------------------
# Generation — now a real writing pass, not a field dump
# ---------------------------------------------------------------------------
class ProposalRequest(BaseModel):
    state: dict | None = None
    transcript: str | None = None
    author_id: int | None = None
    title: str | None = None


class ApproachPhase(BaseModel):
    title: str = ""
    narrative: str = ""
    indicative_activities: list[str] = Field(default_factory=list)


class CommercialOption(BaseModel):
    name: str = ""
    description: str = ""


class TeamRole(BaseModel):
    role: str = ""
    description: str = ""


class StructuredProposal(BaseModel):
    proposal_title: str = "Proposal"
    executive_summary: str = ""
    what_weve_heard_intro: str = ""
    what_weve_heard_themes: list[str] = Field(default_factory=list)
    target_outcomes: list[str] = Field(default_factory=list)
    approach_phases: list[ApproachPhase] = Field(default_factory=list)
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
        _list_block("BUSINESS CHALLENGES", state.get("business_challenges", [])),
        _list_block("PROJECT OBJECTIVES", state.get("project_objectives", [])),
        _str_block("PROPOSED SOLUTION", state.get("proposed_solution")),
        _str_block("DELIVERY APPROACH", state.get("delivery_approach")),
        _list_block("TECHNOLOGIES", state.get("technologies", [])),
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
You are a senior consulting proposal writer. You are drafting a client-facing Proposal
document from a structured extraction of a discovery conversation. Your job is to WRITE the
proposal, not restate the extracted bullets. Every extracted fact must be rewritten in your
own words, elaborated with reasoning and context, and organised into a persuasive narrative
\u2014 the way an experienced consultant would frame it back to a client, not the way a form
would list it.

IMPORTANT:
- Do NOT write markdown, headings, or section numbers \u2014 the caller renders those.
- Do NOT copy extracted bullets verbatim \u2014 rewrite every point as a full sentence (or a
  short paragraph where useful) that explains the "so what", not just the "what".
- Return ONLY valid JSON matching the requested schema below.
- NEVER invent client facts, numbers, dates, headcounts, tool names, or commercial terms
  that are not present in the extracted state or transcript. Where something isn't captured
  (e.g. specific pricing, team size, exact duration), write in general/qualitative terms
  instead of a fabricated number ("a phased engagement" rather than inventing "12 weeks" if
  no duration was captured).
- Where the extracted state genuinely contains very little for a section, it is fine for
  that section to be shorter or more general \u2014 do not pad with invented specifics.

EXTRACTED PROJECT STATE (the ONLY source of client-specific facts you may use):
{state_text}{transcript_block}

WRITING GUIDANCE PER SECTION:

- executive_summary: 2\u20134 sentences. Frame the client's situation (from business_context
  and industry), what they're trying to achieve (from project_objectives), and at a high
  level what's being proposed (from proposed_solution) \u2014 written as a narrative opening,
  not a list.

- what_weve_heard_intro: 1\u20132 sentences setting up the themes that follow, based on
  business_context.
- what_weve_heard_themes: turn each business_challenge (and any relevant assumption) into a
  fully-written theme \u2014 explain the challenge AND its implication for the client, in 1\u20133
  sentences each. Do not just restate the challenge as given; add the "why this matters"
  framing based on context you were given.

- target_outcomes: turn each project_objective into an outcome statement written from the
  client's point of view (what will be true once this succeeds), 1\u20132 sentences each.

- approach_phases: derive a small number of logical phases (2\u20134) from delivery_approach and
  timeline. Each phase needs a short title, a 2\u20134 sentence narrative explaining what happens
  and why it's sequenced that way, and a handful of indicative_activities written as full
  sentences (not fragment bullets) grounded in proposed_solution/technologies/deliverables.
  If timeline data is sparse, phase the approach logically based on delivery_approach alone
  rather than inventing dates.

- in_scope / out_of_scope: rewrite each captured item as a complete, specific sentence.
  Do not add scope items that weren't captured.

- deliverables: rewrite each captured deliverable as a full sentence describing what it is
  and what it enables, not just its name.

- commercial_narrative: 2\u20133 sentences framing the commercial approach based on
  commercial_information and dependencies. If commercial_information is empty, say pricing
  will be confirmed once scope is finalised \u2014 do not invent numbers.
- commercial_options: only populate if commercial_information suggests tiered/optional
  scope; otherwise return an empty list rather than inventing options.
- team_roles: only populate if the state/transcript indicates specific roles/skills needed;
  otherwise return an empty list rather than inventing a team structure.

- why_this_approach: 2\u20133 sentences explaining why this approach fits this client's
  situation specifically, grounded in business_context/business_challenges \u2014 not generic
  marketing copy, and without naming any consulting firm/brand.

- next_steps: rewrite each captured next_step as a clear, actionable full sentence. If
  dependencies were captured and aren't already reflected in next_steps, fold the most
  important ones in as a next step (e.g. "Confirm X before work begins").

- proposal_title: "{state.get('client_name') or 'Client'} \u2014 Proposal" unless a more
  specific project/engagement name is implied by the state.

Return ONLY valid JSON with this structure:
{{
  "proposal_title": "",
  "executive_summary": "",
  "what_weve_heard_intro": "",
  "what_weve_heard_themes": [""],
  "target_outcomes": [""],
  "approach_phases": [
    {{"title": "", "narrative": "", "indicative_activities": [""]}}
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

    # Defensive pass: strip any stray markdown the model injected into
    # free-text fields, same guard SOW generation applies.
    proposal.executive_summary = _strip_markdown_artifacts(proposal.executive_summary)
    proposal.what_weve_heard_intro = _strip_markdown_artifacts(proposal.what_weve_heard_intro)
    proposal.commercial_narrative = _strip_markdown_artifacts(proposal.commercial_narrative)
    proposal.why_this_approach = _strip_markdown_artifacts(proposal.why_this_approach)
    for phase in proposal.approach_phases:
        phase.title = _strip_markdown_artifacts(phase.title)
        phase.narrative = _strip_markdown_artifacts(phase.narrative)
        phase.indicative_activities = [_strip_markdown_artifacts(a) for a in phase.indicative_activities]

    return proposal


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"{BULLET} {item}" for item in items]


def _structured_proposal_to_markdown(proposal: StructuredProposal) -> str:
    lines: list[str] = [
        "## EXECUTIVE SUMMARY",
        "",
        proposal.executive_summary or "Executive summary to be confirmed during discovery.",
        "",
        "## WHAT WE'VE HEARD",
        "",
    ]

    if proposal.what_weve_heard_intro:
        lines.append(proposal.what_weve_heard_intro)
        lines.append("")
    lines.extend(_bullets(proposal.what_weve_heard_themes) or [
        f"{BULLET} Key themes to be confirmed during discovery."
    ])

    lines.extend(["", "## TARGET OUTCOMES", ""])
    lines.extend(_bullets(proposal.target_outcomes) or [
        f"{BULLET} Target outcomes to be confirmed during discovery."
    ])

    lines.extend(["", "## PROPOSED APPROACH", ""])
    if proposal.approach_phases:
        for i, phase in enumerate(proposal.approach_phases, start=1):
            title = phase.title or f"Phase {i}"
            lines.append(f"### Phase {i} \u2014 {title}")
            lines.append("")
            if phase.narrative:
                lines.append(phase.narrative)
                lines.append("")
            if phase.indicative_activities:
                lines.append("**Indicative activities:**")
                lines.append("")
                lines.extend(_bullets(phase.indicative_activities))
            lines.append("")
    else:
        lines.append("The phased approach will be confirmed during discovery.")
        lines.append("")

    lines.extend(["## SCOPE SUMMARY", "", "### In Scope", ""])
    lines.extend(_bullets(proposal.in_scope) or [f"{BULLET} To be confirmed during discovery."])
    lines.extend(["", "### Out of Scope", ""])
    lines.extend(_bullets(proposal.out_of_scope) or [f"{BULLET} To be confirmed during discovery."])

    lines.extend(["", "## DELIVERABLES", ""])
    lines.extend(_bullets(proposal.deliverables) or [f"{BULLET} To be confirmed during discovery."])

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

    lines.extend(["", "## RECOMMENDED NEXT STEPS", ""])
    lines.extend(_bullets(proposal.next_steps) or [f"{BULLET} Next steps to be confirmed."])

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
    proposal_markdown = _structured_proposal_to_markdown(structured_proposal)

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
        "sow": proposal_markdown,  # kept as "sow" so SowViewer/ExportPanel render unchanged
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