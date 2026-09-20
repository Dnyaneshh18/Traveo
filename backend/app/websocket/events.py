"""
Traveo Backend — WebSocket Event Definitions

Server-to-client real-time events for Passenger App, Driver App, and Admin Panel.
Matches exact specification from Part 11.
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, Field


class WSEventType(str, enum.Enum):
    # ── Passenger Events ──
    MATCHING_STARTED = "MatchingStarted"
    PASSENGER_JOINED = "PassengerJoined"
    PASSENGER_LEFT = "PassengerLeft"
    VOTE_STARTED = "VoteStarted"
    VOTE_RESULT = "VoteResult"
    DRIVER_SEARCHING = "DriverSearching"
    DRIVER_ASSIGNED = "DriverAssigned"
    OTP_GENERATED = "OTPGenerated"
    DRIVER_LOCATION_UPDATED = "DriverLocationUpdated"
    PICKUP_STARTED = "PickupStarted"
    PASSENGER_BOARDED = "PassengerBoarded"
    RIDE_STARTED = "RideStarted"
    PASSENGER_DROPPED = "PassengerDropped"
    RIDE_COMPLETED = "RideCompleted"
    PAYMENT_COMPLETED = "PaymentCompleted"
    RIDE_CANCELLED = "RideCancelled"

    # ── Driver Events ──
    RIDE_ASSIGNED = "RideAssigned"
    PASSENGER_CANCELLED = "PassengerCancelled"
    PASSENGER_NO_SHOW = "PassengerNoShow"
    ROUTE_UPDATED = "RouteUpdated"
    OTP_VERIFIED = "OTPVerified"

    # ── Admin Events ──
    RIDE_CREATED = "RideCreated"
    DRIVER_ONLINE = "DriverOnline"
    DRIVER_OFFLINE = "DriverOffline"
    SOS_ACTIVATED = "SOSActivated"
    SYSTEM_ALERT = "SystemAlert"


class WSEventMessage(BaseModel):
    """Envelope for all WebSocket messages broadcast to clients."""

    event: WSEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
    )
