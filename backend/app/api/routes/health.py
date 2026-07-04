from fastapi import APIRouter

from app.core.postgres import check_postgres
from app.core.neo4j import check_neo4j
from app.core.gemini import check_gemini

router = APIRouter()


@router.get("/health/postgres")
def postgres_health():
    return check_postgres()


@router.get("/health/neo4j")
def neo4j_health():
    return check_neo4j()


@router.get("/health/gemini")
def gemini_health():
    return check_gemini()