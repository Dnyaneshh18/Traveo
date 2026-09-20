"""
Traveo Backend — Application Configuration

Loads all settings from environment variables via Pydantic Settings.
Never hardcode secrets or configuration values.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the Traveo backend.

    Values are loaded from environment variables and `.env` files.
    Every configurable value referenced in the specification lives here.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = True
    APP_NAME: str = "Traveo"
    APP_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: Any = ["http://localhost:3000", "http://localhost:8081"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item) for item in v]
        return ["http://localhost:3000", "http://localhost:8081"]

    # ── Supabase ─────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Twilio ───────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM_NUMBER: str | None = None
    DATABASE_URL: str = ""

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Google Maps ──────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""

    # ── Firebase Cloud Messaging ─────────────────────────────
    FCM_SERVER_KEY: str = ""
    FCM_PROJECT_ID: str = ""

    # ── Razorpay ─────────────────────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Ride Engine Defaults (overridden by system_configuration table) ──
    DEFAULT_SEARCH_RADIUS_KM: float = 2.0
    DEFAULT_SEARCH_TIMEOUT_SECONDS: int = 120
    DEFAULT_VOTE_TIMEOUT_SECONDS: int = 30
    DEFAULT_DRIVER_REQUEST_TIMEOUT_SECONDS: int = 20
    DEFAULT_MAX_GROUP_SIZE: int = 4
    DEFAULT_OTP_EXPIRY_MINUTES: int = 15
    DEFAULT_NO_SHOW_WAIT_MINUTES: int = 3
    DEFAULT_PLATFORM_COMMISSION_PERCENT: float = 20.0
    DEFAULT_MINIMUM_DRIVER_RATING: float = 3.5

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
