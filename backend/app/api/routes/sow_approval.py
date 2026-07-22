from fastapi import APIRouter
from sqlalchemy import text
import json
from app.core.postgres import engine
from pydantic import BaseModel
from app.core.llm_router import generate_completion
from difflib import HtmlDiff

from app.services.sow_history.sow_history_search import (
    search_similar_historical_risks,
    search_similar_historical_sows,
)
from app.services.sow_agents.sow_review_orchestrator import review_sow_draft
from app.services.sow_agents.sow_confidence import compute_sow_confidence
from app.services.sow.save_sow import save_generated_sow
from app.api.routes.sow import build_context_summary

router = APIRouter(prefix="/approval", tags=["approval"])

APPROVAL_FLOW = [
    "Architect",
    "Practice Lead",
    "Legal",
    "CFO",
    "Client",
]


class CommentRequest(BaseModel):
    sow_id: int
    version: int
    reviewer_role: str
    section: str
    comment: str
    selected_text:str|None=None
    start_offset:int|None=None
    end_offset:int|None=None

class ApproveRequest(BaseModel):
    sow_id: int
    reviewer_role: str

class RequestChangesRequest(BaseModel):
    sow_id: int
    reviewer_role: str
    comment_ids:list[int]

class DeleteCommentRequest(BaseModel):
    comment_id: int
    reviewer_role: str

class UpdateVersionRequest(BaseModel):
    sow_id:int
    markdown:str
    mode:str

class UpdateTitleRequest(BaseModel):
    sow_id: int
    title: str

class RunReviewRequest(BaseModel):
    sow_id: int
    version: int
    mode: str = "current"   # "current" or "new"

def _json_load_maybe(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value

def _get_version_context(conn, sow_id: int, version: int):
    version_row = conn.execute(text("""
        SELECT v.*, d.title, d.author_id, d.current_version, d.current_stage, d.status
        FROM sow_versions v
        JOIN sow_documents d ON d.id = v.sow_id
        WHERE v.sow_id = :sid
          AND v.version = :ver
    """), {"sid": sow_id, "ver": version}).mappings().first()

    if not version_row:
        return None

    doc = dict(version_row)

    for key in [
        "review",
        "confidence",
        "historical_sows_used",
        "historical_risks_considered",
    ]:
        doc[key] = _json_load_maybe(doc.get(key))

    state = {
        "project_name": doc.get("title") or "Untitled Project",
        "state_json": {},
    }

    context_summary = build_context_summary(state)

    historical_sows = search_similar_historical_sows(context_summary, limit=2)
    historical_risks = search_similar_historical_risks(context_summary, limit=4)

    return {
        "doc": doc,
        "historical_sows": historical_sows,
        "historical_risks": historical_risks,
        "review_markdown": doc.get("markdown") or "",
    }

def build_revision_prompt(markdown: str, comments: list[dict]):

    grouped = {}

    for c in comments:
        grouped.setdefault(c["section"], []).append(c["comment"])

    prompt = f"""
You are editing an EXISTING Statement of Work.

IMPORTANT RULES:

1. Keep EVERY heading exactly as it is.
2. Keep ALL sections unchanged unless explicitly mentioned.
3. Never remove sections.
4. Never summarize the document.
5. Never rewrite unaffected paragraphs.
6. Preserve formatting exactly.
7. If only one sentence changes, rewrite only that sentence.
8. Return the COMPLETE markdown document.

Current SOW

--------------------
{markdown}
--------------------

Reviewer comments:

"""

    for section, items in grouped.items():

        prompt += f"\n### {section}\n"

        for item in items:
            prompt += f"- {item}\n"

    prompt += """

Return ONLY the updated markdown.
"""

    return prompt

@router.get("/sows")
def list_sows():

    with engine.begin() as conn:

        rows = conn.execute(text("""
            SELECT
                d.id,
                d.title,
                d.current_version,
                d.current_stage,
                d.status,
                d.created_at,
                a.name AS author
            FROM sow_documents d
            LEFT JOIN sow_authors a
                ON a.id=d.author_id
            ORDER BY d.updated_at DESC
        """)).mappings().all()

    return [dict(r) for r in rows]

@router.get("/sows/{sow_id}")
def load_sow(sow_id:int):

    with engine.begin() as conn:

        doc = conn.execute(text("""
            SELECT *
            FROM sow_documents
            WHERE id=:id
        """),{"id":sow_id}).mappings().first()

        version = conn.execute(text("""
            SELECT v.*
            FROM sow_versions v
            JOIN sow_documents d
            ON d.id = v.sow_id
            WHERE d.id = :id
            AND v.version = d.current_version
        """),{"id":sow_id}).mappings().first()

    if not doc:
        return {"error": "SOW not found"}
    return {
        "document": dict(doc),
        "version": dict(version) if version else None,
    }

@router.get("/sows/{sow_id}/comments")
def comments(sow_id:int):

    with engine.begin() as conn:

        rows=conn.execute(text("""
            SELECT *
            FROM sow_comments
            WHERE sow_id=:id
            ORDER BY created_at
        """),{"id":sow_id}).mappings().all()

    return [dict(r) for r in rows]

@router.post("/comment")
def add_comment(req:CommentRequest):

    with engine.begin() as conn:

        conn.execute(text("""
            INSERT INTO sow_comments
            (
                sow_id,
                version,
                reviewer_role,
                section,
                comment,
                selected_text,
                start_offset,
                end_offset
            )
            VALUES
            (
                :sid,
                :ver,
                :role,
                :section,
                :comment,
                :selected_text,
                :start,
                :end
            )
        """),{

            "sid":req.sow_id,
            "ver":req.version,
            "role":req.reviewer_role,
            "section":req.section,
            "comment":req.comment,
            "selected_text":req.selected_text,
            "start":req.start_offset,
            "end":req.end_offset
        })

        conn.execute(text("""
            UPDATE sow_documents
            SET updated_at = NOW()
            WHERE id = :id
        """), {"id": req.sow_id})

    return {"success":True}

@router.post("/approve")
def approve(req:ApproveRequest):

    with engine.begin() as conn:

        row=conn.execute(text("""
            SELECT current_stage
            FROM sow_documents
            WHERE id=:id
        """),{"id":req.sow_id}).first()

        if not row:
            return {"error":"Not found"}

        current=row[0]

        if current!=req.reviewer_role:
            return {"error":"Not your stage"}

        if current not in APPROVAL_FLOW:
            return {"error": "Invalid approval stage"}

        index = APPROVAL_FLOW.index(current)

        if index==len(APPROVAL_FLOW)-1:

            conn.execute(text("""
                UPDATE sow_documents
                SET
                    status='Approved',
                    updated_at=NOW()
                WHERE id=:id
            """),{"id":req.sow_id})

            return {"status":"Approved"}

        next_stage=APPROVAL_FLOW[index+1]

        conn.execute(text("""
            UPDATE sow_documents
            SET
                current_stage=:stage,
                status='Pending',
                updated_at=NOW()
            WHERE id=:id
        """),{

            "stage":next_stage,
            "id":req.sow_id

        })

    return {
        "next_stage":next_stage
    }

@router.post("/request-changes")
def request_changes(req: RequestChangesRequest):

    with engine.begin() as conn:

        document = conn.execute(text("""
            SELECT *
            FROM sow_documents
            WHERE id=:id
        """), {"id": req.sow_id}).mappings().first()

        if not document:
            return {"error": "SOW not found"}

        if document["current_stage"] != req.reviewer_role:
            return {"error": "Not your review stage"}

        version = conn.execute(text("""
            SELECT *
            FROM sow_versions
            WHERE sow_id=:id
            ORDER BY version DESC
            LIMIT 1
        """), {"id": req.sow_id}).mappings().first()

        comments = conn.execute(text("""
            SELECT *
            FROM sow_comments
            WHERE sow_id=:id
            AND status='Open'
            AND id = ANY(:ids)
            ORDER BY created_at
        """), {"id": req.sow_id, "ids":req.comment_ids}).mappings().all()

        if not comments:
            return {"error": "No open comments"}

        prompt = build_revision_prompt(
            version["markdown"],
            [dict(c) for c in comments]
        )

        revised_markdown = generate_completion(prompt)

        next_version = version["version"] + 1

        conn.execute(text("""
            INSERT INTO sow_versions
            (
                sow_id,
                version,
                markdown,
                created_by,
                review,
                confidence,
                historical_sows_used,
                historical_risks_considered
            )
            VALUES
            (
                :sid,
                :version,
                :markdown,
                :created_by,
                :review,
                :confidence,
                :historical_sows,
                :historical_risks
            )
        """), {

            "sid": req.sow_id,
            "version": next_version,
            "markdown": revised_markdown,
            "created_by": "AI Revision",

            "review": json.dumps(version["review"]),
            "confidence": json.dumps(version["confidence"]),
            "historical_sows": json.dumps(version["historical_sows_used"]),
            "historical_risks": json.dumps(version["historical_risks_considered"]),

        })

        conn.execute(text("""
            UPDATE sow_documents
            SET
                current_version=:version,
                updated_at=NOW()
            WHERE id=:id
        """), {

            "version": next_version,
            "id": req.sow_id

        })

        conn.execute(text("""
            UPDATE sow_comments
            SET status='Closed'
            WHERE id = ANY(:ids)
        """), {

            "ids":req.comment_ids

        })

    return {
        "success": True,
        "version": next_version
    }

@router.get("/sows/{sow_id}/versions")
def list_versions(sow_id: int):

    with engine.begin() as conn:

        rows = conn.execute(text("""
            SELECT
                version,
                created_by,
                created_at
            FROM sow_versions
            WHERE sow_id=:id
            ORDER BY version DESC
        """), {"id": sow_id}).mappings().all()

    return [dict(r) for r in rows]

@router.get("/sows/{sow_id}/version/{version}")
def load_version(sow_id: int, version: int):

    with engine.begin() as conn:

        row = conn.execute(text("""
            SELECT *
            FROM sow_versions
            WHERE sow_id=:sid
            AND version=:version
        """),{

            "sid": sow_id,
            "version": version

        }).mappings().first()

    if not row:
        return {"error":"Version not found"}

    return dict(row)

@router.delete("/sows/{sow_id}")
def delete_sow(sow_id: int):

    with engine.begin() as conn:

        conn.execute(text("""
            DELETE
            FROM sow_documents
            WHERE id=:id
        """), {
            "id": sow_id
        })

    return {
        "success": True
    }

@router.delete("/sows/{sow_id}/version/{version}")
def delete_version(sow_id: int, version: int):

    with engine.begin() as conn:

        latest = conn.execute(text("""
            SELECT current_version
            FROM sow_documents
            WHERE id=:id
        """), {
            "id": sow_id
        }).scalar()

        if latest == 1:
            return {
                "error": "Cannot delete Version 1"
            }

        conn.execute(text("""
            DELETE
            FROM sow_versions
            WHERE sow_id=:sid
            AND version=:version
        """), {

            "sid": sow_id,
            "version": version

        })

        if latest == version:

            conn.execute(text("""
                UPDATE sow_documents
                SET
                    current_version=current_version-1,
                    updated_at=NOW()
                WHERE id=:id
            """), {

                "id": sow_id

            })

    return {
        "success": True
    }

@router.delete("/comment/{comment_id}")
def delete_comment(comment_id: int, reviewer_role: str):

    with engine.begin() as conn:

        comment = conn.execute(text("""
            SELECT reviewer_role
            FROM sow_comments
            WHERE id=:id
        """), {
            "id": comment_id
        }).mappings().first()

        if not comment:
            return {"error": "Comment not found"}

        if comment["reviewer_role"] != reviewer_role:
            return {"error": "Not allowed"}

        conn.execute(text("""
            DELETE
            FROM sow_comments
            WHERE id=:id
        """), {
            "id": comment_id
        })

    return {"success": True}

@router.post("/update-version")
def update_version(req: UpdateVersionRequest):

    with engine.begin() as conn:

        current = conn.execute(text("""
            SELECT current_version
            FROM sow_documents
            WHERE id=:id
        """),{
            "id":req.sow_id
        }).scalar()

        if req.mode == "current":

            conn.execute(text("""
                UPDATE sow_versions
                SET markdown=:markdown
                WHERE sow_id=:sid
                AND version=:ver
            """),{

                "markdown":req.markdown,
                "sid":req.sow_id,
                "ver":current

            })

        else:

            new_version = current + 1

            conn.execute(text("""
                INSERT INTO sow_versions
                (
                    sow_id,
                    version,
                    markdown,
                    created_by
                )
                SELECT
                    sow_id,
                    :new_version,
                    :markdown,
                    'Manual Edit'
                FROM sow_versions
                WHERE sow_id=:sid
                AND version=:current
            """),{

                "new_version":new_version,
                "markdown":req.markdown,
                "sid":req.sow_id,
                "current":current

            })

            conn.execute(text("""
                UPDATE sow_documents
                SET current_version=:ver
                WHERE id=:id
            """),{

                "ver":new_version,
                "id":req.sow_id

            })

    return {"success":True}

@router.post("/update-title")
def update_title(req: UpdateTitleRequest):

    with engine.begin() as conn:

        conn.execute(text("""
            UPDATE sow_documents
            SET
                title=:title,
                updated_at=NOW()
            WHERE id=:id
        """),{
            "title":req.title,
            "id":req.sow_id
        })

    return {"success":True}

@router.get("/sows/{sow_id}/compare/{v1}/{v2}")
def compare_versions(
    sow_id: int,
    v1: int,
    v2: int,
):
    with engine.begin() as conn:

        old = conn.execute(text("""
            SELECT markdown
            FROM sow_versions
            WHERE sow_id = :sid
            AND version = :v
        """), {
            "sid": sow_id,
            "v": v1
        }).scalar()

        new = conn.execute(text("""
            SELECT markdown
            FROM sow_versions
            WHERE sow_id = :sid
            AND version = :v
        """), {
            "sid": sow_id,
            "v": v2
        }).scalar()

    if old is None or new is None:
        return {
            "error": "One or both versions were not found."
        }

    diff = HtmlDiff().make_table(
        old.splitlines(),
        new.splitlines(),
        fromdesc=f"Version {v1}",
        todesc=f"Version {v2}"
    )

    return {
        "diff": diff
    }

@router.post("/sows/{sow_id}/version/{version}/run-review")
def run_review(sow_id: int, version: int, payload: RunReviewRequest):
    with engine.begin() as conn:
        ctx = _get_version_context(conn, sow_id, version)
        if not ctx:
            return {"error": "Version not found"}

        doc = ctx["doc"]
        historical_sows = ctx["historical_sows"]
        historical_risks = ctx["historical_risks"]
        review_markdown = ctx["review_markdown"]

        review = review_sow_draft(
            state={
                "project_name": doc.get("title") or "Untitled Project",
            },
            draft_markdown=review_markdown,
            historical_sows=historical_sows,
            historical_risks=historical_risks,
        )

        confidence = compute_sow_confidence(
            review_result=review,
            historical_sows=historical_sows,
            historical_risks=historical_risks,
            state={
                "project_name": doc.get("title") or "Untitled Project",
            },
            draft_markdown=review_markdown,
        )

        historical_sows_used = [
            {
                "doc_id": s.get("doc_id"),
                "title": s.get("title"),
                "score": s.get("score"),
            }
            for s in historical_sows
        ]

        review_json = json.dumps(review)
        confidence_json = json.dumps(confidence)
        hs_json = json.dumps(historical_sows_used)
        hr_json = json.dumps(historical_risks)

        if payload.mode == "current" or version == doc["current_version"]:
            conn.execute(text("""
                UPDATE sow_versions
                SET
                    review = CAST(:review AS JSONB),
                    confidence = CAST(:confidence AS JSONB),
                    historical_sows_used = CAST(:historical_sows_used AS JSONB),
                    historical_risks_considered = CAST(:historical_risks_considered AS JSONB)
                WHERE sow_id = :sid
                  AND version = :ver
            """), {
                "sid": sow_id,
                "ver": version,
                "review": review_json,
                "confidence": confidence_json,
                "historical_sows_used": hs_json,
                "historical_risks_considered": hr_json,
            })

            return {
                "success": True,
                "mode": "current",
                "sow_id": sow_id,
                "version": version,
                "review": review,
                "confidence": confidence,
                "historical_sows_used": historical_sows_used,
                "historical_risks_considered": historical_risks,
            }

        next_version = int(doc["current_version"]) + 1

        conn.execute(text("""
            INSERT INTO sow_versions
            (
                sow_id,
                version,
                markdown,
                created_by,
                review,
                confidence,
                historical_sows_used,
                historical_risks_considered
            )
            SELECT
                sow_id,
                :new_version,
                markdown,
                'AI Review',
                CAST(:review AS JSONB),
                CAST(:confidence AS JSONB),
                CAST(:historical_sows_used AS JSONB),
                CAST(:historical_risks_considered AS JSONB)
            FROM sow_versions
            WHERE sow_id = :sid
              AND version = :ver
        """), {
            "sid": sow_id,
            "ver": version,
            "new_version": next_version,
            "review": review_json,
            "confidence": confidence_json,
            "historical_sows_used": hs_json,
            "historical_risks_considered": hr_json,
        })

        conn.execute(text("""
            UPDATE sow_documents
            SET current_version = :new_version,
                updated_at = NOW()
            WHERE id = :sid
        """), {
            "sid": sow_id,
            "new_version": next_version,
        })

        return {
            "success": True,
            "mode": "new",
            "sow_id": sow_id,
            "version": next_version,
            "review": review,
            "confidence": confidence,
            "historical_sows_used": historical_sows_used,
            "historical_risks_considered": historical_risks,
        }