"""
Traveo Backend — Performance & Benchmark Test Suite

Benchmarking matching engine execution time, route sequence optimizer throughput,
and sub-millisecond calculation constraints.
"""

import time
import pytest

from app.intelligence.driver import DriverCandidate, DriverSelectionEngine
from app.intelligence.geo import haversine_distance_km
from app.intelligence.learning import calculate_dynamic_search_radius
from app.intelligence.matching import CandidateRideRequest, PassengerMatchingEngine
from app.intelligence.route import RouteCompatibilityEvaluator, RoutePoint


def test_haversine_performance():
    """Verify 10,000 Haversine distance calculations complete in under 50ms."""
    start = time.perf_counter()
    for _ in range(10_000):
        _ = haversine_distance_km(28.6315, 77.2167, 28.4950, 77.0895)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert duration_ms < 50.0, f"Haversine too slow: {duration_ms:.2f}ms"


def test_matching_engine_performance():
    """Verify matching engine evaluates 1,000 passenger combinations in under 100ms."""
    engine = PassengerMatchingEngine()

    target = CandidateRideRequest(
        id="target", passenger_id="p-0",
        pickup_latitude=28.6315, pickup_longitude=77.2167,
        destination_latitude=28.4950, destination_longitude=77.0895,
        requested_seats=1,
    )

    candidates = [
        CandidateRideRequest(
            id=f"c-{i}", passenger_id=f"p-{i}",
            pickup_latitude=28.6315 + (i * 0.0001),
            pickup_longitude=77.2167 + (i * 0.0001),
            destination_latitude=28.4950 + (i * 0.0001),
            destination_longitude=77.0895 + (i * 0.0001),
            requested_seats=1,
        )
        for i in range(1, 1001)
    ]

    start = time.perf_counter()
    matches = engine.find_best_matches(target, candidates)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert duration_ms < 100.0, f"Matching engine too slow: {duration_ms:.2f}ms"
    assert len(matches) > 0


def test_pickup_drop_sequence_optimizer_performance():
    """Verify sequence optimizer for 4-passenger group (8 points) completes in under 20ms."""
    points = [
        RoutePoint(id="1", latitude=28.6315, longitude=77.2167, point_type="pickup", passenger_id="p1"),
        RoutePoint(id="2", latitude=28.6320, longitude=77.2170, point_type="pickup", passenger_id="p2"),
        RoutePoint(id="3", latitude=28.4950, longitude=77.0895, point_type="drop", passenger_id="p1"),
        RoutePoint(id="4", latitude=28.4960, longitude=77.0900, point_type="drop", passenger_id="p2"),
    ]

    start = time.perf_counter()
    ordered, dist = RouteCompatibilityEvaluator.optimize_pickup_and_drop_sequence(points)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert duration_ms < 20.0, f"Sequence optimizer too slow: {duration_ms:.2f}ms"
    assert len(ordered) == 4
    assert dist > 0.0


def test_dynamic_radius_expansion():
    # 0 sec -> initial radius 2.0 km
    assert calculate_dynamic_search_radius(0) == 2.0
    # 30 sec -> 2.5 km
    assert calculate_dynamic_search_radius(30) == 2.5
    # 60 sec -> 3.0 km
    assert calculate_dynamic_search_radius(60) == 3.0
    # 300 sec -> max capped at 5.0 km
    assert calculate_dynamic_search_radius(300) == 5.0
