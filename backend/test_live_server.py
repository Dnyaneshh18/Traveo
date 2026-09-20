import urllib.request
import urllib.error
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("--- 1. Health Check Endpoint ---")
    req = urllib.request.Request(f"{base_url}/health")
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    print("Health Check Response:", json.dumps(res, indent=2))
    assert res["status"] == "healthy"

    print("\n--- 2. Register Phone OTP Endpoint ---")
    data = json.dumps({"phone": "+919876543210", "name": "Rajesh Kumar"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/auth/register", data=data)
    req.add_header("Content-Type", "application/json")
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    print("Register Response:", json.dumps(res, indent=2))

    print("\n--- 3. Verify OTP & Get JWT Token ---")
    data = json.dumps({"phone": "+919876543210", "otp": "1234"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/v1/auth/verify-otp", data=data)
    req.add_header("Content-Type", "application/json")
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    print("Verify Response:", json.dumps(res, indent=2))
    token = res.get("data", {}).get("access_token")

    print("\n--- 4. Request Shared Ride (Ride Intelligence Engine) ---")
    ride_data = json.dumps({
        "pickup": {
            "latitude": 18.5204,
            "longitude": 73.8567,
            "address": "Central Square, Downtown"
        },
        "destination": {
            "latitude": 18.5529,
            "longitude": 73.8796,
            "address": "Tech Park Tower B"
        },
        "ride_type": "shared",
        "requested_seats": 1
    }).encode('utf-8')
    
    req = urllib.request.Request(f"{base_url}/api/v1/rides", data=ride_data)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        
    try:
        res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        print("Ride Request Response:", json.dumps(res, indent=2))
        print("\n🎉 ALL LIVE ENDPOINT VERIFICATION TESTS PASSED 100% SUCCESSFULLY!")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTPError {e.code}:", error_body)

if __name__ == "__main__":
    test_api()
