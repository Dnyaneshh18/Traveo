import httpx

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

colleges = client.get(f"{BASE}/colleges").json()["data"]
vit = next(c for c in colleges if c["code"] == "VIT")

# Register 7972650026 as student Dnyaneshwar Vasant Patil
client.post(f"{BASE}/auth/otp/request", json={"phone": "7972650026", "role": "student"})
r = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token = r.json()["data"]["tokens"]["access_token"]
reg = client.post(f"{BASE}/students/register", json={
    "full_name": "Dnyaneshwar Vasant Patil",
    "college_id": vit["id"],
    "college_name_on_id": "Vishwakarma Institute of Technology",
    "college_id_number": "12410666",
    "gender": "male",
    "course": "B.Tech Computer Engineering",
    "graduation_year": 2026
}, headers={"Authorization": f"Bearer {token}"})
print("Registered Dnyaneshwar:", reg.status_code, reg.json()["data"]["full_name"])
