"""
Traveo Backend — Notification API Router
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies import get_current_user_id
from app.notifications.schemas import NotificationCountResponse, NotificationResponse
from app.notifications.service import NotificationService

router = APIRouter()


@router.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications(
    limit: int = Query(default=50, le=100),
    unread_only: bool = Query(default=False),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get notifications for the current user."""
    service = NotificationService(db)
    return await service.get_notifications(user_id, limit, unread_only)


@router.get("/notifications/count", response_model=NotificationCountResponse)
async def get_notification_count(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get total and unread notification counts."""
    service = NotificationService(db)
    return await service.get_counts(user_id)


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Mark a notification as read."""
    service = NotificationService(db)
    await service.mark_read(notification_id)


@router.post("/notifications/read-all", status_code=204)
async def mark_all_notifications_read(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Mark all notifications as read."""
    service = NotificationService(db)
    await service.mark_all_read(user_id)
