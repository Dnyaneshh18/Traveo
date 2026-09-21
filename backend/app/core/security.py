"""
Traveo — Security primitives: JWT, password hashing, OTP & matching codes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

_PBKDF2_ITERATIONS = 200_000


# ── Password hashing (PBKDF2-SHA256, no external deps) ─────────────
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return "pbkdf2$%d$%s$%s" % (
        _PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_b64, digest_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False


# ── OTP / codes ────────────────────────────────────────────────────
def generate_numeric_otp(length: int | None = None) -> str:
    n = length or settings.OTP_LENGTH
    return "".join(secrets.choice(string.digits) for _ in range(n))


def generate_ride_otp() -> str:
    """4-digit OTP held only by the ride creator (like Uber/Ola)."""
    return "".join(secrets.choice(string.digits) for _ in range(4))


_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous chars


def generate_matching_code() -> str:
    """Matching ID shown to group members, e.g. `TRV-7K2Q`."""
    return "TRV-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(4))


def hash_code(code: str) -> str:
    return hashlib.sha256(f"{settings.JWT_SECRET}:{code.strip().upper()}".encode()).hexdigest()


def verify_code(code: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_code(code), hashed)


# ── JWT ────────────────────────────────────────────────────────────
def _create_token(subject: str, token_type: str, expires: timedelta, extra: dict | None) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires).timestamp()),
        "jti": secrets.token_hex(8),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), {"role": role}
    )


def create_refresh_token(user_id: str, role: str) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), {"role": role}
    )


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any] | None:
    if not token or not isinstance(token, str):
        return None
    cleaned = token.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    try:
        payload = jwt.decode(cleaned, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload
