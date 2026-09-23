import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_login(client: AsyncClient):
    r = await client.post("/api/v1/auth/admin/login", json={"email": "admin@traveo.app", "password": "Admin@123"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    assert data["data"]["tokens"]["access_token"]
    assert data["data"]["user"]["role"] == "admin"

@pytest.mark.asyncio
async def test_driver_otp_and_register(client: AsyncClient):
    phone = "+919999000011"
    r1 = await client.post("/api/v1/auth/otp/request", json={"phone": phone, "role": "driver"})
    assert r1.status_code == 200
    otp = r1.json()["data"]["dev_otp"]

    r2 = await client.post("/api/v1/auth/otp/verify", json={"phone": phone, "otp": otp, "role": "driver"})
    assert r2.status_code == 200
    token = r2.json()["data"]["tokens"]["access_token"]

    r3 = await client.post(
        "/api/v1/drivers/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Test Driver",
            "license_number": "MH12TEST9988",
            "vehicle_type": "auto",
            "registration_number": "MH12XY8899",
            "make_model": "Bajaj RE",
            "color": "Green"
        }
    )
    assert r3.status_code == 200, r3.text
    assert r3.json()["data"]["driver"]["verification_status"] == "pending"
    assert r3.json()["data"]["driver"]["vehicle"]["registration_number"] == "MH12XY8899"

@pytest.mark.asyncio
async def test_student_otp_and_register(client: AsyncClient):
    phone = "+919999000022"
    r1 = await client.post("/api/v1/auth/otp/request", json={"phone": phone, "role": "student"})
    assert r1.status_code == 200
    otp = r1.json()["data"]["dev_otp"]

    r2 = await client.post("/api/v1/auth/otp/verify", json={"phone": phone, "otp": otp, "role": "student"})
    assert r2.status_code == 200
    token = r2.json()["data"]["tokens"]["access_token"]

    # Get colleges
    rc = await client.get("/api/v1/colleges")
    assert rc.status_code == 200
    colleges = rc.json()["data"]
    coep = next(c for c in colleges if c["code"] == "COEP")

    r3 = await client.post(
        "/api/v1/students/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Rahul Deshmukh",
            "college_id": coep["id"],
            "college_id_number": "112003045",
            "college_name_on_id": "COEP Technological University",
            "gender": "male",
            "course": "B.Tech Computer Science",
            "graduation_year": 2026,
        }
    )
    assert r3.status_code == 200, r3.text
    assert r3.json()["data"]["student"]["verification_status"] == "pending"
    assert r3.json()["data"]["student"]["college_id_number"] == "112003045"
