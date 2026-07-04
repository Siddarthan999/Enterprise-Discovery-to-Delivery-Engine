from sqlalchemy import text
from app.core.embedding import get_embedding
from app.core.postgres import engine


# ---------------- VECTOR SEARCH ----------------
def vector_search(conn, embedding, limit=10):
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
def graph_search(conn, query, limit=10):
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
def hybrid_search(query: str, limit: int = 5):
    embedding = get_embedding(query)
    query_lower = query.lower()   # 🔥 CHANGED: used for keyword boost

    with engine.connect() as conn:

        # 1. VECTOR RESULTS (chunk-level)
        vector_rows = vector_search(conn, embedding, limit * 3)

        vector_results = []
        for r in vector_rows:

            doc_id = r[0]
            title = r[1]
            content = r[2]
            distance = float(r[3])

            # 🔥 CHANGED: convert distance → similarity score
            score = 1 / (1 + distance)

            # 🔥 CHANGED: keyword boost (VERY IMPORTANT FIX)
            if query_lower in content.lower():
                score += 0.5

            if query_lower in (title or "").lower():
                score += 0.3

            vector_results.append({
                "doc_id": doc_id,
                "title": title,
                "content": content,
                "score": score,
                "source": "vector"
            })

        # 2. GRAPH RESULTS (document-level)
        graph_rows = graph_search(conn, query, limit)

        graph_results = []
        for r in graph_rows:
            graph_results.append({
                "doc_id": r[0],
                "title": r[1],
                "type": r[2],
                "source": r[3],
                "uploaded_at": str(r[4]),
                "score": 0.4,   # 🔥 CHANGED: slightly lower base score
                "content": "",
                "source_type": "graph"
            })

        # 3. MERGE + DEDUP
        merged = {}

        # vector priority
        for item in vector_results:
            doc_id = item["doc_id"]

            if doc_id not in merged:
                merged[doc_id] = item
            else:
                # 🔥 CHANGED: additive merge instead of max only
                merged[doc_id]["score"] = max(
                    merged[doc_id]["score"],
                    item["score"]
                )

        # graph enrichment
        for item in graph_results:
            doc_id = item["doc_id"]

            if doc_id not in merged:
                merged[doc_id] = item
            else:
                # 🔥 CHANGED: stronger graph influence
                merged[doc_id]["score"] += 0.25

        # 4. FINAL SORT
        final_results = sorted(
            merged.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return final_results[:limit]