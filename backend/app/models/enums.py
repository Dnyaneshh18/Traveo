"""Traveo — Domain enumerations (single source of truth, mirrored in packages/shared)."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    DRIVER = "driver"
    ADMIN = "admin"


class InstitutionType(StrEnum):
    COLLEGE = "college"
    SCHOOL = "school"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VehicleType(StrEnum):
    """Seat capacity is the number of *passenger* seats."""

    BIKE = "bike"
    AUTO = "auto"
    CAR = "car"
    CAR_XL = "car_xl"


VEHICLE_CAPACITY: dict[VehicleType, int] = {
    VehicleType.BIKE: 1,
    VehicleType.AUTO: 3,
    VehicleType.CAR: 4,
    VehicleType.CAR_XL: 6,
}

VEHICLE_LABEL: dict[VehicleType, str] = {
    VehicleType.BIKE: "Bike",
    VehicleType.AUTO: "Auto Rickshaw",
    VehicleType.CAR: "Car",
    VehicleType.CAR_XL: "Car XL",
}


class RideDirection(StrEnum):
    FROM_COLLEGE = "from_college"
    TO_COLLEGE = "to_college"


class RideRequestStatus(StrEnum):
    OPEN = "open"  # visible in the college feed, accepting co-riders
    LOCKED = "locked"  # creator pressed "Find driver" (or seats full) – dispatching
    DRIVER_ASSIGNED = "driver_assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_DRIVER = "no_driver"  # dispatch exhausted – creator may retry
    CANCELLED = "cancelled"
    EXPIRED = "expired"


ACTIVE_REQUEST_STATUSES = (
    RideRequestStatus.OPEN,
    RideRequestStatus.LOCKED,
    RideRequestStatus.DRIVER_ASSIGNED,
    RideRequestStatus.IN_PROGRESS,
    RideRequestStatus.NO_DRIVER,
)


class MemberRole(StrEnum):
    CREATOR = "creator"
    MEMBER = "member"


class MemberStatus(StrEnum):
    ACCEPTED = "accepted"
    LEFT = "left"
    REMOVED = "removed"
    PICKED_UP = "picked_up"
    DROPPED = "dropped"
    NO_SHOW = "no_show"


ACTIVE_MEMBER_STATUSES = (MemberStatus.ACCEPTED, MemberStatus.PICKED_UP)


class DriverStatus(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    ON_TRIP = "on_trip"


class OfferStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RideStatus(StrEnum):
    DRIVER_ASSIGNED = "driver_assigned"  # driver heading to first pickup
    IN_PROGRESS = "in_progress"  # at least one rider on board
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(StrEnum):
    CASH = "cash"
    UPI = "upi"
    WALLET = "wallet"


class NotificationType(StrEnum):
    GROUP = "group"
    RIDE = "ride"
    DRIVER = "driver"
    SYSTEM = "system"
