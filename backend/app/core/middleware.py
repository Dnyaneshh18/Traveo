"""HTTP middleware stack: request-id, structured access log, security headers, rate limiting, CORS."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["x-request-id"] = request_id
        response.headers["x-response-time-ms"] = str(duration_ms)
        if request.url.path not in ("/health", "/metrics"):
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                ms=duration_ms,
            )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("x-content-type-options", "nosniff")
        response.headers.setdefault("x-frame-options", "DENY")
        response.headers.setdefault("referrer-policy", "no-referrer")
        response.headers.setdefault("permissions-policy", "geolocation=(self)")
        if settings.is_production:
            response.headers.setdefault("strict-transport-security", "max-age=63072000; includeSubDomains")
        return response


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    """In-memory per-client limiter (sufficient for a single instance; swap for Redis when scaling)."""

    def __init__(self, app, limit: int, window_seconds: int):
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(("/health", "/docs", "/openapi", "/uploads")):
            return await call_next(request)
        client = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "anon"
        )
        now = time.time()
        bucket = self._hits[client]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return ORJSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {"code": "rate_limited", "message": "Too many requests", "details": None},
                },
                headers={"retry-after": str(self.window)},
            )
        bucket.append(now)
        return await call_next(request)


def register_middleware(app: FastAPI) -> None:
    # Order matters: outermost first → CORS must wrap everything so errors carry CORS headers.
    app.add_middleware(SlidingWindowRateLimiter, limit=settings.RATE_LIMIT_REQUESTS, window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=r"https?://.*" if "*" in settings.ALLOWED_ORIGINS else None,
        allow_credentials="*" not in settings.ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id"],
    )
