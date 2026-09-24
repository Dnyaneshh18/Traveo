"""
Background maintenance loop:
  • expire OPEN requests past their TTL
  • keep demo drivers' GPS "fresh" in development (so dispatch always has candidates)
  • mark drivers with stale GPS as offline
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.core.config import get_settings
from app.core.database import session_scope
from app.core.logging import get_logger
from app.models import DriverProfile, DriverStatus
from app.modules.rides.repository import RideRepository
from app.modules.rides.service import RideService
from app.realtime.hub import hub

settings = get_settings()
logger = get_logger(__name__)

_task: asyncio.Task | None = None


async def _tick() -> None:
    now = datetime.now(UTC)
    async with session_scope() as db:
        expired = await RideService(db).expire_stale_requests()
        if expired:
            logger.info("requests_expired", count=expired)
        stale_offers = await RideRepository(db).expire_stale_offers(now)
        for o in stale_offers:
            await hub.send_to_user(o.driver_user_id, "dispatch.offer_expired", {"offer_id": o.id})

        stale_cutoff = now - timedelta(seconds=settings.DRIVER_LOCATION_STALE_SECONDS * 4)
        if settings.is_development and settings.SEED_DEMO_DATA:
            # Demo drivers (phones +9199000000xx) never go stale in dev.
            from app.models import User

            demo_ids = (await db.execute(select(User.id).where(User.phone.like("+9199000000%")))).scalars().all()
            if demo_ids:
                await db.execute(
                    update(DriverProfile)
                    .where(DriverProfile.user_id.in_(demo_ids), DriverProfile.status == DriverStatus.ONLINE)
                    .values(location_updated_at=now)
                )
        await db.execute(
            update(DriverProfile)
            .where(
                DriverProfile.status == DriverStatus.ONLINE,
                DriverProfile.current_ride_id.is_(None),
                DriverProfile.location_updated_at.is_not(None),
                DriverProfile.location_updated_at < stale_cutoff,
            )
            .values(status=DriverStatus.OFFLINE)
        )


async def _loop(interval: float) -> None:
    while True:
        try:
            await _tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("maintenance_tick_failed")
        await asyncio.sleep(interval)


def start(interval: float = 20.0) -> None:
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop(interval), name="maintenance")


async def stop() -> None:
    global _task
    if _task:
        _task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _task
        _task = None
