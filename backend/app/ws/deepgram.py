import os
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from deepgram import DeepgramClient
from deepgram.clients.live.v1 import LiveOptions, LiveTranscriptionEvents

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


async def deepgram_ws(websocket: WebSocket):
    await websocket.accept()

    dg_client = DeepgramClient(DEEPGRAM_API_KEY)
    dg_connection = dg_client.listen.websocket.v("1")

    loop = asyncio.get_running_loop()
    transcript_buffer = []

    async def send(payload):
        try:
            await websocket.send_json(payload)
        except Exception:
            pass

    def emit(payload):
        loop.call_soon_threadsafe(asyncio.create_task, send(payload))

    # ---------------- EVENTS ----------------
    def on_message(*args, **kwargs):
        try:
            result = kwargs.get("result") or (args[0] if args else None)
            if not result:
                return

            sentence = result.channel.alternatives[0].transcript

            if sentence:
                transcript_buffer.append(sentence)
                emit({
                    "type": "transcript",
                    "text": sentence
                })

        except Exception as e:
            emit({"type": "error", "error": str(e)})

    def on_close(*args, **kwargs):
        emit({
            "type": "closed",
            "full_transcript": " ".join(transcript_buffer)
        })

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)

    # ✅ IMPORTANT: WEBM CONFIG (THIS IS THE FIX)
    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        interim_results=True,
        vad_events=True,
    )

    started = dg_connection.start(options)
    if not started:
        await websocket.send_json({"type": "error", "error": "Failed to connect to Deepgram"})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_bytes()

            if data:
                dg_connection.send(data)

    except WebSocketDisconnect:
        pass

    finally:
        try:
            dg_connection.finish()
        except:
            pass

        # Only close if still connected
        try:
            await websocket.close()
        except (RuntimeError, Exception):
            pass  # Already closed by disconnect