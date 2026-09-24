"""
Ride service — the passenger-first group lifecycle.

create → (classmates join / leave / creator removes) → lock ("find driver")
→ dispatch → driver assigned → pickups (OTP / matching codes) → drops → done
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.exceptions import (
    ActiveRideExists,
    ForbiddenError,
    GroupFull,
    NotFoundError,
    NotSameCollege,
    RideStateError,
    RouteNotCompatible,
    ValidationFailed,
)
from app.core.geo import LatLng, distance_km
from app.core.logging import get_logger
from app.core.security import generate_matching_code, hash_code
from app.intelligence.fare import TARIFFS, estimate_total, split_fare
from app.intelligence.matching import CandidateTrip, MatchingConfig, RequestSnapshot, evaluate_match
from app.maps.provider import get_maps_provider
from app.models import (
    ACTIVE_MEMBER_STATUSES,
    VEHICLE_CAPACITY,
    VEHICLE_LABEL,
    College,
    Gender,
    HiddenRequest,
    MemberRole,
    MemberStatus,
    NotificationType,
    RideDirection,
    RideMember,
    RideRequest,
    RideRequestStatus,
    RideStatus,
    User,
    VehicleType,
)
from app.modules.rides.repository import RideRepository
from app.modules.rides.schemas import (
    CreateRideRequestIn,
    DispatchOut,
    DriverOut,
    FareOption,
    JoinRideIn,
    MemberOut,
    RideOut,
    RideRequestOut,
    RoutePreviewOut,
)
from app.realtime.hub import hub
from app.schemas.common import Place
from app.services.events import college_topic, record_event, ride_topic
from app.services.notifications import notify
from app.services.runtime_config import load_config

settings = get_settings()
logger = get_logger(__name__)

CAMPUS_RADIUS_KM = 0.5


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class RideService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RideRepository(db)
        self.maps = get_maps_provider()

    # ══════════════════════════════════════════════════════════════
    # Route preview & fare options (booking screen)
    # ══════════════════════════════════════════════════════════════
    async def route_preview(self, current: CurrentUser | None, origin: Place, destination: Place) -> RoutePreviewOut:
        direction = RideDirection.FROM_COLLEGE
        if current and current.student and current.student.college:
            college = current.student.college
            direction = self._direction_for(college, origin, destination)
        route = await self.maps.route([LatLng(origin.lat, origin.lng), LatLng(destination.lat, destination.lng)])
        options = []
        for vt in (VehicleType.AUTO, VehicleType.CAR, VehicleType.CAR_XL, VehicleType.BIKE):
            total = estimate_total(vt, route.distance_km, route.duration_min)
            cap = VEHICLE_CAPACITY[vt]
            options.append(
                FareOption(
                    vehicle_type=vt,
                    label=VEHICLE_LABEL[vt],
                    seat_capacity=cap,
                    total_estimate=total,
                    per_seat_if_full=float(round(total / cap)),
                    solo_estimate=total,
                )
            )
        return RoutePreviewOut(
            distance_km=route.distance_km,
            duration_min=route.duration_min,
            polyline=route.polyline,
            provider=route.provider,
            direction=direction,
            options=options,
        )

    @staticmethod
    def _direction_for(college: College, origin: Place, destination: Place) -> RideDirection:
        campus = LatLng(college.latitude, college.longitude)
        from_campus = distance_km(campus, LatLng(origin.lat, origin.lng)) <= CAMPUS_RADIUS_KM
        to_campus = distance_km(campus, LatLng(destination.lat, destination.lng)) <= CAMPUS_RADIUS_KM
        if from_campus and not to_campus:
            return RideDirection.FROM_COLLEGE
        if to_campus and not from_campus:
            return RideDirection.TO_COLLEGE
        if from_campus and to_campus:
            raise ValidationFailed("Pickup and drop are both at campus – choose a destination away from college")
        raise ValidationFailed(
            f"One end of your trip must be {college.short_name or college.name} (within {CAMPUS_RADIUS_KM:g} km of campus)",
            details={"campus": {"lat": college.latitude, "lng": college.longitude}},
        )

    # ══════════════════════════════════════════════════════════════
    # Create
    # ══════════════════════════════════════════════════════════════
    async def create_request(self, current: CurrentUser, body: CreateRideRequestIn) -> RideRequestOut:
        student = current.student
        assert student is not None
        college = student.college
        if await self.repo.active_request_for_user(current.id):
            raise ActiveRideExists()

        capacity = VEHICLE_CAPACITY[body.vehicle_type]
        if body.seats > capacity:
            raise ValidationFailed(f"{VEHICLE_LABEL[body.vehicle_type]} has only {capacity} seats")
        cfg = await load_config(self.db)
        if body.women_only and not cfg.get("safety.women_only_enabled", True):
            raise ValidationFailed("Women-only rides are disabled right now")
        if body.women_only and student.gender != Gender.FEMALE:
            raise ValidationFailed("Only women can create women-only rides")

        direction = self._direction_for(college, body.origin, body.destination)
        now = datetime.now(UTC)
        departure = _aware(body.departure_at) if body.departure_at else now + timedelta(minutes=10)
        if departure < now - timedelta(minutes=5):
            raise ValidationFailed("Departure time is in the past")
        if departure > now + timedelta(hours=24):
            raise ValidationFailed("You can schedule rides up to 24 hours ahead")

        route = await self.maps.route(
            [LatLng(body.origin.lat, body.origin.lng), LatLng(body.destination.lat, body.destination.lng)]
        )
        total = estimate_total(body.vehicle_type, route.distance_km, route.duration_min)
        ttl = int(cfg.get("request.open_ttl_minutes", settings.REQUEST_OPEN_TTL_MINUTES))

        req = RideRequest(
            creator_id=current.id,
            college_id=college.id,
            direction=direction,
            vehicle_type=body.vehicle_type,
            seat_capacity=capacity,
            seats_taken=body.seats,
            status=RideRequestStatus.OPEN,
            origin_lat=body.origin.lat,
            origin_lng=body.origin.lng,
            origin_address=body.origin.address,
            destination_lat=body.destination.lat,
            destination_lng=body.destination.lng,
            destination_address=body.destination.address,
            departure_at=departure,
            expires_at=departure + timedelta(minutes=ttl),
            note=body.note,
            women_only=body.women_only,
            route_polyline=route.polyline,
            route_distance_km=route.distance_km,
            route_duration_min=route.duration_min,
            estimated_fare_total=total,
            estimated_fare_solo=total,
            members=[],
            rides=[],
            offers=[],
        )
        self.db.add(req)
        await self.db.flush()

        creator = RideMember(
            request_id=req.id,
            user_id=current.id,
            role=MemberRole.CREATOR,
            status=MemberStatus.ACCEPTED,
            seats=body.seats,
            pickup_lat=body.origin.lat,
            pickup_lng=body.origin.lng,
            pickup_address=body.origin.address,
            drop_lat=body.destination.lat,
            drop_lng=body.destination.lng,
            drop_address=body.destination.address,
            distance_km=route.distance_km,
            joined_at=now,
        )
        req.members.append(creator)
        await self.db.flush()
        await self._recompute_shares(req)
        await record_event(self.db, req.id, "request_created", actor_id=current.id, data={"vehicle": body.vehicle_type, "direction": direction})

        await self.db.commit()
        await hub.subscribe(current.id, ride_topic(req.id))
        out = await self.serialize(req, viewer_id=current.id)
        await hub.publish(college_topic(college.id), "feed.request_created", {"request": out.model_dump(mode="json")}, exclude=current.id)
        await hub.broadcast_admin("request.created", {"request_id": req.id, "college_id": college.id})
        logger.info("ride_request_created", request_id=req.id, user_id=current.id, direction=direction)
        return out

    # ══════════════════════════════════════════════════════════════
    # Feed (same college only)
    # ══════════════════════════════════════════════════════════════
    async def feed(
        self,
        current: CurrentUser,
        *,
        pickup: LatLng | None,
        drop: LatLng | None,
        departure_at: datetime | None,
        vehicle_type: VehicleType | None,
    ) -> list[dict]:
        student = current.student
        assert student is not None
        cfg = await load_config(self.db)
        window = float(cfg.get("feed.time_window_minutes", settings.FEED_TIME_WINDOW_MINUTES))
        now = datetime.now(UTC)
        anchor = _aware(departure_at) if departure_at else now
        requests = await self.repo.open_requests_for_college(
            student.college_id,
            exclude_user_id=current.id,
            since=anchor - timedelta(minutes=window * 2),
            until=anchor + timedelta(hours=12),
        )
        mcfg = MatchingConfig(
            max_detour_km=float(cfg.get("feed.max_detour_km", settings.FEED_MAX_DETOUR_KM)),
            max_detour_ratio=float(cfg.get("feed.max_detour_ratio", settings.FEED_MAX_DETOUR_RATIO)),
            time_window_min=window if departure_at else 24 * 60,
        )
        items: list[tuple[float, dict]] = []
        for req in requests:
            if vehicle_type and req.vehicle_type != vehicle_type:
                continue
            if req.women_only and student.gender != Gender.FEMALE:
                continue
            match = None
            if pickup and drop:
                candidate = CandidateTrip(pickup=pickup, drop=drop, departure_at=anchor, seats=1, rating=student.average_rating)
                snapshot = RequestSnapshot(
                    origin=LatLng(req.origin_lat, req.origin_lng),
                    destination=LatLng(req.destination_lat, req.destination_lng),
                    departure_at=_aware(req.departure_at),
                    seats_available=req.seats_available,
                    polyline=req.route_polyline,
                    direction=req.direction,
                    route_distance_km=req.route_distance_km,
                )
                match = evaluate_match(candidate, snapshot, mcfg)
                if not match.compatible:
                    continue
            out = await self.serialize(req, viewer_id=current.id, light=True)
            sort_key = -(match.score if match else 0.0) if match else _aware(req.departure_at).timestamp() / 1e12
            items.append((sort_key, {"request": out.model_dump(mode="json"), "match": match.to_dict() if match else None}))
        items.sort(key=lambda x: x[0])
        return [i for _, i in items]

    # ══════════════════════════════════════════════════════════════
    # Join / leave / hide / remove
    # ══════════════════════════════════════════════════════════════
    async def join(self, current: CurrentUser, request_id: str, body: JoinRideIn) -> RideRequestOut:
        student = current.student
        assert student is not None
        req = await self.repo.get_request(request_id)
        if not req:
            raise NotFoundError("Ride not found")
        if req.college_id != student.college_id:
            raise NotSameCollege()
        if req.status != RideRequestStatus.OPEN:
            raise RideStateError("This ride is no longer accepting co-riders")
        if req.women_only and student.gender != Gender.FEMALE:
            raise ForbiddenError("This is a women-only ride")
        if req.seats_available < body.seats:
            raise GroupFull()
        active = await self.repo.active_request_for_user(current.id)
        if active and active.id != req.id:
            raise ActiveRideExists()

        existing = await self.repo.get_member(req.id, current.id)
        if existing and existing.status in ACTIVE_MEMBER_STATUSES:
            raise RideStateError("You are already in this ride")

        cfg = await load_config(self.db)
        match = evaluate_match(
            CandidateTrip(
                pickup=LatLng(body.pickup.lat, body.pickup.lng),
                drop=LatLng(body.drop.lat, body.drop.lng),
                departure_at=_aware(req.departure_at),
                seats=body.seats,
                rating=student.average_rating,
            ),
            RequestSnapshot(
                origin=LatLng(req.origin_lat, req.origin_lng),
                destination=LatLng(req.destination_lat, req.destination_lng),
                departure_at=_aware(req.departure_at),
                seats_available=req.seats_available,
                polyline=req.route_polyline,
                direction=req.direction,
                route_distance_km=req.route_distance_km,
            ),
            MatchingConfig(
                max_detour_km=float(cfg.get("feed.max_detour_km", settings.FEED_MAX_DETOUR_KM)),
                max_detour_ratio=float(cfg.get("feed.max_detour_ratio", settings.FEED_MAX_DETOUR_RATIO)),
                time_window_min=24 * 60,
            ),
        )
        if not match.compatible:
            raise RouteNotCompatible(details=match.to_dict())

        now = datetime.now(UTC)
        code = generate_matching_code()
        own_route = await self.maps.route([LatLng(body.pickup.lat, body.pickup.lng), LatLng(body.drop.lat, body.drop.lng)])
        if existing:
            member = existing
            member.status = MemberStatus.ACCEPTED
            member.left_at = None
            member.joined_at = now
        else:
            member = RideMember(request_id=req.id, user_id=current.id, role=MemberRole.MEMBER, joined_at=now)
            req.members.append(member)
        member.seats = body.seats
        member.pickup_lat, member.pickup_lng, member.pickup_address = body.pickup.lat, body.pickup.lng, body.pickup.address
        member.drop_lat, member.drop_lng, member.drop_address = body.drop.lat, body.drop.lng, body.drop.address
        member.matching_code_plain = code
        member.matching_code_hash = hash_code(code)
        member.detour_km = round(match.detour_km, 2)
        member.match_score = match.score
        member.distance_km = own_route.distance_km
        req.seats_taken += body.seats
        await self.db.flush()

        await self._refresh_group_route(req)
        await self._recompute_shares(req)
        await record_event(self.db, req.id, "member_joined", actor_id=current.id, data={"seats": body.seats, "score": match.score})
        await self.db.commit()
        await hub.subscribe(current.id, ride_topic(req.id))

        out = await self.serialize(req, viewer_id=current.id)
        await self._broadcast_group(req, "group.member_joined", {"user_id": current.id, "full_name": current.user.full_name}, exclude=current.id)
        await notify(
            self.db,
            [m.user_id for m in req.members if m.status in ACTIVE_MEMBER_STATUSES and m.user_id != current.id],
            type=NotificationType.GROUP,
            title="New co-rider joined 🎉",
            body=f"{current.user.full_name or 'A classmate'} joined your ride. {req.seats_available} seat(s) left.",
            data={"request_id": req.id, "screen": "ride"},
        )
        await hub.publish(college_topic(req.college_id), "feed.request_updated", {"request_id": req.id, "seats_available": req.seats_available, "status": req.status})

        if req.seats_available == 0:
            await self._lock(req, actor_id=current.id, reason="seats_full")
            out = await self.serialize(req, viewer_id=current.id)
        return out

    async def leave(self, current: CurrentUser, request_id: str) -> RideRequestOut | None:
        req = await self.repo.get_request(request_id)
        if not req:
            raise NotFoundError("Ride not found")
        member = await self.repo.get_member(req.id, current.id)
        if not member or member.status not in ACTIVE_MEMBER_STATUSES:
            raise RideStateError("You are not part of this ride")
        if member.status == MemberStatus.PICKED_UP:
            raise RideStateError("You are already on board – ask the driver to drop you")
        if req.status in (RideRequestStatus.COMPLETED, RideRequestStatus.CANCELLED, RideRequestStatus.EXPIRED):
            raise RideStateError("This ride is already closed")

        now = datetime.now(UTC)
        member.status = MemberStatus.LEFT
        member.left_at = now
        req.seats_taken = max(0, req.seats_taken - member.seats)
        await self.db.flush()
        await record_event(self.db, req.id, "member_left", actor_id=current.id)
        await hub.unsubscribe(current.id, ride_topic(req.id))

        remaining = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        if member.role == MemberRole.CREATOR:
            if remaining:
                # Hand the group over to the earliest co-rider.
                heir = sorted(remaining, key=lambda m: m.joined_at)[0]
                heir.role = MemberRole.CREATOR
                heir.matching_code_plain = None
                heir.matching_code_hash = None
                req.creator_id = heir.user_id
                if req.otp_plain:
                    from app.core.security import generate_ride_otp

                    otp = generate_ride_otp()
                    req.otp_plain, req.otp_hash = otp, hash_code(otp)
                await record_event(self.db, req.id, "creator_transferred", actor_id=current.id, data={"to": heir.user_id})
                await notify(self.db, [heir.user_id], type=NotificationType.GROUP, title="You're now the ride lead", body="The creator left – you now hold the boarding OTP.", data={"request_id": req.id, "screen": "ride"})
            else:
                await self._cancel(req, actor_id=current.id, reason="creator_left")
                return None
        elif not remaining:
            await self._cancel(req, actor_id=current.id, reason="empty")
            return None

        if req.status == RideRequestStatus.LOCKED and req.seats_taken == 0:
            await self._cancel(req, actor_id=current.id, reason="empty")
            return None

        await self._refresh_group_route(req)
        await self._recompute_shares(req)
        await self.db.commit()
        await self._broadcast_group(req, "group.member_left", {"user_id": current.id, "full_name": current.user.full_name})
        await hub.publish(college_topic(req.college_id), "feed.request_updated", {"request_id": req.id, "seats_available": req.seats_available, "status": req.status})
        if req.status == RideRequestStatus.DRIVER_ASSIGNED and req.ride:
            await hub.send_to_user(req.ride.driver_user_id, "ride.updated", {"request_id": req.id, "reason": "member_left"})
        return await self.serialize(req, viewer_id=current.id)

    async def hide(self, current: CurrentUser, request_id: str) -> None:
        req = await self.repo.get_request(request_id, with_members=False)
        if not req:
            raise NotFoundError("Ride not found")
        existing = await self.db.scalar(
            select(HiddenRequest).where(HiddenRequest.request_id == request_id, HiddenRequest.user_id == current.id)
        )
        if not existing:
            self.db.add(HiddenRequest(request_id=request_id, user_id=current.id, created_at=datetime.now(UTC)))
            await self.db.flush()

    async def remove_member(self, current: CurrentUser, request_id: str, user_id: str) -> RideRequestOut:
        req = await self._owned_request(current, request_id)
        member = await self.repo.get_member(req.id, user_id)
        if not member or member.status not in ACTIVE_MEMBER_STATUSES or member.role == MemberRole.CREATOR:
            raise RideStateError("Member not found in this ride")
        if member.status == MemberStatus.PICKED_UP:
            raise RideStateError("Passenger is already on board")
        member.status = MemberStatus.REMOVED
        member.left_at = datetime.now(UTC)
        req.seats_taken = max(0, req.seats_taken - member.seats)
        await self.db.flush()
        await record_event(self.db, req.id, "member_removed", actor_id=current.id, data={"user_id": user_id})
        await hub.unsubscribe(user_id, ride_topic(req.id))
        await notify(self.db, [user_id], type=NotificationType.GROUP, title="Removed from ride", body="The ride creator removed you from the group.", data={"request_id": req.id})
        await hub.send_to_user(user_id, "group.removed", {"request_id": req.id})
        await self._refresh_group_route(req)
        await self._recompute_shares(req)
        await self.db.commit()
        await self._broadcast_group(req, "group.member_left", {"user_id": user_id})
        await hub.publish(college_topic(req.college_id), "feed.request_updated", {"request_id": req.id, "seats_available": req.seats_available, "status": req.status})
        return await self.serialize(req, viewer_id=current.id)

    # ══════════════════════════════════════════════════════════════
    # Lock ("Find driver now"), cancel, retry
    # ══════════════════════════════════════════════════════════════
    async def lock(self, current: CurrentUser, request_id: str) -> RideRequestOut:
        req = await self._owned_request(current, request_id)
        if req.status != RideRequestStatus.OPEN:
            raise RideStateError("Ride is not open")
        await self._lock(req, actor_id=current.id, reason="creator")
        return await self.serialize(req, viewer_id=current.id)

    async def retry_dispatch(self, current: CurrentUser, request_id: str) -> RideRequestOut:
        req = await self._owned_request(current, request_id)
        if req.status != RideRequestStatus.NO_DRIVER:
            raise RideStateError("Ride is not waiting for a retry")
        await self._lock(req, actor_id=current.id, reason="retry")
        return await self.serialize(req, viewer_id=current.id)

    async def reopen(self, current: CurrentUser, request_id: str) -> RideRequestOut:
        """Creator changed their mind while dispatching – go back to collecting co-riders."""
        req = await self._owned_request(current, request_id)
        if req.status not in (RideRequestStatus.LOCKED, RideRequestStatus.NO_DRIVER):
            raise RideStateError("Ride cannot be reopened now")
        from app.modules.dispatch.service import dispatcher

        await dispatcher.stop(req.id, reason="reopened")
        req.status = RideRequestStatus.OPEN
        req.locked_at = None
        await self.db.flush()
        await record_event(self.db, req.id, "reopened", actor_id=current.id)
        await self.db.commit()
        await self._broadcast_group(req, "group.reopened", {"request_id": req.id})
        await hub.publish(college_topic(req.college_id), "feed.request_updated", {"request_id": req.id, "seats_available": req.seats_available, "status": req.status})
        return await self.serialize(req, viewer_id=current.id)

    async def cancel(self, current: CurrentUser, request_id: str, reason: str | None) -> None:
        req = await self._owned_request(current, request_id)
        if req.status in (RideRequestStatus.IN_PROGRESS, RideRequestStatus.COMPLETED):
            raise RideStateError("Ride already started – it can't be cancelled from the app")
        if req.status in (RideRequestStatus.CANCELLED, RideRequestStatus.EXPIRED):
            return
        await self._cancel(req, actor_id=current.id, reason=reason or "creator_cancelled")

    async def _lock(self, req: RideRequest, *, actor_id: str, reason: str) -> None:
        from app.modules.dispatch.service import dispatcher

        req.status = RideRequestStatus.LOCKED
        req.locked_at = datetime.now(UTC)
        req.dispatch_started_at = None
        req.dispatch_radius_km = None
        await self.db.flush()
        await record_event(self.db, req.id, "locked", actor_id=actor_id, data={"reason": reason})
        await self._broadcast_group(req, "group.locked", {"request_id": req.id, "reason": reason})
        await hub.publish(college_topic(req.college_id), "feed.request_updated", {"request_id": req.id, "seats_available": 0, "status": req.status})
        await notify(
            self.db,
            [m.user_id for m in req.members if m.status in ACTIVE_MEMBER_STATUSES],
            type=NotificationType.RIDE,
            title="Finding your driver 🚕",
            body="Your group is locked. We're searching nearby drivers now.",
            data={"request_id": req.id, "screen": "ride"},
            push=False,
        )
        await self.db.commit()
        dispatcher.start(req.id)

    async def _cancel(self, req: RideRequest, *, actor_id: str | None, reason: str) -> None:
        from app.modules.dispatch.service import dispatcher

        await dispatcher.stop(req.id, reason="cancelled")
        prev_status = req.status
        req.status = RideRequestStatus.CANCELLED
        req.cancel_reason = reason
        active_ids = [m.user_id for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        ride = req.ride
        if ride and ride.status in (RideStatus.DRIVER_ASSIGNED, RideStatus.IN_PROGRESS):
            ride.status = RideStatus.CANCELLED
            ride.cancelled_at = datetime.now(UTC)
            ride.cancel_reason = reason
            driver = await self.repo.driver_profile_by_user(ride.driver_user_id)
            if driver:
                from app.models import DriverStatus

                driver.current_ride_id = None
                if driver.status == DriverStatus.ON_TRIP:
                    driver.status = DriverStatus.ONLINE
            await hub.unsubscribe(ride.driver_user_id, ride_topic(req.id))
            await hub.send_to_user(ride.driver_user_id, "ride.cancelled", {"request_id": req.id, "ride_id": ride.id, "reason": reason})
            await notify(self.db, [ride.driver_user_id], type=NotificationType.RIDE, title="Ride cancelled", body="The passenger group cancelled this ride.", data={"request_id": req.id})
        await self.db.flush()
        await record_event(self.db, req.id, "cancelled", actor_id=actor_id, data={"reason": reason, "from": prev_status})
        await self.db.commit()
        await self._broadcast_group(req, "ride.cancelled", {"request_id": req.id, "reason": reason})
        await notify(
            self.db,
            [uid for uid in active_ids if uid != actor_id],
            type=NotificationType.RIDE,
            title="Ride cancelled",
            body="This ride was cancelled. You can join another one from the feed.",
            data={"request_id": req.id},
        )
        await hub.publish(college_topic(req.college_id), "feed.request_removed", {"request_id": req.id})
        await hub.broadcast_admin("request.cancelled", {"request_id": req.id})

    async def expire_stale_requests(self) -> int:
        now = datetime.now(UTC)
        rows = await self.repo.expired_open_requests(now)
        for req in rows:
            req.status = RideRequestStatus.EXPIRED
            await record_event(self.db, req.id, "expired")
            await self._broadcast_group(req, "ride.expired", {"request_id": req.id})
            await hub.publish(college_topic(req.college_id), "feed.request_removed", {"request_id": req.id})
        return len(rows)

    # ══════════════════════════════════════════════════════════════
    # Queries
    # ══════════════════════════════════════════════════════════════
    async def detail(self, current: CurrentUser, request_id: str) -> RideRequestOut:
        req = await self.repo.get_request(request_id)
        if not req:
            raise NotFoundError("Ride not found")
        is_member = any(m.user_id == current.id for m in req.members)
        is_driver = bool(req.ride and req.ride.driver_user_id == current.id)
        same_college = current.student is not None and current.student.college_id == req.college_id
        if not (is_member or is_driver or same_college or current.role == "admin"):
            raise ForbiddenError()
        if is_member:
            await hub.subscribe(current.id, ride_topic(req.id))
        return await self.serialize(req, viewer_id=current.id)

    async def active(self, current: CurrentUser) -> RideRequestOut | None:
        req = await self.repo.active_request_for_user(current.id)
        if not req:
            return None
        await hub.subscribe(current.id, ride_topic(req.id))
        return await self.serialize(req, viewer_id=current.id)

    async def history(self, current: CurrentUser, limit: int, offset: int) -> list[RideRequestOut]:
        rows = await self.repo.history_for_user(current.id, limit, offset)
        return [await self.serialize(r, viewer_id=current.id, light=True) for r in rows]

    async def _owned_request(self, current: CurrentUser, request_id: str) -> RideRequest:
        req = await self.repo.get_request(request_id)
        if not req:
            raise NotFoundError("Ride not found")
        if req.creator_id != current.id:
            raise ForbiddenError("Only the ride creator can do this")
        return req

    # ══════════════════════════════════════════════════════════════
    # Internals
    # ══════════════════════════════════════════════════════════════
    async def _refresh_group_route(self, req: RideRequest) -> None:
        """Recompute route geometry through all active pickups & drops (simple corridor order)."""
        members = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        if not members:
            return
        origin = LatLng(req.origin_lat, req.origin_lng)
        destination = LatLng(req.destination_lat, req.destination_lng)
        pickups = [LatLng(m.pickup_lat, m.pickup_lng) for m in members]
        drops = [LatLng(m.drop_lat, m.drop_lng) for m in members]
        if req.direction == RideDirection.FROM_COLLEGE:
            # Everyone boards at campus; order drops by distance from campus.
            drops.sort(key=lambda p: distance_km(origin, p))
            waypoints = [origin, *[d for d in drops if distance_km(d, destination) > 0.05], destination]
        else:
            pickups.sort(key=lambda p: -distance_km(destination, p))
            waypoints = [*[p for p in pickups if distance_km(p, origin) > 0.05 or p == pickups[0]], destination]
            if distance_km(waypoints[0], origin) > 0.05:
                waypoints.insert(0, origin)
        dedup: list[LatLng] = []
        for w in waypoints:
            if not dedup or distance_km(dedup[-1], w) > 0.05:
                dedup.append(w)
        route = await self.maps.route(dedup)
        req.route_polyline = route.polyline
        req.route_distance_km = route.distance_km
        req.route_duration_min = route.duration_min
        req.estimated_fare_total = estimate_total(req.vehicle_type, route.distance_km, route.duration_min)
        await self.db.flush()

    async def _recompute_shares(self, req: RideRequest) -> None:
        members = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        if not members or not req.estimated_fare_total:
            return
        cfg = await load_config(self.db)
        fee = float(cfg.get("fare.platform_fee_percent", settings.PLATFORM_FEE_PERCENT))
        distances = {m.id: float(m.distance_km or req.route_distance_km or 1.0) * m.seats for m in members}
        breakdown = split_fare(req.vehicle_type, req.estimated_fare_total, distances, fee)
        for m in members:
            m.fare_share_inr = breakdown.shares.get(m.id)
        await self.db.flush()

    async def _broadcast_group(self, req: RideRequest, event: str, payload: dict, exclude: str | None = None) -> None:
        payload = {**payload, "request_id": req.id, "status": req.status, "seats_available": req.seats_available}
        await hub.publish(ride_topic(req.id), event, payload, exclude=exclude)

    # ── serialization ──────────────────────────────────────────────
    async def serialize(self, req: RideRequest, *, viewer_id: str | None, light: bool = False) -> RideRequestOut:
        users = await self.repo.users_for_members(list(req.members))
        college = await self.db.get(College, req.college_id)
        members_out: list[MemberOut] = []
        me: RideMember | None = None
        for m in req.members:
            if m.status in (MemberStatus.LEFT, MemberStatus.REMOVED) and light:
                continue
            u = users.get(m.user_id)
            sp = u.student_profile if u else None
            if m.user_id == viewer_id:
                me = m
            members_out.append(
                MemberOut(
                    id=m.id,
                    user_id=m.user_id,
                    full_name=(u.full_name if u else "Student"),
                    avatar_url=u.avatar_url if u else None,
                    gender=sp.gender if sp else None,
                    course=sp.course if sp else None,
                    rating=round(sp.average_rating, 1) if sp else 5.0,
                    role=m.role,
                    status=m.status,
                    seats=m.seats,
                    pickup_lat=m.pickup_lat,
                    pickup_lng=m.pickup_lng,
                    pickup_address=m.pickup_address,
                    drop_lat=m.drop_lat,
                    drop_lng=m.drop_lng,
                    drop_address=m.drop_address,
                    pickup_order=m.pickup_order,
                    drop_order=m.drop_order,
                    pickup_eta_min=m.pickup_eta_min,
                    distance_km=m.distance_km,
                    fare_share_inr=m.fare_share_inr,
                    detour_km=m.detour_km,
                    match_score=m.match_score,
                    joined_at=m.joined_at,
                    picked_up_at=m.picked_up_at,
                    dropped_at=m.dropped_at,
                    is_me=(m.user_id == viewer_id),
                )
            )

        driver_out = None
        ride_out = None
        if req.ride:
            ride_out = RideOut.model_validate(req.ride)
            if not light:
                driver_out = await self._driver_out(req.ride.driver_user_id, req.ride.driver_eta_min)

        my_code = None
        my_code_kind = None
        if me and me.status in ACTIVE_MEMBER_STATUSES and req.status in (RideRequestStatus.DRIVER_ASSIGNED, RideRequestStatus.IN_PROGRESS):
            if me.role == MemberRole.CREATOR:
                my_code, my_code_kind = req.otp_plain, "otp"
            else:
                my_code, my_code_kind = me.matching_code_plain, "matching_code"

        my_savings = None
        if me and me.fare_share_inr is not None and req.estimated_fare_solo:
            solo = estimate_total(req.vehicle_type, me.distance_km or req.route_distance_km or 1.0, (me.distance_km or req.route_distance_km or 1.0) / 22 * 60) * me.seats
            my_savings = max(0.0, round(solo - me.fare_share_inr))

        dispatch = None
        if req.status in (RideRequestStatus.LOCKED, RideRequestStatus.NO_DRIVER):
            cfg = await load_config(self.db)
            steps = cfg.get("dispatch.radius_steps_km", settings.DISPATCH_RADIUS_STEPS_KM)
            dispatch = DispatchOut(started_at=req.dispatch_started_at, radius_km=req.dispatch_radius_km, attempts=req.dispatch_attempts, max_radius_km=float(steps[-1]))

        return RideRequestOut(
            id=req.id,
            creator_id=req.creator_id,
            college_id=req.college_id,
            college_name=college.short_name or college.name if college else "",
            direction=req.direction,
            vehicle_type=req.vehicle_type,
            vehicle_label=VEHICLE_LABEL[VehicleType(req.vehicle_type)],
            seat_capacity=req.seat_capacity,
            seats_taken=req.seats_taken,
            seats_available=req.seats_available,
            status=req.status,
            origin_lat=req.origin_lat,
            origin_lng=req.origin_lng,
            origin_address=req.origin_address,
            destination_lat=req.destination_lat,
            destination_lng=req.destination_lng,
            destination_address=req.destination_address,
            departure_at=req.departure_at,
            expires_at=req.expires_at,
            note=req.note,
            women_only=req.women_only,
            route_polyline=req.route_polyline,
            route_distance_km=req.route_distance_km,
            route_duration_min=req.route_duration_min,
            estimated_fare_total=req.estimated_fare_total,
            estimated_fare_solo=req.estimated_fare_solo,
            created_at=req.created_at,
            locked_at=req.locked_at,
            members=members_out,
            driver=driver_out,
            ride=ride_out,
            dispatch=dispatch,
            my_role=me.role if me else None,
            my_status=me.status if me else None,
            my_code=my_code,
            my_code_kind=my_code_kind,
            my_fare_share_inr=me.fare_share_inr if me else None,
            my_savings_inr=my_savings,
        )

    async def _driver_out(self, driver_user_id: str, eta_min: float | None) -> DriverOut | None:
        profile = await self.repo.driver_profile_by_user(driver_user_id)
        if not profile:
            return None
        user: User = profile.user
        pos = hub.get_position(driver_user_id)
        if pos is None and profile.latitude is not None:
            pos_dict = {"lat": profile.latitude, "lng": profile.longitude, "heading": profile.heading, "updated_at": profile.location_updated_at.timestamp() if profile.location_updated_at else None}
        else:
            pos_dict = pos.to_dict() if pos else None
        v = profile.vehicle
        return DriverOut(
            user_id=driver_user_id,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            phone=user.phone,
            rating=round(profile.average_rating, 1),
            completed_rides=profile.completed_rides,
            vehicle_type=v.vehicle_type if v else VehicleType.CAR,
            vehicle_label=VEHICLE_LABEL[VehicleType(v.vehicle_type)] if v else "Car",
            registration_number=v.registration_number if v else None,
            make_model=v.make_model if v else None,
            color=v.color if v else None,
            eta_min=eta_min,
            position=pos_dict,
        )


_ = TARIFFS
