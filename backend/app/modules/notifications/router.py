from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import DB, Current
from app.schemas.common import ok
from app.services.notifications import list_notifications, mark_read, unread_count

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_mine(db: DB, current: Current, limit: int = Query(30, le=100)):
    items = await list_notifications(db, current.id, limit)
    return ok(items, meta={"unread": await unread_count(db, current.id)})


@router.post("/read", summary="Mark all as read")
async def read_all(db: DB, current: Current):
    await mark_read(db, current.id, None)
    return ok()


@router.post("/{notification_id}/read")
async def read_one(notification_id: str, db: DB, current: Current):
    await mark_read(db, current.id, notification_id)
    return ok()
