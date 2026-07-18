import json
import re

from app.core.llm_router import generate_completion


def _extract_json_block(response: str) -> str:
    response = (response or "").strip()
    if "```" in response:
        response = re.sub(r"```(?:json)?", "", response).strip()

    if response.startswith("{") and response.endswith("}"):
        return response

    match = re.search(r"\{.*\}", response, re.DOTALL)
    return match.group(0) if match else response


def _safe_json(response: str, fallback: dict) -> dict:
    try:
        parsed = json.loads(_extract_json_block(response))
        if not isinstance(parsed, dict):
            raise ValueError(f"Parsed JSON was not an object: {type(parsed)}")
        return {
            "agent": str(parsed.get("agent", fallback["agent"])),
            "score": int(parsed.get("score", 0) or 0),
            "status": str(parsed.get("status", "warning")).lower(),
            "findings": parsed.get("findings", []) if isinstance(parsed.get("findings", []), list) else [],
            "strengths": [str(x).strip() for x in parsed.get("strengths", []) if str(x).strip()] if isinstance(parsed.get("strengths", []), list) else [],
            "missing_items": [str(x).strip() for x in parsed.get("missing_items", []) if str(x).strip()] if isinstance(parsed.get("missing_items", []), list) else [],
            "red_flags": [str(x).strip() for x in parsed.get("red_flags", []) if str(x).strip()] if isinstance(parsed.get("red_flags", []), list) else [],
        }
    except Exception as e:
        # Surfaced into the UI now (orchestrator passes red_flags through
        # in full) so a parse failure is visible on the card itself
        # instead of silently showing an empty-looking agent.
        snippet = (response or "")[:300].replace("\n", " ")
        print(f"DEBUG [{fallback['agent']}] JSON parse failed: {e}")
        print(f"DEBUG [{fallback['agent']}] raw response snippet: {snippet!r}")

        result = dict(fallback)
        result["red_flags"] = [f"Reviewer output could not be parsed ({e}). Check backend logs for the raw response."]
        return result


def _truncate(text: str, limit: int = 8000) -> str:
    return (text or "")[:limit]


def _compact_state(state: dict) -> dict:
    """Sends a trimmed version of state to each agent — the full raw
    dict via json.dumps can be large if discovery captured a lot, and
    every field isn't needed for a review pass. Keeps the schema stable
    (same keys) so agent prompts don't need special-casing."""
    return {
        "context_summary": (state.get("context_summary", "") or "")[:600],
        "requirements": state.get("requirements", [])[:15],
        "risks": state.get("risks", [])[:15],
        "assumptions": state.get("assumptions", [])[:10],
        "stakeholders": state.get("stakeholders", [])[:10],
        "deliverables": state.get("deliverables", [])[:15],
        "timeline": (state.get("timeline", "") or "")[:400],
    }


def _compact_historical_sows(historical_sows: list, limit: int = 3) -> list:
    """Only title + a short content excerpt — the full chunk content and
    any extra retrieval metadata (score, doc_id, etc.) isn't needed for
    the reviewer to judge style/structure precedent, and was a major
    contributor to prompt bloat."""
    compact = []
    for sow in (historical_sows or [])[:limit]:
        compact.append({
            "title": sow.get("title", "Unknown"),
            "excerpt": (sow.get("content") or "")[:400],
        })
    return compact


def _compact_historical_risks(historical_risks: list, limit: int = 8) -> list:
    compact = []
    for r in (historical_risks or [])[:limit]:
        compact.append({
            "risk": r.get("risk_description", ""),
            "mitigation": r.get("mitigation_approach", ""),
            "category": r.get("category", ""),
        })
    return compact


def _review_prompt(
    agent_name: str,
    mission: str,
    state: dict,
    draft_markdown: str,
    historical_sows: list,
    historical_risks: list,
) -> str:
    return f"""
You are the {agent_name} for Statement of Work quality review.

MISSION:
{mission}

You must review the DRAFT SOW against:
1. the project input state,
2. similar historical SOW precedents,
3. historical risk/mitigation precedents where relevant.

Be strict, concrete, and non-generic.
Do not rewrite the whole SOW.
Only identify review findings.

Return ONLY valid JSON, no markdown fences, no extra text, no explanations:
{{
  "agent": "{agent_name}",
  "score": <integer 0-100>,
  "status": "<pass|warning|fail>",
  "findings": [
    {{
      "severity": "<critical|high|medium|low>",
      "section": "<section name or general>",
      "issue": "<what is wrong or missing>",
      "why_it_matters": "<short reason>",
      "recommended_fix": "<specific fix>"
    }}
  ],
  "strengths": ["<specific strength 1>", "<specific strength 2>"],
  "missing_items": ["<missing item 1>", "<missing item 2>"],
  "red_flags": ["<major red flag 1>", "<major red flag 2>"]
}}

SCORING RULES:
- 90-100: strong, only minor improvements
- 75-89: usable, but has notable gaps
- 50-74: significant concerns
- below 50: not safe to use without revision

PROJECT INPUT STATE:
{json.dumps(_compact_state(state), ensure_ascii=False)}

DRAFT SOW:
{_truncate(draft_markdown, 8000)}

SIMILAR HISTORICAL SOWS:
{json.dumps(_compact_historical_sows(historical_sows), ensure_ascii=False)}

HISTORICAL RISK PRECEDENTS:
{json.dumps(_compact_historical_risks(historical_risks), ensure_ascii=False)}
""".strip()


def run_validation_agent(state, draft_markdown, historical_sows, historical_risks) -> dict:
    prompt = _review_prompt(
        "Validation Agent",
        """Check for internal contradictions, unresolved placeholders,
missing client/project specifics that should already be known, duplicated
sections, malformed section structure, and unsupported definitive claims.""",
        state, draft_markdown, historical_sows, historical_risks,
    )
    return _safe_json(generate_completion(prompt), _fallback("Validation Agent"))


def run_coverage_agent(state, draft_markdown, historical_sows, historical_risks) -> dict:
    prompt = _review_prompt(
        "Coverage Agent",
        """Check whether the SOW covers the important project dimensions
implied by the input state: objectives, scope, deliverables, assumptions,
dependencies, timeline, stakeholders, exclusions, acceptance, and risks.
Flag omissions and shallow treatment.""",
        state, draft_markdown, historical_sows, historical_risks,
    )
    return _safe_json(generate_completion(prompt), _fallback("Coverage Agent"))


def run_grc_agent(state, draft_markdown, historical_sows, historical_risks) -> dict:
    prompt = _review_prompt(
        "GRC Agent",
        """Check governance, risk, and compliance framing. Look for weak
language around approvals, change control, responsibilities, security,
data handling, auditability, acceptance criteria, assumptions, exclusions,
and contract-style ambiguity that may create delivery or legal exposure.""",
        state, draft_markdown, historical_sows, historical_risks,
    )
    return _safe_json(generate_completion(prompt), _fallback("GRC Agent"))


def run_risk_agent(state, draft_markdown, historical_sows, historical_risks) -> dict:
    prompt = _review_prompt(
        "Risk Agent",
        """Check whether project risks are realistically represented and
whether mitigations are credible. Use historical risk precedents as a
grounding signal. Flag risk blind spots, generic mitigations, and risks
that should exist given the context but do not appear in the draft.""",
        state, draft_markdown, historical_sows, historical_risks,
    )
    return _safe_json(generate_completion(prompt), _fallback("Risk Agent"))


def run_feasibility_agent(state, draft_markdown, historical_sows, historical_risks) -> dict:
    prompt = _review_prompt(
        "Feasibility Agent",
        """Check whether the stated scope, deliverables, timeline,
dependencies, and operating model are practically achievable together.
Flag overloaded timelines, missing client dependencies, vague staffing,
and deliverables that lack implementation realism.""",
        state, draft_markdown, historical_sows, historical_risks,
    )
    return _safe_json(generate_completion(prompt), _fallback("Feasibility Agent"))


def _fallback(agent_name: str) -> dict:
    return {
        "agent": agent_name,
        "score": 0,
        "status": "warning",
        "findings": [],
        "strengths": [],
        "missing_items": [],
        "red_flags": ["Reviewer output could not be parsed"],
    }