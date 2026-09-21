"""
WebSocket endpoint — `/ws?token=<access_token>`

Client → server messages (JSON):
  {"type": "ping"}
  {"type": "subscribe", "topic": "ride:<request_id>"}          (members / driver only)
  {"type": "location", "lat": .., "lng": .., "heading": .., "speed": .., "accuracy": ..}
      • drivers: stored + fanned out to the ride group + admin map
      • students with an active ride: fanned out to the driver (so the driver
        sees riders walking to the pickup) + admin map

Server → client: {"type": "<event>", "payload": {...}, "ts": <unix>}
Events: feed.request_created / feed.request_updated / feed.request_removed,
group.member_joined / group.member_left / group.locked / group.reopened / group.removed,
dispatch.status / dispatch.offer / dispatch.offer_expired,
ride.driver_assigned / ride.driver_location / ride.rider_location / ride.driver_arrived /
ride.member_picked_up / ride.member_dropped / ride.member_no_show / ride.completed /
ride.cancelled / ride.driver_cancelled / ride.no_driver / ride.expired, notification, profile.updated
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.core.deps import resolve_user_from_token
from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger
from app.models import ACTIVE_MEMBER_STATUSES, ACTIVE_REQUEST_STATUSES, DriverProfile, RideMember, RideRequest, UserRole
from app.realtime.hub import LivePosition, hub
from app.services.events import college_topic, ride_topic

router = APIRouter(tags=["Realtime"])
settings = get_settings()
logger = get_logger(__name__)


async def _initial_topics(user_id: str, role: str, college_id: str | None) -> tuple[list[str], str | None]:
    """Topics to auto-subscribe on connect + the user's active request id (if any)."""
    topics: list[str] = []
    active_request_id: str | None = None
    async with SessionFactory() as db:
        if role == UserRole.ADMIN:
            topics.append("admin")
        if role == UserRole.STUDENT and college_id:
            topics.append(college_topic(college_id))
            row = await db.scalar(
                select(RideMember.request_id)
                .join(RideRequest, RideRequest.id == RideMember.request_id)
                .where(RideMember.user_id == user_id, RideMember.status.in_(ACTIVE_MEMBER_STATUSES), RideRequest.status.in_(ACTIVE_REQUEST_STATUSES))
                .order_by(RideRequest.created_at.desc())
                .limit(1)
            )
            if row:
                active_request_id = row
                topics.append(ride_topic(row))
        if role == UserRole.DRIVER:
            from app.models import Ride, RideStatus

            row = await db.scalar(
                select(Ride.request_id)
                .where(Ride.driver_user_id == user_id, Ride.status.in_((RideStatus.DRIVER_ASSIGNED, RideStatus.IN_PROGRESS)))
                .order_by(Ride.created_at.desc())
                .limit(1)
            )
            if row:
                active_request_id = row
                topics.append(ride_topic(row))
    return topics, active_request_id


async def _authorised_for_topic(user_id: str, role: str, topic: str) -> bool:
    if topic == "admin":
        return role == UserRole.ADMIN
    if topic.startswith("ride:"):
        request_id = topic.split(":", 1)[1]
        async with SessionFactory() as db:
            member = await db.scalar(select(RideMember.id).where(RideMember.request_id == request_id, RideMember.user_id == user_id))
            if member:
                return True
            from app.models import Ride

            ride = await db.scalar(select(Ride.id).where(Ride.request_id == request_id, Ride.driver_user_id == user_id))
            return bool(ride) or role == UserRole.ADMIN
    if topic.startswith("college:"):
        return True  # validated on connect via profile
    return False


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None):
    raw = token or (websocket.headers.get("authorization") or "").replace("Bearer ", "").strip()
    try:
        async with SessionFactory() as db:
            current = await resolve_user_from_token(db, raw)
            college_id = current.student.college_id if current.student else None
    except UnauthorizedError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    user_id, role = current.id, str(current.role)
    await hub.connect(user_id, websocket)
    topics, active_request_id = await _initial_topics(user_id, role, college_id)
    for t in topics:
        await hub.subscribe(user_id, t)
    await websocket.send_text(json.dumps({"type": "connected", "payload": {"user_id": user_id, "role": role, "topics": topics, "active_request_id": active_request_id, "heartbeat": settings.WS_HEARTBEAT_SECONDS}, "ts": time.time()}))

    last_db_write = 0.0

    async def heartbeat():
        while True:
            await asyncio.sleep(settings.WS_HEARTBEAT_SECONDS)
            with contextlib.suppress(Exception):
                await websocket.send_text(json.dumps({"type": "ping", "payload": {}, "ts": time.time()}))

    hb = asyncio.create_task(heartbeat())
    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                continue
            mtype = msg.get("type")
            if mtype in ("ping", "pong"):
                if mtype == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "payload": {}, "ts": time.time()}))
                continue
            if mtype == "subscribe":
                topic = str(msg.get("topic", ""))
                if await _authorised_for_topic(user_id, role, topic):
                    await hub.subscribe(user_id, topic)
                    if topic.startswith("ride:"):
                        active_request_id = topic.split(":", 1)[1]
                continue
            if mtype == "unsubscribe":
                await hub.unsubscribe(user_id, str(msg.get("topic", "")))
                continue
            if mtype == "location":
                try:
                    lat, lng = float(msg["lat"]), float(msg["lng"])
                except (KeyError, TypeError, ValueError):
                    continue
                pos = LivePosition(
                    user_id=user_id,
                    role="driver" if role == UserRole.DRIVER else "student",
                    lat=lat,
                    lng=lng,
                    heading=msg.get("heading"),
                    speed=msg.get("speed"),
                    accuracy=msg.get("accuracy"),
                    ride_id=active_request_id,
                )
                hub.update_position(pos)
                if role == UserRole.DRIVER:
                    now = time.time()
                    if now - last_db_write > 5:
                        last_db_write = now
                        async with SessionFactory() as db:
                            profile = await db.scalar(select(DriverProfile).where(DriverProfile.user_id == user_id))
                            if profile:
                                profile.latitude, profile.longitude, profile.heading = lat, lng, msg.get("heading")
                                profile.location_updated_at = datetime.now(UTC)
                                if profile.current_ride_id and not active_request_id:
                                    from app.models import Ride

                                    active_request_id = await db.scalar(select(Ride.request_id).where(Ride.id == profile.current_ride_id))
                                    if active_request_id:
                                        await hub.subscribe(user_id, ride_topic(active_request_id))
                                        pos.ride_id = active_request_id
                            await db.commit()
                    if active_request_id:
                        await hub.publish(ride_topic(active_request_id), "ride.driver_location", {**pos.to_dict(), "request_id": active_request_id}, exclude=user_id)
                    await hub.broadcast_admin("driver.location", pos.to_dict())
                elif active_request_id:
                    await hub.publish(ride_topic(active_request_id), "ride.rider_location", {**pos.to_dict(), "request_id": active_request_id}, exclude=user_id)
                    await hub.broadcast_admin("rider.location", pos.to_dict())
                continue
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("ws_error", user_id=user_id, error=str(exc))
    finally:
        hb.cancel()
        await hub.disconnect(user_id, websocket)
