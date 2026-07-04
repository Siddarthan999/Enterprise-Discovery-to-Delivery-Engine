from fastapi import APIRouter
from app.graph.graph_builder import driver

router = APIRouter()


@router.get("/graph/search")
def graph_search(query: str):

    with driver.session() as session:
        result = session.run(
            """
            MATCH (d:Document)
            WHERE toLower(d.title) CONTAINS toLower($q)
            RETURN d
            LIMIT 20
            """,
            q=query
        )

        return [r["d"] for r in result]


# from fastapi import APIRouter
# from app.graph.graph_builder import driver

# router = APIRouter()


# # ---------------- ROOT GRAPH FETCH ----------------
# @router.get("/graph/search")
# def graph_search(query: str):
#     with driver.session() as session:
#         result = session.run(
#             """
#             MATCH (d:Document)
#             WHERE toLower(d.title) CONTAINS toLower($q)
#             OPTIONAL MATCH (d)-[r]->(n)
#             RETURN d, collect({rel: type(r), node: n}) AS relations
#             LIMIT 10
#             """,
#             q=query
#         )

#         output = []

#         for record in result:
#             d = record["d"]
#             relations = record["relations"]

#             output.append({
#                 "id": d["id"],
#                 "title": d.get("title"),
#                 "type": d.get("type"),
#                 "source": d.get("source"),
#                 "relations": [
#                     {
#                         "type": rel["rel"],
#                         "target": dict(rel["node"]) if rel["node"] else None
#                     }
#                     for rel in relations if rel["node"]
#                 ]
#             })

#         return output


# # ---------------- NODE EXPANSION (IMPORTANT) ----------------
# @router.get("/graph/expand/{doc_id}")
# def expand_node(doc_id: int):

#     with driver.session() as session:
#         result = session.run(
#             """
#             MATCH (d:Document {id: $id})-[r]->(n)
#             RETURN type(r) AS rel, n
#             """,
#             id=doc_id
#         )

#         return [
#             {
#                 "relationship": r["rel"],
#                 "node": dict(r["n"])
#             }
#             for r in result
#         ]