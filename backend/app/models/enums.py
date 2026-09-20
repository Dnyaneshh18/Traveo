"""
Traveo Backend — Enum Types

All status and type enumerations used across database models.
Defined separately to avoid circular imports and enable reuse in schemas.
"""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    PASSENGER = "passenger"
    DRIVER = "driver"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SUPPORT = "support"
    FINANCE = "finance"
    OPERATIONS = "operations"


class RideType(str, enum.Enum):
    SHARED = "shared"
    SOLO = "solo"          # Future
    RENTAL = "rental"      # Future
    AIRPORT = "airport"    # Future
    INTERCITY = "intercity" # Future


class VehicleCategory(str, enum.Enum):
    AUTO_RICKSHAW = "auto_rickshaw"    # Capacity: 3 seats max
    SEDAN_4_SEATER = "sedan_4_seater"   # Capacity: 4 seats max
    SUV_6_8_SEATER = "suv_6_8_seater"   # Capacity: 6-8 seats max


class RideRequestStatus(str, enum.Enum):
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GroupStatus(str, enum.Enum):
    FORMING = "forming"
    WAITING_FOR_VOTE = "waiting_for_vote"
    VOTING = "voting"
    FINALIZED = "finalized"
    SEARCHING_DRIVER = "searching_driver"
    DRIVER_ASSIGNED = "driver_assigned"
    LOCKED = "locked"
    CANCELLED = "cancelled"


class BoardingStatus(str, enum.Enum):
    WAITING = "waiting"
    BOARDED = "boarded"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class DropStatus(str, enum.Enum):
    PENDING = "pending"
    DROPPED = "dropped"
    CANCELLED = "cancelled"


class VoteChoice(str, enum.Enum):
    CONTINUE = "continue"
    WAIT = "wait"
    CANCEL = "cancel"


class DriverAssignmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class RideStatus(str, enum.Enum):
    """Complete ride state machine from Part 5."""
    REQUEST_CREATED = "request_created"
    SEARCHING_PASSENGERS = "searching_passengers"
    GROUP_FORMING = "group_forming"
    WAITING_FOR_VOTE = "waiting_for_vote"
    SEARCHING_DRIVER = "searching_driver"
    DRIVER_ASSIGNED = "driver_assigned"
    OTP_GENERATED = "otp_generated"
    DRIVER_EN_ROUTE = "driver_en_route"
    PICKUP_IN_PROGRESS = "pickup_in_progress"
    ALL_PASSENGERS_BOARDED = "all_passengers_boarded"
    RIDE_STARTED = "ride_started"
    DROP_IN_PROGRESS = "drop_in_progress"
    RIDE_COMPLETED = "ride_completed"
    PAYMENT_COMPLETED = "payment_completed"
    RATING_PENDING = "rating_pending"
    RATING_COMPLETED = "rating_completed"
    # Error states
    PASSENGER_CANCELLED = "passenger_cancelled"
    DRIVER_CANCELLED = "driver_cancelled"
    GROUP_CANCELLED = "group_cancelled"
    MATCHING_FAILED = "matching_failed"
    NO_DRIVER_FOUND = "no_driver_found"
    PAYMENT_FAILED = "payment_failed"
    REFUND_INITIATED = "refund_initiated"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VehicleStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class OnlineStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    CARD = "card"
    WALLET = "wallet"
    CASH = "cash"
    NET_BANKING = "net_banking"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PayoutStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WalletTransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    REFUND = "refund"
    PROMOTION = "promotion"
    RIDE_PAYMENT = "ride_payment"
    PAYOUT = "payout"
    ADJUSTMENT = "adjustment"


class NotificationType(str, enum.Enum):
    RIDE = "ride"
    PAYMENT = "payment"
    PROMOTION = "promotion"
    SUPPORT = "support"
    SYSTEM = "system"
    SECURITY = "security"
    WALLET = "wallet"


class MessageType(str, enum.Enum):
    TEXT = "text"
    EMOJI = "emoji"
    SYSTEM = "system"
    IMAGE = "image"       # Future
    LOCATION = "location" # Future


class SupportTicketStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
