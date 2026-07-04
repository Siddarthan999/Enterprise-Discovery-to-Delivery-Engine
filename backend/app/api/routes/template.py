from fastapi import APIRouter, UploadFile, File
from app.services.template_storage import (
    store_file,
    load_templates,
    save_templates
)
from app.services.template_parser import extract_sections

router = APIRouter()


@router.post("/upload")
async def upload_template(file: UploadFile = File(...)):

    content = await file.read()

    template_id, filename, path = store_file(content)

    parsed = extract_sections(path)

    templates = load_templates()

    templates.append({
        "id": template_id,
        "name": file.filename,
        "filename": filename,
        "sections": parsed["sections"]
    })

    save_templates(templates)

    return {
        "id": template_id,
        "sections": parsed["sections"]
    }


@router.get("/list")
def list_templates():
    return load_templates()