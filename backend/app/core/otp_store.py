"""
Traveo Backend — OTP Store

Redis-backed OTP storage with TTL-based expiry, attempt tracking,
and rate limiting. Falls back to in-memory storage when Redis is
unavailable (development mode).
"""

from __future__ import annotations

import time
from typing import Any

import structlog

from app.core.cache import cache
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Redis key prefixes
_OTP_PREFIX = "otp:"
_OTP_ATTEMPTS_PREFIX = "otp_attempts:"
_OTP_RATE_PREFIX = "otp_rate:"

# Configuration
OTP_TTL_SECONDS = 300  # 5 minutes
MAX_VERIFY_ATTEMPTS = 5
MAX_SEND_PER_WINDOW = 3
RATE_WINDOW_SECONDS = 300  # 5-minute window for send rate limit

# In-memory fallback for development without Redis
_memory_store: dict[str, dict[str, Any]] = {}


class OTPStore:
    """
    Production-grade OTP storage with Redis.

    Features:
    - TTL-based automatic expiry
    - Max verification attempt tracking (brute-force protection)
    - Rate limiting on OTP send requests
    - Graceful fallback to in-memory when Redis is unavailable
    """

    async def store_otp(self, phone: str, otp: str) -> bool:
        """
        Store OTP for a phone number with TTL.

        Returns True if stored successfully, False if rate-limited.
        """
        # Check send rate limit
        rate_limited = await self._check_send_rate_limit(phone)
        if rate_limited:
            return False

        key = f"{_OTP_PREFIX}{phone}"
        attempts_key = f"{_OTP_ATTEMPTS_PREFIX}{phone}"

        stored = await cache.set(key, otp, ttl_seconds=OTP_TTL_SECONDS)
        if stored:
            # Reset attempt counter on new OTP
            await cache.set(attempts_key, "0", ttl_seconds=OTP_TTL_SECONDS)
            # Increment send counter
            await self._increment_send_counter(phone)
            logger.info("otp_stored", phone=phone, ttl=OTP_TTL_SECONDS)
            return True

        # Fallback to in-memory
        _memory_store[phone] = {
            "otp": otp,
            "attempts": 0,
            "expires_at": time.time() + OTP_TTL_SECONDS,
        }
        logger.info("otp_stored_memory_fallback", phone=phone)
        return True

    async def verify_otp(self, phone: str, otp: str) -> tuple[bool, str]:
        """
        Verify OTP for a phone number.

        Returns:
            (True, "ok") on success
            (False, reason) on failure — reason is one of:
                "expired", "invalid", "max_attempts", "not_found"
        """
        key = f"{_OTP_PREFIX}{phone}"
        attempts_key = f"{_OTP_ATTEMPTS_PREFIX}{phone}"

        # Check development bypass
        if settings.APP_ENV == "development" and otp in ("1234", "123456"):
            await self.delete_otp(phone)
            return True, "ok"

        # Try Redis first
        stored_otp = await cache.get(key)

        if stored_otp is not None:
            # Check attempt count
            attempts_str = await cache.get(attempts_key) or "0"
            attempts = int(attempts_str)

            if attempts >= MAX_VERIFY_ATTEMPTS:
                await self.delete_otp(phone)
                return False, "max_attempts"

            if stored_otp != otp:
                await cache.set(
                    attempts_key, str(attempts + 1), ttl_seconds=OTP_TTL_SECONDS
                )
                return False, "invalid"

            # Success — clean up
            await self.delete_otp(phone)
            return True, "ok"

        # Fallback to in-memory
        entry = _memory_store.get(phone)
        if not entry:
            return False, "not_found"

        if time.time() > entry["expires_at"]:
            _memory_store.pop(phone, None)
            return False, "expired"

        if entry["attempts"] >= MAX_VERIFY_ATTEMPTS:
            _memory_store.pop(phone, None)
            return False, "max_attempts"

        if entry["otp"] != otp:
            entry["attempts"] += 1
            return False, "invalid"

        # Success
        _memory_store.pop(phone, None)
        return True, "ok"

    async def delete_otp(self, phone: str) -> None:
        """Delete OTP and related keys for a phone number."""
        await cache.delete(f"{_OTP_PREFIX}{phone}")
        await cache.delete(f"{_OTP_ATTEMPTS_PREFIX}{phone}")
        _memory_store.pop(phone, None)

    async def _check_send_rate_limit(self, phone: str) -> bool:
        """Check if phone has exceeded OTP send rate limit."""
        rate_key = f"{_OTP_RATE_PREFIX}{phone}"
        count = await cache.increment_counter(rate_key, RATE_WINDOW_SECONDS)
        if count > MAX_SEND_PER_WINDOW:
            logger.warning("otp_rate_limited", phone=phone, count=count)
            return True
        return False

    async def _increment_send_counter(self, phone: str) -> None:
        """Track OTP send count for rate limiting."""
        rate_key = f"{_OTP_RATE_PREFIX}{phone}"
        await cache.increment_counter(rate_key, RATE_WINDOW_SECONDS)


# Singleton instance
otp_store = OTPStore()
