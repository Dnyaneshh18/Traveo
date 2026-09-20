"""
Traveo Backend — SQLAlchemy ORM Models

Complete database schema per Parts 3 & 12 of the specification.
Every table uses UUID PK, created_at, updated_at.
Models contain NO business logic, NO validation, NO queries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import (
    BoardingStatus,
    DriverAssignmentStatus,
    DropStatus,
    Gender,
    GroupStatus,
    MessageType,
    NotificationType,
    OnlineStatus,
    PaymentMethod,
    PaymentStatus,
    PayoutStatus,
    RefundStatus,
    RideRequestStatus,
    RideStatus,
    RideType,
    SupportTicketStatus,
    UserRole,
    VehicleStatus,
    VerificationStatus,
    VoteChoice,
    WalletTransactionType,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


# =====================================================================
# IDENTITY DOMAIN
# =====================================================================

class User(Base):
    """Master user table — one row per authenticated person."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    profile_completed = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationships
    passenger_profile = relationship("PassengerProfile", back_populates="user", uselist=False)
    driver_profile = relationship("DriverProfile", back_populates="user", uselist=False)
    admin_profile = relationship("AdminProfile", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    saved_places = relationship("SavedPlace", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


# =====================================================================
# PASSENGER DOMAIN
# =====================================================================

class PassengerProfile(Base):
    __tablename__ = "passenger_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    gender = Column(Enum(Gender, name="gender_type"), nullable=True)
    age = Column(Integer, nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    profile_photo = Column(String(500), nullable=True)
    home_location = Column(Text, nullable=True)  # JSON: {lat, lng, address}
    work_location = Column(Text, nullable=True)   # JSON: {lat, lng, address}
    preferred_language = Column(String(10), default="en", nullable=False)
    average_rating = Column(Float, default=0.0, nullable=False)
    completed_rides = Column(Integer, default=0, nullable=False)
    cancelled_rides = Column(Integer, default=0, nullable=False)
    emergency_contact = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    user = relationship("User", back_populates="passenger_profile")

    __table_args__ = (
        CheckConstraint("average_rating >= 0 AND average_rating <= 5", name="chk_passenger_rating"),
        CheckConstraint("completed_rides >= 0", name="chk_passenger_completed"),
        CheckConstraint("cancelled_rides >= 0", name="chk_passenger_cancelled"),
    )


class SavedPlace(Base):
    __tablename__ = "saved_places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="saved_places")


class PassengerLocation(Base):
    __tablename__ = "passenger_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# =====================================================================
# DRIVER DOMAIN
# =====================================================================

class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    license_number = Column(String(50), unique=True, nullable=True)
    license_expiry = Column(DateTime(timezone=True), nullable=True)
    aadhaar_number = Column(String(50), nullable=True)  # Encrypted at rest
    pan_number = Column(String(20), nullable=True)       # Encrypted at rest
    profile_photo = Column(String(500), nullable=True)
    driver_rating = Column(Float, default=0.0, nullable=False)
    completed_rides = Column(Integer, default=0, nullable=False)
    cancelled_rides = Column(Integer, default=0, nullable=False)
    verification_status = Column(
        Enum(VerificationStatus, name="verification_status_type"),
        default=VerificationStatus.PENDING, nullable=False, index=True,
    )
    online_status = Column(
        Enum(OnlineStatus, name="online_status_type"),
        default=OnlineStatus.OFFLINE, nullable=False, index=True,
    )
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    preferred_language = Column(String(10), default="en", nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    user = relationship("User", back_populates="driver_profile")
    vehicles = relationship("Vehicle", back_populates="driver")

    __table_args__ = (
        CheckConstraint("driver_rating >= 0 AND driver_rating <= 5", name="chk_driver_rating"),
    )


class DriverLocation(Base):
    """Real-time driver location — latest only, historical moves to analytics."""

    __tablename__ = "driver_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# =====================================================================
# VEHICLE DOMAIN
# =====================================================================

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("driver_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False)
    vehicle_brand = Column(String(100), nullable=True)
    vehicle_model = Column(String(100), nullable=True)
    vehicle_color = Column(String(50), nullable=True)
    registration_number = Column(String(30), unique=True, nullable=False)
    seat_capacity = Column(Integer, nullable=False)
    insurance_number = Column(String(100), nullable=True)
    insurance_expiry = Column(DateTime(timezone=True), nullable=True)
    pollution_certificate = Column(String(500), nullable=True)
    registration_document = Column(String(500), nullable=True)
    vehicle_photo = Column(String(500), nullable=True)
    status = Column(Enum(VehicleStatus, name="vehicle_status_type"), default=VehicleStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    driver = relationship("DriverProfile", back_populates="vehicles")

    __table_args__ = (
        CheckConstraint("seat_capacity > 0", name="chk_seat_capacity"),
    )


# =====================================================================
# RIDE DOMAIN
# =====================================================================

class RideRequest(Base):
    __tablename__ = "ride_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    pickup_address = Column(Text, nullable=True)
    destination_latitude = Column(Float, nullable=False)
    destination_longitude = Column(Float, nullable=False)
    destination_address = Column(Text, nullable=True)
    requested_seats = Column(Integer, default=1, nullable=False)
    ride_type = Column(Enum(RideType, name="ride_type_enum"), default=RideType.SHARED, nullable=False)
    status = Column(Enum(RideRequestStatus, name="ride_request_status_type"), default=RideRequestStatus.PENDING, nullable=False, index=True)
    estimated_fare = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("requested_seats > 0 AND requested_seats <= 6", name="chk_requested_seats"),
        Index("idx_ride_requests_status_created", "status", "created_at"),
    )


class MatchingSession(Base):
    __tablename__ = "matching_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_request_id = Column(UUID(as_uuid=True), ForeignKey("ride_requests.id"), nullable=False, index=True)
    matching_radius = Column(Float, nullable=False)
    matching_status = Column(String(30), default="active", nullable=False)
    timer_started = Column(DateTime(timezone=True), nullable=True)
    timer_expired = Column(DateTime(timezone=True), nullable=True)
    matched_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class RideGroup(Base):
    """Core ride group — the heart of Traveo's passenger-first model."""

    __tablename__ = "ride_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_status = Column(Enum(GroupStatus, name="group_status_type"), default=GroupStatus.FORMING, nullable=False, index=True)
    maximum_capacity = Column(Integer, default=4, nullable=False)
    current_passengers = Column(Integer, default=0, nullable=False)
    estimated_fare = Column(Float, nullable=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    common_otp = Column(String(10), nullable=True)
    search_radius = Column(Float, nullable=True)
    matching_completed = Column(Boolean, default=False, nullable=False)
    group_locked = Column(Boolean, default=False, nullable=False)
    pickup_sequence_generated = Column(Boolean, default=False, nullable=False)
    drop_sequence_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    members = relationship("RideGroupMember", back_populates="group")
    votes = relationship("GroupVote", back_populates="group")


class RideGroupMember(Base):
    __tablename__ = "ride_group_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("ride_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    ride_request_id = Column(UUID(as_uuid=True), ForeignKey("ride_requests.id"), nullable=True)
    pickup_order = Column(Integer, nullable=True)
    drop_order = Column(Integer, nullable=True)
    boarding_status = Column(Enum(BoardingStatus, name="boarding_status_type"), default=BoardingStatus.WAITING, nullable=False)
    drop_status = Column(Enum(DropStatus, name="drop_status_type"), default=DropStatus.PENDING, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    group = relationship("RideGroup", back_populates="members")

    __table_args__ = (
        UniqueConstraint("group_id", "passenger_id", name="uq_group_passenger"),
    )


class GroupVote(Base):
    __tablename__ = "group_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("ride_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vote = Column(Enum(VoteChoice, name="vote_choice_type"), nullable=False)
    voted_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    group = relationship("RideGroup", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("group_id", "passenger_id", name="uq_group_vote"),
    )


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_group_id = Column(UUID(as_uuid=True), ForeignKey("ride_groups.id"), nullable=False, index=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(DriverAssignmentStatus, name="driver_assignment_status_type"), default=DriverAssignmentStatus.PENDING, nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)


class Ride(Base):
    """Main ride record — created after driver accepts and OTP is generated."""

    __tablename__ = "rides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_group_id = Column(UUID(as_uuid=True), ForeignKey("ride_groups.id"), nullable=False, index=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    ride_status = Column(Enum(RideStatus, name="ride_status_type"), default=RideStatus.DRIVER_ASSIGNED, nullable=False, index=True)
    ride_started = Column(DateTime(timezone=True), nullable=True)
    ride_completed = Column(DateTime(timezone=True), nullable=True)
    actual_distance = Column(Float, nullable=True)
    actual_duration = Column(Float, nullable=True)  # minutes
    total_fare = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_rides_driver_status", "driver_id", "ride_status"),
    )


class RideOTP(Base):
    __tablename__ = "ride_otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_group_id = Column(UUID(as_uuid=True), ForeignKey("ride_groups.id"), nullable=False, index=True)
    otp = Column(String(10), nullable=False)  # Hashed in production
    generated_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified = Column(Boolean, default=False, nullable=False)


class PickupEvent(Base):
    __tablename__ = "pickup_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pickup_time = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    no_show = Column(Boolean, default=False, nullable=False)


class DropEvent(Base):
    __tablename__ = "drop_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    drop_time = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)


# =====================================================================
# PAYMENT DOMAIN
# =====================================================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False, index=True)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    method = Column(Enum(PaymentMethod, name="payment_method_type"), nullable=True)
    status = Column(Enum(PaymentStatus, name="payment_status_type"), default=PaymentStatus.PENDING, nullable=False, index=True)
    transaction_reference = Column(String(255), unique=True, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=True)
    payment_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount"),
    )


class DriverPayout(Base):
    __tablename__ = "driver_payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False)
    gross_amount = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    status = Column(Enum(PayoutStatus, name="payout_status_type"), default=PayoutStatus.PENDING, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(RefundStatus, name="refund_status_type"), default=RefundStatus.PENDING, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# =====================================================================
# WALLET DOMAIN
# =====================================================================

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="chk_wallet_balance"),
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(WalletTransactionType, name="wallet_tx_type"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    wallet = relationship("Wallet", back_populates="transactions")


# =====================================================================
# RATINGS
# =====================================================================

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False, index=True)
    rater_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rated_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_rating_range"),
        UniqueConstraint("ride_id", "rater_id", "rated_id", name="uq_ride_rating"),
    )


# =====================================================================
# NOTIFICATIONS
# =====================================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType, name="notification_type_enum"), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read"),
    )


# =====================================================================
# CHAT
# =====================================================================

class RideMessage(Base):
    __tablename__ = "ride_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_group_id = Column(UUID(as_uuid=True), ForeignKey("ride_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType, name="message_type_enum"), default=MessageType.TEXT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# =====================================================================
# SUPPORT
# =====================================================================

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(SupportTicketStatus, name="support_status_type"), default=SupportTicketStatus.OPEN, nullable=False, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


# =====================================================================
# ADMIN
# =====================================================================

class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department = Column(String(100), nullable=True)
    permissions = Column(Text, nullable=True)  # JSON list of permissions
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="admin_profile")


class SystemConfiguration(Base):
    """Admin-editable key-value configuration store."""

    __tablename__ = "system_configuration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


# =====================================================================
# AUDIT & ERROR LOGS
# =====================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=True)
    entity_id = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    device = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user_created", "user_id", "created_at"),
    )


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String(100), nullable=False)
    error_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# =====================================================================
# ANALYTICS
# =====================================================================

class RideStatistic(Base):
    __tablename__ = "ride_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False, index=True)
    matching_duration_seconds = Column(Float, nullable=True)
    driver_assignment_seconds = Column(Float, nullable=True)
    total_pickup_seconds = Column(Float, nullable=True)
    total_ride_seconds = Column(Float, nullable=True)
    occupancy = Column(Integer, nullable=True)
    route_efficiency = Column(Float, nullable=True)  # 0-1
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class DailyStatistic(Base):
    __tablename__ = "daily_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    total_rides = Column(Integer, default=0, nullable=False)
    completed_rides = Column(Integer, default=0, nullable=False)
    cancelled_rides = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Float, default=0.0, nullable=False)
    average_occupancy = Column(Float, default=0.0, nullable=False)
    average_wait_seconds = Column(Float, default=0.0, nullable=False)
    active_passengers = Column(Integer, default=0, nullable=False)
    active_drivers = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
