"""
Traveo Backend — Admin & Operations Schemas
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import VerificationStatus


class DashboardKpiResponse(BaseModel):
    """GET /api/v1/admin/dashboard"""

    active_rides: int
    active_passengers: int
    online_drivers: int
    waiting_groups: int
    matching_success_rate: float  # percentage
    average_wait_time_minutes: float
    revenue_today: float
    revenue_this_week: float
    revenue_this_month: float
    cancellation_rate: float
    driver_acceptance_rate: float
    average_occupancy: float


class DriverApprovalRequest(BaseModel):
    """POST /api/v1/admin/drivers/{id}/approve or /reject"""

    status: VerificationStatus
    rejection_reason: str | None = None


class SystemConfigUpdateRequest(BaseModel):
    """PUT /api/v1/admin/configuration"""

    key: str
    value: str
    description: str | None = None


class SystemConfigResponse(BaseModel):
    id: str
    key: str
    value: str
    description: str | None
    updated_at: datetime


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    action: str
    entity: str | None
    entity_id: str | None
    old_value: str | None
    new_value: str | None
    ip_address: str | None
    created_at: datetime
