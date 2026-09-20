"""
Traveo Backend — Notification Repository

Data access layer for notification CRUD.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification
from app.models.enums import NotificationType


class NotificationRepository:
    """Repository for notification database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_notification(
        self,
        user_id: str | UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
        )
        self.db.add(notif)
        await self.db.flush()
        return notif

    async def get_user_notifications(
        self, user_id: str | UUID, limit: int = 50, unread_only: bool = False
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: str | UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )

    async def mark_all_read(self, user_id: str | UUID) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        return result.rowcount  # type: ignore

    async def get_unread_count(self, user_id: str | UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar_one() or 0

    async def get_total_count(self, user_id: str | UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
            )
        )
        return result.scalar_one() or 0
