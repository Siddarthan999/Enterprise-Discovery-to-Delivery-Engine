from fastapi import APIRouter, UploadFile, File
from app.services.ingestion import ingest_document
from app.core.parsers import parse_document
import shutil
import os

router = APIRouter()


@router.post("/ingest/document")
async def ingest(file: UploadFile = File(...)):

    file_path = f"/tmp/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = parse_document(file_path)

    result = ingest_document(doc)

    os.remove(file_path)

    return result