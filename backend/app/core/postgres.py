import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set in environment variables")

engine = create_engine(DATABASE_URL)

def check_postgres():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}