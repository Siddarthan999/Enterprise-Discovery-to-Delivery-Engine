from fastapi import APIRouter
from pydantic import BaseModel
from app.services.project_extractor import extract_project_state
from app.services.project_state_service import save_project_state

router = APIRouter()


class DiscoveryRequest(BaseModel):
    title: str = "Discovery Session"
    transcript: str


@router.post("/discovery/extract")
def discovery(payload: DiscoveryRequest):

    transcript = payload.transcript

    if not transcript:
        return {
            "error": "Transcript is empty",
            "state": None
        }

    state = extract_project_state(transcript)

    save_project_state(
        payload.title,
        state
    )

    return {
        "title": payload.title,
        "state": state
    }