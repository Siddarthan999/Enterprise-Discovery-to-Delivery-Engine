from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


def check_neo4j():
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}