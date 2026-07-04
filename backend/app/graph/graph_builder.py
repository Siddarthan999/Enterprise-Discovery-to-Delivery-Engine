from neo4j import GraphDatabase
import os

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)


# ---------------- SAFE NODE CREATION ----------------
def create_entity(tx, label: str, name: str):
    tx.run(
        f"""
        MERGE (e:{label} {{name: toLower($name)}})
        """,
        name=name
    )


# ---------------- SAFE RELATIONSHIP ----------------
def create_relationship(tx, from_label: str, from_name: str,
                        rel: str,
                        to_label: str, to_name: str):

    tx.run(
        f"""
        MERGE (a:{from_label} {{name: toLower($from_name)}})
        MERGE (b:{to_label} {{name: toLower($to_name)}})
        MERGE (a)-[:{rel}]->(b)
        """,
        from_name=from_name,
        to_name=to_name
    )


# ---------------- DOCUMENT LINKING ----------------
def link_document(tx, doc_id: int, title: str, doc_type: str):
    tx.run(
        """
        MERGE (d:Document {id: $id})
        SET d.title = $title,
            d.type = $type
        """,
        id=doc_id,
        title=title,
        type=doc_type
    )