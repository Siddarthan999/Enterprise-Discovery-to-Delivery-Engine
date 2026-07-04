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
