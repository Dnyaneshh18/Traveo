"""Data access for ride requests, members, offers and rides."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ACTIVE_MEMBER_STATUSES,
    ACTIVE_REQUEST_STATUSES,
    DriverOffer,
    DriverProfile,
    HiddenRequest,
    OfferStatus,
    Ride,
    RideMember,
    RideRequest,
    RideRequestStatus,
    User,
)


class RideRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── requests ───────────────────────────────────────────────────
    async def get_request(self, request_id: str, *, with_members: bool = True) -> RideRequest | None:
        stmt = select(RideRequest).where(RideRequest.id == request_id)
        if with_members:
            stmt = stmt.options(
                selectinload(RideRequest.members),
                selectinload(RideRequest.rides),
                selectinload(RideRequest.offers),
            )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def active_request_for_user(self, user_id: str) -> RideRequest | None:
        stmt = (
            select(RideRequest)
            .join(RideMember, RideMember.request_id == RideRequest.id)
            .where(
                RideMember.user_id == user_id,
                RideMember.status.in_(ACTIVE_MEMBER_STATUSES),
                RideRequest.status.in_(ACTIVE_REQUEST_STATUSES),
            )
            .options(selectinload(RideRequest.members), selectinload(RideRequest.rides))
            .order_by(RideRequest.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def open_requests_for_college(
        self, college_id: str, *, exclude_user_id: str, since: datetime, until: datetime
    ) -> list[RideRequest]:
        hidden = select(HiddenRequest.request_id).where(HiddenRequest.user_id == exclude_user_id)
        stmt = (
            select(RideRequest)
            .where(
                RideRequest.college_id == college_id,
                RideRequest.status == RideRequestStatus.OPEN,
                RideRequest.creator_id != exclude_user_id,
                RideRequest.expires_at > datetime.now(UTC),
                RideRequest.departure_at >= since,
                RideRequest.departure_at <= until,
                RideRequest.id.not_in(hidden),
            )
            .options(selectinload(RideRequest.members))
            .order_by(RideRequest.departure_at.asc())
            .limit(60)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def history_for_user(self, user_id: str, limit: int, offset: int) -> list[RideRequest]:
        stmt = (
            select(RideRequest)
            .join(RideMember, RideMember.request_id == RideRequest.id)
            .where(
                RideMember.user_id == user_id,
                RideRequest.status.in_(
                    (RideRequestStatus.COMPLETED, RideRequestStatus.CANCELLED, RideRequestStatus.EXPIRED)
                ),
            )
            .options(selectinload(RideRequest.members), selectinload(RideRequest.rides))
            .order_by(RideRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.db.execute(stmt)).scalars().unique().all())

    async def expired_open_requests(self, now: datetime) -> list[RideRequest]:
        stmt = (
            select(RideRequest)
            .where(RideRequest.status == RideRequestStatus.OPEN, RideRequest.expires_at <= now)
            .options(selectinload(RideRequest.members))
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ── members ────────────────────────────────────────────────────
    async def get_member(self, request_id: str, user_id: str) -> RideMember | None:
        return await self.db.scalar(
            select(RideMember).where(RideMember.request_id == request_id, RideMember.user_id == user_id)
        )

    async def users_for_members(self, members: list[RideMember]) -> dict[str, User]:
        ids = [m.user_id for m in members]
        if not ids:
            return {}
        rows = (
            await self.db.execute(
                select(User).options(selectinload(User.student_profile)).where(User.id.in_(ids))
            )
        ).scalars().all()
        return {u.id: u for u in rows}

    # ── offers ─────────────────────────────────────────────────────
    async def get_offer(self, offer_id: str) -> DriverOffer | None:
        return await self.db.get(DriverOffer, offer_id)

    async def pending_offer_for_driver(self, driver_user_id: str) -> DriverOffer | None:
        return await self.db.scalar(
            select(DriverOffer)
            .where(
                DriverOffer.driver_user_id == driver_user_id,
                DriverOffer.status == OfferStatus.PENDING,
                DriverOffer.expires_at > datetime.now(UTC),
            )
            .order_by(DriverOffer.created_at.desc())
            .limit(1)
        )

    async def cancel_pending_offers(self, request_id: str) -> list[DriverOffer]:
        rows = list(
            (
                await self.db.execute(
                    select(DriverOffer).where(DriverOffer.request_id == request_id, DriverOffer.status == OfferStatus.PENDING)
                )
            ).scalars().all()
        )
        now = datetime.now(UTC)
        for o in rows:
            o.status = OfferStatus.CANCELLED
            o.responded_at = now
        await self.db.flush()
        return rows

    async def expire_stale_offers(self, now: datetime) -> list[DriverOffer]:
        rows = list(
            (
                await self.db.execute(
                    select(DriverOffer).where(DriverOffer.status == OfferStatus.PENDING, DriverOffer.expires_at < now - timedelta(seconds=5))
                )
            ).scalars().all()
        )
        for o in rows:
            o.status = OfferStatus.EXPIRED
            o.responded_at = now
        await self.db.flush()
        return rows

    async def offered_driver_ids(self, request_id: str) -> set[str]:
        rows = (
            await self.db.execute(select(DriverOffer.driver_user_id).where(DriverOffer.request_id == request_id))
        ).scalars().all()
        return set(rows)

    # ── drivers ────────────────────────────────────────────────────
    async def available_drivers_in_bbox(
        self, min_lat: float, min_lng: float, max_lat: float, max_lng: float, fresh_after: datetime
    ) -> list[DriverProfile]:
        from app.models import DriverStatus, VerificationStatus

        stmt = (
            select(DriverProfile)
            .options(selectinload(DriverProfile.vehicle), selectinload(DriverProfile.user))
            .where(
                DriverProfile.status == DriverStatus.ONLINE,
                DriverProfile.verification_status == VerificationStatus.VERIFIED,
                DriverProfile.current_ride_id.is_(None),
                DriverProfile.latitude.is_not(None),
                DriverProfile.latitude.between(min_lat, max_lat),
                DriverProfile.longitude.between(min_lng, max_lng),
                or_(DriverProfile.location_updated_at.is_(None), DriverProfile.location_updated_at >= fresh_after),
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def driver_profile_by_user(self, user_id: str) -> DriverProfile | None:
        return await self.db.scalar(
            select(DriverProfile)
            .options(selectinload(DriverProfile.vehicle), selectinload(DriverProfile.user))
            .where(DriverProfile.user_id == user_id)
        )

    # ── rides ──────────────────────────────────────────────────────
    async def get_ride(self, ride_id: str) -> Ride | None:
        return (
            await self.db.execute(
                select(Ride)
                .options(
                    selectinload(Ride.request).selectinload(RideRequest.members),
                    selectinload(Ride.request).selectinload(RideRequest.rides),
                    selectinload(Ride.request).selectinload(RideRequest.offers),
                )
                .where(Ride.id == ride_id)
            )
        ).scalar_one_or_none()

    async def ride_for_request(self, request_id: str) -> Ride | None:
        return await self.db.scalar(
            select(Ride).where(Ride.request_id == request_id).order_by(Ride.created_at.desc()).limit(1)
        )

    async def active_ride_for_driver(self, driver_user_id: str) -> Ride | None:
        from app.models import RideStatus

        return (
            await self.db.execute(
                select(Ride)
                .options(
                    selectinload(Ride.request).selectinload(RideRequest.members),
                    selectinload(Ride.request).selectinload(RideRequest.rides),
                )
                .where(
                    Ride.driver_user_id == driver_user_id,
                    Ride.status.in_((RideStatus.DRIVER_ASSIGNED, RideStatus.IN_PROGRESS)),
                )
                .order_by(Ride.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def driver_ride_history(self, driver_user_id: str, limit: int, offset: int) -> list[Ride]:
        from app.models import RideStatus

        return list(
            (
                await self.db.execute(
                    select(Ride)
                    .options(
                        selectinload(Ride.request).selectinload(RideRequest.members),
                        selectinload(Ride.request).selectinload(RideRequest.rides),
                    )
                    .where(
                        Ride.driver_user_id == driver_user_id,
                        Ride.status.in_((RideStatus.COMPLETED, RideStatus.CANCELLED)),
                    )
                    .order_by(Ride.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).scalars().all()
        )


_ = and_
