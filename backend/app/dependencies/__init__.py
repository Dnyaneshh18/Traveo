"""
Traveo Backend — FastAPI Dependencies

Reusable dependencies for authentication, authorization, and database
session injection via FastAPI's Depends() system.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.security import verify_access_token
from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    UserNotFoundError,
)


# ── Settings Dependency ──────────────────────────────────────
SettingsDep = Annotated[Settings, Depends(get_settings)]

# ── Database Session Dependency ──────────────────────────────
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# ── Current User ─────────────────────────────────────────────
async def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """
    Extract and validate the current user from the Authorization header.

    Returns the user_id (UUID string) from a valid JWT access token.

    Raises:
        AuthenticationError: Missing or invalid token.
    """
    if not authorization:
        raise AuthenticationError(message="Authorization header is required.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidTokenError(message="Invalid authorization scheme. Use 'Bearer <token>'.")

    payload = verify_access_token(token)
    if payload is None:
        raise InvalidTokenError()

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError(message="Token does not contain a valid user identifier.")

    return user_id


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_current_user_role(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> tuple[str, str]:
    """
    Extract user_id AND role from the JWT. Returns (user_id, role).
    """
    if not authorization:
        raise AuthenticationError(message="Authorization header is required.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidTokenError()

    payload = verify_access_token(token)
    if payload is None:
        raise InvalidTokenError()

    user_id = payload.get("sub", "")
    role = payload.get("role", "")
    if not user_id or not role:
        raise InvalidTokenError(message="Token missing required claims.")

    return user_id, role


# ── Role-Based Authorization ─────────────────────────────────
class RequireRole:
    """
    Dependency that enforces role-based access control.

    Usage:
        @router.get("/admin/dashboard", dependencies=[Depends(RequireRole("admin", "super_admin"))])
        async def admin_dashboard(): ...

    Or as a parameter:
        async def endpoint(user: tuple = Depends(RequireRole("driver"))):
            user_id, role = user
    """

    def __init__(self, *allowed_roles: str) -> None:
        self.allowed_roles = set(allowed_roles)

    async def __call__(
        self,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> tuple[str, str]:
        user_id, role = await get_current_user_role(authorization)
        if role not in self.allowed_roles:
            raise AuthorizationError(
                message=f"This endpoint requires one of: {', '.join(self.allowed_roles)}.",
                details={"required_roles": list(self.allowed_roles), "current_role": role},
            )
        return user_id, role


# ── Convenience Role Dependencies ────────────────────────────
RequirePassenger = RequireRole("passenger")
RequireDriver = RequireRole("driver")
RequireAdmin = RequireRole("admin", "super_admin", "operations", "finance", "support")
RequireSuperAdmin = RequireRole("super_admin")
RequireFinance = RequireRole("finance", "super_admin")
RequireSupport = RequireRole("support", "operations", "super_admin")
