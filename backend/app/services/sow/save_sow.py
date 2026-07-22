import json

from sqlalchemy import text

from app.core.postgres import engine


def save_generated_sow(
    title: str,
    markdown: str,
    author_id: int | None,
    state: dict | None = None,
    review: dict | None = None,
    confidence: dict | None = None,
    historical_sows_used: list | None = None,
    historical_risks_considered: list | None = None,
):
    with engine.begin() as conn:

        sow_id = conn.execute(
            text("""
            INSERT INTO sow_documents
            (
                title,
                author_id
            )
            VALUES
            (
                :title,
                :author
            )
            RETURNING id
            """),
            {
                "title": title,
                "author": author_id,
            },
        ).scalar()

        version_id = conn.execute(
            text("""
            INSERT INTO sow_versions
            (
                sow_id,
                version,
                markdown,
                created_by,
                review,
                confidence,
                historical_sows_used,
                historical_risks_considered,
                source_state_json
            )
            VALUES
            (
                :sow,
                1,
                :markdown,
                'AI Generator',
                CAST(:review AS JSONB),
                CAST(:confidence AS JSONB),
                CAST(:historical_sows_used AS JSONB),
                CAST(:historical_risks_considered AS JSONB),
                CAST(:source_state_json AS JSONB)
            )
            RETURNING id
            """),
            {
                "sow": sow_id,
                "markdown": markdown,
                "review": json.dumps(review) if review is not None else None,
                "confidence": json.dumps(confidence) if confidence is not None else None,
                "historical_sows_used": json.dumps(historical_sows_used) if historical_sows_used is not None else None,
                "historical_risks_considered": json.dumps(historical_risks_considered) if historical_risks_considered is not None else None,
                "source_state_json": json.dumps(state) if state is not None else None,
            },
        ).scalar()

    return {"sow_id": sow_id, "version_id": version_id}