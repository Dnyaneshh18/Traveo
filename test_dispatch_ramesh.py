import httpx
import time

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

# 1. Login student Dnyaneshwar
r_st = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token_st = r_st.json()["data"]["tokens"]["access_token"]
print("Student Dnyaneshwar logged in")

# 2. Check and clean up any previous active ride
act = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token_st}"}).json()["data"]
if act and act.get("status") not in ("completed", "cancelled"):
    client.post(f"{BASE}/rides/requests/{act['id']}/cancel", json={"reason": "reset"}, headers={"Authorization": f"Bearer {token_st}"})
    print("Cancelled previous ride:", act["id"])

# 3. Create fresh ride from VIT Pune to Swargate Bus Stand
r_pub = client.post(f"{BASE}/rides/requests", json={
    "origin": {"lat": 18.4636, "lng": 73.8682, "name": "VIT Pune", "address": "Bibwewadi, Pune"},
    "destination": {"lat": 18.5018, "lng": 73.8585, "name": "Swargate Bus Stand", "address": "Swargate, Pune"},
    "vehicle_type": "auto",
    "seats": 1,
    "departure_at": "2026-09-20T21:40:00Z",
    "note": "Leaving now"
}, headers={"Authorization": f"Bearer {token_st}"})
assert r_pub.status_code == 200, f"Failed to publish: {r_pub.text}"
ride_id = r_pub.json()["data"]["id"]
print(f"Ride created: {ride_id}")

# 4. Lock ride (trigger driver search)
r_lock = client.post(f"{BASE}/rides/requests/{ride_id}/lock", headers={"Authorization": f"Bearer {token_st}"})
print(f"Ride locked status: {r_lock.json()['data']['status']}")

time.sleep(1)

# 5. Check Ramesh Pawar (+919900000001) offer
r_drv = client.post(f"{BASE}/auth/otp/verify", json={"phone": "9900000001", "otp": "123456", "role": "driver"})
token_drv = r_drv.json()["data"]["tokens"]["access_token"]
offer = client.get(f"{BASE}/drivers/me/offer", headers={"Authorization": f"Bearer {token_drv}"}).json()["data"]
print("Ramesh Pawar offer:", offer["offer_id"] if offer else "None")
assert offer is not None, "Driver Ramesh Pawar should receive offer!"
print(f"Offer Pickup: {offer['pickup_address']} -> {offer['destination_address']}, Distance to pickup: {offer['distance_to_pickup_km']} km")
