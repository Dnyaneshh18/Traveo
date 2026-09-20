"""
Traveo Ride Intelligence Engine — Passenger Matching Engine

Implements candidate discovery, hard constraint checking, and multi-factor
matching score calculation according to Part 13 specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.intelligence.geo import haversine_distance_km
from app.intelligence.route import RouteCompatibilityEvaluator, RoutePoint


@dataclass
class CandidateRideRequest:
    id: str
    passenger_id: str
    pickup_latitude: float
    pickup_longitude: float
    destination_latitude: float
    destination_longitude: float
    requested_seats: int
    waiting_time_minutes: float = 0.0


@dataclass
class MatchCandidateResult:
    request_a_id: str
    request_b_id: str
    score: float
    route_overlap: float
    pickup_distance_km: float
    destination_distance_km: float
    is_compatible: bool
    rejection_reason: str | None = None


class PassengerMatchingEngine:
    """
    Core passenger matching engine. Matches incoming ride requests with
    existing waiting requests to form high-quality shared ride groups.
    """

    def __init__(
        self,
        weight_route_overlap: float = 0.35,
        weight_pickup_efficiency: float = 0.20,
        weight_destination_similarity: float = 0.20,
        weight_waiting_fairness: float = 0.15,
        weight_vehicle_utilization: float = 0.10,
        weight_delay_penalty: float = 0.15,
        max_pickup_distance_km: float = 3.0,
        max_destination_distance_km: float = 5.0,
        max_direction_angle_degrees: float = 45.0,
        max_capacity: int = 4,
    ) -> None:
        self.w1 = weight_route_overlap
        self.w2 = weight_pickup_efficiency
        self.w3 = weight_destination_similarity
        self.w4 = weight_waiting_fairness
        self.w5 = weight_vehicle_utilization
        self.w6 = weight_delay_penalty

        self.max_pickup_dist = max_pickup_distance_km
        self.max_dest_dist = max_destination_distance_km
        self.max_direction_angle = max_direction_angle_degrees
        self.max_capacity = max_capacity

    def evaluate_match(
        self, req_a: CandidateRideRequest, req_b: CandidateRideRequest
    ) -> MatchCandidateResult:
        """
        Evaluate compatibility between two ride requests.
        Enforces hard constraints first, then calculates weighted score.
        """
        # Hard Constraint 1: Seat capacity
        if req_a.requested_seats + req_b.requested_seats > self.max_capacity:
            return MatchCandidateResult(
                request_a_id=req_a.id,
                request_b_id=req_b.id,
                score=0.0,
                route_overlap=0.0,
                pickup_distance_km=0.0,
                destination_distance_km=0.0,
                is_compatible=False,
                rejection_reason="Capacity exceeded",
            )

        # Distance lookups
        pickup_dist = haversine_distance_km(
            req_a.pickup_latitude, req_a.pickup_longitude,
            req_b.pickup_latitude, req_b.pickup_longitude,
        )
        dest_dist = haversine_distance_km(
            req_a.destination_latitude, req_a.destination_longitude,
            req_b.destination_latitude, req_b.destination_longitude,
        )

        # Hard Constraint 2: Pickup proximity
        if pickup_dist > self.max_pickup_dist:
            return MatchCandidateResult(
                request_a_id=req_a.id,
                request_b_id=req_b.id,
                score=0.0,
                route_overlap=0.0,
                pickup_distance_km=pickup_dist,
                destination_distance_km=dest_dist,
                is_compatible=False,
                rejection_reason="Pickup distance too large",
            )

        # Hard Constraint 3: Direction compatibility
        direction_ok, _ = RouteCompatibilityEvaluator.evaluate_direction_compatibility(
            (req_a.pickup_latitude, req_a.pickup_longitude),
            (req_a.destination_latitude, req_a.destination_longitude),
            (req_b.pickup_latitude, req_b.pickup_longitude),
            (req_b.destination_latitude, req_b.destination_longitude),
            max_angle_diff_degrees=self.max_direction_angle,
        )

        if not direction_ok:
            return MatchCandidateResult(
                request_a_id=req_a.id,
                request_b_id=req_b.id,
                score=0.0,
                route_overlap=0.0,
                pickup_distance_km=pickup_dist,
                destination_distance_km=dest_dist,
                is_compatible=False,
                rejection_reason="Incompatible trip direction",
            )

        # Calculate Score Factors (all normalized 0.0 - 1.0)
        route_overlap = RouteCompatibilityEvaluator.calculate_route_overlap(
            (req_a.pickup_latitude, req_a.pickup_longitude),
            (req_a.destination_latitude, req_a.destination_longitude),
            (req_b.pickup_latitude, req_b.pickup_longitude),
            (req_b.destination_latitude, req_b.destination_longitude),
        )

        pickup_efficiency = max(0.0, 1.0 - (pickup_dist / self.max_pickup_dist))
        dest_similarity = max(0.0, 1.0 - (dest_dist / self.max_dest_dist))

        # Waiting fairness boosts requests that have been waiting longer
        waiting_fairness = min(1.0, max(req_a.waiting_time_minutes, req_b.waiting_time_minutes) / 5.0)

        # Vehicle utilization score (higher when closer to max capacity)
        total_seats = req_a.requested_seats + req_b.requested_seats
        vehicle_utilization = total_seats / self.max_capacity

        # Delay penalty based on detour distance
        delay_penalty = pickup_dist / self.max_pickup_dist

        # Overall Weighted Score Formula from Part 13
        score = (
            (route_overlap * self.w1)
            + (pickup_efficiency * self.w2)
            + (dest_similarity * self.w3)
            + (waiting_fairness * self.w4)
            + (vehicle_utilization * self.w5)
            - (delay_penalty * self.w6)
        )

        normalized_score = round(max(0.0, min(1.0, score)), 4)

        return MatchCandidateResult(
            request_a_id=req_a.id,
            request_b_id=req_b.id,
            score=normalized_score,
            route_overlap=route_overlap,
            pickup_distance_km=round(pickup_dist, 2),
            destination_distance_km=round(dest_dist, 2),
            is_compatible=True,
        )

    def find_best_matches(
        self,
        target_request: CandidateRideRequest,
        candidates: list[CandidateRideRequest],
        min_score_threshold: float = 0.30,
    ) -> list[MatchCandidateResult]:
        """
        Rank candidate ride requests for a target request.
        Returns sorted list of valid matches in descending score order.
        """
        results: list[MatchCandidateResult] = []

        for candidate in candidates:
            if candidate.id == target_request.id:
                continue
            if candidate.passenger_id == target_request.passenger_id:
                continue

            res = self.evaluate_match(target_request, candidate)
            if res.is_compatible and res.score >= min_score_threshold:
                results.append(res)

        # Sort by highest score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
