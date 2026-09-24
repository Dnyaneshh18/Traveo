"""
Dispatch engine — finds a driver for a locked passenger group.

Algorithm (Uber/Ola style)
--------------------------
1. Anchor = first pickup (campus gate for `from_college`, the creator's
   pickup for `to_college`).
2. For each radius ring (1 → 2 → 3.5 → 5 → 8 km): load online, verified,
   idle drivers with fresh GPS inside the ring, rank them
   (proximity, rating, acceptance rate, vehicle fit) and offer the ride to
   the best one **sequentially** with a countdown.  Passengers see the live
   ring radius ("Searching within 2 km…").
3. Reject / timeout → next driver → next ring.  After the last ring the
   cycle pauses briefly and restarts (drivers come online all the time)
   until the max dispatch duration → `no_driver` (creator can retry).
4. Acceptance is handled by `accept_offer` (driver API) which atomically
   creates the `Ride`, generates the creator OTP + member matching codes,
   computes the optimised pickup/drop order and notifies everybody.

One asyncio task per request; state lives in the DB so the API can be
restarted safely (a sweeper re-arms LOCKED requests on boot).
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import session_scope
from app.core.geo import LatLng, bounding_box
from app.core.logging import get_logger
from app.core.security import generate_ride_otp, hash_code
from app.intelligence.dispatch import DriverCandidate, rank_drivers
from app.intelligence.routing import MemberTrip, optimise_stops, sequence_numbers
from app.maps.provider import get_maps_provider
from app.models import (
    ACTIVE_MEMBER_STATUSES,
    VEHICLE_LABEL,
    DriverOffer,
    DriverProfile,
    DriverStatus,
    MemberRole,
    NotificationType,
    OfferStatus,
    Ride,
    RideDirection,
    RideRequest,
    RideRequestStatus,
    RideStatus,
    VehicleType,
)
from app.modules.rides.repository import RideRepository
from app.realtime.hub import hub
from app.services.events import record_event, ride_topic
from app.services.notifications import notify
from app.services.runtime_config import load_config

settings = get_settings()
logger = get_logger(__name__)


class Dispatcher:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self._offer_events: dict[str, asyncio.Event] = {}

    # ── lifecycle ──────────────────────────────────────────────────
    def start(self, request_id: str) -> None:
        existing = self._tasks.get(request_id)
        if existing and not existing.done():
            return
        self._tasks[request_id] = asyncio.create_task(self._run(request_id), name=f"dispatch:{request_id}")

    async def stop(self, request_id: str, *, reason: str) -> None:
        task = self._tasks.pop(request_id, None)
        if task and not task.done() and task is not asyncio.current_task():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        if reason != "accepted":
            # Release any driver still looking at an offer for this request.
            async with session_scope() as db:
                cancelled = await RideRepository(db).cancel_pending_offers(request_id)
            for o in cancelled:
                await hub.send_to_user(o.driver_user_id, "dispatch.offer_expired", {"offer_id": o.id})
        logger.info("dispatch_stopped", request_id=request_id, reason=reason)

    def signal_offer(self, offer_id: str) -> None:
        ev = self._offer_events.get(offer_id)
        if ev:
            ev.set()

    async def resume_pending(self) -> None:
        """Re-arm dispatch loops after a restart."""
        from sqlalchemy import select

        async with session_scope() as db:
            rows = (
                await db.execute(select(RideRequest.id).where(RideRequest.status == RideRequestStatus.LOCKED))
            ).scalars().all()
        for rid in rows:
            self.start(rid)
        if rows:
            logger.info("dispatch_resumed", count=len(rows))

    # ── main loop ──────────────────────────────────────────────────
    async def _run(self, request_id: str) -> None:
        try:
            async with session_scope() as db:
                cfg = await load_config(db)
            radius_steps = [float(x) for x in cfg.get("dispatch.radius_steps_km", settings.DISPATCH_RADIUS_STEPS_KM)]
            offer_timeout = int(cfg.get("dispatch.offer_timeout_seconds", settings.DISPATCH_OFFER_TIMEOUT_SECONDS))
            max_duration = int(cfg.get("dispatch.max_duration_seconds", settings.DISPATCH_MAX_DURATION_SECONDS))
            pause = int(cfg.get("dispatch.retry_pause_seconds", settings.DISPATCH_RETRY_PAUSE_SECONDS))

            started = datetime.now(UTC)
            async with session_scope() as db:
                req = await RideRepository(db).get_request(request_id)
                if not req or req.status != RideRequestStatus.LOCKED:
                    return
                req.dispatch_started_at = started
                req.dispatch_attempts = 0

            cycle = 0
            while True:
                cycle += 1
                for radius in radius_steps:
                    accepted = await self._search_ring(request_id, radius, offer_timeout)
                    if accepted is None:  # request no longer dispatching
                        return
                    if accepted:
                        return
                    if (datetime.now(UTC) - started).total_seconds() > max_duration:
                        await self._give_up(request_id)
                        return
                await self._publish_status(request_id, radius_km=radius_steps[-1], phase="retrying", cycle=cycle)
                await asyncio.sleep(pause)
                if (datetime.now(UTC) - started).total_seconds() > max_duration:
                    await self._give_up(request_id)
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("dispatch_crashed", request_id=request_id)
        finally:
            self._tasks.pop(request_id, None)

    async def _search_ring(self, request_id: str, radius: float, offer_timeout: int) -> bool | None:
        """Returns True if a driver accepted, False to continue, None if dispatch should stop."""
        async with session_scope() as db:
            repo = RideRepository(db)
            req = await repo.get_request(request_id)
            if not req or req.status != RideRequestStatus.LOCKED:
                return None
            req.dispatch_radius_km = radius
            anchor = self._anchor(req)
            required_seats = req.seats_taken
            min_lat, min_lng, max_lat, max_lng = bounding_box(anchor.lat, anchor.lng, radius * 1.05)
            fresh_after = datetime.now(UTC) - timedelta(seconds=settings.DRIVER_LOCATION_STALE_SECONDS)
            drivers = await repo.available_drivers_in_bbox(min_lat, min_lng, max_lat, max_lng, fresh_after)
            already = await repo.offered_driver_ids(request_id)
            candidates = [
                DriverCandidate(
                    user_id=d.user_id,
                    position=LatLng(d.latitude, d.longitude),  # type: ignore[arg-type]
                    vehicle_type=VehicleType(d.vehicle.vehicle_type),
                    seat_capacity=d.vehicle.seat_capacity,
                    rating=d.average_rating,
                    acceptance_rate=d.acceptance_rate,
                    completed_rides=d.completed_rides,
                    already_offered=d.user_id in already and self._recently_offered(req, d.user_id),
                )
                for d in drivers
                if d.vehicle is not None
            ]
            ranked = rank_drivers(anchor, candidates, VehicleType(req.vehicle_type), required_seats, radius)
            await db.commit()

        await self._publish_status(request_id, radius_km=radius, phase="searching", candidates=len(ranked))
        logger.info("dispatch_ring", request_id=request_id, radius=radius, candidates=len(ranked))

        for ranked_driver in ranked[:4]:
            result = await self._offer(request_id, ranked_driver, radius, offer_timeout)
            if result is None:
                return None
            if result:
                return True
        return False

    @staticmethod
    def _recently_offered(req: RideRequest, driver_user_id: str) -> bool:
        cutoff = datetime.now(UTC) - timedelta(seconds=90)
        for o in req.offers:
            if o.driver_user_id == driver_user_id and o.status in (OfferStatus.REJECTED, OfferStatus.EXPIRED):
                created = o.created_at if o.created_at.tzinfo else o.created_at.replace(tzinfo=UTC)
                if created > cutoff:
                    return True
        return False

    @staticmethod
    def _anchor(req: RideRequest) -> LatLng:
        if req.direction == RideDirection.FROM_COLLEGE:
            return LatLng(req.origin_lat, req.origin_lng)
        creator = next((m for m in req.members if m.role == MemberRole.CREATOR and m.status in ACTIVE_MEMBER_STATUSES), None)
        if creator:
            return LatLng(creator.pickup_lat, creator.pickup_lng)
        return LatLng(req.origin_lat, req.origin_lng)

    async def _offer(self, request_id: str, ranked, radius: float, offer_timeout: int) -> bool | None:
        now = datetime.now(UTC)
        async with session_scope() as db:
            repo = RideRepository(db)
            req = await repo.get_request(request_id)
            if not req or req.status != RideRequestStatus.LOCKED:
                return None
            # Skip drivers who picked up another job meanwhile.
            profile = await repo.driver_profile_by_user(ranked.candidate.user_id)
            if not profile or profile.status != DriverStatus.ONLINE or profile.current_ride_id:
                return False
            pending = await repo.pending_offer_for_driver(ranked.candidate.user_id)
            if pending:
                return False
            cfg = await load_config(db)
            fee = float(cfg.get("fare.platform_fee_percent", settings.PLATFORM_FEE_PERCENT))
            payout = round((req.estimated_fare_total or 0) * (1 - fee / 100))
            offer = DriverOffer(
                request_id=req.id,
                driver_user_id=ranked.candidate.user_id,
                status=OfferStatus.PENDING,
                radius_km=radius,
                distance_km=ranked.distance_km,
                eta_min=ranked.eta_min,
                score=ranked.score,
                driver_payout_inr=payout,
                created_at=now,
                expires_at=now + timedelta(seconds=offer_timeout),
            )
            db.add(offer)
            req.dispatch_attempts += 1
            profile.offers_received += 1
            await db.flush()
            offer_id = offer.id
            payload = await self._offer_payload(db, req, offer)
            await record_event(db, req.id, "offer_sent", data={"driver_user_id": offer.driver_user_id, "radius_km": radius, "eta_min": ranked.eta_min})

        ev = asyncio.Event()
        self._offer_events[offer_id] = ev
        await hub.send_to_user(ranked.candidate.user_id, "dispatch.offer", payload)
        async with session_scope() as db:
            await notify(
                db,
                [ranked.candidate.user_id],
                type=NotificationType.DRIVER,
                title="New ride request 🚕",
                body=f"{payload['passenger_count']} student(s) · {payload['pickup_address'][:40]} · ₹{payload['driver_payout_inr']:.0f}",
                data={"offer_id": offer_id, "screen": "offer"},
            )
        await self._publish_status(request_id, radius_km=radius, phase="offering", eta_min=ranked.eta_min)

        try:
            await asyncio.wait_for(ev.wait(), timeout=offer_timeout + 1)
        except TimeoutError:
            pass
        finally:
            self._offer_events.pop(offer_id, None)

        async with session_scope() as db:
            offer = await RideRepository(db).get_offer(offer_id)
            if not offer:
                return False
            if offer.status == OfferStatus.ACCEPTED:
                return True
            if offer.status == OfferStatus.PENDING:
                offer.status = OfferStatus.EXPIRED
                offer.responded_at = datetime.now(UTC)
                await db.flush()
                await hub.send_to_user(offer.driver_user_id, "dispatch.offer_expired", {"offer_id": offer_id})
                await record_event(db, request_id, "offer_expired", data={"driver_user_id": offer.driver_user_id})
            req = await RideRepository(db).get_request(request_id, with_members=False)
            if not req or req.status != RideRequestStatus.LOCKED:
                return None
        return False

    async def _offer_payload(self, db: AsyncSession, req: RideRequest, offer: DriverOffer) -> dict:
        members = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        anchor = self._anchor(req)
        first_pickup = next((m for m in members if m.role == MemberRole.CREATOR), members[0] if members else None)
        return {
            "offer_id": offer.id,
            "request_id": req.id,
            "expires_at": offer.expires_at.isoformat(),
            "timeout_seconds": int((offer.expires_at - offer.created_at).total_seconds()),
            "vehicle_type": req.vehicle_type,
            "vehicle_label": VEHICLE_LABEL[VehicleType(req.vehicle_type)],
            "passenger_count": sum(m.seats for m in members),
            "stops": len({(round(m.pickup_lat, 4), round(m.pickup_lng, 4)) for m in members}) + len({(round(m.drop_lat, 4), round(m.drop_lng, 4)) for m in members}),
            "pickup_lat": anchor.lat,
            "pickup_lng": anchor.lng,
            "pickup_address": first_pickup.pickup_address if first_pickup else req.origin_address,
            "destination_address": req.destination_address,
            "destination_lat": req.destination_lat,
            "destination_lng": req.destination_lng,
            "distance_to_pickup_km": offer.distance_km,
            "eta_to_pickup_min": offer.eta_min,
            "route_distance_km": req.route_distance_km,
            "route_duration_min": req.route_duration_min,
            "fare_total_inr": req.estimated_fare_total,
            "driver_payout_inr": offer.driver_payout_inr,
            "departure_at": req.departure_at.isoformat(),
            "college_id": req.college_id,
            "note": req.note,
            "polyline": req.route_polyline,
        }

    async def _publish_status(self, request_id: str, **payload) -> None:
        async with session_scope() as db:
            req = await RideRepository(db).get_request(request_id, with_members=False)
            if not req:
                return
            data = {"request_id": request_id, "status": req.status, "attempts": req.dispatch_attempts, **payload}
        await hub.publish(ride_topic(request_id), "dispatch.status", data)
        await hub.broadcast_admin("dispatch.status", data)

    async def _give_up(self, request_id: str) -> None:
        async with session_scope() as db:
            repo = RideRepository(db)
            req = await repo.get_request(request_id)
            if not req or req.status != RideRequestStatus.LOCKED:
                return
            req.status = RideRequestStatus.NO_DRIVER
            await db.flush()
            await record_event(db, req.id, "no_driver", data={"attempts": req.dispatch_attempts})
            ids = [m.user_id for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
            await notify(
                db,
                ids,
                type=NotificationType.RIDE,
                title="No drivers nearby yet",
                body="We couldn't find a driver in time. Tap retry to search again or wait for more co-riders.",
                data={"request_id": req.id, "screen": "ride"},
            )
        await hub.publish(ride_topic(request_id), "ride.no_driver", {"request_id": request_id, "status": RideRequestStatus.NO_DRIVER})
        logger.info("dispatch_no_driver", request_id=request_id)

    # ══════════════════════════════════════════════════════════════
    # Driver responses
    # ══════════════════════════════════════════════════════════════
    async def accept_offer(self, db: AsyncSession, driver_user_id: str, offer_id: str) -> Ride:
        from app.core.exceptions import OfferUnavailable

        repo = RideRepository(db)
        offer = await repo.get_offer(offer_id)
        now = datetime.now(UTC)
        if not offer or offer.driver_user_id != driver_user_id or offer.status != OfferStatus.PENDING:
            raise OfferUnavailable()
        expires = offer.expires_at if offer.expires_at.tzinfo else offer.expires_at.replace(tzinfo=UTC)
        if expires < now - timedelta(seconds=2):
            offer.status = OfferStatus.EXPIRED
            raise OfferUnavailable("The offer timed out")
        req = await repo.get_request(offer.request_id)
        if not req or req.status != RideRequestStatus.LOCKED:
            offer.status = OfferStatus.CANCELLED
            raise OfferUnavailable("The passengers are no longer waiting")
        profile = await repo.driver_profile_by_user(driver_user_id)
        if not profile or not profile.vehicle or profile.current_ride_id:
            raise OfferUnavailable("You already have an active ride")

        offer.status = OfferStatus.ACCEPTED
        offer.responded_at = now
        profile.offers_accepted += 1
        profile.status = DriverStatus.ON_TRIP

        otp = generate_ride_otp()
        req.otp_plain, req.otp_hash = otp, hash_code(otp)
        for m in req.members:
            if m.status in ACTIVE_MEMBER_STATUSES and m.role != MemberRole.CREATOR and not m.matching_code_plain:
                from app.core.security import generate_matching_code

                code = generate_matching_code()
                m.matching_code_plain, m.matching_code_hash = code, hash_code(code)

        ride = Ride(
            request_id=req.id,
            driver_user_id=driver_user_id,
            offer_id=offer.id,
            status=RideStatus.DRIVER_ASSIGNED,
            vehicle_type=profile.vehicle.vehicle_type,
            vehicle_registration=profile.vehicle.registration_number,
            driver_eta_min=offer.eta_min,
        )
        req.rides.append(ride)
        await db.flush()
        profile.current_ride_id = ride.id
        req.status = RideRequestStatus.DRIVER_ASSIGNED

        driver_pos = LatLng(profile.latitude or req.origin_lat, profile.longitude or req.origin_lng)
        await self.plan_stops(db, req, driver_pos)
        await record_event(db, req.id, "driver_assigned", actor_id=driver_user_id, data={"ride_id": ride.id, "eta_min": offer.eta_min})
        await db.flush()

        # Cancel any other pending offers for this request (defensive).
        for o in req.offers:
            if o.id != offer.id and o.status == OfferStatus.PENDING:
                o.status = OfferStatus.CANCELLED
                await hub.send_to_user(o.driver_user_id, "dispatch.offer_expired", {"offer_id": o.id})

        await db.commit()
        await hub.subscribe(driver_user_id, ride_topic(req.id))
        self.signal_offer(offer.id)
        await self.stop(req.id, reason="accepted")

        ids = [m.user_id for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        await hub.publish(
            ride_topic(req.id),
            "ride.driver_assigned",
            {"request_id": req.id, "ride_id": ride.id, "driver_user_id": driver_user_id, "eta_min": offer.eta_min, "status": req.status},
        )
        await notify(
            db,
            ids,
            type=NotificationType.RIDE,
            title="Driver assigned ✅",
            body=f"{profile.user.full_name} ({VEHICLE_LABEL[VehicleType(profile.vehicle.vehicle_type)]} · {profile.vehicle.registration_number}) is {offer.eta_min:.0f} min away.",
            data={"request_id": req.id, "screen": "ride"},
        )
        await hub.broadcast_admin("ride.driver_assigned", {"request_id": req.id, "ride_id": ride.id, "driver_user_id": driver_user_id})
        logger.info("offer_accepted", request_id=req.id, driver=driver_user_id, ride_id=ride.id)
        return ride

    async def reject_offer(self, db: AsyncSession, driver_user_id: str, offer_id: str, reason: str | None) -> None:
        from app.core.exceptions import OfferUnavailable

        repo = RideRepository(db)
        offer = await repo.get_offer(offer_id)
        if not offer or offer.driver_user_id != driver_user_id:
            raise OfferUnavailable()
        if offer.status != OfferStatus.PENDING:
            return
        offer.status = OfferStatus.REJECTED
        offer.responded_at = datetime.now(UTC)
        await db.flush()
        await record_event(db, offer.request_id, "offer_rejected", actor_id=driver_user_id, data={"reason": reason})
        await db.commit()
        self.signal_offer(offer_id)

    # ══════════════════════════════════════════════════════════════
    # Stop planning (pickup / drop order + ETAs)
    # ══════════════════════════════════════════════════════════════
    async def plan_stops(self, db: AsyncSession, req: RideRequest, driver_pos: LatLng) -> None:
        members = [m for m in req.members if m.status in ACTIVE_MEMBER_STATUSES]
        if not members:
            return
        trips = [
            MemberTrip(
                member_id=m.id,
                pickup=LatLng(m.pickup_lat, m.pickup_lng),
                pickup_address=m.pickup_address,
                drop=LatLng(m.drop_lat, m.drop_lng),
                drop_address=m.drop_address,
            )
            for m in members
        ]
        stops = optimise_stops(driver_pos, trips)
        pickup_order, drop_order = sequence_numbers(stops)
        waypoints = [driver_pos]
        for s in stops:
            if not waypoints or (abs(waypoints[-1].lat - s.point.lat) > 1e-4 or abs(waypoints[-1].lng - s.point.lng) > 1e-4):
                waypoints.append(s.point)
        route = await get_maps_provider().route(waypoints)
        # cumulative ETA per stop
        cum_min = 0.0
        leg_idx = 0
        eta_by_point: dict[tuple[float, float], float] = {}
        prev = driver_pos
        for s in stops:
            key = (round(s.point.lat, 4), round(s.point.lng, 4))
            if key not in eta_by_point:
                if leg_idx < len(route.legs) and (abs(prev.lat - s.point.lat) > 1e-4 or abs(prev.lng - s.point.lng) > 1e-4):
                    cum_min += route.legs[leg_idx]["duration_min"]
                    leg_idx += 1
                    prev = s.point
                eta_by_point[key] = round(cum_min, 1)
        for m in members:
            m.pickup_order = pickup_order.get(m.id)
            m.drop_order = drop_order.get(m.id)
            m.pickup_eta_min = eta_by_point.get((round(m.pickup_lat, 4), round(m.pickup_lng, 4)))
        req.route_polyline = route.polyline
        req.route_distance_km = route.distance_km
        req.route_duration_min = route.duration_min
        if req.ride:
            first = min((m.pickup_eta_min or 0 for m in members), default=None)
            req.ride.driver_eta_min = first
        await db.flush()


dispatcher = Dispatcher()
_ = DriverProfile
