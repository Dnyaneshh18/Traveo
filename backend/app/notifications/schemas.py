"""
Traveo Backend — Notification Schemas
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import NotificationType


class CreateNotificationRequest(BaseModel):
    user_id: str
    title: str
    message: str
    type: NotificationType


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime


class NotificationCountResponse(BaseModel):
    total: int
    unread: int
