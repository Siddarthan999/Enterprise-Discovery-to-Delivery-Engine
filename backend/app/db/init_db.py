from app.core.postgres import engine
from sqlalchemy import text

def init_db():
    with engine.begin() as conn:

        # ---------------- PGVECTOR EXTENSION ----------------
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # ---------------- DOCUMENTS TABLE ----------------
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            type TEXT,
            source TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
        """))

        # ---------------- DOCUMENT CHUNKS TABLE ----------------
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            doc_id INTEGER REFERENCES documents(id),
            content TEXT,
            embedding VECTOR(384),
            type TEXT,
            chunk_index INT,
            start_word INT,
            end_word INT
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS project_states (
            id SERIAL PRIMARY KEY,
            project_name TEXT,
            state_json JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """))

        # ---------------- HISTORICAL SOW SUPPORT ----------------
        # Tags every document with a category so historical SOWs can be
        # ingested through the SAME parsing/chunking/embedding pipeline as
        # regular knowledge-base docs, without polluting chat/search
        # results. ADD COLUMN IF NOT EXISTS is safe to re-run even though
        # `documents` already exists — existing rows default to
        # 'knowledge_base' so nothing already ingested changes behavior.
        conn.execute(text("""
        ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'knowledge_base'
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_documents_category ON documents (category)
        """))

        # Structured risk/mitigation pairs extracted from historical SOWs
        # at ingestion time. VECTOR(384) matches document_chunks above —
        # both use the same get_embedding() output, so they must match.
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sow_risk_examples (
            id SERIAL PRIMARY KEY,
            source_doc_id INT REFERENCES documents(id) ON DELETE CASCADE,
            risk_description TEXT NOT NULL,
            mitigation_approach TEXT,
            category TEXT,
            embedding VECTOR(384),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_sow_risk_examples_source_doc
            ON sow_risk_examples (source_doc_id)
        """))