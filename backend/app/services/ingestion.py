from app.core.embedding import get_embedding
from app.services.chunking import chunk_text
from app.services.entity_extractor import extract_entities
from app.core.postgres import engine
from sqlalchemy import text
from app.core.neo4j import driver
from datetime import datetime


# ---------------- CLEANER ----------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").strip()


# ---------------- INGESTION ----------------
def ingest_document(doc):
    title = doc.get("title", "unknown")
    content = clean_text(doc.get("content", ""))
    doc_type = doc.get("type") or "unknown"
    source = doc.get("source", "upload")
    uploaded_at = datetime.utcnow()

    chunks = chunk_text(content)

    with engine.begin() as conn:

        # 1. INSERT DOCUMENT
        doc_id = conn.execute(
            text("""
                INSERT INTO documents (title, content, type, source, uploaded_at)
                VALUES (:t, :c, :ty, :s, :u)
                RETURNING id
            """),
            {
                "t": title,
                "c": content,
                "ty": doc_type,
                "s": source,
                "u": uploaded_at
            }
        ).fetchone()[0]

        # 2. INSERT CHUNKS (structured)
        for chunk in chunks:
            clean_chunk = clean_text(chunk["content"])

            embedding = get_embedding(clean_chunk)

            conn.execute(
                text("""
                    INSERT INTO document_chunks (
                        doc_id,
                        content,
                        embedding,
                        chunk_index,
                        start_word,
                        end_word,
                        type
                    )
                    VALUES (
                        :doc_id,
                        :c,
                        :e,
                        :idx,
                        :start,
                        :end,
                        :ty
                    )
                """),
                {
                    "doc_id": doc_id,
                    "c": clean_chunk,
                    "e": embedding,
                    "idx": chunk["index"],
                    "start": chunk["start_word"],
                    "end": chunk["end_word"],
                    "ty": doc_type
                }
            )

    # 3. ENTITY EXTRACTION
    entities = extract_entities(content)

    with driver.session() as session:

        session.run(
            """
            MERGE (d:Document {id: $id})
            SET d.title = $title,
                d.type = $type,
                d.source = $source
            """,
            id=doc_id,
            title=title,
            type=doc_type,
            source=source
        )

        for label, values in entities.items():

            # SAFE label handling (prevents Cypher injection)
            safe_label = (
                label[:-1].capitalize()
                if label.endswith("s")
                else label.capitalize()
            )

            for value in values:
                session.run(
                    f"""
                    MERGE (e:{safe_label} {{name: $name}})
                    WITH e
                    MATCH (d:Document {{id: $doc_id}})
                    MERGE (d)-[:HAS_{label.upper()}]->(e)
                    """,
                    name=value,
                    doc_id=doc_id
                )

    return {
        "doc_id": doc_id,
        "chunks": len(chunks),
        "type": doc_type,
        "source": source,
        "uploaded_at": uploaded_at.isoformat()
    }