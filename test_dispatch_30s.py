import httpx
import time

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

# 1. Login Driver Ramesh
r_drv = client.post(f"{BASE}/auth/otp/verify", json={"phone": "9900000001", "otp": "123456", "role": "driver"})
token_drv = r_drv.json()["data"]["tokens"]["access_token"]
print("Driver Ramesh authenticated")

# 2. Login Student Dnyaneshwar
r_st = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token_st = r_st.json()["data"]["tokens"]["access_token"]
print("Student Dnyaneshwar authenticated")

# 3. Clean up active ride
act = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token_st}"}).json()["data"]
if act and act.get("status") not in ("completed", "cancelled"):
    client.post(f"{BASE}/rides/requests/{act['id']}/cancel", json={"reason": "reset"}, headers={"Authorization": f"Bearer {token_st}"})
    print("Cancelled previous ride:", act["id"])

# 4. Create ride from VIT Pune to Sukh Sagar Nagar
r_pub = client.post(f"{BASE}/rides/requests", json={
    "origin": {"lat": 18.4636, "lng": 73.8682, "name": "VIT Pune", "address": "Bibwewadi, Pune"},
    "destination": {"lat": 18.4558, "lng": 73.8694, "name": "Sukh Sagar Nagar", "address": "Katraj-Kondhwa, Pune"},
    "vehicle_type": "auto",
    "seats": 1,
    "departure_at": "2026-09-20T21:50:00Z",
    "note": "Leaving immediately"
}, headers={"Authorization": f"Bearer {token_st}"})
ride_id = r_pub.json()["data"]["id"]
print("Created ride ID:", ride_id)

# 5. Lock ride
client.post(f"{BASE}/rides/requests/{ride_id}/lock", headers={"Authorization": f"Bearer {token_st}"})
print("Ride locked! Dispatch searching drivers...")

# 6. Check offer
time.sleep(0.5)
offer_res = client.get(f"{BASE}/drivers/me/offer", headers={"Authorization": f"Bearer {token_drv}"}).json()
print("Offer response:", offer_res.get("data"))
