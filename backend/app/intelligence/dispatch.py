"""
Ride Intelligence Engine — Driver ranking & radius expansion policy.

Mirrors the Uber/Ola dispatch model: search the closest ring first, offer the
ride to the best driver, and expand the ring only when nobody in it accepts.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.geo import LatLng, distance_km
from app.models.enums import VEHICLE_CAPACITY, VehicleType

AVERAGE_APPROACH_SPEED_KMPH = 20.0


@dataclass(slots=True)
class DriverCandidate:
    user_id: str
    position: LatLng
    vehicle_type: VehicleType
    seat_capacity: int
    rating: float
    acceptance_rate: float
    completed_rides: int
    already_offered: bool = False


@dataclass(slots=True)
class RankedDriver:
    candidate: DriverCandidate
    distance_km: float
    eta_min: float
    score: float


def vehicle_compatible(requested: VehicleType, offered: VehicleType, required_seats: int) -> bool:
    """A driver may serve a request if the vehicle class is the same or bigger and has room."""
    order = [VehicleType.BIKE, VehicleType.AUTO, VehicleType.CAR, VehicleType.CAR_XL]
    if requested == VehicleType.BIKE:
        return offered == VehicleType.BIKE and required_seats <= 1
    if offered == VehicleType.BIKE:
        return False
    if order.index(offered) < order.index(requested):
        return False
    return VEHICLE_CAPACITY[offered] >= required_seats


def rank_drivers(
    pickup: LatLng,
    candidates: list[DriverCandidate],
    requested_vehicle: VehicleType,
    required_seats: int,
    radius_km: float,
) -> list[RankedDriver]:
    ranked: list[RankedDriver] = []
    for c in candidates:
        if c.already_offered:
            continue
        if not vehicle_compatible(requested_vehicle, c.vehicle_type, required_seats):
            continue
        d = distance_km(pickup, c.position) * 1.25  # road factor
        if d > radius_km * 1.25:
            continue
        eta = max(1.0, d / AVERAGE_APPROACH_SPEED_KMPH * 60)
        proximity = 1.0 - min(1.0, d / max(radius_km * 1.25, 0.1))
        rating = max(0.0, min(1.0, (c.rating - 3.0) / 2.0))
        experience = min(1.0, c.completed_rides / 50.0)
        exact_vehicle = 1.0 if c.vehicle_type == requested_vehicle else 0.6
        score = (
            0.50 * proximity
            + 0.20 * rating
            + 0.15 * c.acceptance_rate
            + 0.05 * experience
            + 0.10 * exact_vehicle
        )
        ranked.append(RankedDriver(c, round(d, 2), round(eta, 1), round(score, 4)))
    ranked.sort(key=lambda r: (-r.score, r.distance_km))
    return ranked
