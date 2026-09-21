"""Ride event timeline helper + realtime topic naming."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RideEvent


def ride_topic(request_id: str) -> str:
    return f"ride:{request_id}"


def college_topic(college_id: str) -> str:
    return f"college:{college_id}"


async def record_event(
    db: AsyncSession, request_id: str, event: str, *, actor_id: str | None = None, data: dict[str, Any] | None = None
) -> RideEvent:
    row = RideEvent(
        request_id=request_id,
        actor_id=actor_id,
        event=event,
        data=json.dumps(data or {}, default=str),
        created_at=datetime.now(UTC),
    )
    db.add(row)
    await db.flush()
    return row


async def timeline(db: AsyncSession, request_id: str) -> list[dict[str, Any]]:
    rows = (
        await db.execute(select(RideEvent).where(RideEvent.request_id == request_id).order_by(RideEvent.created_at.asc()))
    ).scalars().all()
    return [
        {"id": r.id, "event": r.event, "actor_id": r.actor_id, "data": json.loads(r.data or "{}"), "created_at": r.created_at.isoformat()}
        for r in rows
    ]
