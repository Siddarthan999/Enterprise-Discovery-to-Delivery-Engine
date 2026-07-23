import json

from sqlalchemy import text

from app.core.postgres import engine

from .jira_client import JiraClient
from .jira_mapper import map_jira_backlog


def push_jira_backlog(sow_id: int):
    """
    Pushes the generated Jira Backlog artifact into Jira.

    Order:
        Epic
            -> Feature (Story)
            -> User Stories
    """

    with engine.begin() as conn:

        artifact = conn.execute(
            text(
                """
                SELECT
                    id,
                    version,
                    content
                FROM delivery_artifacts
                WHERE sow_id=:sow
                  AND artifact_type='jira_backlog'
                """
            ),
            {
                "sow": sow_id,
            },
        ).mappings().first()

    if not artifact:
        raise Exception(
            "Generate the Jira Backlog artifact first."
        )

    backlog = artifact["content"]

    #
    # JSONB may come back as string depending on driver
    #
    if isinstance(backlog, str):
        backlog = json.loads(backlog)

    work_items = map_jira_backlog(backlog)

    jira = JiraClient()

    #
    # Keeps track of Epic Summary -> Jira Key
    #
    epic_keys = {}

    created = []

    for item in work_items:

        parent = None

        #
        # Stories belong under an Epic
        #
        if item["kind"] != "epic":
            parent = epic_keys[item["epic_id"]]

        issue = jira.create_issue(
            summary=item["summary"],
            description=item["description"],
            issue_type=item["issue_type"],
            parent_key=parent,
        )

        created.append(
            {
                "summary": item["summary"],
                "type": item["issue_type"],
                "jira_key": issue["key"],
                "url": f"{jira.base_url}/browse/{issue['key']}",
            }
        )

        #
        # Remember Epic key
        #
        if item["kind"] == "epic":
            epic_keys[item["epic_id"]] = issue["key"]

    #
    # Update delivery artifact
    #
    with engine.begin() as conn:

        conn.execute(
            text(
                """
                UPDATE delivery_artifacts
                SET
                    jira_created = TRUE,
                    jira_project_key = :project,
                    updated_at = NOW()
                WHERE sow_id = :sow
                  AND artifact_type = 'jira_backlog'
                """
            ),
            {
                "project": jira.project_key,
                "sow": sow_id,
            },
        )

    return {
        "success": True,
        "project": jira.project_key,
        "created": created,
    }