"""
Traveo Backend — WebSocket Router

Endpoint for real-time WebSocket connections.
Authenticates clients during handshake using JWT token query parameter.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import verify_access_token
from app.websocket.manager import manager

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    WebSocket connection endpoint.
    Example: wss://api.traveo.com/ws?token=eyJhbG...
    """
    # Authenticate token during handshake
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized: Invalid token")
        return

    user_id = payload.get("sub")
    role = payload.get("role", "passenger")

    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized: Missing subject")
        return

    # Accept & register connection
    await manager.connect(websocket, user_id, role)

    try:
        while True:
            # Handle incoming ping/pong or client messages
            data = await websocket.receive_text()
            # Echo or process client messages (e.g. driver location updates)
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, role)
    except Exception as e:
        logger.warning("ws_error", user_id=user_id, error=str(e))
        manager.disconnect(websocket, user_id, role)
