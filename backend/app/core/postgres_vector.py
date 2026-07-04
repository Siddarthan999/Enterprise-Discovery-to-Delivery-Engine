from sqlalchemy import text
from app.core.postgres import engine

def store_chunk(title, content, embedding, doc_type):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO documents (title, content, embedding, type)
                VALUES (:title, :content, :embedding, :type)
            """),
            {
                "title": title,
                "content": content,
                "embedding": embedding,
                "type": doc_type
            }
        )
        conn.commit()