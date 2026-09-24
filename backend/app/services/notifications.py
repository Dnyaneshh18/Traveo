"""
Notification service — persists in-app notifications, pushes them over the
realtime hub, and (when a push token exists) via Expo Push.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Notification, NotificationType, User
from app.realtime.hub import hub

logger = get_logger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def notify(
    db: AsyncSession,
    user_ids: list[str] | set[str],
    *,
    type: NotificationType,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    push: bool = True,
) -> None:
    ids = list(dict.fromkeys(user_ids))
    if not ids:
        return
    now = datetime.now(UTC)
    payload = json.dumps(data or {})
    notes = [Notification(user_id=uid, type=type, title=title, body=body, data=payload, created_at=now) for uid in ids]
    db.add_all(notes)
    await db.flush()

    for n in notes:
        await hub.send_to_user(
            n.user_id,
            "notification",
            {"id": n.id, "type": type, "title": title, "body": body, "data": data or {}, "created_at": now.isoformat()},
        )

    if push:
        tokens = (
            await db.execute(select(User.push_token).where(User.id.in_(ids), User.push_token.is_not(None)))
        ).scalars().all()
        # Skip devices that are connected via WebSocket right now (they already got it).
        offline_tokens = []
        rows = (await db.execute(select(User.id, User.push_token).where(User.id.in_(ids), User.push_token.is_not(None)))).all()
        for uid, tok in rows:
            if tok and not hub.is_online(uid):
                offline_tokens.append(tok)
        if offline_tokens:
            await _send_expo_push(offline_tokens, title, body, data or {})
        _ = tokens


async def _send_expo_push(tokens: list[str], title: str, body: str, data: dict[str, Any]) -> None:
    messages = [{"to": t, "title": title, "body": body, "data": data, "sound": "default"} for t in tokens if t.startswith("ExponentPushToken")]
    if not messages:
        return
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            await client.post(EXPO_PUSH_URL, json=messages)
    except Exception as exc:  # pragma: no cover - network
        logger.warning("expo_push_failed", error=str(exc))


async def list_notifications(db: AsyncSession, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "data": json.loads(n.data or "{}"),
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]


async def unread_count(db: AsyncSession, user_id: str) -> int:
    return int(
        await db.scalar(
            select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        or 0
    )


async def mark_read(db: AsyncSession, user_id: str, notification_id: str | None) -> None:
    stmt = update(Notification).where(Notification.user_id == user_id)
    if notification_id:
        stmt = stmt.where(Notification.id == notification_id)
    await db.execute(stmt.values(is_read=True))
