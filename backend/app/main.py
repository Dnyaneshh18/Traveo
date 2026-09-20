"""
Traveo Backend — Application Entry Point

Responsible ONLY for:
  - Creating the FastAPI application
  - Registering middleware
  - Registering routers
  - Initializing logging
  - Lifecycle events (startup / shutdown)

No business logic lives here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.core.config import get_settings
from app.core.database import check_database_health, engine
from app.core.logging import setup_logging
from app.exceptions.handlers import register_exception_handlers
from app.middleware import register_middleware

logger = structlog.get_logger(__name__)
settings = get_settings()


# ── Lifecycle ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    # ── Startup ──
    setup_logging()
    logger.info(
        "application_starting",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
    )

    # Verify database connectivity
    db_healthy = await check_database_health()
    if db_healthy:
        logger.info("database_connected")
    else:
        logger.error("database_connection_failed")

    # Initialize Redis cache
    from app.core.cache import cache
    await cache.initialize()

    # Start background scheduler
    from app.workers.scheduler import start_scheduler
    start_scheduler()

    yield

    # ── Shutdown ──
    logger.info("application_shutting_down")

    # Stop background scheduler
    from app.workers.scheduler import stop_scheduler
    stop_scheduler()

    # Close Redis
    from app.core.cache import cache as redis_cache
    await redis_cache.close()

    await engine.dispose()
    logger.info("database_connections_closed")


# ── Application Factory ─────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Shared Ride Platform — Backend API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Register middleware stack
    register_middleware(app)

    # Register global exception handlers
    register_exception_handlers(app)

    # Register routers
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all API routers under the versioned prefix."""
    prefix = settings.API_PREFIX

    # Health check (no prefix, no auth)
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        db_ok = await check_database_health()

        # Check Redis health
        redis_ok = False
        try:
            from app.core.cache import cache
            if cache._redis:
                await cache._redis.ping()
                redis_ok = True
        except Exception:
            pass

        return {
            "status": "healthy" if db_ok else "degraded",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "services": {
                "database": "up" if db_ok else "down",
                "redis": "up" if redis_ok else "down",
            },
        }

    # --- Auth Router ---
    from app.authentication.router import router as auth_router
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["Authentication"])

    # --- Ride Routers ---
    from app.rides.router import router as ride_router
    from app.rides.driver_router import driver_router
    app.include_router(ride_router, prefix=f"{prefix}/rides", tags=["Passenger Rides"])
    app.include_router(driver_router, prefix=f"{prefix}/driver", tags=["Driver Rides"])

    # --- Payment & Wallet Routers ---
    from app.payments.router import router as payment_router
    app.include_router(payment_router, prefix=f"{prefix}/payments", tags=["Payments & Wallet"])

    # --- Rating Router ---
    from app.ratings.router import router as rating_router
    app.include_router(rating_router, prefix=f"{prefix}", tags=["Ratings"])

    # --- Notification Router ---
    from app.notifications.router import router as notification_router
    app.include_router(notification_router, prefix=f"{prefix}", tags=["Notifications"])

    # --- Admin Router ---
    from app.admin.router import router as admin_router
    app.include_router(admin_router, prefix=f"{prefix}/admin", tags=["Admin & Operations"])

    # --- WebSocket Router ---
    from app.websocket.router import router as ws_router
    app.include_router(ws_router, tags=["WebSocket"])


# ── App Instance ─────────────────────────────────────────────
app = create_app()
