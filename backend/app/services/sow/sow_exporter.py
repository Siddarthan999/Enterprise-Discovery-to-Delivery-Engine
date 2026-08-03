from io import BytesIO
from docx import Document
from app.services.sow.template_engine import export_docx_from_template
import subprocess
import uuid
import os


# -----------------------------
# MARKDOWN (RAW)
# -----------------------------
def export_markdown(sow_text: str) -> str:
    return sow_text


# -----------------------------
# DOCX (TEMPLATE-BASED - FIXED)
# -----------------------------
def export_docx(
    sow_text: str,
    template_path: str | None = None,
    cover_fields: dict | None = None,
    doc_type: str = "sow",
) -> bytes:
    """
    Uses template engine (preserves branding, layout, headers, footer)
    """
    docx_bytes = export_docx_from_template(
        template_path=template_path,
        sow_markdown=sow_text,
        cover_fields=cover_fields,
        doc_type=doc_type,
    )
    return docx_bytes


# -----------------------------
# PDF (FIXED - TEMPLATE SAFE)
# -----------------------------
def export_pdf(
    sow_text: str,
    template_path: str | None = None,
    cover_fields: dict | None = None,
    doc_type: str = "sow",
) -> bytes:
    """
    Best practice:
    DOCX → PDF using LibreOffice (preserves formatting)
    """
    docx_bytes = export_docx_from_template(
        template_path=template_path,
        sow_markdown=sow_text,
        cover_fields=cover_fields,
        for_pdf=True,
        doc_type=doc_type,
    )

    tmp_id = str(uuid.uuid4())
    input_docx = f"/tmp/{tmp_id}.docx"
    output_dir = "/tmp"

    with open(input_docx, "wb") as f:
        f.write(docx_bytes)

    subprocess.run([
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        input_docx
    ], check=True)

    pdf_path = f"{output_dir}/{tmp_id}.pdf"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    os.remove(input_docx)
    os.remove(pdf_path)

    return pdf_bytes