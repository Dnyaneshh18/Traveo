"""
Traveo Backend — Ride Schemas

Pydantic v2 request/response models for all ride-related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator
from app.models.enums import (
    BoardingStatus,
    DropStatus,
    GroupStatus,
    RideRequestStatus,
    RideStatus,
    RideType,
    VehicleCategory,
    VoteChoice,
)


# ── Location ────────────────────────────────────────────────
class LocationInput(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str | None = None


# ── Ride Request ────────────────────────────────────────────
class CreateRideRequest(BaseModel):
    pickup: LocationInput
    destination: LocationInput
    requested_seats: int = Field(default=1, ge=1, le=8)
    vehicle_category: VehicleCategory = VehicleCategory.SEDAN_4_SEATER
    ride_type: RideType = RideType.SHARED

    @model_validator(mode="after")
    def validate_seat_occupancy_capacity(self) -> CreateRideRequest:
        max_seats = 4
        if self.vehicle_category == VehicleCategory.AUTO_RICKSHAW:
            max_seats = 3
        elif self.vehicle_category == VehicleCategory.SEDAN_4_SEATER:
            max_seats = 4
        elif self.vehicle_category == VehicleCategory.SUV_6_8_SEATER:
            max_seats = 8

        if self.requested_seats > max_seats:
            raise ValueError(
                f"{self.vehicle_category.value} supports a maximum of {max_seats} seats. Requested: {self.requested_seats}."
            )
        return self


class CreateRideResponse(BaseModel):
    ride_request_id: str
    status: RideRequestStatus
    estimated_fare: float
    matching_started: bool


class RideRequestDetailResponse(BaseModel):
    id: str
    passenger_id: str
    pickup_latitude: float
    pickup_longitude: float
    pickup_address: str | None
    destination_latitude: float
    destination_longitude: float
    destination_address: str | None
    requested_seats: int
    status: RideRequestStatus
    estimated_fare: float | None
    created_at: datetime


# ── Group ───────────────────────────────────────────────────
class GroupMemberResponse(BaseModel):
    passenger_id: str
    boarding_status: BoardingStatus
    drop_status: DropStatus
    pickup_order: int | None
    drop_order: int | None


class GroupDetailResponse(BaseModel):
    group_id: str
    group_status: GroupStatus
    current_passengers: int
    maximum_capacity: int
    estimated_fare: float | None
    driver_id: str | None
    common_otp: str | None
    members: list[GroupMemberResponse]


# ── Voting ──────────────────────────────────────────────────
class VoteRequest(BaseModel):
    vote: VoteChoice


class VoteResponse(BaseModel):
    group_id: str
    vote: VoteChoice
    total_votes: int
    required_votes: int
    outcome: str  # "pending", "proceed", "wait"


# ── Ride Detail ─────────────────────────────────────────────
class RideDetailResponse(BaseModel):
    ride_id: str
    ride_group_id: str
    driver_id: str
    ride_status: RideStatus
    total_fare: float | None
    ride_started: datetime | None
    ride_completed: datetime | None
    actual_distance: float | None
    actual_duration: float | None
    created_at: datetime
    group: GroupDetailResponse | None = None


class RideHistoryItem(BaseModel):
    ride_id: str
    ride_status: RideStatus
    total_fare: float | None
    ride_started: datetime | None
    ride_completed: datetime | None
    created_at: datetime


class RideHistoryResponse(BaseModel):
    rides: list[RideHistoryItem]
    total: int


# ── Driver Operations ──────────────────────────────────────
class DriverLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    heading: float | None = Field(default=None, ge=0, le=360)
    speed: float | None = Field(default=None, ge=0)


class DriverOnlineResponse(BaseModel):
    status: str  # "online" or "offline"
    message: str


class DriverRideAssignment(BaseModel):
    assignment_id: str
    ride_group_id: str
    group_status: str
    current_passengers: int
    estimated_fare: float | None
    pickup_locations: list[dict[str, Any]]


class AcceptRejectResponse(BaseModel):
    status: str
    ride_id: str | None = None
    otp: str | None = None
    message: str


class VerifyOTPRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=6)


class DriverActiveRideResponse(BaseModel):
    ride_id: str
    ride_group_id: str
    ride_status: RideStatus
    total_fare: float | None
    group: GroupDetailResponse | None = None


class PickupPassengerRequest(BaseModel):
    passenger_id: str


class DropPassengerRequest(BaseModel):
    passenger_id: str
