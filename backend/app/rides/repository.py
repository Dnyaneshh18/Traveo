"""
Traveo Backend — Ride & Group Repository

Data access layer for ride requests, matching sessions, ride groups, group members,
group votes, driver assignments, rides, and OTPs.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    DriverAssignment,
    DriverLocation,
    DriverProfile,
    DropEvent,
    GroupVote,
    MatchingSession,
    PassengerProfile,
    PickupEvent,
    Ride,
    RideGroup,
    RideGroupMember,
    RideOTP,
    RideRequest,
    User,
    Vehicle,
)
from app.models.enums import (
    BoardingStatus,
    DriverAssignmentStatus,
    DropStatus,
    GroupStatus,
    OnlineStatus,
    RideRequestStatus,
    RideStatus,
    RideType,
    VerificationStatus,
)


def to_uuid(val: str | UUID | None) -> UUID | None:
    if val is None:
        return None
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


class RideRepository:
    """Repository for all ride domain database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Ride Request Queries & Mutations ────────────────────

    async def get_active_request_by_passenger(
        self, passenger_id: str | UUID
    ) -> RideRequest | None:
        result = await self.db.execute(
            select(RideRequest).where(
                RideRequest.passenger_id == to_uuid(passenger_id),
                RideRequest.status.in_([
                    RideRequestStatus.PENDING,
                    RideRequestStatus.MATCHING,
                    RideRequestStatus.MATCHED,
                ]),
            )
        )
        return result.scalar_one_or_none()

    async def create_ride_request(
        self, passenger_id: str | UUID, pickup_lat: float, pickup_lon: float,
        pickup_address: str | None, dest_lat: float, dest_lon: float, dest_address: str | None,
        seats: int, estimated_fare: float, ride_type: RideType = RideType.SHARED
    ) -> RideRequest:
        req = RideRequest(
            passenger_id=to_uuid(passenger_id),
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lon,
            pickup_address=pickup_address,
            destination_latitude=dest_lat,
            destination_longitude=dest_lon,
            destination_address=dest_address,
            requested_seats=seats,
            ride_type=ride_type,
            status=RideRequestStatus.MATCHING,
            estimated_fare=estimated_fare,
        )
        self.db.add(req)
        await self.db.flush()
        return req

    async def get_ride_request_by_id(self, request_id: str | UUID) -> RideRequest | None:
        result = await self.db.execute(
            select(RideRequest).where(RideRequest.id == to_uuid(request_id))
        )
        return result.scalar_one_or_none()

    async def get_pending_matching_requests(
        self, exclude_request_id: str | UUID | None = None
    ) -> list[RideRequest]:
        stmt = select(RideRequest).where(
            RideRequest.status == RideRequestStatus.MATCHING
        )
        if exclude_request_id:
            stmt = stmt.where(RideRequest.id != to_uuid(exclude_request_id))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_request_status(
        self, request_id: str | UUID, status: RideRequestStatus
    ) -> None:
        await self.db.execute(
            update(RideRequest)
            .where(RideRequest.id == to_uuid(request_id))
            .values(status=status)
        )

    # ── Ride Group Queries & Mutations ──────────────────────

    async def create_ride_group(
        self, capacity: int = 4, estimated_fare: float = 0.0
    ) -> RideGroup:
        group = RideGroup(
            group_status=GroupStatus.FORMING,
            maximum_capacity=capacity,
            current_passengers=0,
            estimated_fare=estimated_fare,
        )
        self.db.add(group)
        await self.db.flush()
        return group

    async def add_passenger_to_group(
        self, group_id: str | UUID, passenger_id: str | UUID, request_id: str | UUID
    ) -> RideGroupMember:
        member = RideGroupMember(
            group_id=to_uuid(group_id),
            passenger_id=to_uuid(passenger_id),
            ride_request_id=to_uuid(request_id),
            boarding_status=BoardingStatus.WAITING,
            drop_status=DropStatus.PENDING,
        )
        self.db.add(member)

        # Increment passenger count on group
        await self.db.execute(
            update(RideGroup)
            .where(RideGroup.id == to_uuid(group_id))
            .values(current_passengers=RideGroup.current_passengers + 1)
        )
        await self.db.flush()
        return member

    async def get_group_with_members(
        self, group_id: str | UUID
    ) -> RideGroup | None:
        result = await self.db.execute(
            select(RideGroup)
            .options(selectinload(RideGroup.members), selectinload(RideGroup.votes))
            .where(RideGroup.id == to_uuid(group_id))
        )
        return result.scalar_one_or_none()

    async def update_group_status(
        self, group_id: str | UUID, status: GroupStatus
    ) -> None:
        await self.db.execute(
            update(RideGroup)
            .where(RideGroup.id == to_uuid(group_id))
            .values(group_status=status)
        )

    async def assign_driver_to_group(
        self, group_id: str | UUID, driver_id: str | UUID, otp: str
    ) -> None:
        await self.db.execute(
            update(RideGroup)
            .where(RideGroup.id == to_uuid(group_id))
            .values(
                driver_id=to_uuid(driver_id),
                common_otp=otp,
                group_status=GroupStatus.DRIVER_ASSIGNED,
            )
        )

    async def get_groups_searching_driver(self) -> list[RideGroup]:
        """Get all groups that need a driver assigned."""
        result = await self.db.execute(
            select(RideGroup)
            .options(selectinload(RideGroup.members))
            .where(RideGroup.group_status == GroupStatus.SEARCHING_DRIVER)
        )
        return list(result.scalars().all())

    # ── Voting Queries & Mutations ──────────────────────────

    async def record_group_vote(
        self, group_id: str | UUID, passenger_id: str | UUID, vote: str
    ) -> GroupVote:
        vote_record = GroupVote(
            group_id=to_uuid(group_id),
            passenger_id=to_uuid(passenger_id),
            vote=vote,
        )
        self.db.add(vote_record)
        await self.db.flush()
        return vote_record

    async def get_group_votes(self, group_id: str | UUID) -> list[GroupVote]:
        result = await self.db.execute(
            select(GroupVote).where(GroupVote.group_id == to_uuid(group_id))
        )
        return list(result.scalars().all())

    # ── Driver Queries ──────────────────────────────────────

    async def get_nearby_online_drivers(
        self,
        lat: float,
        lon: float,
        radius_km: float = 10.0,
    ) -> list[tuple[DriverProfile, Vehicle | None]]:
        """
        Find online, verified drivers with their vehicles.
        Uses simple lat/lon bounding box for pre-filtering.
        """
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * 0.85)

        result = await self.db.execute(
            select(DriverProfile)
            .options(selectinload(DriverProfile.vehicles))
            .where(
                DriverProfile.online_status == OnlineStatus.ONLINE,
                DriverProfile.verification_status == VerificationStatus.APPROVED,
                DriverProfile.current_latitude.isnot(None),
                DriverProfile.current_longitude.isnot(None),
                DriverProfile.current_latitude.between(lat - lat_delta, lat + lat_delta),
                DriverProfile.current_longitude.between(lon - lon_delta, lon + lon_delta),
            )
        )
        drivers = list(result.scalars().all())

        driver_vehicle_pairs = []
        for driver in drivers:
            vehicle = next(
                (v for v in driver.vehicles if v.status.value == "approved"),
                None,
            )
            driver_vehicle_pairs.append((driver, vehicle))

        return driver_vehicle_pairs

    async def update_driver_online_status(
        self, user_id: str | UUID, status: OnlineStatus
    ) -> None:
        await self.db.execute(
            update(DriverProfile)
            .where(DriverProfile.user_id == to_uuid(user_id))
            .values(online_status=status)
        )

    async def update_driver_location(
        self,
        user_id: str | UUID,
        latitude: float,
        longitude: float,
        heading: float | None = None,
        speed: float | None = None,
    ) -> None:
        """Update driver's current location on their profile."""
        uid = to_uuid(user_id)
        await self.db.execute(
            update(DriverProfile)
            .where(DriverProfile.user_id == uid)
            .values(
                current_latitude=latitude,
                current_longitude=longitude,
            )
        )
        existing = await self.db.execute(
            select(DriverLocation).where(DriverLocation.driver_id == uid)
        )
        loc = existing.scalar_one_or_none()
        if loc:
            await self.db.execute(
                update(DriverLocation)
                .where(DriverLocation.driver_id == uid)
                .values(
                    latitude=latitude,
                    longitude=longitude,
                    heading=heading,
                    speed=speed,
                    timestamp=datetime.now(UTC),
                )
            )
        else:
            loc = DriverLocation(
                driver_id=uid,
                latitude=latitude,
                longitude=longitude,
                heading=heading,
                speed=speed,
            )
            self.db.add(loc)

    async def get_driver_profile_by_user_id(
        self, user_id: str | UUID
    ) -> DriverProfile | None:
        result = await self.db.execute(
            select(DriverProfile)
            .options(selectinload(DriverProfile.vehicles))
            .where(DriverProfile.user_id == to_uuid(user_id))
        )
        return result.scalar_one_or_none()

    # ── Driver Assignment Queries & Mutations ───────────────

    async def create_driver_assignment(
        self,
        group_id: str | UUID,
        driver_id: str | UUID,
    ) -> DriverAssignment:
        assignment = DriverAssignment(
            ride_group_id=to_uuid(group_id),
            driver_id=to_uuid(driver_id),
            status=DriverAssignmentStatus.PENDING,
        )
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def get_pending_assignment(
        self, group_id: str | UUID, driver_id: str | UUID
    ) -> DriverAssignment | None:
        result = await self.db.execute(
            select(DriverAssignment).where(
                DriverAssignment.ride_group_id == to_uuid(group_id),
                DriverAssignment.driver_id == to_uuid(driver_id),
                DriverAssignment.status == DriverAssignmentStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_assignment_for_driver(
        self, driver_id: str | UUID
    ) -> DriverAssignment | None:
        result = await self.db.execute(
            select(DriverAssignment).where(
                DriverAssignment.driver_id == to_uuid(driver_id),
                DriverAssignment.status == DriverAssignmentStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def update_assignment_status(
        self,
        assignment_id: str | UUID,
        status: DriverAssignmentStatus,
    ) -> None:
        values: dict = {"status": status}
        if status == DriverAssignmentStatus.ACCEPTED:
            values["accepted_at"] = datetime.now(UTC)
        elif status == DriverAssignmentStatus.REJECTED:
            values["rejected_at"] = datetime.now(UTC)
        elif status == DriverAssignmentStatus.TIMED_OUT:
            values["rejected_at"] = datetime.now(UTC)

        await self.db.execute(
            update(DriverAssignment)
            .where(DriverAssignment.id == to_uuid(assignment_id))
            .values(**values)
        )

    async def get_timed_out_assignments(
        self, timeout_seconds: int = 20
    ) -> list[DriverAssignment]:
        cutoff = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        result = await self.db.execute(
            select(DriverAssignment).where(
                DriverAssignment.status == DriverAssignmentStatus.PENDING,
                DriverAssignment.assigned_at < cutoff,
            )
        )
        return list(result.scalars().all())

    # ── Ride Execution Queries & Mutations ──────────────────

    async def create_ride_record(
        self, group_id: str | UUID, driver_id: str | UUID, total_fare: float
    ) -> Ride:
        ride = Ride(
            ride_group_id=to_uuid(group_id),
            driver_id=to_uuid(driver_id),
            ride_status=RideStatus.DRIVER_ASSIGNED,
            total_fare=total_fare,
        )
        self.db.add(ride)
        await self.db.flush()
        return ride

    async def get_ride_by_id(self, ride_id: str | UUID) -> Ride | None:
        result = await self.db.execute(
            select(Ride).where(Ride.id == to_uuid(ride_id))
        )
        return result.scalar_one_or_none()

    async def get_active_ride_for_driver(self, driver_id: str | UUID) -> Ride | None:
        result = await self.db.execute(
            select(Ride).where(
                Ride.driver_id == to_uuid(driver_id),
                Ride.ride_status.in_([
                    RideStatus.DRIVER_ASSIGNED,
                    RideStatus.OTP_GENERATED,
                    RideStatus.DRIVER_EN_ROUTE,
                    RideStatus.PICKUP_IN_PROGRESS,
                    RideStatus.ALL_PASSENGERS_BOARDED,
                    RideStatus.RIDE_STARTED,
                    RideStatus.DROP_IN_PROGRESS,
                ]),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_ride_for_passenger(self, passenger_id: str | UUID) -> Ride | None:
        member_result = await self.db.execute(
            select(RideGroupMember.group_id).where(
                RideGroupMember.passenger_id == to_uuid(passenger_id),
                RideGroupMember.boarding_status.in_([
                    BoardingStatus.WAITING,
                    BoardingStatus.BOARDED,
                ]),
            )
        )
        group_ids = [row[0] for row in member_result.all()]
        if not group_ids:
            return None

        result = await self.db.execute(
            select(Ride).where(
                Ride.ride_group_id.in_(group_ids),
                Ride.ride_status.in_([
                    RideStatus.DRIVER_ASSIGNED,
                    RideStatus.OTP_GENERATED,
                    RideStatus.DRIVER_EN_ROUTE,
                    RideStatus.PICKUP_IN_PROGRESS,
                    RideStatus.ALL_PASSENGERS_BOARDED,
                    RideStatus.RIDE_STARTED,
                    RideStatus.DROP_IN_PROGRESS,
                ]),
            )
        )
        return result.scalar_one_or_none()

    async def get_ride_history_for_driver(
        self, driver_id: str | UUID, limit: int = 20, offset: int = 0
    ) -> list[Ride]:
        result = await self.db.execute(
            select(Ride)
            .where(Ride.driver_id == to_uuid(driver_id))
            .order_by(desc(Ride.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_ride_history_for_passenger(
        self, passenger_id: str | UUID, limit: int = 20, offset: int = 0
    ) -> list[Ride]:
        member_result = await self.db.execute(
            select(RideGroupMember.group_id).where(
                RideGroupMember.passenger_id == to_uuid(passenger_id),
            )
        )
        group_ids = [row[0] for row in member_result.all()]
        if not group_ids:
            return []

        result = await self.db.execute(
            select(Ride)
            .where(Ride.ride_group_id.in_(group_ids))
            .order_by(desc(Ride.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_ride_status(
        self, ride_id: str | UUID, status: RideStatus
    ) -> None:
        values: dict = {"ride_status": status}
        if status == RideStatus.RIDE_STARTED:
            values["ride_started"] = datetime.now(UTC)
        elif status == RideStatus.RIDE_COMPLETED:
            values["ride_completed"] = datetime.now(UTC)

        await self.db.execute(
            update(Ride).where(Ride.id == to_uuid(ride_id)).values(**values)
        )

    async def create_ride_otp(
        self, group_id: str | UUID, otp: str, expires_in_minutes: int = 15
    ) -> RideOTP:
        expires_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)
        ride_otp = RideOTP(
            ride_group_id=to_uuid(group_id),
            otp=otp,
            expires_at=expires_at,
            verified=False,
        )
        self.db.add(ride_otp)
        await self.db.flush()
        return ride_otp

    async def get_valid_otp(
        self, group_id: str | UUID
    ) -> RideOTP | None:
        result = await self.db.execute(
            select(RideOTP).where(
                RideOTP.ride_group_id == to_uuid(group_id),
                RideOTP.verified.is_(False),
                RideOTP.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def mark_otp_verified(self, otp_id: str | UUID) -> None:
        await self.db.execute(
            update(RideOTP).where(RideOTP.id == to_uuid(otp_id)).values(verified=True)
        )

    # ── Pickup & Drop Events ────────────────────────────────

    async def create_pickup_event(
        self, ride_id: str | UUID, passenger_id: str | UUID
    ) -> PickupEvent:
        event = PickupEvent(
            ride_id=to_uuid(ride_id),
            passenger_id=to_uuid(passenger_id),
            verified=True,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def create_drop_event(
        self, ride_id: str | UUID, passenger_id: str | UUID
    ) -> DropEvent:
        event = DropEvent(
            ride_id=to_uuid(ride_id),
            passenger_id=to_uuid(passenger_id),
            completed=True,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def update_member_boarding_status(
        self, group_id: str | UUID, passenger_id: str | UUID, status: BoardingStatus
    ) -> None:
        await self.db.execute(
            update(RideGroupMember)
            .where(
                RideGroupMember.group_id == to_uuid(group_id),
                RideGroupMember.passenger_id == to_uuid(passenger_id),
            )
            .values(boarding_status=status)
        )

    async def update_member_drop_status(
        self, group_id: str | UUID, passenger_id: str | UUID, status: DropStatus
    ) -> None:
        await self.db.execute(
            update(RideGroupMember)
            .where(
                RideGroupMember.group_id == to_uuid(group_id),
                RideGroupMember.passenger_id == to_uuid(passenger_id),
            )
            .values(drop_status=status)
        )

    # ── Stale Request Cleanup ───────────────────────────────

    async def expire_stale_matching_requests(
        self, timeout_seconds: int = 120
    ) -> int:
        cutoff = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        result = await self.db.execute(
            update(RideRequest)
            .where(
                RideRequest.status == RideRequestStatus.MATCHING,
                RideRequest.created_at < cutoff,
            )
            .values(status=RideRequestStatus.EXPIRED)
        )
        return result.rowcount  # type: ignore
