# api/websocket.py
from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/query/stream/{session_id}")
async def ws_query(websocket: WebSocket, session_id: str):
    await websocket.accept()
    await websocket.send_text("Streaming not yet implemented")
    await websocket.close()
