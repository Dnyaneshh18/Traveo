"""
Traveo API — application factory.

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import check_database_health, create_schema, engine, session_scope
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import register_middleware
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.colleges.router import router as colleges_router
from app.modules.drivers.router import router as drivers_router
from app.modules.maps.router import router as maps_router
from app.modules.notifications.router import router as notifications_router
from app.modules.ratings.router import router as ratings_router
from app.modules.rides.router import router as rides_router
from app.modules.students.router import router as students_router
from app.realtime.hub import hub
from app.realtime.router import router as ws_router
from app.workers import maintenance

settings = get_settings()
setup_logging()
logger = get_logger("traveo")

DESCRIPTION = """
**Traveo** — the college-verified, passenger-first shared ride platform.

* Students verify with their **college identity** and only ever see rides from their own campus.
* A student publishes a ride (campus ⇄ destination); classmates on the same route **accept** it
  until the creator says *go* — no waiting for a full vehicle.
* The **dispatch engine** then finds a driver Uber/Ola style (expanding radius, ranked offers,
  20-second countdown) and optimises the pickup/drop order.
* The creator holds the **boarding OTP**; every co-rider gets a **matching code** the driver verifies.
* Live locations stream over the WebSocket (`/ws`) and render on **Mappls (MapmyIndia)** maps.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", env=settings.APP_ENV, db="sqlite" if settings.is_sqlite else "postgres", maps="mappls" if settings.mappls_enabled else "local")
    if settings.AUTO_CREATE_SCHEMA:
        await create_schema()
    async with session_scope() as db:
        from app.seed import seed

        await seed(db)
    from app.modules.dispatch.service import dispatcher

    await dispatcher.resume_pending()
    maintenance.start()
    yield
    await maintenance.stop()
    await engine.dispose()
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        description=DESCRIPTION,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={"persistAuthorization": True, "displayRequestDuration": True},
    )
    register_middleware(app)
    register_exception_handlers(app)

    api = settings.API_PREFIX
    for r in (
        auth_router,
        colleges_router,
        students_router,
        rides_router,
        drivers_router,
        maps_router,
        ratings_router,
        notifications_router,
        admin_router,
    ):
        app.include_router(r, prefix=api)
    app.include_router(ws_router)

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    @app.get("/health", tags=["System"], include_in_schema=True)
    async def health():
        db_ok = await check_database_health()
        return {
            "status": "ok" if db_ok else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "database": "up" if db_ok else "down",
            "maps_provider": "mappls" if settings.mappls_enabled else "local",
            "realtime_connections": hub.online_count(),
        }

    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": settings.APP_NAME, "docs": "/docs", "health": "/health", "api": api}

    return app


app = create_app()
