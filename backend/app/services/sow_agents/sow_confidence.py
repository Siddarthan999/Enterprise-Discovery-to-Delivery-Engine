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
            precedent_strength = round(sum(similarities) / len(similarities) * 100)
            precedent_strength = max(0, min(precedent_strength, 100))

    risk_coverage = min(len(historical_risks) * 12, 100)

    red_flag_penalty = min(len(review_result.get("red_flags", [])) * 8, 40)
    required_edit_penalty = min(len(review_result.get("required_edits", [])) * 6, 36)

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

    return {
        "overall_confidence": overall_confidence,
        "label": label,
        "components": {
            "avg_agent_score": avg_agent_score,
            "precedent_strength": precedent_strength,
            "risk_coverage": risk_coverage,
            "red_flag_penalty": red_flag_penalty,
            "required_edit_penalty": required_edit_penalty,
        }
    }