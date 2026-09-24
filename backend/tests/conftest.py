from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

_tmp = tempfile.mkdtemp(prefix="traveo-test-")
os.environ.setdefault("APP_ENV", "test")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["MAPS_PROVIDER"] = "local"
os.environ["DISPATCH_OFFER_TIMEOUT_SECONDS"] = "2"
os.environ["DISPATCH_MAX_DURATION_SECONDS"] = "12"
os.environ["DISPATCH_RETRY_PAUSE_SECONDS"] = "1"
os.environ["RATE_LIMIT_REQUESTS"] = "100000"
os.environ["LOG_LEVEL"] = "WARNING"

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


API = "/api/v1"


async def login(client: AsyncClient, phone: str, role: str = "student") -> dict:
    r = await client.post(f"{API}/auth/otp/request", json={"phone": phone, "role": role})
    assert r.status_code == 200, r.text
    otp = r.json()["data"]["dev_otp"]
    r = await client.post(f"{API}/auth/otp/verify", json={"phone": phone, "otp": otp, "role": role})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    return {"token": data["tokens"]["access_token"], "user": data["user"], "headers": {"Authorization": f"Bearer {data['tokens']['access_token']}"}}


async def register_student(client: AsyncClient, phone: str, name: str, college_code: str, id_number: str, name_on_id: str | None = None, gender: str = "male") -> dict:
    session = await login(client, phone, "student")
    r = await client.get(f"{API}/colleges", params={"q": college_code})
    colleges = r.json()["data"]
    college = next(c for c in colleges if c["code"] == college_code)
    r = await client.post(
        f"{API}/students/register",
        headers=session["headers"],
        json={
            "full_name": name,
            "college_id": college["id"],
            "college_name_on_id": name_on_id or college["name"],
            "college_id_number": id_number,
            "gender": gender,
            "course": "B.Tech CS",
            "graduation_year": 2026,
        },
    )
    assert r.status_code == 200, r.text
    session["user"] = r.json()["data"]
    session["college"] = college
    return session
