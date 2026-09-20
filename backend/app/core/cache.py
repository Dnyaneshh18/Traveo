"""
Traveo Backend — Async Redis Cache Layer

High-performance caching wrapper for system configuration settings,
rate limiting counters, and transient matching state.
"""

from __future__ import annotations

import json
from typing import Any
import structlog
import redis.asyncio as redis

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class RedisCache:
    """Async Redis cache client wrapper."""

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def initialize(self) -> None:
        """Connect to Redis server."""
        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3.0,
            )
            await self._redis.ping()
            logger.info("redis_connected", url=settings.REDIS_URL)
        except Exception as e:
            logger.warning("redis_connection_warning", error=str(e))
            self._redis = None

    async def close(self) -> None:
        """Close connection."""
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> str | None:
        """Get string value by key."""
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except Exception:
            return None

    async def set(
        self, key: str, value: str | dict | list, ttl_seconds: int = 300
    ) -> bool:
        """Set key with TTL."""
        if not self._redis:
            return False
        try:
            val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            await self._redis.setex(key, ttl_seconds, val_str)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            return False

    async def increment_counter(
        self, key: str, window_seconds: int = 60
    ) -> int:
        """Increment rate limit counter and set TTL if new."""
        if not self._redis:
            return 1
        try:
            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()
            return int(results[0])
        except Exception:
            return 1


# Singleton instance
cache = RedisCache()
