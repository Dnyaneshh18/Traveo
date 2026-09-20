"""
Traveo Backend — Background Scheduler

APScheduler-based background job runner for periodic tasks.
Runs inside the FastAPI process via asyncio.

Jobs:
- Expire stale matching requests (every 30s)
- Time out pending driver assignments (every 15s)
- Reassign groups stuck in SEARCHING_DRIVER (every 60s)
"""

from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Scheduler instance (created but not started until startup)
scheduler = AsyncIOScheduler()


async def expire_stale_requests() -> None:
    """Mark matching requests older than timeout as EXPIRED."""
    try:
        from app.core.database import async_session_factory
        async with async_session_factory() as db:
            from app.rides.repository import RideRepository
            repo = RideRepository(db)
            count = await repo.expire_stale_matching_requests(
                timeout_seconds=settings.DEFAULT_SEARCH_TIMEOUT_SECONDS
            )
            if count > 0:
                logger.info("stale_requests_expired", count=count)
            await db.commit()
    except Exception as e:
        logger.error("expire_stale_requests_failed", error=str(e))


async def timeout_driver_assignments() -> None:
    """Auto-reject driver assignments that have been pending too long."""
    try:
        from app.core.database import async_session_factory
        async with async_session_factory() as db:
            from app.rides.repository import RideRepository
            from app.models.enums import DriverAssignmentStatus
            repo = RideRepository(db)
            timed_out = await repo.get_timed_out_assignments(
                timeout_seconds=settings.DEFAULT_DRIVER_REQUEST_TIMEOUT_SECONDS
            )
            for assignment in timed_out:
                await repo.update_assignment_status(
                    assignment.id, DriverAssignmentStatus.TIMED_OUT
                )
                logger.info(
                    "driver_assignment_timed_out",
                    assignment_id=str(assignment.id),
                    driver_id=str(assignment.driver_id),
                )
            if timed_out:
                await db.commit()
    except Exception as e:
        logger.error("timeout_driver_assignments_failed", error=str(e))


async def reassign_searching_groups() -> None:
    """Re-attempt driver assignment for groups stuck in SEARCHING_DRIVER."""
    try:
        from app.core.database import async_session_factory
        async with async_session_factory() as db:
            from app.rides.repository import RideRepository
            from app.rides.service import RideService
            repo = RideRepository(db)
            groups = await repo.get_groups_searching_driver()

            if not groups:
                return

            service = RideService(db)
            for group in groups:
                await service._attempt_driver_assignment(str(group.id))

            await db.commit()
            if groups:
                logger.info("groups_reassignment_attempted", count=len(groups))
    except Exception as e:
        logger.error("reassign_searching_groups_failed", error=str(e))


def start_scheduler() -> None:
    """Register all background jobs and start the scheduler."""
    if scheduler.running:
        return

    scheduler.add_job(
        expire_stale_requests,
        trigger=IntervalTrigger(seconds=30),
        id="expire_stale_requests",
        name="Expire stale matching requests",
        replace_existing=True,
    )

    scheduler.add_job(
        timeout_driver_assignments,
        trigger=IntervalTrigger(seconds=15),
        id="timeout_driver_assignments",
        name="Timeout pending driver assignments",
        replace_existing=True,
    )

    scheduler.add_job(
        reassign_searching_groups,
        trigger=IntervalTrigger(seconds=60),
        id="reassign_searching_groups",
        name="Reassign groups searching for drivers",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("background_scheduler_started", jobs=3)


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("background_scheduler_stopped")
