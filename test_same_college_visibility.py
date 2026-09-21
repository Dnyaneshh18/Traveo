import httpx
from datetime import datetime, timezone, timedelta

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

print("==================================================")
print("TESTING SAME-COLLEGE ISOLATION & RIDE VISIBILITY")
print("==================================================")

# Colleges
colleges = client.get(f"{BASE}/colleges").json()["data"]
vit = next(c for c in colleges if c["code"] == "VIT")
coep = next(c for c in colleges if c["code"] == "COEP")

# --- STUDENT 1 (VIT Pune): Dnyaneshwar ---
r1 = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token1 = r1.json()["data"]["tokens"]["access_token"]
user1 = r1.json()["data"]["user"]
print(f"Student 1: {user1['full_name']} | College: {user1['student']['college']['name']}")

# Clean up any old active ride
r_old = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token1}"}).json()["data"]
if r_old:
    client.post(f"{BASE}/rides/requests/{r_old['id']}/cancel", json={"reason": "cleanup"}, headers={"Authorization": f"Bearer {token1}"})

# Student 1 creates a ride from VIT to Amba Mata Mandir
dep_time = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
r_pub = client.post(f"{BASE}/rides/requests", json={
    "origin": {"lat": 18.4636, "lng": 73.8682, "name": "VIT Pune", "address": "Bibwewadi, Pune"},
    "destination": {"lat": 18.4558, "lng": 73.8694, "name": "Amba Mata Mandir", "address": "Bibwewadi, Pune"},
    "vehicle_type": "auto",
    "seats": 1,
    "departure_at": dep_time,
    "note": "Leaving after college lecture"
}, headers={"Authorization": f"Bearer {token1}"})
assert r_pub.status_code == 200, f"Publish failed: {r_pub.text}"
ride1_id = r_pub.json()["data"]["id"]
print(f"✓ Student 1 created Ride ID: {ride1_id}")

# --- STUDENT 2 (SAME COLLEGE: VIT Pune): Neha Patil ---
phone2 = "9822114455"
client.post(f"{BASE}/auth/otp/request", json={"phone": phone2, "role": "student"})
r2 = client.post(f"{BASE}/auth/otp/verify", json={"phone": phone2, "otp": "123456", "role": "student"})
token2 = r2.json()["data"]["tokens"]["access_token"]
# Ensure registered to VIT
client.post(f"{BASE}/students/register", json={
    "full_name": "Neha Patil",
    "college_id": vit["id"],
    "college_name_on_id": "Vishwakarma Institute of Technology",
    "college_id_number": "12410999",
    "gender": "female"
}, headers={"Authorization": f"Bearer {token2}"})

# Student 2 views the Feed
feed2 = client.get(f"{BASE}/rides/feed", headers={"Authorization": f"Bearer {token2}"}).json()["data"]
visible_ride_ids_2 = [item["request"]["id"] for item in feed2]
print(f"Feed for Student 2 ({vit['name']}): found {len(feed2)} rides")
assert ride1_id in visible_ride_ids_2, f"Ride {ride1_id} SHOULD be visible to fellow VIT student!"
print(f"✓ SUCCESS: Ride created by Dnyaneshwar IS VISIBLE to fellow VIT student Neha!")

# --- STUDENT 3 (DIFFERENT COLLEGE: COEP Pune): Rahul Joshi ---
phone3 = "9822336699"
client.post(f"{BASE}/auth/otp/request", json={"phone": phone3, "role": "student"})
r3 = client.post(f"{BASE}/auth/otp/verify", json={"phone": phone3, "otp": "123456", "role": "student"})
token3 = r3.json()["data"]["tokens"]["access_token"]
# Register to COEP
client.post(f"{BASE}/students/register", json={
    "full_name": "Rahul Joshi",
    "college_id": coep["id"],
    "college_name_on_id": "College of Engineering Pune",
    "college_id_number": "112003045",
    "gender": "male"
}, headers={"Authorization": f"Bearer {token3}"})

# Student 3 views the Feed
feed3 = client.get(f"{BASE}/rides/feed", headers={"Authorization": f"Bearer {token3}"}).json()["data"]
visible_ride_ids_3 = [item["request"]["id"] for item in feed3]
print(f"Feed for Student 3 ({coep['name']}): found {len(feed3)} rides")
assert ride1_id not in visible_ride_ids_3, f"Ride {ride1_id} MUST NOT be visible to COEP student!"
print(f"✓ SUCCESS: Strict College Isolation confirmed! COEP student CANNOT see VIT ride.")

# Clean up
client.post(f"{BASE}/rides/requests/{ride1_id}/cancel", json={"reason": "test complete"}, headers={"Authorization": f"Bearer {token1}"})
print("\nAll visibility & college isolation assertions PASSED perfectly!")
