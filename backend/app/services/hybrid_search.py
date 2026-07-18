import re

from sqlalchemy import text
from app.core.embedding import get_embedding
from app.core.postgres import engine

# Common words that add noise to keyword matching without adding signal.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "with", "by", "from", "up",
    "about", "into", "over", "after", "and", "or", "but", "if", "not",
    "can", "you", "get", "me", "what", "who", "why", "how", "when",
    "where", "which", "do", "does", "did", "tell", "give", "please",
    "i", "my", "your", "our", "it", "this", "that", "these", "those",
}


def _extract_keywords(query: str) -> list:
    """Pulls out the meaningful words from a question, dropping stopwords
    and short filler tokens. 'What are the three ways to consolidate
    Notion boards?' -> ['three', 'ways', 'consolidate', 'notion', 'boards']
    """
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _keyword_overlap_score(keywords: list, text_value: str) -> float:
    """Fraction of query keywords that appear in the given text.
    Returns 0.0-1.0."""
    if not keywords or not text_value:
        return 0.0
    text_lower = text_value.lower()
    matched = sum(1 for kw in keywords if kw in text_lower)
    return matched / len(keywords)


# ---------------- VECTOR SEARCH ----------------
def vector_search(conn, embedding, limit=10, category=None):
    if category:
        return conn.execute(
            text("""
                SELECT
                    c.doc_id,
                    d.title,
                    c.content,
                    c.embedding <-> CAST(:emb AS vector) AS distance
                FROM document_chunks c
                JOIN documents d ON d.id = c.doc_id
                WHERE d.category = :category
                ORDER BY c.embedding <-> CAST(:emb AS vector)
                LIMIT :limit
            """),
            {"emb": embedding, "limit": limit, "category": category}
        ).fetchall()

    return conn.execute(
        text("""
            SELECT
                c.doc_id,
                d.title,
                c.content,
                c.embedding <-> CAST(:emb AS vector) AS distance
            FROM document_chunks c
            JOIN documents d ON d.id = c.doc_id
            ORDER BY c.embedding <-> CAST(:emb AS vector)
            LIMIT :limit
        """),
        {"emb": embedding, "limit": limit}
    ).fetchall()


# ---------------- GRAPH SEARCH ----------------
def graph_search(conn, query, limit=10, category=None):
    if category:
        return conn.execute(
            text("""
                SELECT id, title, type, source, uploaded_at
                FROM documents
                WHERE (LOWER(title) LIKE LOWER(:q)
                   OR LOWER(type) LIKE LOWER(:q))
                  AND category = :category
                LIMIT :limit
            """),
            {"q": f"%{query}%", "limit": limit, "category": category}
        ).fetchall()

    return conn.execute(
        text("""
            SELECT id, title, type, source, uploaded_at
            FROM documents
            WHERE LOWER(title) LIKE LOWER(:q)
               OR LOWER(type) LIKE LOWER(:q)
            LIMIT :limit
        """),
        {"q": f"%{query}%", "limit": limit}
    ).fetchall()


# ---------------- HYBRID MERGE ----------------
def hybrid_search(query: str, limit: int = 5, debug: bool = False, category: str | None = None):
    embedding = get_embedding(query)
    keywords = _extract_keywords(query)

    with engine.connect() as conn:
        vector_rows = vector_search(conn, embedding, limit * 6, category=category)

        vector_results = []
        for r in vector_rows:
            doc_id = r[0]
            title = r[1]
            content = r[2]
            distance = float(r[3])

            score = 1 / (1 + distance)

            content_overlap = _keyword_overlap_score(keywords, content)
            title_overlap = _keyword_overlap_score(keywords, title or "")

            score += content_overlap * 0.4
            score += title_overlap * 0.3

            vector_results.append({
                "doc_id": doc_id,
                "title": title,
                "content": content,
                "score": score,
                "source": "vector",
                "_distance": distance,
                "_keyword_overlap": content_overlap,
            })

        graph_rows = graph_search(conn, query, limit, category=category)

        graph_results = []
        for r in graph_rows:
            graph_results.append({
                "doc_id": r[0],
                "title": r[1],
                "type": r[2],
                "source": r[3],
                "uploaded_at": str(r[4]),
                "score": 0.4,
                "content": "",
                "source_type": "graph"
            })

        merged = {}

        for item in vector_results:
            doc_id = item["doc_id"]
            if doc_id not in merged:
                merged[doc_id] = item
            else:
                merged[doc_id]["score"] = max(merged[doc_id]["score"], item["score"])

        for item in graph_results:
            doc_id = item["doc_id"]
            if doc_id not in merged:
                merged[doc_id] = item
            else:
                merged[doc_id]["score"] += 0.25

        final_results = sorted(
            merged.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        if not final_results:
            print(f"⚠️ hybrid_search: 0 results for category={category!r}, query={query!r}")

        if debug:
            return final_results

        return final_results[:limit]