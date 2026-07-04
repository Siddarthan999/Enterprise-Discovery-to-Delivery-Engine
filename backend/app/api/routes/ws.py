from fastapi import APIRouter, WebSocket
from app.ws.deepgram import deepgram_ws

router = APIRouter()

@router.websocket("/ws/transcribe")
async def transcribe_socket(websocket: WebSocket):
    await deepgram_ws(websocket)