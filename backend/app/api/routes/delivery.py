from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
import traceback

from app.core.postgres import engine
from app.services.delivery.builder import ( generate_delivery_artifact, generate_all_delivery_artifacts, )
from app.services.jira.importer import push_jira_backlog

router = APIRouter(tags=["Delivery"])


# --------------------------------------------------------------------
# Request Models
# --------------------------------------------------------------------

class GenerateArtifactRequest(BaseModel):
    sow_id: int
    artifact_type: str


class GenerateAllArtifactsRequest(BaseModel):
    sow_id: int


# --------------------------------------------------------------------
# Generate Single Artifact
# --------------------------------------------------------------------

@router.post("/delivery/generate")
def generate_artifact(payload: GenerateArtifactRequest):

    try:
        return generate_delivery_artifact(
            sow_id=payload.sow_id,
            artifact_type=payload.artifact_type,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# --------------------------------------------------------------------
# Generate All Artifacts
# --------------------------------------------------------------------

@router.post("/delivery/generate-all")
def generate_all(payload: GenerateAllArtifactsRequest):

    try:
        return generate_all_delivery_artifacts(
            sow_id=payload.sow_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# --------------------------------------------------------------------
# List Artifacts
# --------------------------------------------------------------------

@router.get("/delivery/{sow_id}/artifacts")
def get_artifacts(sow_id: int):

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

    with engine.begin() as conn:

        rows = conn.execute(
            text(
                """
                SELECT
                    artifact_type,
                    status,
                    jira_created,
                    jira_project_key,
                    updated_at
                FROM delivery_artifacts
                WHERE sow_id = :sow
                """
            ),
            {
                "sow": sow_id,
            },
        ).mappings().all()

    existing = {
        row["artifact_type"]: dict(row)
        for row in rows
    }

    result = []

    for artifact in artifact_types:

        if artifact in existing:

            result.append(existing[artifact])

        else:

            result.append(
                {
                    "artifact_type": artifact,
                    "status": "Not Generated",
                    "jira_created": False,
                    "jira_project_key": None,
                    "updated_at": None,
                }
            )

    return result


# --------------------------------------------------------------------
# Get Single Artifact
# --------------------------------------------------------------------

@router.get("/delivery/{sow_id}/artifact/{artifact_type}")
def get_artifact(
    sow_id: int,
    artifact_type: str,
):

    with engine.begin() as conn:

        row = conn.execute(
            text(
                """
                SELECT *
                FROM delivery_artifacts
                WHERE sow_id = :sow
                AND version = (
                    SELECT current_version
                    FROM sow_documents
                    WHERE id = :sow
                )
                AND artifact_type = :artifact
                """
            ),
            {
                "sow": sow_id,
                "artifact": artifact_type,
            },
        ).mappings().first()

    if not row:

        return {
            "artifact_type": artifact_type,
            "status": "Not Generated",
            "content": None,
            "jira_created": False,
            "jira_project_key": None,
        }

    return dict(row)

# --------------------------------------------------------------------
# Jira Backlog Push
# --------------------------------------------------------------------
@router.post("/delivery/{sow_id}/push-jira")
def push_to_jira(sow_id: int):
    """
    Pushes the generated Jira Backlog into Jira.
    """

    try:
        result = push_jira_backlog(sow_id)

        return {
            "success": True,
            "message": "Successfully created Jira issues.",
            **result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )