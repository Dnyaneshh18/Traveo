"""
Traveo Backend — Fare & Payment Tests

Validates FareEngine calculation (base fare, distance, duration, taxes, shared discount)
and SharedFareSplitter proportional allocation logic.
"""

import pytest

from app.payments.fare import FareEngine, SharedFareSplitter


def test_fare_engine_calculation():
    engine = FareEngine(
        base_fare=30.0,
        per_km_rate=12.0,
        per_minute_rate=2.0,
        platform_fee_percent=10.0,
        tax_percent=5.0,
        shared_ride_discount_percent=15.0,
    )

    # 10 km, 20 minutes trip
    breakdown = engine.calculate_total_fare(distance_km=10.0, duration_minutes=20.0, is_shared=True)

    assert breakdown.base_fare == 30.0
    assert breakdown.distance_fare == 120.0
    assert breakdown.duration_fare == 40.0
    assert breakdown.discount_amount > 0.0
    assert breakdown.total_fare > 0.0


def test_shared_fare_splitter_proportional():
    # 2 passengers: Pass A traveled 10 km, Pass B traveled 5 km. Group total = $300.
    passenger_distances = {
        "pass_a": 10.0,
        "pass_b": 5.0,
    }
    group_total = 300.0

    splits = SharedFareSplitter.split_group_fare(passenger_distances, group_total)

    assert len(splits) == 2

    fare_a = next(s.final_fare for s in splits if s.passenger_id == "pass_a")
    fare_b = next(s.final_fare for s in splits if s.passenger_id == "pass_b")

    # Pass A traveled 2x distance of Pass B, so Pass A fare should be ~2x Pass B fare
    assert fare_a == pytest.approx(200.0, abs=1.0)
    assert fare_b == pytest.approx(100.0, abs=1.0)

    # Sum of splits MUST equal total group fare
    assert fare_a + fare_b == group_total
