import os
import tempfile

from annotated_types import doc

from fastapi import APIRouter, UploadFile, File
from sqlalchemy import text

from app.parsers.document_parser import parse_document
from app.services.ingestion import ingest_document
from app.services.sow_history.sow_risk_extractor import extract_risk_examples
from app.core.embedding import get_embedding
from app.core.postgres import engine
from app.core.neo4j import driver

router = APIRouter()


@router.post("/sow-history/upload")
async def upload_historical_sow(file: UploadFile = File(...)):
    """Ingests a past SOW as precedent material — same parsing/chunking/
    embedding pipeline as the general knowledge base, but tagged
    category='sow_history' so it never surfaces in chat or /search
    (see hybrid_search.py's category filter). Also extracts risk/
    mitigation pairs into sow_risk_examples for future SOW generation
    grounding and the upcoming Risk agent.
    """
    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        doc = parse_document(tmp_path)
        # Preserve original uploaded filename
        doc["title"] = file.filename
        ingest_result = ingest_document(doc, category="sow_history")
        doc_id = ingest_result["doc_id"]

        risk_examples = extract_risk_examples(doc["content"])

        stored_risks = 0
        with engine.begin() as conn:
            for risk in risk_examples:
                embedding = get_embedding(risk["risk_description"])
                conn.execute(
                    text("""
                        INSERT INTO sow_risk_examples
                            (source_doc_id, risk_description, mitigation_approach, category, embedding)
                        VALUES
                            (:doc_id, :desc, :mitigation, :category, :embedding)
                    """),
                    {
                        "doc_id": doc_id,
                        "desc": risk["risk_description"],
                        "mitigation": risk["mitigation_approach"],
                        "category": risk["category"],
                        "embedding": embedding,
                    }
                )
                stored_risks += 1

        return {
            "id": doc_id,
            "title": doc["title"],
            "type": doc["type"],
            "uploaded_at": ingest_result["uploaded_at"],
            "chunks": ingest_result["chunks"],
            "risk_examples_extracted": stored_risks,
        }

    finally:
        os.remove(tmp_path)


@router.get("/sow-history/list")
def list_historical_sows():
    """Includes risk_count per document — lets the Resources UI show
    '3 risks extracted' directly, which doubles as a quick sanity check
    that extraction actually worked without needing to query Postgres by hand."""
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    d.id,
                    d.title,
                    d.type,
                    d.uploaded_at,
                    COUNT(r.id) AS risk_count
                FROM documents d
                LEFT JOIN sow_risk_examples r ON r.source_doc_id = d.id
                WHERE d.category = 'sow_history'
                GROUP BY d.id, d.title, d.type, d.uploaded_at
                ORDER BY d.uploaded_at DESC
            """)
        ).mappings().all()

        return [dict(r) for r in rows]

@router.get("/sow-history/{doc_id}/risks")
def get_historical_sow_risks(doc_id: int):
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    id,
                    category,
                    risk_description,
                    mitigation_approach
                FROM sow_risk_examples
                WHERE source_doc_id = :doc_id
                ORDER BY id
            """),
            {"doc_id": doc_id},
        ).mappings().all()

    return [dict(r) for r in rows]

@router.delete("/sow-history/{doc_id}")
def delete_historical_sow(doc_id: int):
    """document_chunks has no ON DELETE CASCADE in your schema (see
    init_db.py), so chunks must be deleted explicitly before the document
    row — sow_risk_examples DOES cascade (defined that way in the schema
    above) so that cleans up automatically. Also removes the matching
    Neo4j node so it doesn't linger as an orphaned graph entry."""
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM document_chunks WHERE doc_id = :id"),
            {"id": doc_id}
        )
        result = conn.execute(
            text("DELETE FROM documents WHERE id = :id AND category = 'sow_history'"),
            {"id": doc_id}
        )
        deleted = result.rowcount > 0

    if deleted:
        with driver.session() as session:
            session.run("MATCH (d:Document {id: $id}) DETACH DELETE d", id=doc_id)

    return {"deleted": deleted, "id": doc_id}