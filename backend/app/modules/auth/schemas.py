from __future__ import annotations

import re

from pydantic import EmailStr, Field, field_validator

from app.models.enums import Gender, UserRole, VehicleType
from app.schemas.common import APIModel

_PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


def normalise_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", raw.strip())
    if not _PHONE_RE.match(digits):
        raise ValueError("Enter a valid mobile number (10 digits)")
    if digits.startswith("+"):
        return digits
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    return "+" + digits


class RequestOtpIn(APIModel):
    phone: str
    role: UserRole = UserRole.STUDENT

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalise_phone(v)

    @field_validator("role")
    @classmethod
    def _role(cls, v: UserRole) -> UserRole:
        if v == UserRole.ADMIN:
            raise ValueError("Admins sign in with email & password")
        return v


class RequestOtpOut(APIModel):
    phone: str
    expires_in_seconds: int
    dev_otp: str | None = None  # only populated outside production


class VerifyOtpIn(APIModel):
    phone: str
    otp: str = Field(min_length=4, max_length=8)
    role: UserRole = UserRole.STUDENT
    push_token: str | None = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalise_phone(v)


class TokenPair(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CollegeBrief(APIModel):
    id: str
    code: str
    name: str
    short_name: str | None = None
    city: str
    latitude: float
    longitude: float
    institution_type: str
    address: str | None = None


class StudentProfileOut(APIModel):
    college: CollegeBrief
    college_id_number: str
    college_name_on_id: str
    identity_match_score: float
    verification_status: str
    verification_note: str | None = None
    id_card_url: str | None = None
    gender: Gender | None = None
    course: str | None = None
    graduation_year: int | None = None
    emergency_contact: str | None = None
    average_rating: float
    rating_count: int
    completed_rides: int
    total_saved_inr: float


class VehicleOut(APIModel):
    id: str
    vehicle_type: VehicleType
    registration_number: str
    make_model: str | None = None
    color: str | None = None
    seat_capacity: int
    is_verified: bool


class DriverProfileOut(APIModel):
    license_number: str | None = None
    verification_status: str
    status: str
    average_rating: float
    rating_count: int
    completed_rides: int
    total_earnings_inr: float
    acceptance_rate: float
    current_ride_id: str | None = None
    vehicle: VehicleOut | None = None


class UserOut(APIModel):
    id: str
    phone: str | None = None
    email: str | None = None
    role: UserRole
    full_name: str
    avatar_url: str | None = None
    profile_completed: bool
    student: StudentProfileOut | None = None
    driver: DriverProfileOut | None = None


class AuthResult(APIModel):
    tokens: TokenPair
    user: UserOut
    is_new_user: bool


class RefreshIn(APIModel):
    refresh_token: str


class AdminLoginIn(APIModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class PushTokenIn(APIModel):
    push_token: str = Field(min_length=8, max_length=255)
