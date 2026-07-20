from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text

from app.services.ingestion import ingest_document
from app.core.parsers import parse_document
from app.core.postgres import engine
import shutil
import os

router = APIRouter(tags=["ingest"])


@router.post("/ingest/document")
async def ingest(file: UploadFile = File(...)):

    file_path = f"/tmp/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = parse_document(file_path)

    result = ingest_document(doc)

    os.remove(file_path)

    return result


@router.get("/ingest/documents")
def list_documents():
    """
    Lists all documents currently in the knowledge base, most recently
    uploaded first. Mirrors the same `documents` table used by
    hybrid_search.py's graph_search.
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, title, type, source, uploaded_at
                FROM documents
                ORDER BY uploaded_at DESC
            """)
        ).fetchall()

    return [
        {
            "id": r[0],
            "title": r[1],
            "type": r[2],
            "source": r[3],
            "uploaded_at": str(r[4]),
        }
        for r in rows
    ]


@router.delete("/ingest/document/{doc_id}")
def delete_document(doc_id: str):
    """
    Deletes a document and its associated chunks from the knowledge base.
    Uses engine.begin() so the delete is committed automatically (unlike
    plain engine.connect(), which requires an explicit commit for DML).
    """
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM documents WHERE id = :id"),
            {"id": doc_id}
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Document not found")

        conn.execute(
            text("DELETE FROM document_chunks WHERE doc_id = :id"),
            {"id": doc_id}
        )
        conn.execute(
            text("DELETE FROM documents WHERE id = :id"),
            {"id": doc_id}
        )

    return {"status": "deleted", "id": doc_id}