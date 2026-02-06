from fastapi import APIRouter, WebSocket
from app.services.live_session import GeminiLiveSession

router = APIRouter()

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    session = GeminiLiveSession()
    await session.start(websocket)
