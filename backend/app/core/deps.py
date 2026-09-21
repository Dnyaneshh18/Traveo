"""FastAPI dependencies: database session, current user, role guards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Query, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import DriverNotVerified, ForbiddenError, StudentNotVerified, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import decode_token
from app.models import DriverProfile, StudentProfile, User, UserRole, VerificationStatus

logger = get_logger(__name__)


DB = Annotated[AsyncSession, Depends(get_db)]


@dataclass(slots=True)
class CurrentUser:
    id: str
    role: UserRole
    user: User

    @property
    def student(self) -> StudentProfile | None:
        return self.user.student_profile

    @property
    def driver(self) -> DriverProfile | None:
        return self.user.driver_profile


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        logger.warning("missing_bearer_header", authorization=authorization); raise UnauthorizedError("Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


async def load_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.student_profile).selectinload(StudentProfile.college),
            selectinload(User.driver_profile).selectinload(DriverProfile.vehicle),
        )
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def resolve_user_from_token(db: AsyncSession, token: str) -> CurrentUser:
    payload = decode_token(token, "access")
    if not payload:
        raise UnauthorizedError("Invalid or expired token")
    user = await load_user(db, payload["sub"])
    if not user or not user.is_active:
        raise UnauthorizedError("Account not found or disabled")
    return CurrentUser(id=user.id, role=UserRole(user.role), user=user)


from fastapi import Cookie, Request

async def get_current_user(
    request: Request,
    db: DB,
    authorization: Annotated[str | None, Header()] = None,
    traveo_token: Annotated[str | None, Cookie()] = None,
    _token: Annotated[str | None, Query()] = None,
) -> CurrentUser:
    raw_token = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()
    elif traveo_token:
        raw_token = traveo_token.strip()
    elif "traveo_token" in request.cookies:
        raw_token = request.cookies.get("traveo_token", "").strip()
    elif _token:
        raw_token = _token.strip()
    elif "_token" in request.query_params:
        raw_token = request.query_params.get("_token", "").strip()

    if not raw_token:
        auth_cookie = request.cookies.get("Authorization")
        if auth_cookie and auth_cookie.lower().startswith("bearer "):
            raw_token = auth_cookie.split(" ", 1)[1].strip()

    if not raw_token:
        logger.warning("missing_bearer_header", authorization=authorization, cookie_present=bool(traveo_token), all_cookies=list(request.cookies.keys()))
        raise UnauthorizedError("Missing bearer token")
    return await resolve_user_from_token(db, raw_token)


async def get_ws_user(websocket: WebSocket, db: DB, token: Annotated[str | None, Query()] = None) -> CurrentUser:
    raw = token or _extract_bearer(websocket.headers.get("authorization"))
    return await resolve_user_from_token(db, raw)


Current = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    async def _guard(current: Current) -> CurrentUser:
        if current.role not in roles:
            raise ForbiddenError(f"Requires role: {', '.join(roles)}")
        return current

    return _guard


async def get_verified_student(current: Current) -> CurrentUser:
    if current.role != UserRole.STUDENT or not current.student:
        raise ForbiddenError("Student account required")
    if current.student.verification_status != VerificationStatus.VERIFIED:
        raise StudentNotVerified()
    return current


async def get_student(current: Current) -> CurrentUser:
    if current.role != UserRole.STUDENT:
        raise ForbiddenError("Student account required")
    return current


async def get_driver(current: Current) -> CurrentUser:
    if current.role != UserRole.DRIVER or not current.driver:
        raise ForbiddenError("Driver account required")
    return current


async def get_verified_driver(current: Current) -> CurrentUser:
    if current.role != UserRole.DRIVER or not current.driver:
        raise ForbiddenError("Driver account required")
    if current.driver.verification_status != VerificationStatus.VERIFIED:
        raise DriverNotVerified()
    return current


async def get_admin(current: Current) -> CurrentUser:
    if current.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")
    return current


VerifiedStudent = Annotated[CurrentUser, Depends(get_verified_student)]
Student = Annotated[CurrentUser, Depends(get_student)]
Driver = Annotated[CurrentUser, Depends(get_driver)]
VerifiedDriver = Annotated[CurrentUser, Depends(get_verified_driver)]
Admin = Annotated[CurrentUser, Depends(get_admin)]
