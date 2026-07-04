# from fastapi import APIRouter
# from sqlalchemy import text
# from app.core.embedding import get_embedding
# from app.core.postgres import engine

# router = APIRouter()

# @router.get("/search")
# def search(query: str):

#     embedding = get_embedding(query)

#     conn = engine.connect()

#     results = conn.execute(
#         text("""
#         SELECT dc.content, d.title
#         FROM document_chunks dc
#         JOIN documents d ON d.id = dc.doc_id
#         ORDER BY dc.embedding <-> CAST(:emb AS vector)
#         LIMIT 5
#         """),
#         {"emb": embedding}
#     ).fetchall()

#     return [
#         {
#             "title": r[1],
#             "content": r[0]
#         }
#         for r in results
#     ]

from fastapi import APIRouter
from app.services.hybrid_search import hybrid_search

router = APIRouter()


@router.get("/search")
def search(query: str):

    results = hybrid_search(query)

    return results