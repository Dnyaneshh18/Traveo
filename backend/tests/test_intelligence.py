"""
Traveo Backend — Ride Intelligence Engine Tests

Validates Haversine math, route overlap evaluation, passenger matching scoring formula,
and driver ranking algorithm.
"""

import pytest

from app.intelligence.driver import DriverCandidate, DriverSelectionEngine
from app.intelligence.geo import (
    bearing_difference,
    calculate_bearing,
    calculate_bounding_box,
    haversine_distance_km,
)
from app.intelligence.matching import CandidateRideRequest, PassengerMatchingEngine
from app.intelligence.route import RouteCompatibilityEvaluator, RoutePoint


def test_haversine_distance():
    # Distance between Connaught Place, Delhi and Cyber City, Gurgaon (~24 km)
    delhi_cp = (28.6315, 77.2167)
    gurgaon_cyber = (28.4950, 77.0895)

    dist = haversine_distance_km(delhi_cp[0], delhi_cp[1], gurgaon_cyber[0], gurgaon_cyber[1])
    assert 15.0 < dist < 25.0


def test_calculate_bounding_box():
    lat, lon = 28.6315, 77.2167
    min_lat, max_lat, min_lon, max_lon = calculate_bounding_box(lat, lon, radius_km=5.0)

    assert min_lat < lat < max_lat
    assert min_lon < lon < max_lon


def test_bearing_and_difference():
    # Heading North (0 deg) vs Heading East (90 deg) -> diff = 90 deg
    b1 = calculate_bearing(28.0, 77.0, 29.0, 77.0)  # North
    b2 = calculate_bearing(28.0, 77.0, 28.0, 78.0)  # East

    diff = bearing_difference(b1, b2)
    assert abs(diff - 90.0) < 5.0


def test_passenger_matching_engine_compatible():
    engine = PassengerMatchingEngine()

    # Two passengers heading in similar direction (Delhi to Gurgaon)
    p1 = CandidateRideRequest(
        id="req-1",
        passenger_id="pass-1",
        pickup_latitude=28.6315,
        pickup_longitude=77.2167,
        destination_latitude=28.4950,
        destination_longitude=77.0895,
        requested_seats=1,
    )

    p2 = CandidateRideRequest(
        id="req-2",
        passenger_id="pass-2",
        pickup_latitude=28.6350,
        pickup_longitude=77.2200,
        destination_latitude=28.4980,
        destination_longitude=77.0920,
        requested_seats=1,
    )

    result = engine.evaluate_match(p1, p2)
    assert result.is_compatible is True
    assert result.score > 0.5
    assert result.rejection_reason is None


def test_passenger_matching_engine_capacity_exceeded():
    engine = PassengerMatchingEngine(max_capacity=4)

    p1 = CandidateRideRequest(
        id="req-1", passenger_id="pass-1",
        pickup_latitude=28.6315, pickup_longitude=77.2167,
        destination_latitude=28.4950, destination_longitude=77.0895,
        requested_seats=3,
    )

    p2 = CandidateRideRequest(
        id="req-2", passenger_id="pass-2",
        pickup_latitude=28.6315, pickup_longitude=77.2167,
        destination_latitude=28.4950, destination_longitude=77.0895,
        requested_seats=2,
    )

    result = engine.evaluate_match(p1, p2)
    assert result.is_compatible is False
    assert result.rejection_reason == "Capacity exceeded"


def test_driver_selection_engine():
    engine = DriverSelectionEngine()

    driver1 = DriverCandidate(
        driver_id="d1",
        user_id="u1",
        latitude=28.6300,
        longitude=77.2150,
        rating=4.8,
        completed_rides=150,
        cancelled_rides=2,
        seat_capacity=4,
        is_online=True,
        is_verified=True,
    )

    driver2 = DriverCandidate(
        driver_id="d2",
        user_id="u2",
        latitude=28.6900,  # Far away
        longitude=77.3000,
        rating=4.0,
        completed_rides=20,
        cancelled_rides=5,
        seat_capacity=4,
        is_online=True,
        is_verified=True,
    )

    ranked = engine.rank_drivers(
        drivers=[driver1, driver2],
        first_pickup_lat=28.6315,
        first_pickup_lon=77.2167,
        required_seats=2,
    )

    assert len(ranked) > 0
    assert ranked[0].driver_id == "d1"
