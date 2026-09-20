"""
Traveo Backend — Rate Limiting Middleware

Redis-backed sliding window rate limiter.
Enforces per-IP and per-user request limits.
"""

from __future__ import annotations

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.cache import cache
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Paths exempt from rate limiting
EXEMPT_PATHS = {"/health", "/healthz", "/readyz", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis.

    Limits:
    - Per-IP: RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW_SECONDS
    - Returns 429 Too Many Requests when exceeded
    - Adds X-RateLimit-* headers to every response
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip WebSocket connections
        if request.url.path.startswith("/ws"):
            return await call_next(request)

        # Determine rate limit key
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"

        # Check if user is authenticated (from JWT)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # Use user-specific key for authenticated requests
            try:
                from app.core.security import verify_access_token
                token = auth_header.split(" ", 1)[1]
                payload = verify_access_token(token)
                if payload and payload.get("sub"):
                    key = f"ratelimit:user:{payload['sub']}"
            except Exception:
                pass

        # Increment counter
        max_requests = settings.RATE_LIMIT_REQUESTS
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        count = await cache.increment_counter(key, window)

        # Build response
        if count > max_requests:
            logger.warning(
                "rate_limit_exceeded",
                key=key,
                count=count,
                limit=max_requests,
            )
            from fastapi.responses import ORJSONResponse
            return ORJSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": window,
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window),
                    "Retry-After": str(window),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, max_requests - count)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(window)

        return response
