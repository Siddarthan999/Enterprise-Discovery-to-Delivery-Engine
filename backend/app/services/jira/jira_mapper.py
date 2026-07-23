from typing import List, Dict


def map_jira_backlog(backlog: dict) -> List[Dict]:
    """
    Converts the generated Jira Backlog artifact into
    an ordered list of Jira work items.

    Order is important:
    Epic
        -> Stories (Features)
        -> Stories (User Stories)
    """

    work_items = []

    for epic in backlog.get("epics", []):

        epic_id = epic["summary"]

        #
        # Epic
        #
        work_items.append(
            {
                "kind": "epic",
                "epic_id": epic_id,
                "summary": epic["summary"],
                "description": epic.get("description", ""),
                "issue_type": "Epic",
            }
        )

        #
        # Features
        #
        for feature in epic.get("features", []):

            work_items.append(
                {
                    "kind": "feature",
                    "epic_id": epic_id,
                    "summary": feature["summary"],
                    "description": feature.get("description", ""),
                    "issue_type": "Story",
                }
            )

            #
            # User Stories
            #
            for story in feature.get("stories", []):

                acceptance = "\n".join(
                    [
                        f"• {item}"
                        for item in story.get(
                            "acceptance_criteria",
                            [],
                        )
                    ]
                )

                description = f"""
Priority:
{story.get("priority", "")}

Story Points:
{story.get("story_points", "")}

Description:
{story.get("description", "")}

Acceptance Criteria:

{acceptance}
""".strip()

                work_items.append(
                    {
                        "kind": "story",
                        "epic_id": epic_id,
                        "summary": story["summary"],
                        "description": description,
                        "issue_type": "Story",
                    }
                )

    return work_items