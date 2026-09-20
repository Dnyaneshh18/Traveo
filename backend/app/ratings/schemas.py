"""
Traveo Backend — Rating Schemas
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SubmitRatingRequest(BaseModel):
    ride_id: str
    rated_id: str
    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class RatingResponse(BaseModel):
    id: str
    ride_id: str
    rater_id: str
    rated_id: str
    rating: int
    review: str | None
    created_at: datetime
