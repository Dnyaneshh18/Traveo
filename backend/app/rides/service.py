"""
Traveo Backend — Ride & Matching Service

Core orchestrator for ride booking, matching engine invocation, passenger group voting,
driver assignment, OTP verification, and state machine transitions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_ride_otp
from app.exceptions import (
    DriverAlreadyAssignedError,
    DuplicateBookingError,
    GroupFullError,
    GroupLockedError,
    GroupNotFoundError,
    InvalidRideStateError,
    NoDriverFoundError,
    OTPExpiredError,
    OTPInvalidError,
    RideError,
    RideNotFoundError,
)
from app.intelligence.driver import DriverCandidate, DriverSelectionEngine
from app.intelligence.matching import CandidateRideRequest, PassengerMatchingEngine
from app.intelligence.route import RouteCompatibilityEvaluator, RoutePoint
from app.models.enums import (
    BoardingStatus,
    DriverAssignmentStatus,
    DropStatus,
    GroupStatus,
    OnlineStatus,
    RideRequestStatus,
    RideStatus,
    RideType,
    VoteChoice,
)
from app.rides.repository import RideRepository
from app.rides.schemas import (
    AcceptRejectResponse,
    CreateRideRequest,
    CreateRideResponse,
    DriverActiveRideResponse,
    DriverLocationUpdate,
    DriverOnlineResponse,
    DriverRideAssignment,
    GroupDetailResponse,
    GroupMemberResponse,
    RideDetailResponse,
    RideHistoryItem,
    RideHistoryResponse,
    RideRequestDetailResponse,
    VoteRequest,
    VoteResponse,
)

logger = structlog.get_logger(__name__)


class RideService:
    """Business logic for ride booking, matching, and execution lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RideRepository(db)
        self.matching_engine = PassengerMatchingEngine()
        self.driver_engine = DriverSelectionEngine()

    # ══════════════════════════════════════════════════════
    # PASSENGER: Ride Booking
    # ══════════════════════════════════════════════════════

    async def create_ride_request(
        self, passenger_id: str, request: CreateRideRequest
    ) -> CreateRideResponse:
        """
        Passenger submits a ride request.
        1. Check duplicate active requests.
        2. Calculate estimated fare.
        3. Save request as MATCHING.
        4. Trigger passenger matching algorithm.
        """
        # Check active requests
        existing = await self.repo.get_active_request_by_passenger(passenger_id)
        if existing:
            raise DuplicateBookingError()

        # Dynamic vehicle category fare rates and seat occupancy scaling
        from app.intelligence.geo import haversine_distance_km
        from app.models.enums import VehicleCategory

        dist_km = haversine_distance_km(
            request.pickup.latitude, request.pickup.longitude,
            request.destination.latitude, request.destination.longitude,
        )

        base_fare = 30.0
        per_km = 12.0
        max_seats = 4

        if request.vehicle_category == VehicleCategory.AUTO_RICKSHAW:
            base_fare = 20.0
            per_km = 8.0
            max_seats = 3
        elif request.vehicle_category == VehicleCategory.SUV_6_8_SEATER:
            base_fare = 50.0
            per_km = 18.0
            max_seats = 6

        raw_vehicle_fare = base_fare + (dist_km * per_km)
        # Shared seat fare proportion
        seat_ratio = request.requested_seats / max_seats
        estimated_fare = round(raw_vehicle_fare * (0.6 + 0.4 * seat_ratio), 2)

        # Save request
        req = await self.repo.create_ride_request(
            passenger_id=passenger_id,
            pickup_lat=request.pickup.latitude,
            pickup_lon=request.pickup.longitude,
            pickup_address=request.pickup.address,
            dest_lat=request.destination.latitude,
            dest_lon=request.destination.longitude,
            dest_address=request.destination.address,
            seats=request.requested_seats,
            estimated_fare=estimated_fare,
            ride_type=request.ride_type,
        )

        logger.info("ride_request_created", request_id=str(req.id), passenger_id=passenger_id)

        if request.ride_type == RideType.SOLO or request.requested_seats == max_seats:
            # Solo ride logic: Create a group of 1 and bypass matching
            group = await self.repo.create_ride_group(
                capacity=request.requested_seats,
                estimated_fare=estimated_fare,
            )
            await self.repo.add_passenger_to_group(str(group.id), passenger_id, str(req.id))
            await self.repo.update_request_status(str(req.id), RideRequestStatus.MATCHED)
            await self.repo.update_group_status(str(group.id), GroupStatus.SEARCHING_DRIVER)
            await self._attempt_driver_assignment(str(group.id))
            
            return CreateRideResponse(
                ride_request_id=str(req.id),
                status=RideRequestStatus.MATCHED,
                estimated_fare=estimated_fare,
                matching_started=False,
            )

        # Attempt immediate matching with existing pending requests
        await self._attempt_passenger_matching(req)

        return CreateRideResponse(
            ride_request_id=str(req.id),
            status=req.status,
            estimated_fare=estimated_fare,
            matching_started=True,
        )

    async def cancel_ride_request(self, passenger_id: str, request_id: str) -> None:
        """Cancel a pending/matching ride request."""
        req = await self.repo.get_ride_request_by_id(request_id)
        if not req or str(req.passenger_id) != passenger_id:
            raise RideNotFoundError()

        if req.status in (RideRequestStatus.CANCELLED, RideRequestStatus.EXPIRED):
            return

        await self.repo.update_request_status(request_id, RideRequestStatus.CANCELLED)
        logger.info("ride_request_cancelled", request_id=request_id, passenger_id=passenger_id)

    async def get_ride_request_detail(
        self, passenger_id: str, request_id: str
    ) -> RideRequestDetailResponse:
        """Get details of a specific ride request."""
        req = await self.repo.get_ride_request_by_id(request_id)
        if not req or str(req.passenger_id) != passenger_id:
            raise RideNotFoundError()

        return RideRequestDetailResponse(
            id=str(req.id),
            passenger_id=str(req.passenger_id),
            pickup_latitude=cast(float, req.pickup_latitude),
            pickup_longitude=cast(float, req.pickup_longitude),
            pickup_address=cast(str | None, req.pickup_address),
            destination_latitude=cast(float, req.destination_latitude),
            destination_longitude=cast(float, req.destination_longitude),
            destination_address=cast(str | None, req.destination_address),
            requested_seats=cast(int, req.requested_seats),
            status=req.status,
            estimated_fare=cast(float | None, req.estimated_fare),
            created_at=cast(datetime, req.created_at),
        )

    # ══════════════════════════════════════════════════════
    # PASSENGER: Active Ride & History
    # ══════════════════════════════════════════════════════

    async def get_active_ride_for_passenger(
        self, passenger_id: str
    ) -> RideDetailResponse | None:
        """Get the current active ride for a passenger."""
        ride = await self.repo.get_active_ride_for_passenger(passenger_id)
        if not ride:
            return None
        return await self._build_ride_detail(ride)

    async def get_passenger_ride_history(
        self, passenger_id: str, limit: int = 20, offset: int = 0
    ) -> RideHistoryResponse:
        """Get ride history for a passenger."""
        rides = await self.repo.get_ride_history_for_passenger(passenger_id, limit, offset)
        items = [
            RideHistoryItem(
                ride_id=str(r.id),
                ride_status=r.ride_status,
                total_fare=cast(float | None, r.total_fare),
                ride_started=cast(datetime | None, r.ride_started),
                ride_completed=cast(datetime | None, r.ride_completed),
                created_at=cast(datetime, r.created_at),
            )
            for r in rides
        ]
        return RideHistoryResponse(rides=items, total=len(items))

    # ══════════════════════════════════════════════════════
    # PASSENGER: Group Voting
    # ══════════════════════════════════════════════════════

    async def record_vote(
        self, passenger_id: str, group_id: str, request: VoteRequest
    ) -> VoteResponse:
        """Record passenger vote (continue, wait, cancel) when group is waiting."""
        group = await self.repo.get_group_with_members(group_id)
        if not group:
            raise GroupNotFoundError()

        # Record vote
        await self.repo.record_group_vote(group_id, passenger_id, request.vote.value)

        # Re-fetch updated votes
        votes = await self.repo.get_group_votes(group_id)
        total_members = len(group.members)
        total_votes = len(votes)

        outcome = "pending"
        if total_votes >= total_members:
            # Majority evaluation
            continue_votes = sum(1 for v in votes if v.vote == VoteChoice.CONTINUE.value)
            if continue_votes >= (total_members / 2):
                outcome = "proceed"
                await self.repo.update_group_status(group_id, GroupStatus.SEARCHING_DRIVER)
            else:
                outcome = "wait"

        return VoteResponse(
            group_id=group_id,
            vote=request.vote,
            total_votes=total_votes,
            required_votes=total_members,
            outcome=outcome,
        )

    # ══════════════════════════════════════════════════════
    # PASSENGER MATCHING CORE ALGORITHM
    # ══════════════════════════════════════════════════════

    async def _attempt_passenger_matching(self, target_req) -> None:
        """
        Matches target request against pending waiting requests in DB.
        If a compatible match is found, forms a RideGroup.
        """
        other_requests = await self.repo.get_pending_matching_requests(
            exclude_request_id=str(target_req.id)
        )

        if not other_requests:
            logger.info("matching_no_candidates", request_id=str(target_req.id))
            return

        target_candidate = CandidateRideRequest(
            id=str(target_req.id),
            passenger_id=str(target_req.passenger_id),
            pickup_latitude=cast(float, target_req.pickup_latitude),
            pickup_longitude=cast(float, target_req.pickup_longitude),
            destination_latitude=cast(float, target_req.destination_latitude),
            destination_longitude=cast(float, target_req.destination_longitude),
            requested_seats=cast(int, target_req.requested_seats),
        )

        candidate_list = [
            CandidateRideRequest(
                id=str(r.id),
                passenger_id=str(r.passenger_id),
                pickup_latitude=cast(float, r.pickup_latitude),
                pickup_longitude=cast(float, r.pickup_longitude),
                destination_latitude=cast(float, r.destination_latitude),
                destination_longitude=cast(float, r.destination_longitude),
                requested_seats=cast(int, r.requested_seats),
            )
            for r in other_requests
        ]

        matches = self.matching_engine.find_best_matches(
            target_candidate, candidate_list
        )

        if not matches:
            logger.info("matching_no_compatible_matches", request_id=str(target_req.id))
            return

        best_match = matches[0]
        logger.info(
            "passenger_match_found",
            req_a=str(target_req.id),
            req_b=best_match.request_b_id,
            score=best_match.score,
        )

        # Form a new RideGroup for these matched passengers
        est_fare = float(target_req.estimated_fare) if target_req.estimated_fare is not None else 50.0
        group = await self.repo.create_ride_group(
            capacity=4,
            estimated_fare=round(est_fare * 0.85, 2),  # Shared discount
        )

        # Add target request to group
        await self.repo.add_passenger_to_group(str(group.id), str(target_req.passenger_id), str(target_req.id))
        await self.repo.update_request_status(str(target_req.id), RideRequestStatus.MATCHED)

        # Add matched request to group
        other_req = next(r for r in other_requests if str(r.id) == best_match.request_b_id)
        await self.repo.add_passenger_to_group(str(group.id), str(other_req.passenger_id), str(other_req.id))
        await self.repo.update_request_status(str(other_req.id), RideRequestStatus.MATCHED)

        # Move group to SEARCHING_DRIVER
        await self.repo.update_group_status(str(group.id), GroupStatus.SEARCHING_DRIVER)

        # Auto-trigger driver assignment
        await self._attempt_driver_assignment(str(group.id))

        # Broadcast matching event via WebSocket
        await self._broadcast_group_event(
            str(group.id),
            "MatchingCompleted",
            {"group_id": str(group.id), "passengers": 2},
        )

    # ══════════════════════════════════════════════════════
    # DRIVER ASSIGNMENT ENGINE
    # ══════════════════════════════════════════════════════

    async def _attempt_driver_assignment(self, group_id: str) -> None:
        """
        Find and assign the best available driver for a ride group.
        1. Get group with members to find first pickup location.
        2. Query nearby online, verified drivers.
        3. Run through DriverSelectionEngine ranking.
        4. Create DriverAssignment record for top-ranked driver.
        """
        group = await self.repo.get_group_with_members(group_id)
        if not group or not group.members:
            logger.warning("driver_assignment_no_group", group_id=group_id)
            return

        # Use first member's pickup as reference point
        first_member = group.members[0]
        req = await self.repo.get_ride_request_by_id(str(first_member.ride_request_id))
        if not req:
            return

        # Dynamic radius expansion to prioritize closest drivers
        search_radii = [1.5, 2.5, 3.5]
        best = None
        total_seats = sum(1 for _ in group.members)

        for radius in search_radii:
            driver_vehicle_pairs = await self.repo.get_nearby_online_drivers(
                lat=cast(float, req.pickup_latitude),
                lon=cast(float, req.pickup_longitude),
                radius_km=radius,
            )

            if not driver_vehicle_pairs:
                continue

            # Build candidates for ranking
            candidates = []
            for driver_profile, vehicle in driver_vehicle_pairs:
                if not driver_profile.current_latitude or not driver_profile.current_longitude:
                    continue
                seat_cap = cast(int, vehicle.seat_capacity) if vehicle else 4
                candidates.append(DriverCandidate(
                    driver_id=str(driver_profile.id),
                    user_id=str(driver_profile.user_id),
                    latitude=cast(float, driver_profile.current_latitude),
                    longitude=cast(float, driver_profile.current_longitude),
                    rating=cast(float, driver_profile.driver_rating),
                    completed_rides=cast(int, driver_profile.completed_rides),
                    cancelled_rides=cast(int, driver_profile.cancelled_rides),
                    seat_capacity=seat_cap,
                    is_online=True,
                    is_verified=True,
                ))

            if not candidates:
                continue

            # Rank and select best
            ranked = self.driver_engine.rank_drivers(
                candidates,
                first_pickup_lat=cast(float, req.pickup_latitude),
                first_pickup_lon=cast(float, req.pickup_longitude),
                required_seats=total_seats,
            )

            if ranked:
                best = ranked[0]
                logger.info("driver_found_at_radius", radius=radius, group_id=group_id)
                break

        if not best:
            logger.info("no_eligible_drivers_after_expansion", group_id=group_id, max_radius=search_radii[-1])
            return

        # Create assignment
        assignment = await self.repo.create_driver_assignment(
            group_id=group_id,
            driver_id=best.user_id,
        )

        logger.info(
            "driver_assignment_created",
            group_id=group_id,
            driver_id=best.user_id,
            score=best.score,
            eta_minutes=best.eta_minutes,
        )

        # Notify driver via WebSocket
        await self._broadcast_to_user(
            best.user_id,
            "RideAssigned",
            {
                "assignment_id": str(assignment.id),
                "ride_group_id": group_id,
                "passengers": total_seats,
                "estimated_fare": cast(float | None, group.estimated_fare),
                "pickup_lat": cast(float, req.pickup_latitude),
                "pickup_lon": cast(float, req.pickup_longitude),
                "pickup_address": cast(str | None, req.pickup_address),
            },
        )

    # ══════════════════════════════════════════════════════
    # DRIVER: Accept / Reject Ride
    # ══════════════════════════════════════════════════════

    async def accept_ride(self, driver_id: str) -> AcceptRejectResponse:
        """
        Driver accepts the pending ride assignment.
        Creates Ride record, generates OTP, assigns driver to group.
        """
        assignment = await self.repo.get_pending_assignment_for_driver(driver_id)
        if not assignment:
            raise RideNotFoundError(message="No pending ride assignment found.")

        # Update assignment
        await self.repo.update_assignment_status(
            str(assignment.id), DriverAssignmentStatus.ACCEPTED
        )

        # Get group for fare info
        group = await self.repo.get_group_with_members(str(assignment.ride_group_id))
        if not group:
            raise GroupNotFoundError()

        # Generate OTP
        otp = generate_ride_otp()
        await self.repo.create_ride_otp(str(assignment.ride_group_id), otp)

        # Assign driver to group
        await self.repo.assign_driver_to_group(
            str(assignment.ride_group_id), driver_id, otp
        )

        # Create Ride record
        group_fare = cast(float, group.estimated_fare) if group.estimated_fare is not None else 0.0
        ride = await self.repo.create_ride_record(
            group_id=str(assignment.ride_group_id),
            driver_id=driver_id,
            total_fare=group_fare,
        )

        # Update ride status
        await self.repo.update_ride_status(str(ride.id), RideStatus.OTP_GENERATED)

        # Set driver to busy
        await self.repo.update_driver_online_status(driver_id, OnlineStatus.BUSY)

        logger.info(
            "ride_accepted",
            ride_id=str(ride.id),
            driver_id=driver_id,
            group_id=str(assignment.ride_group_id),
        )

        # Notify passengers via WebSocket
        for member in group.members:
            await self._broadcast_to_user(
                str(member.passenger_id),
                "DriverAssigned",
                {
                    "ride_id": str(ride.id),
                    "driver_id": driver_id,
                    "otp": otp,
                    "group_id": str(assignment.ride_group_id),
                },
            )

        return AcceptRejectResponse(
            status="accepted",
            ride_id=str(ride.id),
            otp=otp,
            message="Ride accepted. Proceed to pickup.",
        )

    async def reject_ride(self, driver_id: str) -> AcceptRejectResponse:
        """Driver rejects the pending ride assignment."""
        assignment = await self.repo.get_pending_assignment_for_driver(driver_id)
        if not assignment:
            raise RideNotFoundError(message="No pending ride assignment found.")

        await self.repo.update_assignment_status(
            str(assignment.id), DriverAssignmentStatus.REJECTED
        )

        logger.info("ride_rejected", driver_id=driver_id, group_id=str(assignment.ride_group_id))

        # Try to assign next best driver
        await self._attempt_driver_assignment(str(assignment.ride_group_id))

        return AcceptRejectResponse(
            status="rejected",
            message="Ride rejected. Looking for another driver.",
        )

    # ══════════════════════════════════════════════════════
    # DRIVER: Go Online / Offline
    # ══════════════════════════════════════════════════════

    async def go_online(self, driver_id: str) -> DriverOnlineResponse:
        """Set driver status to online."""
        profile = await self.repo.get_driver_profile_by_user_id(driver_id)
        if not profile:
            raise RideError(message="Driver profile not found.")

        await self.repo.update_driver_online_status(driver_id, OnlineStatus.ONLINE)
        logger.info("driver_online", driver_id=driver_id)

        return DriverOnlineResponse(status="online", message="You are now online and receiving rides.")

    async def go_offline(self, driver_id: str) -> DriverOnlineResponse:
        """Set driver status to offline."""
        await self.repo.update_driver_online_status(driver_id, OnlineStatus.OFFLINE)
        logger.info("driver_offline", driver_id=driver_id)

        return DriverOnlineResponse(status="offline", message="You are now offline.")

    # ══════════════════════════════════════════════════════
    # DRIVER: Location Update
    # ══════════════════════════════════════════════════════

    async def update_driver_location(
        self, driver_id: str, update: DriverLocationUpdate
    ) -> None:
        """Update driver's real-time location."""
        await self.repo.update_driver_location(
            user_id=driver_id,
            latitude=update.latitude,
            longitude=update.longitude,
            heading=update.heading,
            speed=update.speed,
        )

        # If driver has an active ride, broadcast location to passengers
        ride = await self.repo.get_active_ride_for_driver(driver_id)
        if ride:
            group = await self.repo.get_group_with_members(str(ride.ride_group_id))
            if group:
                for member in group.members:
                    await self._broadcast_to_user(
                        str(member.passenger_id),
                        "DriverLocationUpdated",
                        {
                            "latitude": update.latitude,
                            "longitude": update.longitude,
                            "heading": update.heading,
                            "speed": update.speed,
                        },
                    )

    # ══════════════════════════════════════════════════════
    # DRIVER: OTP Verification & Ride Execution
    # ══════════════════════════════════════════════════════

    async def verify_ride_otp(
        self, driver_id: str, ride_id: str, otp: str
    ) -> bool:
        """
        Driver verifies passenger OTP at pickup.
        Marks passenger boarded and transitions ride state.
        """
        ride = await self.repo.get_ride_by_id(ride_id)
        if not ride:
            raise RideNotFoundError()

        if str(ride.driver_id) != driver_id:
            raise RideError(message="Driver is not assigned to this ride.")

        valid_otp = await self.repo.get_valid_otp(str(ride.ride_group_id))
        if not valid_otp:
            raise OTPExpiredError()

        if valid_otp.otp != otp:
            raise OTPInvalidError()

        # OTP verified
        await self.repo.mark_otp_verified(str(valid_otp.id))
        await self.repo.update_ride_status(str(ride.id), RideStatus.PICKUP_IN_PROGRESS)

        logger.info("ride_otp_verified", ride_id=ride_id, driver_id=driver_id)

        # Broadcast to group
        await self._broadcast_group_event(
            str(ride.ride_group_id),
            "OTPVerified",
            {"ride_id": ride_id},
        )

        return True

    async def pickup_passenger(
        self, driver_id: str, ride_id: str, passenger_id: str
    ) -> None:
        """Driver confirms a specific passenger has boarded."""
        ride = await self.repo.get_ride_by_id(ride_id)
        if not ride or str(ride.driver_id) != driver_id:
            raise RideNotFoundError()

        # Create pickup event
        await self.repo.create_pickup_event(str(ride.id), passenger_id)
        await self.repo.update_member_boarding_status(
            str(ride.ride_group_id), passenger_id, BoardingStatus.BOARDED
        )

        logger.info("passenger_boarded", ride_id=ride_id, passenger_id=passenger_id)

        # Check if all passengers are boarded
        group = await self.repo.get_group_with_members(str(ride.ride_group_id))
        if group:
            all_boarded = all(
                m.boarding_status == BoardingStatus.BOARDED
                for m in group.members
            )
            if all_boarded:
                await self.repo.update_ride_status(str(ride.id), RideStatus.ALL_PASSENGERS_BOARDED)

        # Broadcast
        await self._broadcast_group_event(
            str(ride.ride_group_id),
            "PassengerBoarded",
            {"passenger_id": passenger_id},
        )

    async def start_ride(self, driver_id: str, ride_id: str) -> None:
        """Driver starts the ride trip after passengers board."""
        ride = await self.repo.get_ride_by_id(ride_id)
        if not ride or str(ride.driver_id) != driver_id:
            raise RideNotFoundError()

        await self.repo.update_ride_status(str(ride.id), RideStatus.RIDE_STARTED)
        logger.info("ride_started", ride_id=ride_id)

        # Broadcast
        await self._broadcast_group_event(
            str(ride.ride_group_id),
            "RideStarted",
            {"ride_id": ride_id},
        )

    async def drop_passenger(
        self, driver_id: str, ride_id: str, passenger_id: str
    ) -> None:
        """Driver confirms a specific passenger has been dropped off."""
        ride = await self.repo.get_ride_by_id(ride_id)
        if not ride or str(ride.driver_id) != driver_id:
            raise RideNotFoundError()

        await self.repo.create_drop_event(str(ride.id), passenger_id)
        await self.repo.update_member_drop_status(
            str(ride.ride_group_id), passenger_id, DropStatus.DROPPED
        )

        logger.info("passenger_dropped", ride_id=ride_id, passenger_id=passenger_id)

        # Check if all passengers are dropped
        group = await self.repo.get_group_with_members(str(ride.ride_group_id))
        if group:
            all_dropped = all(
                m.drop_status == DropStatus.DROPPED
                for m in group.members
            )
            if all_dropped:
                await self.complete_ride(driver_id, ride_id)

        # Broadcast
        await self._broadcast_group_event(
            str(ride.ride_group_id),
            "PassengerDropped",
            {"passenger_id": passenger_id},
        )

    async def complete_ride(self, driver_id: str, ride_id: str) -> None:
        """Driver completes the ride trip after final drop-off."""
        ride = await self.repo.get_ride_by_id(ride_id)
        if not ride or str(ride.driver_id) != driver_id:
            raise RideNotFoundError()

        await self.repo.update_ride_status(str(ride.id), RideStatus.RIDE_COMPLETED)
        await self.repo.update_group_status(str(ride.ride_group_id), GroupStatus.LOCKED)

        # Set driver back to online
        await self.repo.update_driver_online_status(driver_id, OnlineStatus.ONLINE)

        logger.info("ride_completed", ride_id=ride_id)

        # Broadcast
        await self._broadcast_group_event(
            str(ride.ride_group_id),
            "RideCompleted",
            {"ride_id": ride_id, "total_fare": cast(float | None, ride.total_fare)},
        )

    # ══════════════════════════════════════════════════════
    # DRIVER: Active Ride & History
    # ══════════════════════════════════════════════════════

    async def get_active_ride_for_driver(
        self, driver_id: str
    ) -> DriverActiveRideResponse | None:
        """Get the current active ride for a driver."""
        ride = await self.repo.get_active_ride_for_driver(driver_id)
        if not ride:
            return None

        group = await self.repo.get_group_with_members(str(ride.ride_group_id))
        group_detail = self._build_group_detail(group) if group else None

        return DriverActiveRideResponse(
            ride_id=str(ride.id),
            ride_group_id=str(ride.ride_group_id),
            ride_status=ride.ride_status,
            total_fare=cast(float | None, ride.total_fare),
            group=group_detail,
        )

    async def get_driver_ride_history(
        self, driver_id: str, limit: int = 20, offset: int = 0
    ) -> RideHistoryResponse:
        """Get ride history for a driver."""
        rides = await self.repo.get_ride_history_for_driver(driver_id, limit, offset)
        items = [
            RideHistoryItem(
                ride_id=str(r.id),
                ride_status=r.ride_status,
                total_fare=cast(float | None, r.total_fare),
                ride_started=cast(datetime | None, r.ride_started),
                ride_completed=cast(datetime | None, r.ride_completed),
                created_at=cast(datetime, r.created_at),
            )
            for r in rides
        ]
        return RideHistoryResponse(rides=items, total=len(items))

    # ══════════════════════════════════════════════════════
    # HELPER: Build Response Models
    # ══════════════════════════════════════════════════════

    async def _build_ride_detail(self, ride) -> RideDetailResponse:
        """Build a full ride detail response including group info."""
        group = await self.repo.get_group_with_members(str(ride.ride_group_id))
        group_detail = self._build_group_detail(group) if group else None

        return RideDetailResponse(
            ride_id=str(ride.id),
            ride_group_id=str(ride.ride_group_id),
            driver_id=str(ride.driver_id),
            ride_status=ride.ride_status,
            total_fare=cast(float | None, ride.total_fare),
            ride_started=cast(datetime | None, ride.ride_started),
            ride_completed=cast(datetime | None, ride.ride_completed),
            actual_distance=cast(float | None, ride.actual_distance),
            actual_duration=cast(float | None, ride.actual_duration),
            created_at=cast(datetime, ride.created_at),
            group=group_detail,
        )

    @staticmethod
    def _build_group_detail(group) -> GroupDetailResponse:
        """Build group detail from ORM model."""
        members = [
            GroupMemberResponse(
                passenger_id=str(m.passenger_id),
                boarding_status=m.boarding_status,
                drop_status=m.drop_status,
                pickup_order=cast(int | None, m.pickup_order),
                drop_order=cast(int | None, m.drop_order),
            )
            for m in group.members
        ]
        return GroupDetailResponse(
            group_id=str(group.id),
            group_status=group.group_status,
            current_passengers=cast(int, group.current_passengers),
            maximum_capacity=cast(int, group.maximum_capacity),
            estimated_fare=cast(float | None, group.estimated_fare),
            driver_id=str(group.driver_id) if group.driver_id else None,
            common_otp=cast(str | None, group.common_otp),
            members=members,
        )

    # ══════════════════════════════════════════════════════
    # HELPER: WebSocket Broadcasts
    # ══════════════════════════════════════════════════════

    @staticmethod
    async def _broadcast_group_event(
        group_id: str, event_name: str, payload: dict
    ) -> None:
        """Broadcast an event to all members of a ride group."""
        try:
            from app.websocket.manager import manager
            from app.websocket.events import WSEventType

            event_type = WSEventType(event_name) if event_name in WSEventType.__members__.values() else None
            if event_type:
                await manager.broadcast_to_group(group_id, event_type, payload)
        except Exception as e:
            logger.warning("ws_broadcast_failed", group_id=group_id, error=str(e))

    @staticmethod
    async def _broadcast_to_user(
        user_id: str, event_name: str, payload: dict
    ) -> None:
        """Send an event to a specific user."""
        try:
            from app.websocket.manager import manager
            from app.websocket.events import WSEventType

            event_map = {e.value: e for e in WSEventType}
            event_type = event_map.get(event_name)
            if event_type:
                await manager.send_to_user(user_id, event_type, payload)
        except Exception as e:
            logger.warning("ws_send_failed", user_id=user_id, error=str(e))
