"""Authentication service: phone OTP login, admin login, token refresh."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import load_user
from app.core.exceptions import OtpInvalid, RateLimited, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_numeric_otp,
    hash_code,
    verify_code,
    verify_password,
)
from app.models import OtpCode, RefreshToken, User, UserRole
from app.modules.auth.schemas import (
    AuthResult,
    CollegeBrief,
    DriverProfileOut,
    RequestOtpOut,
    StudentProfileOut,
    TokenPair,
    UserOut,
    VehicleOut,
)
from app.services.sms import send_sms

settings = get_settings()
logger = get_logger(__name__)


def serialize_user(user: User) -> UserOut:
    student = None
    driver = None
    if user.student_profile:
        sp = user.student_profile
        student = StudentProfileOut(
            college=CollegeBrief.model_validate(sp.college),
            college_id_number=sp.college_id_number,
            college_name_on_id=sp.college_name_on_id,
            identity_match_score=sp.identity_match_score,
            verification_status=sp.verification_status,
            verification_note=sp.verification_note,
            id_card_url=sp.id_card_url,
            gender=sp.gender,
            course=sp.course,
            graduation_year=sp.graduation_year,
            emergency_contact=sp.emergency_contact,
            average_rating=sp.average_rating,
            rating_count=sp.rating_count,
            completed_rides=sp.completed_rides,
            total_saved_inr=sp.total_saved_inr,
        )
    if user.driver_profile:
        dp = user.driver_profile
        driver = DriverProfileOut(
            license_number=dp.license_number,
            verification_status=dp.verification_status,
            verification_note=dp.verification_note,
            status=dp.status,
            average_rating=dp.average_rating,
            rating_count=dp.rating_count,
            completed_rides=dp.completed_rides,
            total_earnings_inr=dp.total_earnings_inr,
            acceptance_rate=round(dp.acceptance_rate, 3),
            current_ride_id=dp.current_ride_id,
            vehicle=VehicleOut.model_validate(dp.vehicle) if dp.vehicle else None,
        )
    return UserOut(
        id=user.id,
        phone=user.phone,
        email=user.email,
        role=UserRole(user.role),
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        profile_completed=user.profile_completed,
        student=student,
        driver=driver,
    )


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── OTP ────────────────────────────────────────────────────────
    async def request_otp(self, phone: str, role: UserRole) -> RequestOtpOut:
        now = datetime.now(UTC)
        # In non-production/hackathon mode, allow unlimited OTP requests
        if settings.is_production and settings.OTP_RATE_LIMIT_PER_HOUR > 0:
            window_start = now - timedelta(hours=1)
            recent = await self.db.scalar(
                select(func.count()).select_from(OtpCode).where(OtpCode.phone == phone, OtpCode.created_at >= window_start)
            )
            if (recent or 0) >= settings.OTP_RATE_LIMIT_PER_HOUR:
                raise RateLimited("Too many OTP requests. Please try again later")

        code = generate_numeric_otp()
        self.db.add(
            OtpCode(
                phone=phone,
                code_hash=hash_code(code),
                purpose=f"login:{role}",
                expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
                created_at=now,
            )
        )
        await self.db.flush()
        await send_sms(phone, f"{code} is your Traveo verification code. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.")
        logger.info("otp_requested", phone=phone[-4:], role=role)
        return RequestOtpOut(
            phone=phone,
            expires_in_seconds=settings.OTP_EXPIRE_MINUTES * 60,
            dev_otp=code if not settings.is_production else None,
        )

    async def verify_otp(self, phone: str, otp: str, role: UserRole, push_token: str | None) -> AuthResult:
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(OtpCode)
            .where(OtpCode.phone == phone, OtpCode.consumed.is_(False))
            .order_by(OtpCode.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        static_ok = (not settings.is_production) and otp == settings.DEV_STATIC_OTP

        if not static_ok:
            if not record:
                raise OtpInvalid("Request an OTP first")
            expires = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=UTC)
            if expires < now or record.attempts >= settings.OTP_MAX_ATTEMPTS:
                raise OtpInvalid("OTP expired. Request a new one")
            if not verify_code(otp, record.code_hash):
                record.attempts += 1
                await self.db.flush()
                raise OtpInvalid()
        if record:
            record.consumed = True

        # Find or create the user for this role.
        user = await self.db.scalar(select(User).where(User.phone == phone))
        is_new = False
        if user is None:
            user = User(phone=phone, role=role, full_name="", profile_completed=False)
            self.db.add(user)
            await self.db.flush()
            is_new = True
        elif user.role != role:
            raise UnauthorizedError(
                f"This number is registered as a {user.role}. Please use the {user.role} app."
            )
        if push_token:
            user.push_token = push_token
        user.last_login_at = now
        await self.db.flush()

        full_user = await load_user(self.db, user.id)
        tokens = await self.issue_tokens(full_user)  # type: ignore[arg-type]
        logger.info("login_success", user_id=user.id, role=role, new=is_new)
        return AuthResult(tokens=tokens, user=serialize_user(full_user), is_new_user=is_new)  # type: ignore[arg-type]

    # ── Admin ──────────────────────────────────────────────────────
    async def admin_login(self, email: str, password: str) -> AuthResult:
        user = await self.db.scalar(select(User).where(User.email == email.lower(), User.role == UserRole.ADMIN))
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        user.last_login_at = datetime.now(UTC)
        full_user = await load_user(self.db, user.id)
        tokens = await self.issue_tokens(full_user)  # type: ignore[arg-type]
        return AuthResult(tokens=tokens, user=serialize_user(full_user), is_new_user=False)  # type: ignore[arg-type]

    # ── Tokens ─────────────────────────────────────────────────────
    async def issue_tokens(self, user: User) -> TokenPair:
        access = create_access_token(user.id, user.role)
        refresh = create_refresh_token(user.id, user.role)
        payload = decode_token(refresh, "refresh") or {}
        self.db.add(
            RefreshToken(
                user_id=user.id,
                jti=payload.get("jti", ""),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0), tz=UTC),
                created_at=datetime.now(UTC),
            )
        )
        await self.db.flush()
        return TokenPair(access_token=access, refresh_token=refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    async def refresh(self, refresh_token: str) -> TokenPair:
        logger.info("refresh_call_received", token_prefix=refresh_token[:20] if refresh_token else None)
        payload = decode_token(refresh_token, "refresh")
        if not payload:
            raise UnauthorizedError("Invalid refresh token")
        stored = await self.db.scalar(select(RefreshToken).where(RefreshToken.jti == payload.get("jti")))
        if not stored or stored.revoked:
            raise UnauthorizedError("Refresh token revoked")
        user = await self.db.get(User, payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedError("Account disabled")
        stored.revoked = True  # rotation
        return await self.issue_tokens(user)

    async def logout(self, user_id: str, refresh_token: str | None) -> None:
        if refresh_token:
            payload = decode_token(refresh_token, "refresh")
            if payload:
                stored = await self.db.scalar(select(RefreshToken).where(RefreshToken.jti == payload.get("jti")))
                if stored:
                    stored.revoked = True
        user = await self.db.get(User, user_id)
        if user:
            user.push_token = None
