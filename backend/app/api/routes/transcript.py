from fastapi import APIRouter, UploadFile, File
from app.parsers.document_parser import parse_document
import tempfile
import os
from pydantic import BaseModel
from typing import List

router = APIRouter(tags=["transcripts"])


@router.post("/transcript/upload")
async def upload_transcript(files: List[UploadFile] = File(...)):
    combined_text = []
    titles = []

    for file in files:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            doc = parse_document(tmp_path)
            titles.append(doc["title"])
            combined_text.append(
                f"""
    ==============================
    FILE: {doc["title"]}
    TYPE: {doc.get("type","unknown")}
    ==============================

    {doc["content"]}
    """
            )
        finally:
            os.remove(tmp_path)
    return {
        "title": "Client Context",
        "files": titles,
        "transcript": "\n\n".join(combined_text)
    }

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