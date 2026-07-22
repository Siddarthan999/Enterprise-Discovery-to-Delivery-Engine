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
        
        # ---------------- SOW AUTHORS ----------------
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sow_authors (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """))

        # ---------------- SOW DOCUMENTS ----------------
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sow_documents (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author_id INT REFERENCES sow_authors(id),
            current_version INT DEFAULT 1,
            current_stage TEXT DEFAULT 'Architect',
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """))

        # ---------------- SOW VERSIONS ----------------
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sow_versions (
            id SERIAL PRIMARY KEY,
            sow_id INT REFERENCES sow_documents(id) ON DELETE CASCADE,
            version INT NOT NULL,
            markdown TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT NOW(),

            -- Reviewer output for this version
            review JSONB,

            -- Confidence scores and reasoning
            confidence JSONB,

            -- Historical references used during review
            historical_sows_used JSONB,
            historical_risks_considered JSONB,

            source_state_json JSONB,

            UNIQUE (sow_id, version)
        )
        """))

        conn.execute(text("""
            ALTER TABLE sow_versions
            ADD COLUMN IF NOT EXISTS source_state_json JSONB
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sow_comments (
            id SERIAL PRIMARY KEY,
            sow_id INT REFERENCES sow_documents(id) ON DELETE CASCADE,
            version INT,
            reviewer_role TEXT,
            section TEXT,
            comment TEXT,
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """))

        conn.execute(text("""
        ALTER TABLE sow_comments
        ADD COLUMN IF NOT EXISTS selected_text TEXT
        """))

        conn.execute(text("""
        ALTER TABLE sow_comments
        ADD COLUMN IF NOT EXISTS start_offset INT
        """))

        conn.execute(text("""
        ALTER TABLE sow_comments
        ADD COLUMN IF NOT EXISTS end_offset INT
        """))