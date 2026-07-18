from app.services.sow_agents.sow_review_agents import (
    run_validation_agent,
    run_coverage_agent,
    run_grc_agent,
    run_risk_agent,
    run_feasibility_agent,
)


def review_sow_draft(
    state: dict,
    draft_markdown: str,
    historical_sows: list,
    historical_risks: list,
) -> dict:

    validation = run_validation_agent(
        state, draft_markdown, historical_sows, historical_risks
    )
    coverage = run_coverage_agent(
        state, draft_markdown, historical_sows, historical_risks
    )
    grc = run_grc_agent(
        state, draft_markdown, historical_sows, historical_risks
    )
    risk = run_risk_agent(
        state, draft_markdown, historical_sows, historical_risks
    )
    feasibility = run_feasibility_agent(
        state, draft_markdown, historical_sows, historical_risks
    )

    agents = [validation, coverage, grc, risk, feasibility]

    all_findings = []
    all_red_flags = []
    all_missing_items = []
    all_strengths = []

    for agent in agents:
        all_findings.extend(agent.get("findings", []))
        all_red_flags.extend(agent.get("red_flags", []))
        all_missing_items.extend(agent.get("missing_items", []))
        all_strengths.extend(agent.get("strengths", []))

    overall_score = round(
        sum(int(a.get("score", 0)) for a in agents) / max(len(agents), 1)
    )

    if any(a.get("status") == "fail" for a in agents):
        overall_status = "fail"
    elif any(a.get("status") == "warning" for a in agents):
        overall_status = "warning"
    else:
        overall_status = "pass"

    required_edits = [
        f for f in all_findings
        if str(f.get("severity", "")).lower() in {"critical", "high"}
    ]
    optional_improvements = [
        f for f in all_findings
        if str(f.get("severity", "")).lower() in {"medium", "low"}
    ]

    return {
        "overall_score": overall_score,
        "overall_status": overall_status,
        "agents": [
            {
                # "agent" — NOT "name" — this is the field ReviewPanel.tsx
                # actually reads via agent.agent. Renaming it here was
                # silently breaking every agent name in the UI.
                "agent": a.get("agent", "Unknown Agent"),
                "score": int(a.get("score", 0) or 0),
                "status": a.get("status", "warning"),
                # Full arrays, not just counts — ReviewPanel.tsx renders
                # the actual findings/strengths/missing_items/red_flags
                # lists per agent, so it needs the real data, not a number.
                "findings": a.get("findings", []) or [],
                "strengths": a.get("strengths", []) or [],
                "missing_items": a.get("missing_items", []) or [],
                "red_flags": a.get("red_flags", []) or [],
            }
            for a in agents
        ],
        "red_flags": _dedupe_strings(all_red_flags),
        "missing_items": _dedupe_strings(all_missing_items),
        "strengths": _dedupe_strings(all_strengths),
        "required_edits": _normalize_findings(required_edits),
        "optional_improvements": _normalize_findings(optional_improvements),
    }


def _dedupe_strings(items: list) -> list:
    seen = set()
    output = []
    for item in items:
        val = str(item).strip()
        if not val:
            continue
        key = val.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(val)
    return output


def _normalize_findings(findings: list) -> list:
    output = []
    for f in findings or []:
        if not isinstance(f, dict):
            continue
        output.append({
            "severity": str(f.get("severity", "")).strip().lower(),
            "section": str(f.get("section", "general")).strip(),
            "issue": str(f.get("issue", "")).strip(),
            "why_it_matters": str(f.get("why_it_matters", "")).strip(),
            "recommended_fix": str(f.get("recommended_fix", "")).strip(),
        })
    return output