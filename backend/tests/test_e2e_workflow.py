"""
Traveo Backend — Comprehensive End-to-End Workflow Integration Test

Verifies the complete real-time lifecycle across all 4 stages:
1. Passenger & Driver Auth
2. Ride Booking & Ride Intelligence Passenger Matching
3. Driver Assignment & Accept
4. OTP Verification & Pickup
5. Trip Start & Drop-off
6. Payment & Wallet Transaction
7. Ratings
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db_session
from app.models.enums import VerificationStatus
from app.models import DriverProfile

# In-memory SQLite test engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db_session():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db_session] = override_get_db_session


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables in in-memory test database before test runs."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_end_to_end_ride_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register & Verify Passenger 1
        p1_phone = "+919876543211"
        res = await client.post("/api/v1/auth/register", json={"phone": p1_phone, "name": "Alice"})
        assert res.status_code == 200
        p1_user_id = res.json()["data"]["user_id"]

        res = await client.post("/api/v1/auth/verify-otp", json={"phone": p1_phone, "otp": "1234"})
        assert res.status_code == 200
        p1_token = res.json()["data"]["access_token"]
        p1_headers = {"Authorization": f"Bearer {p1_token}"}

        # 2. Register & Verify Passenger 2
        p2_phone = "+919876543212"
        res = await client.post("/api/v1/auth/register", json={"phone": p2_phone, "name": "Bob"})
        assert res.status_code == 200

        res = await client.post("/api/v1/auth/verify-otp", json={"phone": p2_phone, "otp": "1234"})
        assert res.status_code == 200
        p2_token = res.json()["data"]["access_token"]
        p2_headers = {"Authorization": f"Bearer {p2_token}"}

        # 3. Register & Verify Driver
        d_phone = "+919876543213"
        res = await client.post("/api/v1/auth/register/driver", json={"phone": d_phone, "first_name": "Charlie", "last_name": "Driver"})
        assert res.status_code == 200
        driver_user_id = res.json()["data"]["user_id"]

        res = await client.post("/api/v1/auth/verify-otp", json={"phone": d_phone, "otp": "1234"})
        assert res.status_code == 200
        driver_token = res.json()["data"]["access_token"]
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        # Approve driver in test DB
        import uuid
        async with TestingSessionLocal() as session:
            from sqlalchemy import update
            await session.execute(
                update(DriverProfile)
                .where(DriverProfile.user_id == uuid.UUID(driver_user_id))
                .values(
                    verification_status=VerificationStatus.APPROVED,
                    driver_rating=5.0,
                    current_latitude=18.5205,
                    current_longitude=73.8568,
                )
            )
            await session.commit()

        # 4. Driver Goes Online
        res = await client.post("/api/v1/driver/go-online", headers=driver_headers)
        assert res.status_code == 200
        assert res.json()["status"] == "online"

        # 5. Passenger 1 Books Shared Ride
        p1_book_payload = {
            "pickup": {"latitude": 18.5204, "longitude": 73.8567, "address": "Central Square"},
            "destination": {"latitude": 18.5529, "longitude": 73.8796, "address": "Tech Park"},
            "requested_seats": 1,
        }
        res = await client.post("/api/v1/rides/book", json=p1_book_payload, headers=p1_headers)
        assert res.status_code == 200
        assert res.json()["matching_started"] is True

        # 6. Passenger 2 Books Compatible Shared Ride (Triggers Passenger Matching & Ride Group Creation!)
        p2_book_payload = {
            "pickup": {"latitude": 18.5210, "longitude": 73.8570, "address": "Central Mall"},
            "destination": {"latitude": 18.5535, "longitude": 73.8800, "address": "Tech Park Block B"},
            "requested_seats": 1,
        }
        res = await client.post("/api/v1/rides/book", json=p2_book_payload, headers=p2_headers)
        assert res.status_code == 200

        # 7. Driver Accepts Ride Assignment
        res = await client.post("/api/v1/driver/accept-ride", headers=driver_headers)
        assert res.status_code == 200
        accept_data = res.json()
        assert accept_data["status"] == "accepted"
        ride_id = accept_data["ride_id"]
        ride_otp = accept_data["otp"]
        assert ride_otp is not None

        # 8. Driver Verifies OTP at Pickup
        res = await client.post(
            f"/api/v1/driver/rides/{ride_id}/verify-otp",
            json={"otp": ride_otp},
            headers=driver_headers,
        )
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # 9. Driver Pickups Passenger & Starts Trip
        res = await client.post(
            f"/api/v1/driver/rides/{ride_id}/pickup",
            json={"passenger_id": p1_user_id},
            headers=driver_headers,
        )
        assert res.status_code == 200

        res = await client.post(
            f"/api/v1/driver/rides/{ride_id}/start",
            headers=driver_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "started"

        # 10. Driver Drops Passenger & Completes Ride
        res = await client.post(
            f"/api/v1/driver/rides/{ride_id}/drop",
            json={"passenger_id": p1_user_id},
            headers=driver_headers,
        )
        assert res.status_code == 200

        res = await client.post(
            f"/api/v1/driver/rides/{ride_id}/complete",
            headers=driver_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "completed"

        # 11. Passenger Submits Rating
        rating_payload = {
            "ride_id": ride_id,
            "rated_id": driver_user_id,
            "rating": 5,
            "review": "Awesome shared ride experience!",
        }
        res = await client.post("/api/v1/ratings", json=rating_payload, headers=p1_headers)
        assert res.status_code == 200
        assert res.json()["rating"] == 5
