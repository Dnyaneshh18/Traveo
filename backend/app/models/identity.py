"""Identity domain: colleges, users, student & driver profiles, vehicles."""

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
    DriverStatus,
    Gender,
    InstitutionType,
    UserRole,
    VehicleType,
    VerificationStatus,
)


class College(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registry of institutions.  Ride visibility is scoped to a college."""

    __tablename__ = "colleges"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(60))
    aliases: Mapped[str | None] = mapped_column(Text)  # "|" separated alternative names
    institution_type: Mapped[InstitutionType] = mapped_column(
        String(20), default=InstitutionType.COLLEGE, nullable=False
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    id_pattern: Mapped[str | None] = mapped_column(String(200))  # regex the student ID must match
    id_hint: Mapped[str | None] = mapped_column(String(200))  # human readable example
    email_domain: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    students: Mapped[list[StudentProfile]] = relationship(back_populates="college")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(String(20), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_token: Mapped[str | None] = mapped_column(String(255))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student_profile: Mapped[StudentProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    driver_profile: Mapped[DriverProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("college_id", "college_id_number", name="uq_student_identity"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    college_id: Mapped[str] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    college_id_number: Mapped[str] = mapped_column(String(60), nullable=False)
    college_name_on_id: Mapped[str] = mapped_column(String(200), nullable=False)
    identity_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    id_card_url: Mapped[str | None] = mapped_column(String(500))
    gender: Mapped[Gender | None] = mapped_column(String(10))
    course: Mapped[str | None] = mapped_column(String(120))
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    emergency_contact: Mapped[str | None] = mapped_column(String(20))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(20), default=VerificationStatus.PENDING, nullable=False, index=True
    )
    verification_note: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    average_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_rides: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_rides: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_saved_inr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user: Mapped[User] = relationship(back_populates="student_profile", lazy="selectin")
    college: Mapped[College] = relationship(back_populates="students", lazy="selectin")


class DriverProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "driver_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    license_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    license_url: Mapped[str | None] = mapped_column(String(500))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(20), default=VerificationStatus.PENDING, nullable=False, index=True
    )
    status: Mapped[DriverStatus] = mapped_column(
        String(20), default=DriverStatus.OFFLINE, nullable=False, index=True
    )
    average_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_rides: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offers_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offers_accepted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earnings_inr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_ride_id: Mapped[str | None] = mapped_column(String(32), index=True)
    # Latest known position (denormalised for fast dispatch queries)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    heading: Mapped[float | None] = mapped_column(Float)
    location_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="driver_profile", lazy="selectin")
    vehicle: Mapped[Vehicle | None] = relationship(
        back_populates="driver", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def acceptance_rate(self) -> float:
        if self.offers_received == 0:
            return 1.0
        return self.offers_accepted / self.offers_received


class Vehicle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"

    driver_id: Mapped[str] = mapped_column(
        ForeignKey("driver_profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(String(20), nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    make_model: Mapped[str | None] = mapped_column(String(120))
    color: Mapped[str | None] = mapped_column(String(40))
    seat_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    driver: Mapped[DriverProfile] = relationship(back_populates="vehicle")


class OtpCode(UUIDPrimaryKeyMixin, Base):
    """Phone login OTPs (hashed)."""

    __tablename__ = "otp_codes"
    __table_args__ = (Index("ix_otp_phone_created", "phone", "created_at"),)

    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), default="login", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    jti: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
