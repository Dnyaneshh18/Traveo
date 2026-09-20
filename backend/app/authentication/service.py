"""
Traveo Backend — Authentication Service

Business logic for registration, OTP verification, token management.
Orchestrates repository + security utilities.
Contains NO database queries and NO HTTP concerns.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.repository import AuthRepository
from app.authentication.schemas import (
    DriverRegisterRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserProfileResponse,
    VerifyOTPRequest,
)
from app.core.config import get_settings
from app.core.otp_store import otp_store
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    verify_refresh_token,
)
from app.core.sms import send_sms_otp
from app.exceptions import (
    InvalidTokenError,
    OTPExpiredError,
    OTPInvalidError,
    OTPRateLimitError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class AuthService:
    """Authentication business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AuthRepository(db)

    # ── Login ───────────────────────────────────────────────
    async def login(self, phone: str) -> RegisterResponse:
        """
        Log in an existing user by sending an OTP.
        """
        existing = await self.repo.get_user_by_phone(phone)
        if not existing or not existing.is_active:
            raise UserNotFoundError(message="User not found or deactivated.")

        otp = generate_otp()
        stored = await otp_store.store_otp(phone, otp)
        if not stored:
            raise OTPRateLimitError()
        
        # Send Real SMS via Twilio
        send_sms_otp(phone, otp)

        return RegisterResponse(
            user_id=str(existing.id),
            otp_sent=True,
        )

    # ── Register Passenger ───────────────────────────────
    async def register_passenger(self, request: RegisterRequest) -> RegisterResponse:
        """
        Register a new passenger.
        If user exists and is active, send OTP for login instead.
        """
        existing = await self.repo.get_user_by_phone(request.phone)

        if existing:
            raise UserAlreadyExistsError(
                message="This mobile number is already registered."
            )

        # Create new user
        user = await self.repo.create_passenger_user(
            phone=request.phone,
            name=request.name,
            age=request.age,
        )

        # Generate and store OTP
        otp = generate_otp()
        stored = await otp_store.store_otp(request.phone, otp)
        if not stored:
            raise OTPRateLimitError()
        
        # Send Real SMS via Twilio
        send_sms_otp(request.phone, otp)

        return RegisterResponse(
            user_id=str(user.id),
            otp_sent=True,
        )

    # ── Register Driver ──────────────────────────────────
    async def register_driver(self, request: DriverRegisterRequest) -> RegisterResponse:
        """Register a new driver."""
        existing = await self.repo.get_user_by_phone(request.phone)

        if existing:
            raise UserAlreadyExistsError(
                message="This mobile number is already registered."
            )

        user = await self.repo.create_driver_user(
            phone=request.phone,
            first_name=request.first_name,
            last_name=request.last_name,
            age=request.age,
            aadhaar_number=request.aadhaar_number,
            license_number=request.license_number,
            vehicle_category=request.vehicle_category,
            plate_number=request.plate_number,
        )

        otp = generate_otp()
        stored = await otp_store.store_otp(request.phone, otp)
        if not stored:
            raise OTPRateLimitError()
            
        # Send Real SMS via Twilio
        send_sms_otp(request.phone, otp)

        return RegisterResponse(user_id=str(user.id), otp_sent=True)

    # ── Verify OTP ───────────────────────────────────────
    async def verify_otp(self, request: VerifyOTPRequest) -> TokenResponse:
        """Verify OTP and issue JWT tokens."""
        success, reason = await otp_store.verify_otp(request.phone, request.otp)

        if not success:
            if reason == "max_attempts":
                raise OTPRateLimitError(
                    message="Too many failed OTP attempts. Please request a new OTP."
                )
            if reason == "expired":
                raise OTPExpiredError()
            if reason == "not_found":
                raise OTPExpiredError(message="No OTP found. Please request a new one.")
            # reason == "invalid"
            raise OTPInvalidError()

        # Find user
        user = await self.repo.get_user_by_phone(request.phone)
        if not user:
            raise UserNotFoundError()

        # Mark verified & update login
        await self.repo.mark_user_verified(user.id)
        await self.repo.update_last_login(user.id)

        # Issue tokens
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        logger.info("user_authenticated", user_id=str(user.id), role=user.role.value)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Refresh Token ────────────────────────────────────
    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        """Issue a new access token using a valid refresh token."""
        payload = verify_refresh_token(refresh_token_str)
        if not payload:
            raise InvalidTokenError(message="Invalid or expired refresh token.")

        user_id = payload["sub"]
        user = await self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UserNotFoundError()

        new_access = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )
        new_refresh = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Get Current User ─────────────────────────────────
    async def get_current_user(self, user_id: str) -> UserProfileResponse:
        """Return the current user's profile."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        return UserProfileResponse(
            id=str(user.id),
            phone=user.phone,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            profile_completed=user.profile_completed,
            last_login=user.last_login,
            created_at=user.created_at,
        )

    # ── Logout ───────────────────────────────────────────
    async def logout(self, user_id: str) -> None:
        """
        Invalidate user session.
        In production: blacklist the refresh token in Redis.
        """
        logger.info("user_logged_out", user_id=user_id)
        # TODO: Blacklist refresh token in Redis
