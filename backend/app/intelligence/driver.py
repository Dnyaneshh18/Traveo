"""
Traveo Ride Intelligence Engine — Driver Selection & Ranking Engine

Implements candidate driver filtering and weighted scoring formula from Part 13.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.intelligence.geo import estimate_travel_time_minutes, haversine_distance_km


@dataclass
class DriverCandidate:
    driver_id: str
    user_id: str
    latitude: float
    longitude: float
    rating: float  # 0.0 to 5.0
    completed_rides: int
    cancelled_rides: int
    seat_capacity: int
    is_online: bool
    is_verified: bool


@dataclass
class DriverRankResult:
    driver_id: str
    user_id: str
    score: float
    eta_minutes: float
    distance_km: float
    rating: float
    reliability_score: float


class DriverSelectionEngine:
    """Ranks and selects the best driver for an optimized ride group."""

    def __init__(
        self,
        weight_eta: float = 0.35,
        weight_rating: float = 0.25,
        weight_reliability: float = 0.20,
        weight_route_efficiency: float = 0.20,
        max_driver_eta_minutes: float = 15.0,
        min_driver_rating: float = 3.5,
    ) -> None:
        self.w_eta = weight_eta
        self.w_rating = weight_rating
        self.w_reliability = weight_reliability
        self.w_efficiency = weight_route_efficiency
        self.max_eta = max_driver_eta_minutes
        self.min_rating = min_driver_rating

    def evaluate_driver(
        self,
        driver: DriverCandidate,
        first_pickup_lat: float,
        first_pickup_lon: float,
        required_seats: int,
    ) -> DriverRankResult | None:
        """
        Evaluate a single driver candidate against group requirements.
        Returns DriverRankResult or None if hard constraints fail.
        """
        # Hard Constraints
        if not driver.is_online or not driver.is_verified:
            return None
        if driver.seat_capacity < required_seats:
            return None
        if driver.completed_rides > 0 and driver.rating < self.min_rating:
            return None

        # Distance & ETA to first pickup
        dist_km = haversine_distance_km(
            driver.latitude, driver.longitude,
            first_pickup_lat, first_pickup_lon,
        )
        eta_minutes = estimate_travel_time_minutes(dist_km)

        if eta_minutes > self.max_eta:
            return None

        # Normalized Score Components (0.0 - 1.0)
        eta_score = max(0.0, 1.0 - (eta_minutes / self.max_eta))
        rating_score = max(0.0, (driver.rating - 1.0) / 4.0)

        # Reliability score = completed / (completed + cancelled)
        total_trips = driver.completed_rides + driver.cancelled_rides
        if total_trips > 0:
            reliability_score = driver.completed_rides / total_trips
        else:
            reliability_score = 0.8  # Default neutral for new drivers

        route_efficiency = max(0.0, 1.0 - (dist_km / 10.0))

        # Weighted Driver Ranking Formula from Part 13
        score = (
            (eta_score * self.w_eta)
            + (rating_score * self.w_rating)
            + (reliability_score * self.w_reliability)
            + (route_efficiency * self.w_efficiency)
        )

        return DriverRankResult(
            driver_id=driver.driver_id,
            user_id=driver.user_id,
            score=round(score, 4),
            eta_minutes=round(eta_minutes, 1),
            distance_km=round(dist_km, 2),
            rating=driver.rating,
            reliability_score=round(reliability_score, 2),
        )

    def rank_drivers(
        self,
        drivers: list[DriverCandidate],
        first_pickup_lat: float,
        first_pickup_lon: float,
        required_seats: int,
    ) -> list[DriverRankResult]:
        """Rank all candidate drivers in descending order of suitability."""
        results: list[DriverRankResult] = []

        for driver in drivers:
            rank = self.evaluate_driver(
                driver, first_pickup_lat, first_pickup_lon, required_seats
            )
            if rank is not None:
                results.append(rank)

        results.sort(key=lambda d: d.score, reverse=True)
        return results
