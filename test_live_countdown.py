import httpx
import time

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

# 1. Login Ramesh Pawar
r_drv = client.post(f"{BASE}/auth/otp/verify", json={"phone": "9900000001", "otp": "123456", "role": "driver"})
token_drv = r_drv.json()["data"]["tokens"]["access_token"]
print("Driver Ramesh logged in")

# 2. Login student Dnyaneshwar
r_st = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token_st = r_st.json()["data"]["tokens"]["access_token"]
print("Student Dnyaneshwar logged in")

# 3. Clean up active ride
act = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token_st}"}).json()["data"]
if act and act.get("status") not in ("completed", "cancelled"):
    client.post(f"{BASE}/rides/requests/{act['id']}/cancel", json={"reason": "reset"}, headers={"Authorization": f"Bearer {token_st}"})
    print("Cancelled previous ride:", act["id"])

# 4. Create ride from VIT Pune to Swargate
r_pub = client.post(f"{BASE}/rides/requests", json={
    "origin": {"lat": 18.4636, "lng": 73.8682, "name": "VIT Pune", "address": "Bibwewadi, Pune"},
    "destination": {"lat": 18.5018, "lng": 73.8585, "name": "Swargate Bus Stand", "address": "Swargate, Pune"},
    "vehicle_type": "auto",
    "seats": 1,
    "departure_at": "2026-09-20T21:40:00Z",
    "note": "Leaving now"
}, headers={"Authorization": f"Bearer {token_st}"})
ride_id = r_pub.json()["data"]["id"]
print("Created ride:", ride_id)

# 5. Lock ride
client.post(f"{BASE}/rides/requests/{ride_id}/lock", headers={"Authorization": f"Bearer {token_st}"})
print("Locked ride, dispatch started!")

# 6. Poll driver offer
offer = None
for i in range(10):
    time.sleep(0.5)
    res = client.get(f"{BASE}/drivers/me/offer", headers={"Authorization": f"Bearer {token_drv}"}).json()
    if res.get("data"):
        offer = res["data"]
        print(f"[{i*0.5}s] GOT OFFER! ID={offer['offer_id']}, expires_at={offer['expires_at']}, payout=₹{offer['driver_payout_inr']}")
        break

if not offer:
    print("NO OFFER RECEIVED!")
    exit(1)

# Keep offer active for 60 seconds so user can see it in Port 8082!
print("Keeping offer active for testing in browser on Port 8082...")
