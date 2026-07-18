from sqlalchemy import text

from app.core.embedding import get_embedding
from app.core.postgres import engine
from app.services.hybrid_search import hybrid_search


def search_similar_historical_sows(context_summary: str, limit: int = 3) -> list:
    """Finds past SOWs most similar to the new project's context, for
    style/structure precedent. Reuses hybrid_search's existing vector +
    keyword logic, just scoped to category='sow_history'."""
    if not context_summary or not context_summary.strip():
        return []

    return hybrid_search(context_summary, limit=limit, category="sow_history")


def search_similar_historical_risks(context_summary: str, limit: int = 8) -> list:
    """Finds risk/mitigation examples from past SOWs most similar to the
    new project's context — this is the actual precedent the Risk agent
    (Phase 3b) and the grounding brief use, sharper than generic document
    similarity since it's matched risk-to-risk."""
    if not context_summary or not context_summary.strip():
        return []

    embedding = get_embedding(context_summary)

    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    r.id,
                    r.risk_description,
                    r.mitigation_approach,
                    r.category,
                    d.title AS source_title,
                    r.embedding <-> CAST(:emb AS vector) AS distance
                FROM sow_risk_examples r
                JOIN documents d ON d.id = r.source_doc_id
                ORDER BY r.embedding <-> CAST(:emb AS vector)
                LIMIT :limit
            """),
            {"emb": embedding, "limit": limit}
        ).mappings().all()

        return [dict(r) for r in rows]