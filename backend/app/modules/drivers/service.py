"""Driver service: onboarding, availability, live location, ride execution."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.exceptions import CodeInvalid, ConflictError, NotFoundError, RideStateError, ValidationFailed
from app.core.geo import LatLng
from app.core.logging import get_logger
from app.core.security import verify_code
from app.intelligence.fare import estimate_total, split_fare
from app.models import (
    ACTIVE_MEMBER_STATUSES,
    VEHICLE_CAPACITY,
    VEHICLE_LABEL,
    DriverProfile,
    DriverStatus,
    MemberRole,
    MemberStatus,
    NotificationType,
    Payment,
    PaymentStatus,
    Ride,
    RideRequestStatus,
    RideStatus,
    StudentProfile,
    Vehicle,
    VehicleType,
    VerificationStatus,
)
from app.modules.dispatch.service import dispatcher
from app.modules.drivers.schemas import DriverRegisterIn, LocationIn
from app.modules.rides.repository import RideRepository
from app.modules.rides.service import RideService
from app.realtime.hub import LivePosition, hub
from app.services.events import record_event, ride_topic
from app.services.notifications import notify
from app.services.runtime_config import load_config

settings = get_settings()
logger = get_logger(__name__)


class DriverService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RideRepository(db)

    # ── onboarding ─────────────────────────────────────────────────
    async def register(self, current: CurrentUser, body: DriverRegisterIn) -> None:
        if current.driver:
            raise ConflictError("Driver profile already exists")
        dup = await self.db.scalar(select(Vehicle).where(Vehicle.registration_number == body.registration_number))
        if dup:
            raise ConflictError("This vehicle is already registered")
        dup_lic = await self.db.scalar(select(DriverProfile).where(DriverProfile.license_number == body.license_number))
        if dup_lic:
            raise ConflictError("This licence number is already registered")
        # All registrations go to pending verification review by admin
        profile = DriverProfile(
            user_id=current.id,
            license_number=body.license_number,
            verification_status=VerificationStatus.PENDING,
            verification_note="Driver submitted registration – review licence & vehicle details.",
        )
        self.db.add(profile)
        await self.db.flush()
        vehicle = Vehicle(
            driver_id=profile.id,
            vehicle_type=body.vehicle_type,
            registration_number=body.registration_number,
            make_model=body.make_model,
            color=body.color,
            seat_capacity=VEHICLE_CAPACITY[body.vehicle_type],
            is_verified=False,
        )
        self.db.add(vehicle)
        current.user.full_name = body.full_name.strip()
        current.user.profile_completed = True
        await self.db.flush()
        logger.info("driver_registered", user_id=current.id, vehicle=body.vehicle_type)

    # ── availability ───────────────────────────────────────────────
    async def set_online(self, current: CurrentUser, online: bool, lat: float | None, lng: float | None) -> dict:
        profile = current.driver
        assert profile is not None
        if profile.current_ride_id and not online:
            raise RideStateError("Finish your active ride before going offline")
        if online:
            if profile.verification_status != VerificationStatus.VERIFIED:
                from app.core.exceptions import DriverNotVerified

                raise DriverNotVerified()
            profile.status = DriverStatus.ON_TRIP if profile.current_ride_id else DriverStatus.ONLINE
            if lat is not None and lng is not None:
                await self.update_location(current, LocationIn(lat=lat, lng=lng))
        else:
            profile.status = DriverStatus.OFFLINE
            hub.clear_position(current.id)
        await self.db.flush()
        await hub.broadcast_admin("driver.status", {"user_id": current.id, "status": profile.status})
        return {"status": profile.status}

    async def update_location(self, current: CurrentUser, loc: LocationIn) -> None:
        profile = current.driver
        assert profile is not None
        now = datetime.now(UTC)
        profile.latitude, profile.longitude, profile.heading = loc.lat, loc.lng, loc.heading
        profile.location_updated_at = now
        pos = LivePosition(
            user_id=current.id,
            role="driver",
            lat=loc.lat,
            lng=loc.lng,
            heading=loc.heading,
            speed=loc.speed,
            accuracy=loc.accuracy,
            ride_id=profile.current_ride_id,
        )
        hub.update_position(pos)
        await self.db.flush()
        if profile.current_ride_id:
            ride = await self.db.get(Ride, profile.current_ride_id)
            if ride:
                await hub.publish(ride_topic(ride.request_id), "ride.driver_location", {**pos.to_dict(), "request_id": ride.request_id}, exclude=current.id)
        await hub.broadcast_admin("driver.location", pos.to_dict())

    # ── offers ─────────────────────────────────────────────────────
    async def current_offer(self, current: CurrentUser) -> dict | None:
        offer = await self.repo.pending_offer_for_driver(current.id)
        if not offer:
            return None
        expires = offer.expires_at if offer.expires_at.tzinfo else offer.expires_at.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            return None
        req = await self.repo.get_request(offer.request_id)
        if not req or req.status != RideRequestStatus.LOCKED:
            return None
        return await dispatcher._offer_payload(self.db, req, offer)

    async def accept(self, current: CurrentUser, offer_id: str) -> dict:
        ride = await dispatcher.accept_offer(self.db, current.id, offer_id)
        return await self.trip_view(current, ride.id)

    async def reject(self, current: CurrentUser, offer_id: str, reason: str | None) -> None:
        await dispatcher.reject_offer(self.db, current.id, offer_id, reason)

    # ── trip execution ─────────────────────────────────────────────
    async def active_trip(self, current: CurrentUser) -> dict | None:
        ride = await self.repo.active_ride_for_driver(current.id)
        if not ride:
            return None
        await hub.subscribe(current.id, ride_topic(ride.request_id))
        return await self.trip_view(current, ride.id)

    async def trip_view(self, current: CurrentUser, ride_id: str) -> dict:
        ride = await self.repo.get_ride(ride_id)
        if not ride or ride.driver_user_id != current.id:
            raise NotFoundError("Ride not found")
        req = ride.request
        request_out = await RideService(self.db).serialize(req, viewer_id=None)
        members = [m for m in req.members if m.status in (*ACTIVE_MEMBER_STATUSES, MemberStatus.DROPPED, MemberStatus.NO_SHOW)]
        users = await self.repo.users_for_members(members)
        # Build the ordered stop list for the driver UI.
        stops: list[dict] = []
        for m in members:
            u = users.get(m.user_id)
            base = {
                "member_id": m.id,
                "user_id": m.user_id,
                "full_name": u.full_name if u else "Student",
                "phone": u.phone if u else None,
                "seats": m.seats,
                "role": m.role,
                "status": m.status,
                "code_kind": "otp" if m.role == MemberRole.CREATOR else "matching_code",
                "matching_code": m.matching_code_plain,
                "fare_share_inr": m.fare_share_inr,
            }
            if m.status in ACTIVE_MEMBER_STATUSES and m.status != MemberStatus.PICKED_UP:
                stops.append({**base, "kind": "pickup", "order": m.pickup_order or 99, "lat": m.pickup_lat, "lng": m.pickup_lng, "address": m.pickup_address, "eta_min": m.pickup_eta_min})
            if m.status == MemberStatus.PICKED_UP:
                stops.append({**base, "kind": "drop", "order": 100 + (m.drop_order or 99), "lat": m.drop_lat, "lng": m.drop_lng, "address": m.drop_address, "eta_min": None})
        stops.sort(key=lambda s: (s["order"], s["kind"]))
        live_riders = [hub.get_position(m.user_id).to_dict() for m in members if hub.get_position(m.user_id)]  # type: ignore[union-attr]
        return {
            "ride": {
                "id": ride.id,
                "status": ride.status,
                "started_at": ride.started_at,
                "completed_at": ride.completed_at,
                "driver_eta_min": ride.driver_eta_min,
                "total_fare_inr": ride.total_fare_inr,
                "driver_payout_inr": ride.driver_payout_inr,
                "total_distance_km": ride.total_distance_km,
            },
            "request": request_out.model_dump(mode="json"),
            "stops": stops,
            "next_stop": stops[0] if stops else None,
            "rider_positions": live_riders,
            "passengers_on_board": sum(m.seats for m in members if m.status == MemberStatus.PICKED_UP),
        }

    async def arrived(self, current: CurrentUser, ride_id: str) -> dict:
        ride = await self._own_ride(current, ride_id)
        req = ride.request
        pending = [m for m in req.members if m.status == MemberStatus.ACCEPTED]
        next_order = min((m.pickup_order or 99 for m in pending), default=None)
        targets = [m for m in pending if (m.pickup_order or 99) == next_order]
        await record_event(self.db, req.id, "driver_arrived", actor_id=current.id, data={"stop": next_order})
        await notify(
            self.db,
            [m.user_id for m in targets],
            type=NotificationType.RIDE,
            title="Your driver has arrived 📍",
            body="Share your code with the driver to board.",
            data={"request_id": req.id, "screen": "ride"},
        )
        await hub.publish(ride_topic(req.id), "ride.driver_arrived", {"request_id": req.id, "member_ids": [m.id for m in targets]})
        return await self.trip_view(current, ride_id)

    async def verify_pickup(self, current: CurrentUser, ride_id: str, code: str) -> dict:
        """Board passenger(s) by OTP (creator) or matching code (member)."""
        ride = await self._own_ride(current, ride_id)
        req = ride.request
        if ride.status not in (RideStatus.DRIVER_ASSIGNED, RideStatus.IN_PROGRESS):
            raise RideStateError("Ride is not active")
        now = datetime.now(UTC)
        matched: list = []

        # 1. Match against Lead OTP
        if req.otp_hash and verify_code(code, req.otp_hash):
            pending_creators = [m for m in req.members if m.role == MemberRole.CREATOR and m.status == MemberStatus.ACCEPTED]
            if pending_creators:
                matched = pending_creators
                ride.otp_verified_at = now
            else:
                # If creator is already boarded, allow verifying any remaining co-rider with OTP as well (Uber/Ola single-OTP convenience)
                pending_members = [m for m in req.members if m.status == MemberStatus.ACCEPTED]
                if pending_members:
                    matched = [pending_members[0]]

        # 2. Match against Co-rider Matching Code (case-insensitive)
        if not matched:
            clean_code = code.strip().upper()
            for m in req.members:
                if m.status == MemberStatus.ACCEPTED and m.matching_code_hash:
                    if verify_code(clean_code, m.matching_code_hash) or (m.matching_code_plain and m.matching_code_plain.upper() == clean_code):
                        matched = [m]
                        break

        # 3. Direct Lead OTP fallback: in shared rides, if driver enters the Lead OTP, board all pending members at that stop
        if not matched and req.otp_hash and verify_code(code, req.otp_hash):
            matched = [m for m in req.members if m.status == MemberStatus.ACCEPTED]

        if not matched:
            raise CodeInvalid()

        for m in matched:
            m.status = MemberStatus.PICKED_UP
            m.picked_up_at = now

        if ride.status == RideStatus.DRIVER_ASSIGNED:
            ride.status = RideStatus.IN_PROGRESS
            ride.started_at = now
            req.status = RideRequestStatus.IN_PROGRESS

        await self.db.flush()
        await record_event(self.db, req.id, "member_picked_up", actor_id=current.id, data={"member_ids": [m.id for m in matched]})
        await self.db.commit()
        await hub.publish(ride_topic(req.id), "ride.member_picked_up", {"request_id": req.id, "member_ids": [m.id for m in matched], "user_ids": [m.user_id for m in matched], "status": req.status})
        await notify(self.db, [m.user_id for m in matched], type=NotificationType.RIDE, title="You're on board 🚗", body="Enjoy the ride! Track your route live in the app.", data={"request_id": req.id, "screen": "ride"}, push=False)
        return await self.trip_view(current, ride_id)

    async def no_show(self, current: CurrentUser, ride_id: str, member_id: str) -> dict:
        ride = await self._own_ride(current, ride_id)
        req = ride.request
        member = next((m for m in req.members if m.id == member_id), None)
        if not member or member.status != MemberStatus.ACCEPTED:
            raise RideStateError("Passenger is not waiting for pickup")
        cfg = await load_config(self.db)
        wait_min = float(cfg.get("ride.no_show_wait_minutes", settings.NO_SHOW_WAIT_MINUTES))
        arrived_events = [e for e in await self._events(req.id) if e.event == "driver_arrived"]
        if arrived_events:
            last = arrived_events[-1].created_at
            last = last if last.tzinfo else last.replace(tzinfo=UTC)
            if (datetime.now(UTC) - last).total_seconds() < wait_min * 60:
                raise RideStateError(f"Wait at least {wait_min:g} minutes after arriving before marking a no-show")
        member.status = MemberStatus.NO_SHOW
        member.left_at = datetime.now(UTC)
        req.seats_taken = max(0, req.seats_taken - member.seats)
        sp = await self.db.scalar(select(StudentProfile).where(StudentProfile.user_id == member.user_id))
        if sp:
            sp.cancelled_rides += 1
        await record_event(self.db, req.id, "member_no_show", actor_id=current.id, data={"member_id": member_id})
        await notify(self.db, [member.user_id], type=NotificationType.RIDE, title="Marked as no-show", body="The driver waited but couldn't find you. Repeated no-shows lower your rating.", data={"request_id": req.id})
        if member.role == MemberRole.CREATOR:
            others = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
            if others:
                heir = sorted(others, key=lambda m: m.joined_at)[0]
                heir.role = MemberRole.CREATOR
                req.creator_id = heir.user_id
        remaining = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        await self.db.flush()
        if not remaining:
            await self._complete(ride, reason="all_no_show")
        else:
            await RideService(self.db)._recompute_shares(req)
            await self.db.commit()
            await hub.publish(ride_topic(req.id), "ride.member_no_show", {"request_id": req.id, "member_id": member_id, "status": req.status})
        return await self.trip_view(current, ride_id)

    async def drop(self, current: CurrentUser, ride_id: str, member_id: str) -> dict:
        ride = await self._own_ride(current, ride_id)
        req = ride.request
        member = next((m for m in req.members if m.id == member_id), None)
        if not member or member.status != MemberStatus.PICKED_UP:
            raise RideStateError("Passenger is not on board")
        now = datetime.now(UTC)
        member.status = MemberStatus.DROPPED
        member.dropped_at = now
        await record_event(self.db, req.id, "member_dropped", actor_id=current.id, data={"member_id": member_id})
        await self.db.flush()
        await hub.publish(ride_topic(req.id), "ride.member_dropped", {"request_id": req.id, "member_id": member_id, "user_id": member.user_id, "status": req.status})
        sp = await self.db.scalar(select(StudentProfile).where(StudentProfile.user_id == member.user_id))
        if sp:
            sp.completed_rides += 1
            solo = estimate_total(VehicleType(req.vehicle_type), member.distance_km or req.route_distance_km or 1.0, (member.distance_km or req.route_distance_km or 1.0) / 22 * 60)
            sp.total_saved_inr += max(0.0, solo * member.seats - (member.fare_share_inr or 0))
        await notify(self.db, [member.user_id], type=NotificationType.RIDE, title="You've arrived 🎯", body=f"Fare ₹{member.fare_share_inr:.0f}. Please rate your ride." if member.fare_share_inr else "Please rate your ride.", data={"request_id": req.id, "screen": "rate"})
        if not any(m.status in ACTIVE_MEMBER_STATUSES for m in req.members):
            await self._complete(ride, reason="all_dropped")
        else:
            await self.db.commit()
        return await self.trip_view(current, ride_id)

    async def cancel_by_driver(self, current: CurrentUser, ride_id: str, reason: str) -> None:
        ride = await self._own_ride(current, ride_id)
        req = ride.request
        if ride.status != RideStatus.DRIVER_ASSIGNED:
            raise RideStateError("You can't cancel after passengers boarded – contact support")
        profile = current.driver
        assert profile is not None
        ride.status = RideStatus.CANCELLED
        ride.cancelled_at = datetime.now(UTC)
        ride.cancel_reason = reason
        profile.current_ride_id = None
        profile.status = DriverStatus.ONLINE
        req.status = RideRequestStatus.LOCKED  # re-dispatch to another driver
        req.locked_at = datetime.now(UTC)
        req.otp_plain = req.otp_hash = None
        for m in req.members:
            m.pickup_order = m.drop_order = m.pickup_eta_min = None
        await record_event(self.db, req.id, "driver_cancelled", actor_id=current.id, data={"reason": reason})
        ids = [m.user_id for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        await notify(
            self.db,
            ids,
            type=NotificationType.RIDE,
            title="Driver cancelled",
            body="Don't worry – we're finding you another driver right now.",
            data={"request_id": req.id, "screen": "ride"},
        )
        await self.db.commit()
        await hub.unsubscribe(current.id, ride_topic(req.id))
        await hub.publish(ride_topic(req.id), "ride.driver_cancelled", {"request_id": req.id, "status": req.status})
        await hub.broadcast_admin("ride.driver_cancelled", {"request_id": req.id, "ride_id": ride.id})
        dispatcher.start(req.id)

    async def _complete(self, ride: Ride, *, reason: str) -> None:
        req = ride.request
        now = datetime.now(UTC)
        cfg = await load_config(self.db)
        fee_pct = float(cfg.get("fare.platform_fee_percent", settings.PLATFORM_FEE_PERCENT))
        served = [m for m in req.members if m.status == MemberStatus.DROPPED]
        total = float(req.estimated_fare_total or 0.0) if served else 0.0
        breakdown = split_fare(VehicleType(req.vehicle_type), total, {m.id: float(m.distance_km or req.route_distance_km or 1.0) * m.seats for m in served}, fee_pct) if served else None
        ride.status = RideStatus.COMPLETED
        ride.completed_at = now
        ride.total_distance_km = req.route_distance_km
        ride.total_fare_inr = breakdown.total if breakdown else 0.0
        ride.platform_fee_inr = breakdown.platform_fee if breakdown else 0.0
        ride.driver_payout_inr = breakdown.driver_payout if breakdown else 0.0
        req.status = RideRequestStatus.COMPLETED
        for m in served:
            m.fare_share_inr = breakdown.shares.get(m.id, m.fare_share_inr) if breakdown else m.fare_share_inr
            self.db.add(Payment(ride_id=ride.id, payer_id=m.user_id, amount_inr=m.fare_share_inr or 0.0, status=PaymentStatus.PENDING))
        profile = await self.repo.driver_profile_by_user(ride.driver_user_id)
        if profile:
            profile.current_ride_id = None
            profile.status = DriverStatus.ONLINE
            profile.completed_rides += 1
            profile.total_earnings_inr += ride.driver_payout_inr or 0.0
        await record_event(self.db, req.id, "ride_completed", actor_id=ride.driver_user_id, data={"reason": reason, "fare": ride.total_fare_inr})
        await self.db.commit()
        await hub.publish(ride_topic(req.id), "ride.completed", {"request_id": req.id, "ride_id": ride.id, "status": req.status, "total_fare_inr": ride.total_fare_inr})
        await hub.broadcast_admin("ride.completed", {"request_id": req.id, "ride_id": ride.id, "fare": ride.total_fare_inr})
        logger.info("ride_completed", ride_id=ride.id, fare=ride.total_fare_inr, reason=reason)

    # ── earnings / history ─────────────────────────────────────────
    async def earnings(self, current: CurrentUser) -> dict:
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        rows = await self.db.execute(
            select(func.count(Ride.id), func.coalesce(func.sum(Ride.driver_payout_inr), 0.0)).where(
                Ride.driver_user_id == current.id, Ride.status == RideStatus.COMPLETED, Ride.completed_at >= today
            )
        )
        count, total = rows.one()
        profile = current.driver
        assert profile is not None
        return {
            "today_rides": int(count or 0),
            "today_earnings_inr": float(total or 0.0),
            "total_rides": profile.completed_rides,
            "total_earnings_inr": profile.total_earnings_inr,
            "rating": round(profile.average_rating, 1),
            "acceptance_rate": round(profile.acceptance_rate, 2),
        }

    async def history(self, current: CurrentUser, limit: int, offset: int) -> list[dict]:
        rides = await self.repo.driver_ride_history(current.id, limit, offset)
        out = []
        for r in rides:
            req = r.request
            out.append(
                {
                    "ride_id": r.id,
                    "status": r.status,
                    "completed_at": r.completed_at,
                    "cancelled_at": r.cancelled_at,
                    "origin_address": req.origin_address if req else None,
                    "destination_address": req.destination_address if req else None,
                    "passengers": sum(m.seats for m in req.members if m.status == MemberStatus.DROPPED) if req else 0,
                    "driver_payout_inr": r.driver_payout_inr,
                    "total_distance_km": r.total_distance_km,
                    "vehicle_label": VEHICLE_LABEL[VehicleType(r.vehicle_type)],
                }
            )
        return out

    # ── helpers ────────────────────────────────────────────────────
    async def _own_ride(self, current: CurrentUser, ride_id: str) -> Ride:
        ride = await self.repo.get_ride(ride_id)
        if not ride or ride.driver_user_id != current.id:
            raise NotFoundError("Ride not found")
        return ride

    async def _events(self, request_id: str):
        from app.models import RideEvent

        return (
            await self.db.execute(select(RideEvent).where(RideEvent.request_id == request_id).order_by(RideEvent.created_at.asc()))
        ).scalars().all()


_ = (LatLng, ValidationFailed)
