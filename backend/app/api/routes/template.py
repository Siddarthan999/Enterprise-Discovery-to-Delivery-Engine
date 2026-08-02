from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.sow.template_storage import (
    store_file,
    load_templates,
    save_templates
)
from app.services.sow.template_parser import extract_sections
from app.services.sow.template_pptx_parser import extract_pptx_outline

router = APIRouter(tags=["templates"])

ALLOWED_EXTENSIONS = {"docx", "pptx", "potx"}
PPTX_EXTENSIONS = {"pptx", "potx"}


@router.post("/upload")
async def upload_template(file: UploadFile = File(...)):
    original_name = file.filename or ""
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported template file type. Upload a .docx, .pptx, or .potx file.",
        )

    content = await file.read()

    template_id, filename, path = store_file(content, ext)

    is_pptx = ext in PPTX_EXTENSIONS
    parsed = extract_pptx_outline(path) if is_pptx else extract_sections(path)

    templates = load_templates()

    templates.append({
        "id": template_id,
        "name": file.filename,
        "filename": filename,
        "type": "pptx" if is_pptx else "docx",
        "sections": parsed.get("sections", []),
        "slide_count": parsed.get("slide_count"),
    })

    save_templates(templates)

    return {
        "id": template_id,
        "type": "pptx" if is_pptx else "docx",
        "sections": parsed.get("sections", []),
    }


@router.get("/list")
def list_templates():
    return load_templates()


@router.delete("/{template_id}")
def delete_template(template_id: str):
    templates = load_templates()
    updated = [t for t in templates if t["id"] != template_id]

    if len(updated) == len(templates):
        raise HTTPException(status_code=404, detail="Template not found")

    save_templates(updated)

    return {"status": "deleted", "id": template_id}