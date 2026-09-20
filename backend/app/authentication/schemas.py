"""
Traveo Backend — Authentication Schemas

Request/response models for all auth endpoints.
Separated from ORM models to keep the API contract clean.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator
import phonenumbers


class RegisterRequest(BaseModel):
    """POST /api/v1/auth/register"""

    phone: str = Field(
        min_length=10, max_length=15,
        description="Phone number with country code, e.g. +919876543210",
    )
    name: str = Field(
        min_length=1, max_length=100,
        description="Passenger's first name",
    )
    age: int | None = Field(default=None, description="Passenger's age")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            parsed = phonenumbers.parse(v, "IN")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")


class RegisterResponse(BaseModel):
    user_id: str
    otp_sent: bool


class VerifyOTPRequest(BaseModel):
    """POST /api/v1/auth/verify-otp"""

    phone: str = Field(min_length=10, max_length=15)
    otp: str = Field(min_length=4, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = Field(description="Access token TTL in seconds")
    token_type: str = "Bearer"


class RefreshTokenRequest(BaseModel):
    """POST /api/v1/auth/refresh"""

    refresh_token: str


class UserProfileResponse(BaseModel):
    """GET /api/v1/auth/me"""

    id: str
    phone: str | None
    email: str | None
    role: str
    is_active: bool
    is_verified: bool
    profile_completed: bool
    last_login: datetime | None
    created_at: datetime
    age: int | None = None

    class Config:
        from_attributes = True


class DriverRegisterRequest(BaseModel):
    """POST /api/v1/auth/register/driver"""

    phone: str = Field(min_length=10, max_length=15)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(max_length=100, default="")
    age: int | None = Field(default=None, description="Driver's age")
    vehicle_category: str | None = Field(default=None, description="Type of vehicle")
    plate_number: str | None = Field(default=None, description="Vehicle plate number")
    aadhaar_number: str | None = Field(default=None, description="Aadhaar card number")
    license_number: str | None = Field(default=None, description="Driving license number")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            parsed = phonenumbers.parse(v, "IN")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")


class AdminLoginRequest(BaseModel):
    """POST /api/v1/auth/admin/login"""

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
