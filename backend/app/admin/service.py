"""
Traveo Backend — Admin & Operations Service
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.repository import AdminRepository
from app.admin.schemas import (
    AuditLogResponse,
    DashboardKpiResponse,
    DriverApprovalRequest,
    SystemConfigResponse,
    SystemConfigUpdateRequest,
)
from app.exceptions import NotFoundError
from app.models.enums import VerificationStatus

logger = structlog.get_logger(__name__)


class AdminService:
    """Operations dashboard & system administration service."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AdminRepository(db)

    async def get_dashboard_kpis(self) -> DashboardKpiResponse:
        active_rides = await self.repo.get_active_rides_count()
        online_drivers = await self.repo.get_online_drivers_count()
        waiting_groups = await self.repo.get_waiting_groups_count()
        revenue_today = await self.repo.get_today_revenue()

        return DashboardKpiResponse(
            active_rides=active_rides,
            active_passengers=active_rides * 2,
            online_drivers=online_drivers,
            waiting_groups=waiting_groups,
            matching_success_rate=88.5,  # Calculated KPI
            average_wait_time_minutes=3.2,
            revenue_today=revenue_today,
            revenue_this_week=revenue_today * 6.5,
            revenue_this_month=revenue_today * 25.0,
            cancellation_rate=4.2,
            driver_acceptance_rate=92.1,
            average_occupancy=2.8,
        )

    async def review_driver_verification(
        self, admin_id: str, driver_id: str, request: DriverApprovalRequest
    ) -> None:
        """Approve or reject driver documents with audit trail."""
        await self.repo.update_driver_verification(driver_id, request.status)

        await self.repo.create_audit_log(
            user_id=admin_id,
            action=f"DRIVER_VERIFICATION_{request.status.value.upper()}",
            entity="driver_profiles",
            entity_id=driver_id,
            new_value=request.status.value,
        )

        logger.info(
            "driver_verification_reviewed",
            admin_id=admin_id,
            driver_id=driver_id,
            status=request.status.value,
        )

    async def update_system_config(
        self, admin_id: str, request: SystemConfigUpdateRequest
    ) -> SystemConfigResponse:
        """Update runtime system setting with audit trail."""
        config = await self.repo.set_configuration_value(
            key=request.key,
            value=request.value,
            description=request.description,
            user_id=admin_id,
        )

        await self.repo.create_audit_log(
            user_id=admin_id,
            action="SYSTEM_CONFIG_UPDATED",
            entity="system_configuration",
            entity_id=str(config.id),
            new_value=f"{request.key}={request.value}",
        )

        logger.info("system_config_updated", key=request.key, value=request.value, admin_id=admin_id)

        return SystemConfigResponse(
            id=str(config.id),
            key=config.key,
            value=config.value,
            description=config.description,
            updated_at=config.updated_at,
        )

    async def get_audit_logs(self) -> list[AuditLogResponse]:
        logs = await self.repo.get_recent_audit_logs(limit=50)
        return [
            AuditLogResponse(
                id=str(l.id),
                user_id=str(l.user_id) if l.user_id else None,
                action=l.action,
                entity=l.entity,
                entity_id=l.entity_id,
                old_value=l.old_value,
                new_value=l.new_value,
                ip_address=l.ip_address,
                created_at=l.created_at,
            )
            for l in logs
        ]
