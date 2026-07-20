from fastapi import APIRouter
from sqlalchemy import text
from app.core.postgres import engine

router = APIRouter(tags=["retrieval"])

@router.get("/search")
def search(query: str):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT title, content
            FROM documents
            LIMIT 5
        """))

        return {"results": [dict(r._mapping) for r in result]}