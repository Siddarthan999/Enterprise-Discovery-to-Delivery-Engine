from fastapi import APIRouter
from sqlalchemy import text
import json
from app.core.postgres import engine
from pydantic import BaseModel
from app.core.llm_router import generate_completion

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