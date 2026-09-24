"""
Ride Intelligence Engine — Passenger compatibility scoring.

Decides whether (and how well) a student's trip fits an existing ride request
from the same college.  Pure computation – no I/O – so it is trivially
unit-testable and can later be swapped for a learned model.

Compatibility model
-------------------
* **Hard constraints** – same college (enforced upstream), seats available,
  departure inside the time window, detour within limits, women-only filter.
* **Detour** – extra kilometres the group must drive to include the candidate,
  measured against the request's current route geometry (closest point on the
  polyline for pickup *and* drop).  For a `to_college` ride the drop is the
  campus for everyone, so only the pickup detour matters, and vice-versa.
* **Score (0–1)** – weighted blend of detour, time proximity, seat pressure and
  the candidate's rating.  The feed is sorted by this score.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.geo import LatLng, decode_polyline, detour_km, distance_km, point_to_path_km


@dataclass(slots=True)
class CandidateTrip:
    pickup: LatLng
    drop: LatLng
    departure_at: datetime
    seats: int = 1
    rating: float = 5.0


@dataclass(slots=True)
class RequestSnapshot:
    origin: LatLng
    destination: LatLng
    departure_at: datetime
    seats_available: int
    polyline: str | None
    direction: str  # "from_college" | "to_college"
    route_distance_km: float | None = None


@dataclass(slots=True)
class MatchResult:
    compatible: bool
    score: float
    detour_km: float
    pickup_offset_km: float
    drop_offset_km: float
    time_delta_min: float
    reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "compatible": self.compatible,
            "score": round(self.score, 3),
            "detour_km": round(self.detour_km, 2),
            "pickup_offset_km": round(self.pickup_offset_km, 2),
            "drop_offset_km": round(self.drop_offset_km, 2),
            "time_delta_min": round(self.time_delta_min, 1),
            "reason": self.reason,
        }


@dataclass(slots=True)
class MatchingConfig:
    max_detour_km: float = 2.5
    max_detour_ratio: float = 0.35
    time_window_min: float = 25.0
    max_offset_km: float = 2.0  # how far pickup/drop may be from the route corridor
    w_detour: float = 0.45
    w_time: float = 0.25
    w_seats: float = 0.15
    w_rating: float = 0.15


def evaluate_match(candidate: CandidateTrip, request: RequestSnapshot, cfg: MatchingConfig | None = None) -> MatchResult:
    cfg = cfg or MatchingConfig()

    time_delta = abs((candidate.departure_at - request.departure_at).total_seconds()) / 60.0
    if request.seats_available < candidate.seats:
        return MatchResult(False, 0.0, 0.0, 0.0, 0.0, time_delta, "no_seats")
    if time_delta > cfg.time_window_min:
        return MatchResult(False, 0.0, 0.0, 0.0, 0.0, time_delta, "time_window")

    path = decode_polyline(request.polyline) if request.polyline else [request.origin, request.destination]
    pickup_off, pickup_pos = point_to_path_km(candidate.pickup, path)
    drop_off, drop_pos = point_to_path_km(candidate.drop, path)

    route_km = request.route_distance_km or max(0.5, distance_km(request.origin, request.destination))

    # Travelling direction must agree: pickup must come before drop along the route.
    if drop_pos + 0.02 < pickup_pos and pickup_off < cfg.max_offset_km and drop_off < cfg.max_offset_km:
        return MatchResult(False, 0.0, 0.0, pickup_off, drop_off, time_delta, "opposite_direction")

    # Detour = insert the off-route point(s) into the trip.
    detour = 0.0
    if pickup_off > 0.15:
        detour += detour_km(request.origin, request.destination, candidate.pickup) * 0.6 + pickup_off * 0.4
    if drop_off > 0.15:
        detour += detour_km(request.origin, request.destination, candidate.drop) * 0.6 + drop_off * 0.4

    max_detour = min(cfg.max_detour_km, max(0.8, route_km * cfg.max_detour_ratio))
    if pickup_off > cfg.max_offset_km + 1.0 or drop_off > cfg.max_offset_km + 1.0 or detour > max_detour:
        return MatchResult(False, 0.0, detour, pickup_off, drop_off, time_delta, "too_far_from_route")

    detour_score = 1.0 - min(1.0, detour / max_detour)
    time_score = 1.0 - min(1.0, time_delta / cfg.time_window_min)
    seats_score = min(1.0, request.seats_available / 3.0)
    rating_score = max(0.0, min(1.0, (candidate.rating - 3.0) / 2.0))
    score = (
        cfg.w_detour * detour_score
        + cfg.w_time * time_score
        + cfg.w_seats * seats_score
        + cfg.w_rating * rating_score
    )
    return MatchResult(True, round(score, 4), detour, pickup_off, drop_off, time_delta, None)
