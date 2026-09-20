"""
Traveo Backend — Ratings Service

Business logic for passenger-driver mutual ratings.
Updates average ratings on profiles after each rating.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    DuplicateError,
    NotFoundError,
    RideError,
)
from app.ratings.repository import RatingRepository
from app.ratings.schemas import (
    RatingResponse,
    SubmitRatingRequest,
)

logger = structlog.get_logger(__name__)


class RatingService:
    """Mutual rating system for passengers and drivers."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = RatingRepository(db)

    async def submit_rating(
        self, rater_id: str, request: SubmitRatingRequest
    ) -> RatingResponse:
        """
        Submit a rating after a completed ride.
        - Passenger rates driver
        - Driver rates passenger
        Prevents duplicate ratings.
        """
        # Check ride exists and is completed
        ride = await self.repo.get_ride_by_id(request.ride_id)
        if not ride:
            raise NotFoundError(message="Ride not found.")

        from app.models.enums import RideStatus
        if ride.ride_status != RideStatus.RIDE_COMPLETED:
            raise RideError(message="Ratings can only be submitted for completed rides.")

        # Check for duplicate
        existing = await self.repo.get_existing_rating(
            request.ride_id, rater_id, request.rated_id
        )
        if existing:
            raise DuplicateError(message="You have already rated this user for this ride.")

        # Create rating
        rating = await self.repo.create_rating(
            ride_id=request.ride_id,
            rater_id=rater_id,
            rated_id=request.rated_id,
            rating=request.rating,
            review=request.review,
        )

        # Update the rated user's average rating
        await self._update_average_rating(request.rated_id)

        logger.info(
            "rating_submitted",
            ride_id=request.ride_id,
            rater_id=rater_id,
            rated_id=request.rated_id,
            rating=request.rating,
        )

        return RatingResponse(
            id=str(rating.id),
            ride_id=str(rating.ride_id),
            rater_id=str(rating.rater_id),
            rated_id=str(rating.rated_id),
            rating=rating.rating,
            review=rating.review,
            created_at=rating.created_at,
        )

    async def get_ratings_for_user(
        self, user_id: str, limit: int = 20
    ) -> list[RatingResponse]:
        """Get ratings received by a user."""
        ratings = await self.repo.get_ratings_for_user(user_id, limit)
        return [
            RatingResponse(
                id=str(r.id),
                ride_id=str(r.ride_id),
                rater_id=str(r.rater_id),
                rated_id=str(r.rated_id),
                rating=r.rating,
                review=r.review,
                created_at=r.created_at,
            )
            for r in ratings
        ]

    async def get_ride_ratings(
        self, ride_id: str
    ) -> list[RatingResponse]:
        """Get all ratings for a specific ride."""
        ratings = await self.repo.get_ratings_for_ride(ride_id)
        return [
            RatingResponse(
                id=str(r.id),
                ride_id=str(r.ride_id),
                rater_id=str(r.rater_id),
                rated_id=str(r.rated_id),
                rating=r.rating,
                review=r.review,
                created_at=r.created_at,
            )
            for r in ratings
        ]

    async def _update_average_rating(self, user_id: str) -> None:
        """Recalculate and update the user's average rating."""
        avg = await self.repo.calculate_average_rating(user_id)
        if avg is not None:
            await self.repo.update_user_average_rating(user_id, avg)
