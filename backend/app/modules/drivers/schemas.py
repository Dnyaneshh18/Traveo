from __future__ import annotations

import re

from pydantic import Field, field_validator

from app.models.enums import VehicleType
from app.schemas.common import APIModel


class DriverRegisterIn(APIModel):
    full_name: str = Field(min_length=2, max_length=120)
    license_number: str = Field(min_length=6, max_length=30)
    vehicle_type: VehicleType
    registration_number: str = Field(min_length=6, max_length=15)
    make_model: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=40)

    @field_validator("registration_number")
    @classmethod
    def _reg(cls, v: str) -> str:
        v = re.sub(r"[\s-]", "", v.upper())
        if not re.fullmatch(r"[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{3,4}", v):
            raise ValueError("Enter a valid Indian registration number, e.g. MH12AB1234")
        return v

    @field_validator("license_number")
    @classmethod
    def _lic(cls, v: str) -> str:
        return re.sub(r"\s", "", v.upper())


class DriverStatusIn(APIModel):
    online: bool
    lat: float | None = None
    lng: float | None = None


class LocationIn(APIModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    heading: float | None = Field(default=None, ge=0, le=360)
    speed: float | None = Field(default=None, ge=0)
    accuracy: float | None = Field(default=None, ge=0)


class OfferRespondIn(APIModel):
    reason: str | None = Field(default=None, max_length=120)


class VerifyCodeIn(APIModel):
    code: str = Field(min_length=4, max_length=12)

    @field_validator("code")
    @classmethod
    def _norm(cls, v: str) -> str:
        return v.strip().upper()


class MemberActionIn(APIModel):
    member_id: str


class CancelRideIn(APIModel):
    reason: str = Field(min_length=3, max_length=200)
