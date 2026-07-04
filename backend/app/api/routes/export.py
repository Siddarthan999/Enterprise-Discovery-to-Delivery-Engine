from fastapi import APIRouter
from fastapi.responses import Response

from app.services.sow_exporter import export_pdf, export_docx
from app.services.template_store import get_template_path

router = APIRouter()


@router.post("/sow/export")
def export_sow(payload: dict):

    sow_text = payload.get("sow")
    format_type = payload.get("format", "md")
    template_id = payload.get("template_id")

    if not sow_text:
        return {"error": "No SOW provided"}

    template_path = get_template_path(template_id)

    # ---------------- DOCX ----------------
    if format_type == "docx":

        file_bytes = export_docx(
            sow_text=sow_text,
            template_path=template_path
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
            template_path=template_path
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