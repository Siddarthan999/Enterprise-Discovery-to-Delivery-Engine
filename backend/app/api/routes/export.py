from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional
import io

from app.core.postgres import engine
from app.services.sow.sow_exporter import export_pdf, export_docx
from app.services.sow.template_store import get_template_path
from app.services.sow.cover_field_extractor import derive_cover_fields
from app.services.email.email_service import send_sow_email


router = APIRouter(tags=["export"])


class EmailSOWRequest(BaseModel):
    sow: str
    format: str = "pdf"
    template_id: Optional[str] = None
    state: Optional[dict] = None
    transcript: Optional[str] = None
    sow_id: Optional[int] = None
    version: Optional[int] = None
    recipient_email: EmailStr
    sender_name: Optional[str] = None
    custom_message: Optional[str] = None
    mode: Optional[str] = "sow"


@router.post("/sow/export")
def export_sow(payload: dict):
    sow_text = payload.get("sow")
    format_type = payload.get("format", "md")
    template_id = payload.get("template_id")
    discovery_state = payload.get("state")
    transcript = payload.get("transcript")
    sow_id = payload.get("sow_id")
    version = payload.get("version")
    doc_type = payload.get("mode", "sow")

    if not sow_text:
        return {"error": "No SOW provided"}

    if discovery_state is None and sow_id and version:
        with engine.begin() as conn:
            discovery_state = conn.execute(text("""
                SELECT source_state_json
                FROM sow_versions
                WHERE sow_id = :sid
                AND version = :ver
            """), {
                "sid": sow_id,
                "ver": version,
            }).scalar()

            if discovery_state is None:
                discovery_state = conn.execute(text("""
                    SELECT source_state_json
                    FROM sow_versions
                    WHERE sow_id = :sid
                    AND version = 1
                """), {
                    "sid": sow_id,
                }).scalar()

    template_path = get_template_path(template_id)

    cover_fields = derive_cover_fields(
        state=discovery_state,
        sow_markdown=sow_text,
        transcript=transcript,
    )
    print("DEBUG derived cover_fields:", cover_fields)

    if format_type == "docx":
        file_bytes = export_docx(
            sow_text=sow_text,
            template_path=template_path,
            cover_fields=cover_fields,
            doc_type=doc_type,
        )

        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=sow.docx"}
        )

    if format_type == "pdf":
        file_bytes = export_pdf(
            sow_text=sow_text,
            template_path=template_path,
            cover_fields=cover_fields,
            doc_type=doc_type,
        )

        return Response(
            content=file_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=sow.pdf"}
        )

    return {
        "format": "md",
        "sow": sow_text
    }


@router.post("/sow/email")
async def email_sow(payload: EmailSOWRequest):
    """
    Generate SOW file and send it via email to the specified recipient
    """
    try:
        sow_text = payload.sow
        format_type = payload.format
        template_id = payload.template_id
        discovery_state = payload.state
        transcript = payload.transcript
        sow_id = payload.sow_id
        version = payload.version
        recipient_email = payload.recipient_email
        sender_name = payload.sender_name or "Enterprise OS Team"
        custom_message = payload.custom_message
        doc_type = payload.mode or "sow"

        if not sow_text:
            raise HTTPException(status_code=400, detail="No SOW content provided")

        if discovery_state is None and sow_id and version:
            with engine.begin() as conn:
                discovery_state = conn.execute(text("""
                    SELECT source_state_json
                    FROM sow_versions
                    WHERE sow_id = :sid
                    AND version = :ver
                """), {
                    "sid": sow_id,
                    "ver": version,
                }).scalar()

                if discovery_state is None:
                    discovery_state = conn.execute(text("""
                        SELECT source_state_json
                        FROM sow_versions
                        WHERE sow_id = :sid
                        AND version = 1
                    """), {
                        "sid": sow_id,
                    }).scalar()

        template_path = get_template_path(template_id)
        cover_fields = derive_cover_fields(
            state=discovery_state,
            sow_markdown=sow_text,
            transcript=transcript,
        )

        doc_title = "Statement of Work"
        if sow_id:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT title FROM sow_documents WHERE id = :sid
                """), {"sid": sow_id}).fetchone()
                if result:
                    doc_title = result[0]

        file_bytes = None
        filename = f"{doc_title.replace(' ', '_')}_v{version or 1}"

        if format_type == "docx":
            file_bytes = export_docx(
                sow_text=sow_text,
                template_path=template_path,
                cover_fields=cover_fields,
                doc_type=doc_type,
            )
            filename += ".docx"
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        elif format_type == "pdf":
            file_bytes = export_pdf(
                sow_text=sow_text,
                template_path=template_path,
                cover_fields=cover_fields,
                doc_type=doc_type,
            )
            filename += ".pdf"
            mime_type = "application/pdf"

        elif format_type == "md":
            file_bytes = sow_text.encode("utf-8")
            filename += ".md"
            mime_type = "text/markdown"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")

        success = await send_sow_email(
            recipient_email=recipient_email,
            sender_name=sender_name,
            doc_title=doc_title,
            version=version or 1,
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime_type,
            custom_message=custom_message
        )

        if success:
            return {
                "success": True,
                "message": f"SOW successfully sent to {recipient_email}",
                "recipient": recipient_email,
                "filename": filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")

    except Exception as e:
        print(f"Error sending SOW email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")