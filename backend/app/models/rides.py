"""Ride domain: requests (groups), members, driver offers, rides, events, payments, ratings."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    MemberRole,
    MemberStatus,
    NotificationType,
    OfferStatus,
    PaymentMethod,
    PaymentStatus,
    RideDirection,
    RideRequestStatus,
    RideStatus,
    VehicleType,
)


class RideRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A ride request *is* the passenger group.  The creator publishes it to the
    college feed; classmates on the same route join until the creator locks it
    (or seats run out).  Then a driver is dispatched.
    """

    __tablename__ = "ride_requests"
    __table_args__ = (
        Index("ix_ride_requests_college_status", "college_id", "status"),
        Index("ix_ride_requests_departure", "departure_at"),
    )

    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    college_id: Mapped[str] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    direction: Mapped[RideDirection] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(String(20), nullable=False)
    seat_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_taken: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[RideRequestStatus] = mapped_column(
        String(20), default=RideRequestStatus.OPEN, nullable=False, index=True
    )

    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    origin_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)

    departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(200))
    women_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    route_polyline: Mapped[str | None] = mapped_column(Text)
    route_distance_km: Mapped[float | None] = mapped_column(Float)
    route_duration_min: Mapped[float | None] = mapped_column(Float)
    estimated_fare_total: Mapped[float | None] = mapped_column(Float)
    estimated_fare_solo: Mapped[float | None] = mapped_column(Float)

    otp_hash: Mapped[str | None] = mapped_column(String(64))  # creator's boarding OTP
    otp_plain: Mapped[str | None] = mapped_column(String(8))  # returned only to the creator
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatch_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatch_radius_km: Mapped[float | None] = mapped_column(Float)
    dispatch_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancel_reason: Mapped[str | None] = mapped_column(String(200))

    members: Mapped[list[RideMember]] = relationship(
        back_populates="request", cascade="all, delete-orphan", order_by="RideMember.joined_at", lazy="selectin"
    )
    offers: Mapped[list[DriverOffer]] = relationship(back_populates="request", lazy="selectin")
    rides: Mapped[list[Ride]] = relationship(back_populates="request", order_by="Ride.created_at", lazy="selectin")

    @property
    def seats_available(self) -> int:
        return max(0, self.seat_capacity - self.seats_taken)

    @property
    def ride(self) -> Ride | None:
        """The current (non-cancelled) ride, if a driver is/was assigned."""
        live = [r for r in self.rides if r.status != RideStatus.CANCELLED]
        return live[-1] if live else None


class RideMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ride_members"
    __table_args__ = (UniqueConstraint("request_id", "user_id", name="uq_member_request_user"),)

    request_id: Mapped[str] = mapped_column(
        ForeignKey("ride_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(String(10), default=MemberRole.MEMBER, nullable=False)
    status: Mapped[MemberStatus] = mapped_column(
        String(12), default=MemberStatus.ACCEPTED, nullable=False, index=True
    )
    seats: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    pickup_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_lng: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    drop_lat: Mapped[float] = mapped_column(Float, nullable=False)
    drop_lng: Mapped[float] = mapped_column(Float, nullable=False)
    drop_address: Mapped[str] = mapped_column(Text, nullable=False)

    matching_code_hash: Mapped[str | None] = mapped_column(String(64))
    matching_code_plain: Mapped[str | None] = mapped_column(String(12))  # visible to the member only
    pickup_order: Mapped[int | None] = mapped_column(Integer)
    drop_order: Mapped[int | None] = mapped_column(Integer)
    pickup_eta_min: Mapped[float | None] = mapped_column(Float)
    distance_km: Mapped[float | None] = mapped_column(Float)  # member's own travelled distance
    fare_share_inr: Mapped[float | None] = mapped_column(Float)
    detour_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    request: Mapped[RideRequest] = relationship(back_populates="members")


class HiddenRequest(UUIDPrimaryKeyMixin, Base):
    """A student "rejected" a feed request – hide it from their feed."""

    __tablename__ = "hidden_requests"
    __table_args__ = (UniqueConstraint("request_id", "user_id", name="uq_hidden_request_user"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("ride_requests.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DriverOffer(UUIDPrimaryKeyMixin, Base):
    """One dispatch attempt: an offer sent to one driver with a countdown."""

    __tablename__ = "driver_offers"
    __table_args__ = (Index("ix_offers_driver_status", "driver_user_id", "status"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("ride_requests.id"), nullable=False, index=True)
    driver_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[OfferStatus] = mapped_column(String(12), default=OfferStatus.PENDING, nullable=False)
    radius_km: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    eta_min: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    driver_payout_inr: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    request: Mapped[RideRequest] = relationship(back_populates="offers")


class Ride(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Created the moment a driver accepts; tracks execution until completion."""

    __tablename__ = "rides"

    request_id: Mapped[str] = mapped_column(ForeignKey("ride_requests.id"), nullable=False, index=True)
    driver_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    offer_id: Mapped[str | None] = mapped_column(ForeignKey("driver_offers.id"))
    status: Mapped[RideStatus] = mapped_column(
        String(20), default=RideStatus.DRIVER_ASSIGNED, nullable=False, index=True
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(String(20), nullable=False)
    vehicle_registration: Mapped[str | None] = mapped_column(String(20))
    driver_eta_min: Mapped[float | None] = mapped_column(Float)
    otp_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(String(200))
    total_distance_km: Mapped[float | None] = mapped_column(Float)
    total_fare_inr: Mapped[float | None] = mapped_column(Float)
    platform_fee_inr: Mapped[float | None] = mapped_column(Float)
    driver_payout_inr: Mapped[float | None] = mapped_column(Float)

    request: Mapped[RideRequest] = relationship(back_populates="rides", lazy="selectin")


class RideEvent(UUIDPrimaryKeyMixin, Base):
    """Immutable timeline used by the apps, admin and analytics."""

    __tablename__ = "ride_events"
    __table_args__ = (Index("ix_ride_events_request_created", "request_id", "created_at"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("ride_requests.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(32))
    event: Mapped[str] = mapped_column(String(60), nullable=False)
    data: Mapped[str | None] = mapped_column(Text)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("ride_id", "payer_id", name="uq_payment_ride_payer"),)

    ride_id: Mapped[str] = mapped_column(ForeignKey("rides.id"), nullable=False, index=True)
    payer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(String(10), default=PaymentMethod.CASH, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(String(10), default=PaymentStatus.PENDING, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(120))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Rating(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("ride_id", "rater_id", "ratee_id", name="uq_rating_once"),)

    ride_id: Mapped[str] = mapped_column(ForeignKey("rides.id"), nullable=False, index=True)
    rater_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    ratee_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(String(400), nullable=False)
    data: Mapped[str | None] = mapped_column(Text)  # JSON deep-link payload
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SystemConfig(Base):
    """Admin editable runtime configuration (overrides Settings defaults)."""

    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
