from io import BytesIO
from docx import Document
from app.services.template_engine import export_docx_from_template
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
def export_docx(sow_text: str, template_path: str | None = None,
                 cover_fields: dict | None = None) -> bytes:
    """
    Uses template engine (preserves branding, layout, headers, footer)
    """

    docx_bytes = export_docx_from_template(
        template_path=template_path,
        sow_markdown=sow_text,
        cover_fields=cover_fields
    )

    return docx_bytes


# -----------------------------
# PDF (FIXED - TEMPLATE SAFE)
# -----------------------------
def export_pdf(sow_text: str, template_path: str | None = None,
                cover_fields: dict | None = None) -> bytes:
    """
    Best practice:
    DOCX → PDF using LibreOffice (preserves formatting)
    """

    # 1. generate DOCX first (WITH TEMPLATE)
    docx_bytes = export_docx_from_template(
        template_path=template_path,
        sow_markdown=sow_text,
        cover_fields=cover_fields,
        for_pdf=True
    )

    tmp_id = str(uuid.uuid4())
    input_docx = f"/tmp/{tmp_id}.docx"
    output_dir = "/tmp"

    # 2. write docx to disk
    with open(input_docx, "wb") as f:
        f.write(docx_bytes)

    # 3. convert using LibreOffice
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

    # 4. read result
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 5. cleanup
    os.remove(input_docx)
    os.remove(pdf_path)

    return pdf_bytes