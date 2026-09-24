"""
Runtime configuration — admin-editable overrides on top of environment defaults.

Values live in the `system_config` table and are cached in-process for 30s so
the ride engine can read them on every request without a DB round-trip.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import SystemConfig

settings = get_settings()

DEFAULTS: dict[str, tuple[Any, str]] = {
    "feed.max_detour_km": (settings.FEED_MAX_DETOUR_KM, "Max extra km a group will drive to include a co-rider"),
    "feed.max_detour_ratio": (settings.FEED_MAX_DETOUR_RATIO, "Max detour as a fraction of the route length"),
    "feed.time_window_minutes": (settings.FEED_TIME_WINDOW_MINUTES, "Departure time tolerance for matching"),
    "feed.radius_km": (settings.FEED_RADIUS_KM, "How far from the student we look for requests"),
    "request.open_ttl_minutes": (settings.REQUEST_OPEN_TTL_MINUTES, "Open requests expire after this many minutes past departure"),
    "dispatch.radius_steps_km": (settings.DISPATCH_RADIUS_STEPS_KM, "Driver search rings (km), expanded one by one"),
    "dispatch.offer_timeout_seconds": (settings.DISPATCH_OFFER_TIMEOUT_SECONDS, "Seconds a driver has to accept an offer"),
    "dispatch.max_duration_seconds": (settings.DISPATCH_MAX_DURATION_SECONDS, "Give up searching after this long"),
    "dispatch.retry_pause_seconds": (settings.DISPATCH_RETRY_PAUSE_SECONDS, "Pause between full search cycles"),
    "ride.no_show_wait_minutes": (settings.NO_SHOW_WAIT_MINUTES, "How long the driver waits before marking a no-show"),
    "fare.platform_fee_percent": (settings.PLATFORM_FEE_PERCENT, "Traveo platform fee (%)"),
    "safety.women_only_enabled": (True, "Allow women-only ride requests"),
}


@dataclass(slots=True)
class _Cache:
    values: dict[str, Any]
    loaded_at: float


_cache = _Cache(values={}, loaded_at=0.0)
_TTL = 30.0


async def load_config(db: AsyncSession, force: bool = False) -> dict[str, Any]:
    if not force and _cache.values and time.time() - _cache.loaded_at < _TTL:
        return _cache.values
    rows = (await db.execute(select(SystemConfig))).scalars().all()
    values = {k: v[0] for k, v in DEFAULTS.items()}
    for row in rows:
        try:
            values[row.key] = json.loads(row.value)
        except json.JSONDecodeError:
            values[row.key] = row.value
    _cache.values = values
    _cache.loaded_at = time.time()
    return values


async def get_value(db: AsyncSession, key: str) -> Any:
    cfg = await load_config(db)
    return cfg.get(key, DEFAULTS.get(key, (None, ""))[0])


async def set_value(db: AsyncSession, key: str, value: Any) -> None:
    row = await db.get(SystemConfig, key)
    description = DEFAULTS.get(key, (None, ""))[1]
    if row:
        row.value = json.dumps(value)
        row.updated_at = datetime.now(UTC)
    else:
        db.add(SystemConfig(key=key, value=json.dumps(value), description=description, updated_at=datetime.now(UTC)))
    await db.flush()
    _cache.loaded_at = 0.0


def describe() -> list[dict[str, Any]]:
    return [{"key": k, "default": v[0], "description": v[1]} for k, v in DEFAULTS.items()]
