import httpx
import time

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client()

print("--- 1. Login Rohan Sharma (Ride Lead) ---")
r_rohan = client.post(f"{BASE}/auth/otp/verify", json={"phone": "9812345678", "otp": "123456", "role": "student"})
token_rohan = r_rohan.json()["data"]["tokens"]["access_token"]
print("Rohan logged in successfully")

# Get active ride
active = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token_rohan}"}).json()["data"]
print("Active ride status:", active["status"], "ID:", active["id"])

print("\n--- 2. Lock / Call Driver ---")
lock_res = client.post(f"{BASE}/rides/requests/{active['id']}/lock", headers={"Authorization": f"Bearer {token_rohan}"})
print("Lock response status:", lock_res.status_code, "body:", lock_res.json()["data"]["status"] if lock_res.status_code == 200 else lock_res.text)

time.sleep(1)

print("\n--- 3. Check Driver Offer for Driver Vikas (+919900000004) ---")
r_drv = client.post(f"{BASE}/auth/otp/verify", json={"phone": "9900000004", "otp": "123456", "role": "driver"})
token_drv = r_drv.json()["data"]["tokens"]["access_token"]
offer = client.get(f"{BASE}/drivers/me/offer", headers={"Authorization": f"Bearer {token_drv}"}).json()["data"]
print("Driver Vikas offer:", offer["id"] if offer else "No offer")

if offer:
    print("\n--- 4. Driver Accepts Offer ---")
    accept_res = client.post(f"{BASE}/drivers/offers/{offer['id']}/accept", headers={"Authorization": f"Bearer {token_drv}"})
    print("Driver accepted trip:", accept_res.json()["data"]["status"] if accept_res.status_code == 200 else accept_res.text)

print("\n--- 5. Check Dnyaneshwar's (Rider DV) active ride now ---")
r_dn = client.post(f"{BASE}/auth/otp/verify", json={"phone": "7972650026", "otp": "123456", "role": "student"})
token_dn = r_dn.json()["data"]["tokens"]["access_token"]
active_dn = client.get(f"{BASE}/rides/active", headers={"Authorization": f"Bearer {token_dn}"}).json()["data"]
print("Dnyaneshwar's ride status:", active_dn["status"])
print("Driver assigned:", active_dn.get("driver") or (active_dn.get("rides", [{}])[0].get("driver") if active_dn.get("rides") else "None"))
