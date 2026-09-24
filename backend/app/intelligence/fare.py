"""
Ride Intelligence Engine — Fare engine.

Total fare is computed per vehicle class from the *shared* route distance and
duration, then split between passengers **proportionally to the distance each
one actually travels** (distance-weighted split), with a floor so nobody pays
less than the minimum share.  Students see both their share and what a solo
ride would have cost, so the savings are explicit.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import VehicleType


@dataclass(frozen=True, slots=True)
class Tariff:
    base_fare: float
    per_km: float
    per_min: float
    minimum_fare: float
    min_share: float


TARIFFS: dict[VehicleType, Tariff] = {
    VehicleType.BIKE: Tariff(base_fare=15, per_km=6.0, per_min=0.5, minimum_fare=25, min_share=20),
    VehicleType.AUTO: Tariff(base_fare=25, per_km=11.0, per_min=0.8, minimum_fare=35, min_share=25),
    VehicleType.CAR: Tariff(base_fare=45, per_km=14.0, per_min=1.2, minimum_fare=70, min_share=35),
    VehicleType.CAR_XL: Tariff(base_fare=70, per_km=19.0, per_min=1.5, minimum_fare=110, min_share=45),
}


@dataclass(slots=True)
class FareBreakdown:
    total: float
    solo_estimate: float
    platform_fee: float
    driver_payout: float
    shares: dict[str, float]  # member_id → INR

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "solo_estimate": self.solo_estimate,
            "platform_fee": self.platform_fee,
            "driver_payout": self.driver_payout,
            "shares": self.shares,
        }


def _round_inr(x: float) -> float:
    return float(round(x))


def estimate_total(vehicle: VehicleType, distance_km: float, duration_min: float) -> float:
    t = TARIFFS[vehicle]
    raw = t.base_fare + t.per_km * distance_km + t.per_min * duration_min
    return _round_inr(max(t.minimum_fare, raw))


def solo_estimate(vehicle: VehicleType, distance_km: float, duration_min: float) -> float:
    """What a single rider would pay for the same trip alone (same tariff, no sharing)."""
    return estimate_total(vehicle, distance_km, duration_min)


def split_fare(
    vehicle: VehicleType,
    total: float,
    member_distances_km: dict[str, float],
    platform_fee_percent: float,
) -> FareBreakdown:
    t = TARIFFS[vehicle]
    n = max(1, len(member_distances_km))
    total_distance = sum(max(0.3, d) for d in member_distances_km.values()) or 1.0

    shares: dict[str, float] = {}
    for member_id, d in member_distances_km.items():
        weight = max(0.3, d) / total_distance
        shares[member_id] = max(t.min_share, total * weight)

    # Normalise so the shares add up to the total (rounding to whole rupees).
    scale = total / sum(shares.values()) if shares else 1.0
    rounded = {m: _round_inr(v * scale) for m, v in shares.items()}
    drift = _round_inr(total - sum(rounded.values()))
    if rounded and drift:
        first = next(iter(rounded))
        rounded[first] = _round_inr(rounded[first] + drift)

    platform_fee = _round_inr(total * platform_fee_percent / 100.0)
    return FareBreakdown(
        total=_round_inr(total),
        solo_estimate=0.0,
        platform_fee=platform_fee,
        driver_payout=_round_inr(total - platform_fee),
        shares=rounded if n else {},
    )
