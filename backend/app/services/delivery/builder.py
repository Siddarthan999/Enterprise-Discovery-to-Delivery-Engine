import json
import re

from sqlalchemy import text

from app.core.llm_router import generate_completion
from app.core.postgres import engine

from .prompts import build_delivery_prompt


def _extract_json(response: str):
    """
    LLMs occasionally wrap JSON inside ```json ... ```
    or add extra text. Extract the first JSON object/array.
    """

    if not response:
        return None

    response = response.strip()

    if response.startswith("```"):
        response = re.sub(r"^```(?:json)?", "", response).strip()
        response = re.sub(r"```$", "", response).strip()

    try:
        return json.loads(response)
    except Exception:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except Exception:
        return None


def get_sow_markdown(sow_id: int) -> str:
    """
    Always generate artifacts from the CURRENT approved version.
    """

    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT v.markdown
                FROM sow_documents d
                JOIN sow_versions v
                  ON d.id = v.sow_id
                 AND d.current_version = v.version
                WHERE d.id = :id
                """
            ),
            {"id": sow_id},
        ).mappings().first()

    if not row:
        raise Exception("SOW not found")

    return row["markdown"]


def save_artifact(
    sow_id: int,
    artifact_type: str,
    content: dict,
):
    """
    Inserts on first generation.
    Updates on regeneration.
    One artifact is stored per SOW version.
    """

    with engine.begin() as conn:

        # Get current SOW version
        version = conn.execute(
            text("""
                SELECT current_version
                FROM sow_documents
                WHERE id = :sow
            """),
            {"sow": sow_id},
        ).scalar()

        if version is None:
            raise Exception(f"SOW {sow_id} not found")

        exists = conn.execute(
            text("""
                SELECT id
                FROM delivery_artifacts
                WHERE sow_id = :sow
                  AND version = :version
                  AND artifact_type = :artifact
            """),
            {
                "sow": sow_id,
                "version": version,
                "artifact": artifact_type,
            },
        ).scalar()

        payload = json.dumps(content)

        if exists:

            conn.execute(
                text("""
                    UPDATE delivery_artifacts
                    SET
                        content = CAST(:content AS JSONB),
                        status = 'Generated',
                        updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "id": exists,
                    "content": payload,
                },
            )

        else:

            conn.execute(
                text("""
                    INSERT INTO delivery_artifacts
                    (
                        sow_id,
                        version,
                        artifact_type,
                        content,
                        status
                    )
                    VALUES
                    (
                        :sow,
                        :version,
                        :artifact,
                        CAST(:content AS JSONB),
                        'Generated'
                    )
                """),
                {
                    "sow": sow_id,
                    "version": version,
                    "artifact": artifact_type,
                    "content": payload,
                },
            )


def generate_delivery_artifact(
    sow_id: int,
    artifact_type: str,
):
    """
    Main entry point used by the API.
    """

    sow = get_sow_markdown(sow_id)

    prompt = build_delivery_prompt(
        artifact_type,
        sow,
    )

    llm_response = generate_completion(prompt)

    parsed = _extract_json(llm_response)

    if parsed is None:
        raise Exception(
            f"LLM returned invalid JSON for {artifact_type}"
        )

    save_artifact(
        sow_id=sow_id,
        artifact_type=artifact_type,
        content=parsed,
    )

    return {
        "artifact_type": artifact_type,
        "status": "Generated",
        "content": parsed,
    }


def generate_all_delivery_artifacts(sow_id: int):

    artifact_types = [
        "jira_backlog",
        "raid_register",
        "project_plan",
        "sprint_plan",
        "resource_plan",
        "stakeholder_matrix",
        "raci_matrix",
        "development_order",
    ]

    generated = []
    failed = []

    for artifact in artifact_types:

        try:

            generate_delivery_artifact(
                sow_id,
                artifact,
            )

            generated.append(artifact)

        except Exception as e:

            print(f"{artifact}: {e}")

            failed.append(
                {
                    "artifact": artifact,
                    "error": str(e),
                }
            )

    return {
        "generated": generated,
        "failed": failed,
    }