"""
Traveo — Application configuration.

Every operational parameter is loaded from the environment (or a `.env` file).
Nothing here is hard-coded for a specific deployment.  Development defaults are
chosen so that the platform boots with **zero external services** (SQLite file
database, in-memory realtime hub, local maps provider) – production points the
same settings at PostgreSQL, Redis and Mappls.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    APP_NAME: str = "Traveo"
    APP_VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: Any = ["*"]
    PUBLIC_BASE_URL: str = ""  # e.g. https://api.traveo.app (used for upload URLs)

    # ── Database ───────────────────────────────────────────────────
    # Development: SQLite file (no setup).  Production: postgresql+asyncpg://...
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'data' / 'traveo.db'}"
    DB_ECHO: bool = False
    AUTO_CREATE_SCHEMA: bool = True  # create tables on boot (dev / hackathon mode)
    SEED_DEMO_DATA: bool = True  # seed colleges, demo drivers & admin on first boot

    # ── Security ───────────────────────────────────────────────────
    JWT_SECRET: str = "traveo-dev-secret-change-me-in-production-32+"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    DEV_STATIC_OTP: str = "123456"  # accepted in development / test only
    ADMIN_EMAIL: str = "admin@traveo.app"
    ADMIN_PASSWORD: str = "Admin@123"

    # ── SMS provider (optional) ────────────────────────────────────
    SMS_PROVIDER: Literal["console", "twilio", "msg91"] = "console"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""

    # ── Maps (Mappls / MapmyIndia) ─────────────────────────────────
    MAPS_PROVIDER: Literal["auto", "mappls", "local"] = "auto"
    MAPPLS_REST_KEY: str = ""  # static REST API key (routing, distance matrix)
    MAPPLS_CLIENT_ID: str = ""  # OAuth client credentials (atlas: autosuggest, geocode)
    MAPPLS_CLIENT_SECRET: str = ""
    MAPPLS_ROUTE_BASE_URL: str = "https://route.mappls.com"
    MAPPLS_ATLAS_BASE_URL: str = "https://atlas.mappls.com"
    MAPPLS_OUTPOST_TOKEN_URL: str = "https://outpost.mappls.com/api/security/oauth/token"
    MAPS_HTTP_TIMEOUT_SECONDS: float = 6.0

    # ── Realtime ───────────────────────────────────────────────────
    REDIS_URL: str = ""  # optional; enables multi-instance fan-out
    WS_HEARTBEAT_SECONDS: int = 25
    DRIVER_LOCATION_STALE_SECONDS: int = 90

    # ── Ride engine defaults (overridable from admin "system_config") ──
    FEED_MAX_DETOUR_KM: float = 2.5
    FEED_MAX_DETOUR_RATIO: float = 0.35
    FEED_TIME_WINDOW_MINUTES: int = 25
    FEED_RADIUS_KM: float = 6.0
    REQUEST_OPEN_TTL_MINUTES: int = 45
    DISPATCH_RADIUS_STEPS_KM: Any = [1.0, 2.0, 3.5, 5.0, 8.0]
    DISPATCH_OFFER_TIMEOUT_SECONDS: int = 20
    DISPATCH_MAX_DURATION_SECONDS: int = 240
    DISPATCH_RETRY_PAUSE_SECONDS: int = 5
    NO_SHOW_WAIT_MINUTES: int = 4
    PLATFORM_FEE_PERCENT: float = 8.0

    # ── Storage ────────────────────────────────────────────────────
    UPLOAD_DIR: str = str(BACKEND_DIR / "storage" / "uploads")
    MAX_UPLOAD_MB: int = 6

    # ── Logging ────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "console"

    # ── Rate limiting ──────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100000
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    OTP_RATE_LIMIT_PER_HOUR: int = 100000

    # ── Validators ─────────────────────────────────────────────────
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    return [str(x) for x in json.loads(s)]
                except json.JSONDecodeError:
                    pass
            return [o.strip() for o in s.split(",") if o.strip()]
        if isinstance(v, list):
            return [str(x) for x in v]
        return ["*"]

    @field_validator("DISPATCH_RADIUS_STEPS_KM", mode="before")
    @classmethod
    def _parse_radius(cls, v: Any) -> list[float]:
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                return [float(x) for x in json.loads(s)]
            return [float(x) for x in s.split(",") if x.strip()]
        if isinstance(v, list | tuple):
            return [float(x) for x in v]
        return [1.0, 2.0, 3.5, 5.0, 8.0]

    # ── Helpers ────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV in ("development", "test")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def mappls_enabled(self) -> bool:
        if self.MAPS_PROVIDER == "local":
            return False
        return bool(self.MAPPLS_REST_KEY)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
