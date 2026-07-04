from sqlalchemy import text
from app.core.postgres import engine


def save_project_state(project_name, state):

    with engine.begin() as conn:

        conn.execute(
            text("""
            INSERT INTO project_states
            (
                project_name,
                state_json
            )
            VALUES
            (
                :name,
                CAST(:state AS jsonb)
            )
            """),
            {
                "name": project_name,
                "state": __import__("json").dumps(state)
            }
        )