"""
Traveo Backend — Middleware Stack

Registers all middleware in the correct order. Middleware responsibilities:
  - Request ID injection (tracing)
  - Request/response timing
  - Structured request logging
  - CORS
  - Security headers
"""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


# ── Request ID Middleware ────────────────────────────────────
class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique request ID into every request for distributed tracing.
    The ID is returned in the X-Request-ID response header and bound to
    the structlog context for the duration of the request.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ── Request Logging Middleware ───────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with method, path, status code, and duration.
    Excludes health check endpoints from noisy logging.
    """

    EXCLUDED_PATHS = {"/health", "/healthz", "/readyz", "/docs", "/openapi.json"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            client=request.client.host if request.client else None,
        )
        return response


# ── Security Headers Middleware ──────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response per OWASP recommendations.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(self)"
        )
        return response


# ── Registration ─────────────────────────────────────────────
def register_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI application in correct order."""
    settings = get_settings()

    # Order matters: outermost middleware runs first.
    # 1. Security headers (outermost)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Rate limiting
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # 3. Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # 4. Request ID
    app.add_middleware(RequestIdMiddleware)

    # 5. CORS — must be registered via add_middleware for Starlette compat
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
