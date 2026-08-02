import json
from sqlalchemy import text
from app.core.postgres import engine


def save_generated_proposal(
    title: str,
    markdown: str,
    author_id: int | None,
    state: dict,
    created_by: str = "system",
):
    """Persists a generated proposal as version 1 of a new proposal_documents
    row. Proposals are always freshly created (no in-place edit flow yet),
    mirroring the initial creation path of save_generated_sow but WITHOUT
    review/confidence/historical_* fields, since Proposal mode never calls
    the AI reviewer agents."""
    with engine.begin() as conn:
        doc_row = conn.execute(
            text("""
                INSERT INTO proposal_documents (title, author_id, current_version, status)
                VALUES (:title, :author_id, 1, 'Draft')
                RETURNING id
            """),
            {"title": title, "author_id": author_id},
        ).mappings().first()
        proposal_id = doc_row["id"]

        version_row = conn.execute(
            text("""
                INSERT INTO proposal_versions
                    (proposal_id, version, markdown, created_by, source_state_json)
                VALUES
                    (:proposal_id, 1, :markdown, :created_by, :state_json)
                RETURNING id
            """),
            {
                "proposal_id": proposal_id,
                "markdown": markdown,
                "created_by": created_by,
                "state_json": json.dumps(state),
            },
        ).mappings().first()
        version_id = version_row["id"]

    return {"proposal_id": proposal_id, "version_id": version_id}