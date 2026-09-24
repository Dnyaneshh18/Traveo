from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import (
    MemberRole,
    MemberStatus,
    RideDirection,
    RideRequestStatus,
    RideStatus,
    VehicleType,
)
from app.schemas.common import APIModel, Place

# ── inputs ────────────────────────────────────────────────────────


class RoutePreviewIn(APIModel):
    origin: Place
    destination: Place


class CreateRideRequestIn(APIModel):
    origin: Place
    destination: Place
    vehicle_type: VehicleType
    seats: int = Field(default=1, ge=1, le=5, description="Seats the creator needs (friends travelling together)")
    departure_at: datetime | None = None
    note: str | None = Field(default=None, max_length=200)
    women_only: bool = False

    @field_validator("note")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class JoinRideIn(APIModel):
    pickup: Place
    drop: Place
    seats: int = Field(default=1, ge=1, le=4)


class FeedQuery(APIModel):
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    drop_lat: float | None = None
    drop_lng: float | None = None
    departure_at: datetime | None = None
    vehicle_type: VehicleType | None = None


class CancelIn(APIModel):
    reason: str | None = Field(default=None, max_length=200)


# ── outputs ───────────────────────────────────────────────────────


class FareOption(APIModel):
    vehicle_type: VehicleType
    label: str
    seat_capacity: int
    total_estimate: float
    per_seat_if_full: float
    solo_estimate: float


class RoutePreviewOut(APIModel):
    distance_km: float
    duration_min: float
    polyline: str
    provider: str
    direction: RideDirection
    options: list[FareOption]


class MemberOut(APIModel):
    id: str
    user_id: str
    full_name: str
    avatar_url: str | None = None
    gender: str | None = None
    course: str | None = None
    rating: float
    role: MemberRole
    status: MemberStatus
    seats: int
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    drop_lat: float
    drop_lng: float
    drop_address: str
    pickup_order: int | None = None
    drop_order: int | None = None
    pickup_eta_min: float | None = None
    distance_km: float | None = None
    fare_share_inr: float | None = None
    detour_km: float
    match_score: float
    joined_at: datetime
    picked_up_at: datetime | None = None
    dropped_at: datetime | None = None
    is_me: bool = False


class DriverOut(APIModel):
    user_id: str
    full_name: str
    avatar_url: str | None = None
    phone: str | None = None
    rating: float
    completed_rides: int
    vehicle_type: VehicleType
    vehicle_label: str
    registration_number: str | None = None
    make_model: str | None = None
    color: str | None = None
    eta_min: float | None = None
    position: dict | None = None  # live snapshot {lat,lng,heading,updated_at}


class RideOut(APIModel):
    id: str
    status: RideStatus
    otp_verified_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_fare_inr: float | None = None
    total_distance_km: float | None = None


class DispatchOut(APIModel):
    started_at: datetime | None = None
    radius_km: float | None = None
    attempts: int
    max_radius_km: float


class RideRequestOut(APIModel):
    id: str
    creator_id: str
    college_id: str
    college_name: str
    direction: RideDirection
    vehicle_type: VehicleType
    vehicle_label: str
    seat_capacity: int
    seats_taken: int
    seats_available: int
    status: RideRequestStatus
    origin_lat: float
    origin_lng: float
    origin_address: str
    destination_lat: float
    destination_lng: float
    destination_address: str
    departure_at: datetime
    expires_at: datetime
    note: str | None = None
    women_only: bool
    route_polyline: str | None = None
    route_distance_km: float | None = None
    route_duration_min: float | None = None
    estimated_fare_total: float | None = None
    estimated_fare_solo: float | None = None
    created_at: datetime
    locked_at: datetime | None = None
    members: list[MemberOut]
    driver: DriverOut | None = None
    ride: RideOut | None = None
    dispatch: DispatchOut | None = None
    # viewer-specific
    my_role: MemberRole | None = None
    my_status: MemberStatus | None = None
    my_code: str | None = None  # OTP for creator, matching code for members
    my_code_kind: str | None = None  # "otp" | "matching_code"
    my_fare_share_inr: float | None = None
    my_savings_inr: float | None = None
    match: dict | None = None


class FeedItemOut(APIModel):
    request: RideRequestOut
    match: dict | None = None
