"""
Traveo Ride Intelligence Engine — Route Compatibility & Sequence Optimizer

Evaluates route overlap, calculates detour metrics, and produces optimized
pickup and drop sequence orders for shared ride passenger groups.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from app.intelligence.geo import (
    bearing_difference,
    calculate_bearing,
    estimate_travel_time_minutes,
    haversine_distance_km,
)


@dataclass
class RoutePoint:
    id: str
    latitude: float
    longitude: float
    point_type: str  # "pickup" or "drop"
    passenger_id: str


@dataclass
class RouteEvaluation:
    overlap_percentage: float  # 0.0 to 1.0 (100%)
    total_distance_km: float
    detour_distance_km: float
    estimated_duration_minutes: float
    pickup_sequence: list[str]  # List of passenger_ids in order
    drop_sequence: list[str]    # List of passenger_ids in order


class RouteCompatibilityEvaluator:
    """Evaluates how compatible two or more passenger routes are."""

    @staticmethod
    def evaluate_direction_compatibility(
        p1_pickup: tuple[float, float],
        p1_drop: tuple[float, float],
        p2_pickup: tuple[float, float],
        p2_drop: tuple[float, float],
        max_angle_diff_degrees: float = 45.0,
    ) -> tuple[bool, float]:
        """
        Check if two passenger trips have similar compass directions.
        Returns (is_compatible, angle_difference_degrees).
        """
        b1 = calculate_bearing(p1_pickup[0], p1_pickup[1], p1_drop[0], p1_drop[1])
        b2 = calculate_bearing(p2_pickup[0], p2_pickup[1], p2_drop[0], p2_drop[1])

        angle_diff = bearing_difference(b1, b2)
        is_compatible = angle_diff <= max_angle_diff_degrees
        return is_compatible, angle_diff

    @staticmethod
    def calculate_route_overlap(
        p1_pickup: tuple[float, float],
        p1_drop: tuple[float, float],
        p2_pickup: tuple[float, float],
        p2_drop: tuple[float, float],
    ) -> float:
        """
        Calculate route overlap ratio (0.0 to 1.0) between two trips.
        Overlap is high when pickups are close and destinations are close along the route.
        """
        p1_direct = haversine_distance_km(p1_pickup[0], p1_pickup[1], p1_drop[0], p1_drop[1])
        p2_direct = haversine_distance_km(p2_pickup[0], p2_pickup[1], p2_drop[0], p2_drop[1])

        if p1_direct == 0 or p2_direct == 0:
            return 0.0

        pickup_gap = haversine_distance_km(p1_pickup[0], p1_pickup[1], p2_pickup[0], p2_pickup[1])
        drop_gap = haversine_distance_km(p1_drop[0], p1_drop[1], p2_drop[0], p2_drop[1])

        avg_direct = (p1_direct + p2_direct) / 2.0
        gap_sum = pickup_gap + drop_gap

        # Overlap score decreases as pickup and drop gaps increase relative to trip length
        overlap = max(0.0, 1.0 - (gap_sum / (avg_direct * 2.0)))
        return round(overlap, 4)

    @staticmethod
    def optimize_pickup_and_drop_sequence(
        points: list[RoutePoint],
    ) -> tuple[list[RoutePoint], float]:
        """
        Given a list of pickup and drop points for a group of passengers,
        find the optimal sequence that:
          1. Ensures each passenger's pickup occurs BEFORE their drop
          2. Minimizes total route distance
        Returns (ordered_points, total_distance_km).
        """
        passengers = {pt.passenger_id for pt in points}
        pickups = {pt.passenger_id: pt for pt in points if pt.point_type == "pickup"}
        drops = {pt.passenger_id: pt for pt in points if pt.point_type == "drop"}

        best_sequence: list[RoutePoint] = []
        min_total_dist = float("inf")

        # For small group sizes (2-4 passengers = 4-8 points), brute-force permutation search is optimal and exact
        all_permutations = itertools.permutations(points)

        for perm in all_permutations:
            # Check precedence constraint: for every passenger, pickup MUST come before drop
            valid = True
            seen_pickups = set()
            for pt in perm:
                if pt.point_type == "pickup":
                    seen_pickups.add(pt.passenger_id)
                elif pt.point_type == "drop":
                    if pt.passenger_id not in seen_pickups:
                        valid = False
                        break

            if not valid:
                continue

            # Calculate total distance for this sequence
            dist = 0.0
            for i in range(len(perm) - 1):
                dist += haversine_distance_km(
                    perm[i].latitude, perm[i].longitude,
                    perm[i + 1].latitude, perm[i + 1].longitude,
                )

            if dist < min_total_dist:
                min_total_dist = dist
                best_sequence = list(perm)

        return best_sequence, round(min_total_dist, 3)
