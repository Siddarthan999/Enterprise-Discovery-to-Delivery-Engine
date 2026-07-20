# app/api/routes/answer.py
from fastapi import APIRouter
from pydantic import BaseModel
import uuid

from app.services.rag import generate_answer

router = APIRouter(tags=["answer"])


class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None


@router.post("/answer")
def answer(req: QuestionRequest):
    session_id = req.session_id or str(uuid.uuid4())
    result = generate_answer(req.question, session_id)
    result["session_id"] = session_id
    return result