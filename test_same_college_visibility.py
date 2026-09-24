import asyncio
import httpx

API = "http://127.0.0.1:8000/api/v1"

async def login(client, phone, role="student"):
    r = await client.post(f"{API}/auth/otp/request", json={"phone": phone, "role": role})
    otp = r.json()["data"]["dev_otp"]
    r = await client.post(f"{API}/auth/otp/verify", json={"phone": phone, "otp": otp, "role": role})
    token = r.json()["data"]["tokens"]["access_token"]
    user = r.json()["data"]["user"]
    return {"token": token, "user": user, "headers": {"Authorization": f"Bearer {token}"}}

async def main():
    async with httpx.AsyncClient() as client:
        # Check health
        health = await client.get("http://127.0.0.1:8000/health")
        print("Backend Health:", health.json()["status"])

        # Test login for student
        s1 = await login(client, "+917972650026", "student")
        assert s1["user"]["student"] is not None
        college_code = s1["user"]["student"]["college"]["code"]
        print("Logged in Student 1:", s1["user"]["full_name"], "College:", college_code)

        # Check ride feed
        feed = await client.get(
            f"{API}/rides/feed",
            headers=s1["headers"],
            params={"pickup_lat": 18.4636, "pickup_lng": 73.8682, "drop_lat": 18.5074, "drop_lng": 73.8077}
        )
        print("Student 1 Feed Status:", feed.status_code, "Count:", len(feed.json()["data"]))
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

asyncio.run(main())
