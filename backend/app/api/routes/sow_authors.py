from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.postgres import engine

router = APIRouter(tags=["authors"])


class AuthorRequest(BaseModel):
    name: str


@router.get("/authors")
def list_authors():
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT id, name
                FROM sow_authors
                ORDER BY name
            """)
        ).mappings().all()

    return [dict(r) for r in rows]


@router.post("/authors")
def add_author(payload: AuthorRequest):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                INSERT INTO sow_authors(name)
                VALUES(:name)
                ON CONFLICT(name)
                DO NOTHING
                RETURNING id, name
            """),
            {"name": payload.name.strip()},
        ).mappings().first()

        if row:
            return dict(row)

        existing = conn.execute(
            text("""
                SELECT id, name
                FROM sow_authors
                WHERE name=:name
            """),
            {"name": payload.name.strip()},
        ).mappings().first()

        return dict(existing)


@router.delete("/authors/{author_id}")
def delete_author(author_id: int):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM sow_authors WHERE id=:id"),
            {"id": author_id},
        )

    return {"deleted": True}