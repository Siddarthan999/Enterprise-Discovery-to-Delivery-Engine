"""
TEMPORARY debug route — not for production. Lets you see exactly what
hybrid_search retrieves and how it scored, WITHOUT the RELEVANCE_THRESHOLD
cutoff or the LLM step in between. Use this to answer the question:

  "Is the info missing from my knowledge base, or is it being retrieved
   but filtered out / not making it into the LLM context?"

Usage:
  GET /api/debug/search?query=Three ways to consolidate Notion boards

Remove this route (or gate it behind an env check) before this goes
anywhere near a real deployment — it has no auth and exposes raw content.
"""

from fastapi import APIRouter
from app.services.hybrid_search import hybrid_search
from app.services.rag import RELEVANCE_THRESHOLD

router = APIRouter()


@router.get("/debug/search")
def debug_search(query: str, limit: int = 10):
    results = hybrid_search(query, limit=limit, debug=True)

    return {
        "query": query,
        "relevance_threshold": RELEVANCE_THRESHOLD,
        "results": [
            {
                "doc_id": r.get("doc_id"),
                "title": r.get("title"),
                "score": round(r.get("score", 0), 4),
                "would_pass_threshold": r.get("score", 0) >= RELEVANCE_THRESHOLD,
                "distance": round(r.get("_distance"), 4) if r.get("_distance") is not None else None,
                "keyword_overlap": round(r.get("_keyword_overlap", 0), 4)
                    if r.get("_keyword_overlap") is not None else None,
                "content_preview": (r.get("content") or "")[:200],
            }
            for r in results[:limit]
        ],
    }