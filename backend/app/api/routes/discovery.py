from fastapi import APIRouter
from pydantic import BaseModel
from app.services.sow.project_extractor import extract_project_state
from app.services.sow.project_state_service import save_project_state

router = APIRouter()


class DiscoveryRequest(BaseModel):
    title: str = "Discovery Session"
    transcript: str


@router.post("/discovery/extract")
def discovery(payload: DiscoveryRequest):
    transcript = (payload.transcript or "").strip()

    if not transcript:
        return {
            "error": "Transcript is empty",
            "state": None
        }

    state = extract_project_state(transcript)

    if not isinstance(state, dict):
        return {
            "error": "Discovery extraction returned invalid state",
            "state": None
        }

    if state.get("error"):
        return {
            "title": payload.title,
            "error": f"Discovery extraction failed: {state['error']}",
            "state": state
        }

    save_project_state(payload.title, state)

    return {
        "title": payload.title,
        "state": state
    }