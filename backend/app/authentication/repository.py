"""
Traveo Backend — Authentication Repository

Data access layer for auth-related database operations.
Contains NO business logic — only SQL queries via SQLAlchemy.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, PassengerProfile, DriverProfile, Wallet
from app.models.enums import UserRole


class AuthRepository:
    """Repository for authentication-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── User Queries ─────────────────────────────────────
    async def get_user_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.phone == phone, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str | UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    # ── User Creation ────────────────────────────────────
    async def create_passenger_user(
        self, phone: str, name: str, age: int | None = None
    ) -> User:
        """Create a new passenger user with profile and wallet."""
        user = User(
            phone=phone,
            role=UserRole.PASSENGER,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Create passenger profile
        profile = PassengerProfile(
            user_id=user.id,
            first_name=name,
            age=age,
        )
        self.db.add(profile)

        # Create wallet
        wallet = Wallet(user_id=user.id)
        self.db.add(wallet)

        return user

    async def create_driver_user(
        self, phone: str, first_name: str, last_name: str = "",
        age: int | None = None, aadhaar_number: str | None = None,
        license_number: str | None = None, vehicle_category: str | None = None,
        plate_number: str | None = None
    ) -> User:
        """Create a new driver user with profile and wallet."""
        user = User(
            phone=phone,
            role=UserRole.DRIVER,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        from app.models.enums import VerificationStatus
        profile = DriverProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            age=age,
            aadhaar_number=aadhaar_number,
            license_number=license_number,
            verification_status=VerificationStatus.APPROVED, # Auto-approve for MVP/Testing
        )
        self.db.add(profile)

        # Create vehicle if provided
        if vehicle_category and plate_number:
            from app.models import Vehicle
            vehicle = Vehicle(
                driver_id=profile.id,
                vehicle_type=vehicle_category,
                registration_number=plate_number,
                seat_capacity=3 if "rickshaw" in vehicle_category.lower() else (4 if "sedan" in vehicle_category.lower() else 6)
            )
            self.db.add(vehicle)

        wallet = Wallet(user_id=user.id)
        self.db.add(wallet)

        return user

    # ── User Updates ─────────────────────────────────────
    async def update_last_login(self, user_id: str | UUID) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.now(UTC))
        )

    async def mark_user_verified(self, user_id: str | UUID) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True)
        )

    async def deactivate_user(self, user_id: str | UUID) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False, deleted_at=datetime.now(UTC))
        )
