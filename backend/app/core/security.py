"""
Traveo Backend — Security Utilities

JWT creation/verification, password hashing, OTP generation,
and token management utilities.
"""

from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# ── Password Hashing ────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ──────────────────────────────────────────────────────
def create_access_token(
    subject: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID string).
        role: User role (passenger, driver, admin, etc.).
        extra_claims: Additional claims to embed.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived JWT refresh token.

    Args:
        subject: User ID (UUID string).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": secrets.token_urlsafe(32),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If token is invalid, expired, or tampered.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )


def verify_access_token(token: str) -> dict[str, Any] | None:
    """
    Verify an access token and return its payload, or None if invalid.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    """
    Verify a refresh token and return its payload, or None if invalid.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            return None
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        return None


# ── OTP ──────────────────────────────────────────────────────
def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure numeric OTP.

    Args:
        length: Number of digits (default 6).

    Returns:
        OTP string (e.g. "482139").
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))


def generate_ride_otp(length: int = 4) -> str:
    """
    Generate a 4-digit ride OTP for passenger-driver verification.

    Shorter than auth OTP for easy verbal communication.
    """
    return generate_otp(length)


# ── Misc ─────────────────────────────────────────────────────
def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a URL-safe random token for idempotency keys, etc."""
    return secrets.token_urlsafe(nbytes)
