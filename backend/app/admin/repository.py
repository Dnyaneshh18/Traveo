"""
Traveo Backend — Admin Repository

Data access layer for operational dashboards, driver verification queue,
system configuration settings, and audit trails.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditLog,
    DriverProfile,
    Payment,
    Ride,
    RideGroup,
    RideRequest,
    SystemConfiguration,
    User,
)
from app.models.enums import (
    DriverAssignmentStatus,
    GroupStatus,
    OnlineStatus,
    PaymentStatus,
    RideRequestStatus,
    RideStatus,
    VerificationStatus,
)


class AdminRepository:
    """Repository for administrative and operational metrics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Dashboard KPI Aggregations ──────────────────────────

    async def get_active_rides_count(self) -> int:
        result = await self.db.execute(
            select(func.count(Ride.id)).where(
                Ride.ride_status.in_([
                    RideStatus.DRIVER_ASSIGNED,
                    RideStatus.RIDE_STARTED,
                    RideStatus.DROP_IN_PROGRESS,
                ])
            )
        )
        return result.scalar_one() or 0

    async def get_online_drivers_count(self) -> int:
        result = await self.db.execute(
            select(func.count(DriverProfile.id)).where(
                DriverProfile.online_status == OnlineStatus.ONLINE
            )
        )
        return result.scalar_one() or 0

    async def get_waiting_groups_count(self) -> int:
        result = await self.db.execute(
            select(func.count(RideGroup.id)).where(
                RideGroup.group_status.in_([
                    GroupStatus.FORMING,
                    GroupStatus.SEARCHING_DRIVER,
                ])
            )
        )
        return result.scalar_one() or 0

    async def get_today_revenue(self) -> float:
        now = datetime.now(UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= start_of_day,
            )
        )
        return float(result.scalar_one() or 0.0)

    # ── Driver Verification Queue ───────────────────────────

    async def get_pending_driver_verifications(self) -> list[DriverProfile]:
        result = await self.db.execute(
            select(DriverProfile).where(
                DriverProfile.verification_status.in_([
                    VerificationStatus.PENDING,
                    VerificationStatus.SUBMITTED,
                    VerificationStatus.UNDER_REVIEW,
                ])
            )
        )
        return list(result.scalars().all())

    async def update_driver_verification(
        self, driver_id: str | UUID, status: VerificationStatus
    ) -> None:
        await self.db.execute(
            update(DriverProfile)
            .where(DriverProfile.id == driver_id)
            .values(verification_status=status)
        )

        if status == VerificationStatus.APPROVED:
            # Also mark user verified
            driver = await self.db.execute(
                select(DriverProfile).where(DriverProfile.id == driver_id)
            )
            d = driver.scalar_one_or_none()
            if d:
                await self.db.execute(
                    update(User).where(User.id == d.user_id).values(is_verified=True)
                )

    # ── System Configuration ────────────────────────────────

    async def get_all_configurations(self) -> list[SystemConfiguration]:
        result = await self.db.execute(select(SystemConfiguration))
        return list(result.scalars().all())

    async def set_configuration_value(
        self, key: str, value: str, description: str | None, user_id: str | UUID | None
    ) -> SystemConfiguration:
        result = await self.db.execute(
            select(SystemConfiguration).where(SystemConfiguration.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            if description:
                existing.description = description
            existing.updated_by = user_id
            return existing

        config = SystemConfiguration(
            key=key,
            value=value,
            description=description,
            updated_by=user_id,
        )
        self.db.add(config)
        await self.db.flush()
        return config

    # ── Audit Trail ─────────────────────────────────────────

    async def create_audit_log(
        self,
        user_id: str | UUID | None,
        action: str,
        entity: str | None = None,
        entity_id: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_recent_audit_logs(self, limit: int = 50) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
