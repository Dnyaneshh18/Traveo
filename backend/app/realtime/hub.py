"""
Traveo — Realtime hub.

A single in-process hub that fans out JSON events to connected WebSocket
clients.  Clients are addressed either directly (`user_id`) or via topics
(`ride:{id}`, `college:{id}`, `admin`).  The hub also keeps the **latest
live location** of every driver and rider so a reconnecting client (or the
admin live map) can get an instant snapshot.

For horizontal scaling the `publish` method can be bridged to Redis pub/sub;
for a single API instance (hackathon / small deployments) the in-memory hub
is complete.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import orjson
from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class LivePosition:
    user_id: str
    role: str
    lat: float
    lng: float
    heading: float | None = None
    speed: float | None = None
    accuracy: float | None = None
    ride_id: str | None = None
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "role": self.role,
            "lat": self.lat,
            "lng": self.lng,
            "heading": self.heading,
            "speed": self.speed,
            "accuracy": self.accuracy,
            "ride_id": self.ride_id,
            "updated_at": self.updated_at,
        }


class RealtimeHub:
    def __init__(self) -> None:
        self._user_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._topic_users: dict[str, set[str]] = defaultdict(set)
        self._user_topics: dict[str, set[str]] = defaultdict(set)
        self._positions: dict[str, LivePosition] = {}
        self._lock = asyncio.Lock()

    # ── connections ────────────────────────────────────────────────
    async def connect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._user_sockets[user_id].add(ws)
        logger.debug("ws_connected", user_id=user_id, sockets=len(self._user_sockets[user_id]))

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            sockets = self._user_sockets.get(user_id)
            if sockets:
                sockets.discard(ws)
                if not sockets:
                    self._user_sockets.pop(user_id, None)
                    for topic in list(self._user_topics.get(user_id, ())):
                        self._topic_users[topic].discard(user_id)
                    self._user_topics.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return bool(self._user_sockets.get(user_id))

    def online_count(self) -> int:
        return len(self._user_sockets)

    # ── topics ─────────────────────────────────────────────────────
    async def subscribe(self, user_id: str, topic: str) -> None:
        async with self._lock:
            self._topic_users[topic].add(user_id)
            self._user_topics[user_id].add(topic)

    async def unsubscribe(self, user_id: str, topic: str) -> None:
        async with self._lock:
            self._topic_users[topic].discard(user_id)
            self._user_topics[user_id].discard(topic)

    def topic_members(self, topic: str) -> set[str]:
        return set(self._topic_users.get(topic, ()))

    # ── publishing ─────────────────────────────────────────────────
    @staticmethod
    def _envelope(event: str, payload: dict[str, Any]) -> bytes:
        return orjson.dumps({"type": event, "payload": payload, "ts": time.time()})

    async def _send_raw(self, user_id: str, data: bytes) -> None:
        sockets = list(self._user_sockets.get(user_id, ()))
        for ws in sockets:
            try:
                await ws.send_text(data.decode())
            except Exception:
                await self.disconnect(user_id, ws)

    async def send_to_user(self, user_id: str, event: str, payload: dict[str, Any]) -> None:
        await self._send_raw(user_id, self._envelope(event, payload))

    async def send_to_users(self, user_ids: set[str] | list[str], event: str, payload: dict[str, Any]) -> None:
        data = self._envelope(event, payload)
        await asyncio.gather(*(self._send_raw(uid, data) for uid in set(user_ids)))

    async def publish(self, topic: str, event: str, payload: dict[str, Any], exclude: str | None = None) -> None:
        members = self.topic_members(topic)
        if exclude:
            members.discard(exclude)
        if members:
            await self.send_to_users(members, event, payload)

    async def broadcast_admin(self, event: str, payload: dict[str, Any]) -> None:
        await self.publish("admin", event, payload)

    # ── live positions ─────────────────────────────────────────────
    def update_position(self, pos: LivePosition) -> None:
        self._positions[pos.user_id] = pos

    def get_position(self, user_id: str) -> LivePosition | None:
        return self._positions.get(user_id)

    def clear_position(self, user_id: str) -> None:
        self._positions.pop(user_id, None)

    def positions(self, role: str | None = None, max_age_seconds: float | None = None) -> list[LivePosition]:
        now = time.time()
        out = []
        for p in self._positions.values():
            if role and p.role != role:
                continue
            if max_age_seconds is not None and now - p.updated_at > max_age_seconds:
                continue
            out.append(p)
        return out


hub = RealtimeHub()


def fire_and_forget(coro) -> None:
    """Schedule a coroutine from sync code paths without awaiting it."""
    with contextlib.suppress(RuntimeError):
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
