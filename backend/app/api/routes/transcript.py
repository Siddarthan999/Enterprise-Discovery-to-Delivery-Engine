from fastapi import APIRouter, UploadFile, File
from app.parsers.document_parser import parse_document
import tempfile
import os
from pydantic import BaseModel

router = APIRouter()


@router.post("/transcript/upload")
async def upload_transcript(file: UploadFile = File(...)):

    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tmp:

        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        doc = parse_document(tmp_path)

        return {
            "title": doc["title"],
            "transcript": doc["content"]
        }

    finally:
        os.remove(tmp_path)

class TranscriptTextRequest(BaseModel):
    title: str = "Untitled"
    transcript: str

@router.post("/transcript/text")
def transcript_text(payload: TranscriptTextRequest):

    text = payload.transcript or ""

    return {
        "title": payload.title,
        "transcript": text,
        "length": len(text.split())
    }