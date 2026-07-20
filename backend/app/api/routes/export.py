from fastapi import APIRouter
from fastapi.responses import Response

from app.services.sow.sow_exporter import export_pdf, export_docx
from app.services.sow.template_store import get_template_path
from app.services.sow.cover_field_extractor import derive_cover_fields

router = APIRouter(tags=["export"])


@router.post("/sow/export")
def export_sow(payload: dict):

    sow_text = payload.get("sow")
    format_type = payload.get("format", "md")
    template_id = payload.get("template_id")
    discovery_state = payload.get("state")
    transcript = payload.get("transcript")

    if not sow_text:
        return {"error": "No SOW provided"}

    template_path = get_template_path(template_id)

    # Cover-page fields are derived automatically from the discovery
    # state / generated SOW / transcript — no manual entry required.
    cover_fields = derive_cover_fields(
        state=discovery_state,
        sow_markdown=sow_text,
        transcript=transcript,
    )
    print("DEBUG derived cover_fields:", cover_fields)

    # ---------------- DOCX ----------------
    if format_type == "docx":

        file_bytes = export_docx(
            sow_text=sow_text,
            template_path=template_path,
            cover_fields=cover_fields
        )

        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=sow.docx"}
        )

    # ---------------- PDF ----------------
    if format_type == "pdf":

        file_bytes = export_pdf(
            sow_text=sow_text,
            template_path=template_path,
            cover_fields=cover_fields
        )

        return Response(
            content=file_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=sow.pdf"}
        )

    # ---------------- MD ----------------
    return {
        "format": "md",
        "sow": sow_text
    }