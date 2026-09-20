"""
Traveo Backend — Ratings API Router

Endpoints for submitting and viewing ratings.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies import get_current_user_id
from app.ratings.schemas import RatingResponse, SubmitRatingRequest
from app.ratings.service import RatingService

router = APIRouter()


@router.post("/ratings", response_model=RatingResponse)
async def submit_rating(
    request: SubmitRatingRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Submit a rating after a completed ride."""
    service = RatingService(db)
    return await service.submit_rating(user_id, request)


@router.get("/ratings/me", response_model=list[RatingResponse])
async def get_my_ratings(
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get ratings received by the current user."""
    service = RatingService(db)
    return await service.get_ratings_for_user(user_id, limit)


@router.get("/ratings/ride/{ride_id}", response_model=list[RatingResponse])
async def get_ride_ratings(
    ride_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all ratings for a specific ride."""
    service = RatingService(db)
    return await service.get_ride_ratings(ride_id)
