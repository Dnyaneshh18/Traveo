"""
Traveo — Database engine & session management (SQLAlchemy 2.0 async).

Works with SQLite (development) and PostgreSQL (production) through the same
API.  Sessions are provided to request handlers via `get_db` and to background
workers via `session_scope`.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine():
    url = settings.DATABASE_URL
    kwargs: dict = {"echo": settings.DB_ECHO, "future": True}
    if url.startswith("sqlite"):
        # Ensure the data directory exists for file based SQLite databases.
        if ":///" in url and ":memory:" not in url:
            db_path = url.split(":///", 1)[1]
            Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    else:
        kwargs.update(pool_size=10, max_overflow=20, pool_pre_ping=True)
    eng = create_async_engine(url, **kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(eng.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - driver hook
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

    return eng


engine = _build_engine()
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency – one session per request, committed on success."""
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for background tasks & workers."""
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_schema() -> None:
    """Create all tables and apply non-destructive column additions (development / hackathon mode). Production uses Alembic."""
    from app import models  # noqa: F401 – ensure models are imported

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # SQLite automatic schema patch for local development
        if settings.is_sqlite:
            try:
                res = await conn.execute(text("PRAGMA table_info(driver_profiles)"))
                cols = [r[1] for r in res.fetchall()]
                if cols and "verification_note" not in cols:
                    await conn.execute(text("ALTER TABLE driver_profiles ADD COLUMN verification_note TEXT"))
            except Exception:
                pass


async def check_database_health() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
