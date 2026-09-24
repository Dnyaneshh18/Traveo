"""Shared Pydantic building blocks & the standard success envelope."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Envelope(APIModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    meta: dict[str, Any] | None = None


def ok(data: Any = None, message: str | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "message": message, "meta": meta}


class GeoPoint(APIModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class Place(GeoPoint):
    address: str = Field(min_length=2, max_length=300)
    name: str | None = Field(default=None, max_length=120)


class Pagination(APIModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class TimestampedOut(APIModel):
    created_at: datetime
    updated_at: datetime | None = None
