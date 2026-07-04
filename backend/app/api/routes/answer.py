from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag import generate_answer

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/answer")
def answer(req: QuestionRequest):

    return generate_answer(req.question)