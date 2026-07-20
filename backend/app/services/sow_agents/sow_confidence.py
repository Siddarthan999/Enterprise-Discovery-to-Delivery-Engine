def compute_sow_confidence(
    review_result: dict,
    historical_sows: list,
    historical_risks: list,
    state: dict,
    draft_markdown: str,
) -> dict:
    agent_scores = [
        int(a.get("score", 0))
        for a in review_result.get("agents", [])
    ]
    avg_agent_score = round(sum(agent_scores) / max(len(agent_scores), 1))

    precedent_strength = 0
    if historical_sows:
        similarities = []
        for item in historical_sows[:3]:
            score = item.get("score")
            similarity = item.get("similarity")

            if similarity is not None:
                similarities.append(float(similarity))
            elif score is not None:
                try:
                    similarities.append(float(score))
                except Exception:
                    pass

        if similarities:
            # Historical "score" values here come from hybrid_search's
            # blended vector+keyword score, which can exceed 1.0 (base
            # 1/(1+distance) plus up to +0.7 keyword boost) — clamp each
            # individual similarity to [0, 1] BEFORE averaging, so one
            # inflated match can't skew the whole precedent_strength.
            clamped = [max(0.0, min(s, 1.0)) for s in similarities]
            precedent_strength = round(sum(clamped) / len(clamped) * 100)

    risk_coverage = min(len(historical_risks) * 12, 100)

    red_flags = review_result.get("red_flags", [])
    required_edits = review_result.get("required_edits", [])

    # Reduced per-item weight and lower caps — 5 reviewer agents each
    # flagging a couple of legitimate issues is NORMAL, not a sign the
    # SOW is unusable. The previous caps (40 + 36 = 76) were close
    # enough to the full positive ceiling (100) that a completely
    # ordinary review (7-8 combined flags/findings) could zero out even
    # an 80+ average agent score. These caps now leave enough headroom
    # for a solid avg_agent_score to still land in a sensible range.
    red_flag_penalty = min(len(red_flags) * 4, 20)
    required_edit_penalty = min(len(required_edits) * 3, 18)

    overall_confidence = round(
        (avg_agent_score * 0.55)
        + (precedent_strength * 0.20)
        + (risk_coverage * 0.15)
        + (10 if len(draft_markdown or "") > 1500 else 0)
        - red_flag_penalty
        - required_edit_penalty
    )

    overall_confidence = max(0, min(overall_confidence, 100))

    if overall_confidence >= 85:
        label = "high"
    elif overall_confidence >= 65:
        label = "medium"
    else:
        label = "low"

    components = {
        "avg_agent_score": avg_agent_score,
        "precedent_strength": precedent_strength,
        "risk_coverage": risk_coverage,
        "red_flag_penalty": red_flag_penalty,
        "required_edit_penalty": required_edit_penalty,
        "red_flag_count": len(red_flags),
        "required_edit_count": len(required_edits),
    }

    # TEMP DEBUG — remove once you've confirmed the new balance feels
    # right across a few real generations. Shows exactly what pushed
    # the score wherever it landed.
    # print(f"DEBUG confidence components: {components}")
    # print(f"DEBUG overall_confidence (pre-clamp calc used above): {overall_confidence}")

    return {
        "overall_confidence": overall_confidence,
        "label": label,
        "components": components,
    }