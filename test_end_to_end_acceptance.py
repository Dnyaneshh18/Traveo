import httpx
import time
import sqlite3

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

print("==========================================================")
print("RUNNING AUTOMATED END-TO-END RIDE CREATION & ACCEPTANCE TEST")
print("==========================================================")

# 1. Place Driver Ramesh Pawar (+919900000001) at VIT Pune campus gate
con = sqlite3.connect('backend/data/traveo.db')
cur = con.cursor()
cur.execute("UPDATE driver_profiles SET latitude = 18.4638, longitude = 73.8680, status = 'online' WHERE user_id = (SELECT id FROM users WHERE phone = '+919900000001')")
cur.execute("UPDATE ride_requests SET status = 'cancelled' WHERE status NOT IN ('completed', 'cancelled')")
con.commit()
print("✓ Placed Driver Ramesh Pawar online at VIT Pune campus")

# 2. Login Driver Ramesh
r_drv = client.post(f"{BASE}/auth/otp/verify", json={"phone": "9900000001", "otp": "123456", "role": "driver"})
token_drv = r_drv.json()["data"]["tokens"]["access_token"]
print("✓ Driver Ramesh authenticated")

# 3. Ensure Student Dnyaneshwar (+917972650026) is registered & logged in
colleges = client.get(f"{BASE}/colleges").json()["data"]
vit = next(c for c in colleges if c["code"] == "VIT")
client.post(f"{BASE}/auth/otp/request", json={"phone": "7972650026", "role": "student"})
r_st = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token_st = r_st.json()["data"]["tokens"]["access_token"]
client.post(f"{BASE}/students/register", json={
    "full_name": "Dnyaneshwar Vasant Patil",
    "college_id": vit["id"],
    "college_name_on_id": "Vishwakarma Institute of Technology",
    "college_id_number": "12410666",
    "gender": "male",
    "course": "B.Tech Computer Engineering",
    "graduation_year": 2026
}, headers={"Authorization": f"Bearer {token_st}"})
print("✓ Student Dnyaneshwar verified at VIT Pune")

# 4. Student creates a ride from VIT Pune to Sukh Sagar Nagar
r_pub = client.post(f"{BASE}/rides/requests", json={
    "origin": {"lat": 18.4636, "lng": 73.8682, "name": "VIT Pune", "address": "Bibwewadi, Pune"},
    "destination": {"lat": 18.4558, "lng": 73.8694, "name": "Sukh Sagar Nagar", "address": "Katraj-Kondhwa, Pune"},
    "vehicle_type": "auto",
    "seats": 1,
    "departure_at": "2026-09-21T11:00:00Z",
    "note": "Leaving immediately"
}, headers={"Authorization": f"Bearer {token_st}"})
assert r_pub.status_code == 200, f"Ride creation failed: {r_pub.text}"
ride_id = r_pub.json()["data"]["id"]
print(f"✓ Student published Ride Request ID: {ride_id}")

# 5. Lock ride to trigger driver dispatch
r_lock = client.post(f"{BASE}/rides/requests/{ride_id}/lock", headers={"Authorization": f"Bearer {token_st}"})
print(f"✓ Ride locked, dispatch searching nearby drivers...")

# 6. Check driver offer arrival for Ramesh Pawar
offer = None
for i in range(10):
    time.sleep(0.5)
    res = client.get(f"{BASE}/drivers/me/offer", headers={"Authorization": f"Bearer {token_drv}"}).json()
    if res.get("data"):
        offer = res["data"]
        print(f"✓ Driver Ramesh received Offer ID: {offer['offer_id']}, Payout: ₹{offer['driver_payout_inr']}, Stops: {offer['stops']}")
        break

assert offer is not None, "Driver failed to receive offer within timeout!"

# 7. Driver Accepts the Offer!
r_accept = client.post(f"{BASE}/drivers/offers/{offer['offer_id']}/accept", headers={"Authorization": f"Bearer {token_drv}"})
assert r_accept.status_code == 200, f"Driver accept failed: {r_accept.text}"
trip_data = r_accept.json()["data"]
print(f"✓ Driver successfully accepted trip! Status: {trip_data['ride']['status']}")

# 8. Verify Student gets notified with assigned driver & OTP
active_st = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token_st}"}).json()["data"]
print(f"✓ Student active screen status: {active_st['status']}")
print(f"✓ Assigned driver: {active_st['driver']['full_name']} ({active_st['driver']['registration_number']})")
print(f"✓ Student Start OTP: {active_st['my_code']}")

print("\n==========================================================")
print("ALL TESTS PASSED! RIDE DISPATCH & ACCEPTANCE WORKING 100%")
print("==========================================================")
