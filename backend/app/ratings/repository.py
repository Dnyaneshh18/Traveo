"""
Traveo Backend — Ratings Repository

Data access layer for rating CRUD and average calculation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DriverProfile,
    PassengerProfile,
    Rating,
    Ride,
    User,
)
from app.models.enums import UserRole


def to_uuid(val: str | UUID | None) -> UUID | None:
    if val is None:
        return None
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


class RatingRepository:
    """Repository for rating database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_ride_by_id(self, ride_id: str | UUID) -> Ride | None:
        result = await self.db.execute(
            select(Ride).where(Ride.id == to_uuid(ride_id))
        )
        return result.scalar_one_or_none()

    async def get_existing_rating(
        self, ride_id: str | UUID, rater_id: str | UUID, rated_id: str | UUID
    ) -> Rating | None:
        result = await self.db.execute(
            select(Rating).where(
                Rating.ride_id == to_uuid(ride_id),
                Rating.rater_id == to_uuid(rater_id),
                Rating.rated_id == to_uuid(rated_id),
            )
        )
        return result.scalar_one_or_none()

    async def create_rating(
        self,
        ride_id: str | UUID,
        rater_id: str | UUID,
        rated_id: str | UUID,
        rating: int,
        review: str | None = None,
    ) -> Rating:
        new_rating = Rating(
            ride_id=to_uuid(ride_id),
            rater_id=to_uuid(rater_id),
            rated_id=to_uuid(rated_id),
            rating=rating,
            review=review,
        )
        self.db.add(new_rating)
        await self.db.flush()
        return new_rating

    async def get_ratings_for_user(
        self, user_id: str | UUID, limit: int = 20
    ) -> list[Rating]:
        result = await self.db.execute(
            select(Rating)
            .where(Rating.rated_id == to_uuid(user_id))
            .order_by(Rating.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ratings_for_ride(
        self, ride_id: str | UUID
    ) -> list[Rating]:
        result = await self.db.execute(
            select(Rating).where(Rating.ride_id == to_uuid(ride_id))
        )
        return list(result.scalars().all())

    async def calculate_average_rating(
        self, user_id: str | UUID
    ) -> float | None:
        result = await self.db.execute(
            select(func.avg(Rating.rating)).where(Rating.rated_id == to_uuid(user_id))
        )
        avg = result.scalar_one_or_none()
        return round(float(avg), 2) if avg is not None else None

    async def update_user_average_rating(
        self, user_id: str | UUID, avg_rating: float
    ) -> None:
        uid = to_uuid(user_id)
        user_result = await self.db.execute(
            select(User.role).where(User.id == uid)
        )
        role = user_result.scalar_one_or_none()

        if role == UserRole.DRIVER:
            await self.db.execute(
                update(DriverProfile)
                .where(DriverProfile.user_id == uid)
                .values(driver_rating=avg_rating)
            )
        elif role == UserRole.PASSENGER:
            await self.db.execute(
                update(PassengerProfile)
                .where(PassengerProfile.user_id == uid)
                .values(average_rating=avg_rating)
            )
