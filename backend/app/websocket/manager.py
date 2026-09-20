"""
Traveo Backend — WebSocket Connection Manager

Manages active client WebSocket connections.
Supports targeted unicast (user_id), group broadcast (group_id), and role broadcast.
"""

from __future__ import annotations

import json
from collections import defaultdict
import structlog
from fastapi import WebSocket

from app.websocket.events import WSEventMessage, WSEventType

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Thread-safe connection manager for WebSocket clients."""

    def __init__(self) -> None:
        # user_id -> set of WebSockets (one user can have multiple tabs/devices)
        self._user_connections: dict[str, set[WebSocket]] = defaultdict(set)
        # group_id -> set of user_ids
        self._group_subscribers: dict[str, set[str]] = defaultdict(set)
        # role -> set of WebSockets
        self._role_connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(
        self, websocket: WebSocket, user_id: str, role: str
    ) -> None:
        """Accept connection and index by user_id and role."""
        await websocket.accept()
        self._user_connections[user_id].add(websocket)
        self._role_connections[role].add(websocket)
        logger.info("ws_connected", user_id=user_id, role=role)

    def disconnect(self, websocket: WebSocket, user_id: str, role: str) -> None:
        """Remove connection on disconnect."""
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        if role in self._role_connections:
            self._role_connections[role].discard(websocket)
            if not self._role_connections[role]:
                del self._role_connections[role]

        logger.info("ws_disconnected", user_id=user_id, role=role)

    def subscribe_to_group(self, user_id: str, group_id: str) -> None:
        """Subscribe user to a ride group's real-time events."""
        self._group_subscribers[group_id].add(user_id)

    def unsubscribe_from_group(self, user_id: str, group_id: str) -> None:
        """Unsubscribe user from ride group."""
        if group_id in self._group_subscribers:
            self._group_subscribers[group_id].discard(user_id)

    # ── Dispatch / Broadcast Methods ──────────────────────

    async def send_to_user(
        self, user_id: str, event: WSEventType, payload: dict
    ) -> None:
        """Send message to a specific user across all their connected devices."""
        message = WSEventMessage(event=event, payload=payload).model_dump_json()
        sockets = self._user_connections.get(user_id, set())

        disconnected = set()
        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            sockets.discard(ws)

    async def broadcast_to_group(
        self, group_id: str, event: WSEventType, payload: dict
    ) -> None:
        """Broadcast message to all passengers and driver subscribed to a ride group."""
        users = self._group_subscribers.get(group_id, set())
        for user_id in users:
            await self.send_to_user(user_id, event, payload)

    async def broadcast_to_role(
        self, role: str, event: WSEventType, payload: dict
    ) -> None:
        """Broadcast message to all connected users of a specific role (e.g. admin)."""
        message = WSEventMessage(event=event, payload=payload).model_dump_json()
        sockets = self._role_connections.get(role, set())

        disconnected = set()
        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            sockets.discard(ws)


# Singleton instance
manager = ConnectionManager()
