from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.deps import DB, Current
from app.modules.auth.schemas import (
    AdminLoginIn,
    PushTokenIn,
    RefreshIn,
    RequestOtpIn,
    VerifyOtpIn,
)
from app.modules.auth.service import AuthService, serialize_user
from app.schemas.common import ok

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/otp/request", status_code=status.HTTP_200_OK, summary="Send a login OTP to a phone number")
async def request_otp(body: RequestOtpIn, db: DB):
    data = await AuthService(db).request_otp(body.phone, body.role)
    return ok(data.model_dump(), message="OTP sent")


@router.post("/otp/verify", summary="Verify OTP → access + refresh tokens")
async def verify_otp(body: VerifyOtpIn, response: Response, db: DB):
    data = await AuthService(db).verify_otp(body.phone, body.otp, body.role, body.push_token)
    response.set_cookie(
        key="traveo_token",
        value=data.tokens.access_token,
        max_age=30 * 86400,
        httponly=False,
        samesite="lax",
        path="/"
    )
    return ok(data.model_dump())


@router.post("/admin/login", summary="Admin email + password login")
async def admin_login(body: AdminLoginIn, db: DB):
    data = await AuthService(db).admin_login(body.email, body.password)
    return ok(data.model_dump())


@router.post("/refresh", summary="Rotate refresh token")
async def refresh(body: RefreshIn, response: Response, db: DB):
    data = await AuthService(db).refresh(body.refresh_token)
    response.set_cookie(
        key="traveo_token",
        value=data.access_token,
        max_age=30 * 86400,
        httponly=False,
        samesite="lax",
        path="/"
    )
    return ok(data.model_dump())


@router.post("/logout")
async def logout(response: Response, db: DB, current: Current, body: RefreshIn | None = None):
    await AuthService(db).logout(current.id, body.refresh_token if body else None)
    response.delete_cookie(key="traveo_token", path="/")
    return ok(message="Logged out")



@router.get("/me", summary="Current user with role profile")
async def me(current: Current):
    return ok(serialize_user(current.user).model_dump())


@router.put("/me/push-token")
async def set_push_token(body: PushTokenIn, current: Current, db: DB):
    current.user.push_token = body.push_token
    await db.flush()
    return ok(message="Push token saved")
