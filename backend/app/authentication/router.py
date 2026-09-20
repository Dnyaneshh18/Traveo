"""
Traveo Backend — Authentication Router

HTTP layer for auth endpoints. Contains NO business logic.
Delegates everything to AuthService.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.schemas import (
    AdminLoginRequest,
    DriverRegisterRequest,
    RegisterRequest,
    RefreshTokenRequest,
)
from app.authentication.service import AuthService
from app.core.database import get_db_session
from app.dependencies import get_current_user_id
from app.schemas.base import success_response

router = APIRouter()


def _get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


# ── POST /auth/login ────────────────────────────────────────
from pydantic import BaseModel
class LoginRequest(BaseModel):
    phone: str

@router.post("/login")
async def login(
    request: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """
    Log in an existing passenger or driver.
    """
    result = await service.login(request.phone)
    return success_response(
        data=result.model_dump(),
        message="OTP sent successfully.",
    )


# ── POST /auth/register ─────────────────────────────────────
@router.post("/register")
async def register_passenger(
    request: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """
    Register a new passenger or send OTP to an existing one.
    """
    result = await service.register_passenger(request)
    return success_response(
        data=result.model_dump(),
        message="OTP sent successfully.",
    )


# ── POST /auth/register/driver ──────────────────────────────
@router.post("/register/driver")
async def register_driver(
    request: DriverRegisterRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """
    Register a new driver or send OTP to an existing one.
    """
    result = await service.register_driver(request)
    return success_response(
        data=result.model_dump(),
        message="OTP sent successfully.",
    )


# ── POST /auth/verify-otp ───────────────────────────────────
@router.post("/verify-otp")
async def verify_otp(
    request: dict,  # Using dict to accept VerifyOTPRequest
    service: AuthService = Depends(_get_auth_service),
):
    """
    Verify OTP and receive JWT tokens.
    """
    from app.authentication.schemas import VerifyOTPRequest
    validated = VerifyOTPRequest(**request)
    result = await service.verify_otp(validated)
    return success_response(
        data=result.model_dump(),
        message="Authentication successful.",
    )


# ── POST /auth/refresh ──────────────────────────────────────
@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """
    Refresh an access token using a valid refresh token.
    """
    result = await service.refresh_token(request.refresh_token)
    return success_response(
        data=result.model_dump(),
        message="Token refreshed successfully.",
    )


# ── GET /auth/me ─────────────────────────────────────────────
@router.get("/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    service: AuthService = Depends(_get_auth_service),
):
    """
    Get the current authenticated user's profile.
    """
    result = await service.get_current_user(user_id)
    return success_response(
        data=result.model_dump(),
        message="User profile retrieved.",
    )


# ── POST /auth/logout ───────────────────────────────────────
@router.post("/logout")
async def logout(
    user_id: str = Depends(get_current_user_id),
    service: AuthService = Depends(_get_auth_service),
):
    """
    Logout the current user and invalidate session.
    """
    await service.logout(user_id)
    return success_response(message="Logged out successfully.")
