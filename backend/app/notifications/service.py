"""
Traveo Backend — Notification Service

Handles in-app notification creation, delivery via WebSocket,
and optional Firebase Cloud Messaging push notifications.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.notifications.repository import NotificationRepository
from app.notifications.schemas import (
    NotificationCountResponse,
    NotificationResponse,
)

logger = structlog.get_logger(__name__)


class NotificationService:
    """Notification creation, delivery, and management."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = NotificationRepository(db)

    async def create_and_send(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
    ) -> NotificationResponse:
        """
        Create an in-app notification, store in DB, and attempt delivery via:
        1. WebSocket (if user is connected)
        2. FCM push notification (if configured)
        """
        # Store in database
        notif = await self.repo.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )

        response = NotificationResponse(
            id=str(notif.id),
            title=notif.title,
            message=notif.message,
            type=notif.type,
            is_read=notif.is_read,
            created_at=notif.created_at,
        )

        # Attempt WebSocket delivery
        try:
            from app.websocket.manager import manager
            from app.websocket.events import WSEventType
            await manager.send_to_user(
                user_id,
                WSEventType.SYSTEM_ALERT,
                {
                    "notification_id": str(notif.id),
                    "title": title,
                    "message": message,
                    "type": notification_type.value,
                },
            )
        except Exception as e:
            logger.debug("ws_notification_skipped", user_id=user_id, error=str(e))

        # Attempt FCM push notification
        await self._send_fcm_push(user_id, title, message)

        logger.info(
            "notification_created",
            user_id=user_id,
            type=notification_type.value,
            title=title,
        )

        return response

    async def get_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> list[NotificationResponse]:
        """Get notifications for a user."""
        notifs = await self.repo.get_user_notifications(user_id, limit, unread_only)
        return [
            NotificationResponse(
                id=str(n.id),
                title=n.title,
                message=n.message,
                type=n.type,
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in notifs
        ]

    async def mark_read(self, notification_id: str) -> None:
        """Mark a single notification as read."""
        await self.repo.mark_read(notification_id)

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        return await self.repo.mark_all_read(user_id)

    async def get_counts(self, user_id: str) -> NotificationCountResponse:
        """Get total and unread notification counts."""
        total = await self.repo.get_total_count(user_id)
        unread = await self.repo.get_unread_count(user_id)
        return NotificationCountResponse(total=total, unread=unread)

    @staticmethod
    async def _send_fcm_push(user_id: str, title: str, message: str) -> None:
        """
        Send push notification via Firebase Cloud Messaging.
        Gracefully skips if FCM is not configured.
        """
        try:
            from app.core.config import get_settings
            settings = get_settings()
            if not settings.FCM_SERVER_KEY or not settings.FCM_PROJECT_ID:
                return  # FCM not configured — skip silently

            # In production: Use firebase-admin SDK
            # import firebase_admin
            # from firebase_admin import messaging
            # ... send message ...
            logger.debug("fcm_push_skipped", user_id=user_id, reason="not_implemented")
        except Exception as e:
            logger.warning("fcm_push_failed", user_id=user_id, error=str(e))
