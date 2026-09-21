"""
End-to-end flow through the HTTP API (SQLite, local maps provider):

student A (COEP) creates a ride → student B (COEP, on-route) sees it in the feed & joins
→ student C (PICT) can NOT see it → creator locks → dispatcher offers → demo driver accepts
→ OTP boards the creator, matching code boards B → drops → completed → ratings & payments.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient

from tests.conftest import API, login, register_student

COEP = {"lat": 18.5293, "lng": 73.8567, "address": "COEP Technological University, Shivajinagar"}
KOTHRUD = {"lat": 18.5074, "lng": 73.8077, "address": "Kothrud Depot, Pune"}
NAL_STOP = {"lat": 18.5060, "lng": 73.8310, "address": "Nal Stop, Karve Road"}
HINJEWADI = {"lat": 18.5912, "lng": 73.7389, "address": "Hinjewadi Phase 1"}


@pytest.mark.asyncio
async def test_identity_rules_block_wrong_college_name(client: AsyncClient):
    session = await login(client, "+919811110001", "student")
    r = await client.get(f"{API}/colleges", params={"q": "PICT"})
    pict = next(c for c in r.json()["data"] if c["code"] == "PICT")
    r = await client.post(
        f"{API}/students/register",
        headers=session["headers"],
        json={"full_name": "Wrong Name", "college_id": pict["id"], "college_name_on_id": "MIT World Peace University", "college_id_number": "C2K221001"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "identity_mismatch"

    # Name matches but ID format doesn't → pending manual review, cannot create rides.
    r = await client.post(
        f"{API}/students/register",
        headers=session["headers"],
        json={"full_name": "Pending Student", "college_id": pict["id"], "college_name_on_id": "PICT Pune", "college_id_number": "hello-world"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["student"]["verification_status"] == "pending"
    r = await client.post(f"{API}/rides/requests", headers=session["headers"], json={"origin": COEP, "destination": KOTHRUD, "vehicle_type": "auto"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "student_not_verified"


@pytest.mark.asyncio
async def test_full_ride_lifecycle(client: AsyncClient):
    alice = await register_student(client, "+919811110002", "Alice Deshmukh", "COEP", "112003045", gender="female")
    bob = await register_student(client, "+919811110003", "Bob Patil", "COEP", "112003046")
    carol = await register_student(client, "+919811110004", "Carol Joshi", "PICT", "C2K221002")
    assert alice["user"]["student"]["verification_status"] == "verified"

    # Preview
    r = await client.post(f"{API}/rides/preview", headers=alice["headers"], json={"origin": COEP, "destination": KOTHRUD})
    assert r.status_code == 200, r.text
    preview = r.json()["data"]
    assert preview["direction"] == "from_college"
    assert len(preview["options"]) == 4

    # Trip must touch campus
    r = await client.post(f"{API}/rides/requests", headers=alice["headers"], json={"origin": HINJEWADI, "destination": KOTHRUD, "vehicle_type": "auto"})
    assert r.status_code == 422

    # Create (auto: 3 seats)
    r = await client.post(f"{API}/rides/requests", headers=alice["headers"], json={"origin": COEP, "destination": KOTHRUD, "vehicle_type": "auto", "note": "Leaving after 5pm lecture"})
    assert r.status_code == 200, r.text
    req = r.json()["data"]
    request_id = req["id"]
    assert req["status"] == "open" and req["seats_available"] == 2 and req["my_role"] == "creator"

    # Only one active ride per student
    r = await client.post(f"{API}/rides/requests", headers=alice["headers"], json={"origin": COEP, "destination": KOTHRUD, "vehicle_type": "car"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "active_ride_exists"

    # Bob (same college, on-route) sees it; Carol (PICT) does not.
    r = await client.get(f"{API}/rides/feed", headers=bob["headers"], params={"pickup_lat": COEP["lat"], "pickup_lng": COEP["lng"], "drop_lat": NAL_STOP["lat"], "drop_lng": NAL_STOP["lng"]})
    feed = r.json()["data"]
    assert [i["request"]["id"] for i in feed] == [request_id]
    assert feed[0]["match"]["compatible"] is True
    r = await client.get(f"{API}/rides/feed", headers=carol["headers"])
    assert all(i["request"]["id"] != request_id for i in r.json()["data"])
    # Carol can't join even with the id.
    r = await client.post(f"{API}/rides/requests/{request_id}/join", headers=carol["headers"], json={"pickup": COEP, "drop": NAL_STOP})
    assert r.status_code == 403 and r.json()["error"]["code"] == "not_same_college"

    # Off-route join is rejected.
    r = await client.post(f"{API}/rides/requests/{request_id}/join", headers=bob["headers"], json={"pickup": COEP, "drop": HINJEWADI})
    assert r.status_code == 422 and r.json()["error"]["code"] == "route_not_compatible"

    # Bob joins.
    r = await client.post(f"{API}/rides/requests/{request_id}/join", headers=bob["headers"], json={"pickup": COEP, "drop": NAL_STOP})
    assert r.status_code == 200, r.text
    joined = r.json()["data"]
    assert joined["seats_available"] == 1 and joined["my_role"] == "member"
    assert joined["my_fare_share_inr"] is not None

    # Bob leaves and rejoins (allowed while open)
    r = await client.post(f"{API}/rides/requests/{request_id}/leave", headers=bob["headers"])
    assert r.status_code == 200
    r = await client.post(f"{API}/rides/requests/{request_id}/join", headers=bob["headers"], json={"pickup": COEP, "drop": NAL_STOP})
    assert r.status_code == 200, r.text

    # Creator says go without a full vehicle → LOCKED → dispatch.
    r = await client.post(f"{API}/rides/requests/{request_id}/lock", headers=alice["headers"])
    assert r.status_code == 200, r.text
    assert r.json()["data"]["status"] == "locked"

    # A demo driver near COEP should receive an offer.
    driver = await login(client, "+919900000001", "driver")
    offer = None
    for _ in range(40):
        r = await client.get(f"{API}/drivers/me/offer", headers=driver["headers"])
        offer = r.json()["data"]
        if offer:
            break
        await asyncio.sleep(0.25)
    if not offer:
        # The ranking may have picked another demo driver first – find whoever holds the pending offer.
        for phone in ("+919900000002", "+919900000003", "+919900000004", "+919900000005"):
            d = await login(client, phone, "driver")
            r = await client.get(f"{API}/drivers/me/offer", headers=d["headers"])
            if r.json()["data"]:
                driver, offer = d, r.json()["data"]
                break
    assert offer, "dispatcher did not produce an offer"
    assert offer["request_id"] == request_id and offer["passenger_count"] == 2

    r = await client.post(f"{API}/drivers/offers/{offer['offer_id']}/accept", headers=driver["headers"])
    assert r.status_code == 200, r.text
    trip = r.json()["data"]
    assert trip["ride"]["status"] == "driver_assigned"
    assert trip["next_stop"]["kind"] == "pickup"
    ride_id = trip["ride"]["id"]

    # Passengers see driver + their own codes.
    r = await client.get(f"{API}/rides/active", headers=alice["headers"])
    a_view = r.json()["data"]
    assert a_view["status"] == "driver_assigned" and a_view["driver"]["registration_number"]
    assert a_view["my_code_kind"] == "otp" and len(a_view["my_code"]) == 4
    r = await client.get(f"{API}/rides/active", headers=bob["headers"])
    b_view = r.json()["data"]
    assert b_view["my_code_kind"] == "matching_code" and b_view["my_code"].startswith("TRV-")
    assert b_view["members"][0]["pickup_order"] == b_view["members"][1]["pickup_order"]  # same campus stop

    # Wrong code rejected; OTP boards Alice; matching code boards Bob.
    r = await client.post(f"{API}/drivers/trips/{ride_id}/arrived", headers=driver["headers"])
    assert r.status_code == 200
    r = await client.post(f"{API}/drivers/trips/{ride_id}/verify", headers=driver["headers"], json={"code": "0000"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "code_invalid"
    r = await client.post(f"{API}/drivers/trips/{ride_id}/verify", headers=driver["headers"], json={"code": a_view["my_code"]})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["ride"]["status"] == "in_progress"
    r = await client.post(f"{API}/drivers/trips/{ride_id}/verify", headers=driver["headers"], json={"code": b_view["my_code"].lower()})
    assert r.status_code == 200, r.text
    trip = r.json()["data"]
    assert trip["passengers_on_board"] == 2
    assert all(s["kind"] == "drop" for s in trip["stops"])

    # Drops in order → completed.
    for stop in list(trip["stops"]):
        r = await client.post(f"{API}/drivers/trips/{ride_id}/drop", headers=driver["headers"], json={"member_id": stop["member_id"]})
        assert r.status_code == 200, r.text
    final = r.json()["data"]
    assert final["ride"]["status"] == "completed"
    assert final["ride"]["total_fare_inr"] > 0

    # Driver is free again, earnings updated.
    r = await client.get(f"{API}/drivers/me/earnings", headers=driver["headers"])
    assert r.json()["data"]["today_rides"] >= 1
    r = await client.get(f"{API}/drivers/me/trip", headers=driver["headers"])
    assert r.json()["data"] is None

    # Payments + ratings
    r = await client.get(f"{API}/rides/{ride_id}/payments", headers=alice["headers"])
    assert len(r.json()["data"]) == 2
    r = await client.post(f"{API}/rides/{ride_id}/payments/confirm", headers=alice["headers"], json={"method": "upi", "reference": "UPI123"})
    assert r.status_code == 200
    r = await client.post(f"{API}/ratings", headers=alice["headers"], json={"ride_id": ride_id, "ratee_id": driver["user"]["id"], "stars": 5})
    assert r.status_code == 200, r.text
    r = await client.post(f"{API}/ratings", headers=alice["headers"], json={"ride_id": ride_id, "ratee_id": driver["user"]["id"], "stars": 5})
    assert r.status_code == 409

    # History
    r = await client.get(f"{API}/rides/history", headers=bob["headers"])
    assert r.json()["data"][0]["id"] == request_id
    r = await client.get(f"{API}/rides/active", headers=alice["headers"])
    assert r.json()["data"] is None


@pytest.mark.asyncio
async def test_creator_transfer_and_cancel(client: AsyncClient):
    dan = await register_student(client, "+919811110005", "Dan Kale", "VIT", "12210123")
    eve = await register_student(client, "+919811110006", "Eve Rane", "VIT", "12210124", gender="female")
    r = await client.get(f"{API}/colleges", params={"q": "VIT"})
    vit = next(c for c in r.json()["data"] if c["code"] == "VIT")
    origin = {"lat": vit["latitude"], "lng": vit["longitude"], "address": vit["name"]}
    dest = {"lat": 18.4480, "lng": 73.8580, "address": "Katraj"}
    r = await client.post(f"{API}/rides/requests", headers=dan["headers"], json={"origin": origin, "destination": dest, "vehicle_type": "car"})
    assert r.status_code == 200, r.text
    rid = r.json()["data"]["id"]
    r = await client.post(f"{API}/rides/requests/{rid}/join", headers=eve["headers"], json={"pickup": origin, "drop": {"lat": 18.4570, "lng": 73.8625, "address": "Bharati Vidyapeeth, Dhankawadi"}})
    assert r.status_code == 200, r.text
    # Creator leaves → Eve inherits the group.
    r = await client.post(f"{API}/rides/requests/{rid}/leave", headers=dan["headers"])
    assert r.status_code == 200
    r = await client.get(f"{API}/rides/active", headers=eve["headers"])
    assert r.json()["data"]["my_role"] == "creator"
    # Eve cancels the group.
    r = await client.post(f"{API}/rides/requests/{rid}/cancel", headers=eve["headers"], json={"reason": "plans changed"})
    assert r.status_code == 200
    r = await client.get(f"{API}/rides/requests/{rid}", headers=eve["headers"])
    assert r.json()["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_admin_endpoints(client: AsyncClient):
    r = await client.post(f"{API}/auth/admin/login", json={"email": "admin@traveo.app", "password": "Admin@123"})
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['data']['tokens']['access_token']}"}
    r = await client.get(f"{API}/admin/dashboard", headers=headers)
    assert r.status_code == 200 and r.json()["data"]["students"]["total"] >= 3
    r = await client.get(f"{API}/admin/students", headers=headers, params={"status": "pending"})
    pending = r.json()["data"]
    assert pending
    r = await client.post(f"{API}/admin/students/{pending[0]['id']}/verify", headers=headers, json={"status": "verified", "note": "ID card checked"})
    assert r.status_code == 200
    r = await client.get(f"{API}/admin/live", headers=headers)
    assert r.status_code == 200 and "drivers" in r.json()["data"]
    r = await client.get(f"{API}/admin/config", headers=headers)
    assert any(c["key"] == "dispatch.offer_timeout_seconds" for c in r.json()["data"])
    r = await client.put(f"{API}/admin/config", headers=headers, json={"key": "fare.platform_fee_percent", "value": 10})
    assert r.status_code == 200
    # Non-admin blocked
    student = await login(client, "+919811110002", "student")
    r = await client.get(f"{API}/admin/dashboard", headers=student["headers"])
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_driver_cancel_triggers_redispatch_and_no_driver_retry(client: AsyncClient):
    fay = await register_student(client, "+919811110007", "Fay Naik", "TRAVEO_DEMO", "DEMO1001")
    r = await client.get(f"{API}/colleges", params={"q": "TRAVEO_DEMO"})
    demo = next(c for c in r.json()["data"] if c["code"] == "TRAVEO_DEMO")
    origin = {"lat": demo["latitude"], "lng": demo["longitude"], "address": demo["name"]}
    dest = {"lat": 18.5975, "lng": 73.7620, "address": "Wakad"}
    r = await client.post(f"{API}/rides/requests", headers=fay["headers"], json={"origin": origin, "destination": dest, "vehicle_type": "car"})
    assert r.status_code == 200, r.text
    rid = r.json()["data"]["id"]
    r = await client.post(f"{API}/rides/requests/{rid}/lock", headers=fay["headers"])
    assert r.status_code == 200

    # Only demo driver #5 (Hinjewadi) is close enough.
    driver = await login(client, "+919900000005", "driver")
    offer = None
    for _ in range(40):
        offer = (await client.get(f"{API}/drivers/me/offer", headers=driver["headers"])).json()["data"]
        if offer:
            break
        await asyncio.sleep(0.25)
    assert offer and offer["request_id"] == rid
    r = await client.post(f"{API}/drivers/offers/{offer['offer_id']}/accept", headers=driver["headers"])
    assert r.status_code == 200, r.text
    ride_id = r.json()["data"]["ride"]["id"]

    # Driver bails before pickup → group goes back to dispatch.
    r = await client.post(f"{API}/drivers/trips/{ride_id}/cancel", headers=driver["headers"], json={"reason": "vehicle breakdown"})
    assert r.status_code == 200, r.text
    r = await client.get(f"{API}/rides/active", headers=fay["headers"])
    view = r.json()["data"]
    assert view["status"] == "locked" and view["driver"] is None and view["my_code"] is None
    r = await client.get(f"{API}/drivers/me/trip", headers=driver["headers"])
    assert r.json()["data"] is None

    # Take the only nearby driver offline → dispatcher eventually gives up → creator retries.
    r = await client.put(f"{API}/drivers/me/status", headers=driver["headers"], json={"online": False})
    assert r.status_code == 200
    for _ in range(80):
        view = (await client.get(f"{API}/rides/active", headers=fay["headers"])).json()["data"]
        if view["status"] == "no_driver":
            break
        await asyncio.sleep(0.25)
    assert view["status"] == "no_driver", view["status"]
    assert view["dispatch"]["max_radius_km"] == 8.0
    r = await client.put(f"{API}/drivers/me/status", headers=driver["headers"], json={"online": True, "lat": 18.5900, "lng": 73.7400})
    r = await client.post(f"{API}/rides/requests/{rid}/retry", headers=fay["headers"])
    assert r.status_code == 200 and r.json()["data"]["status"] == "locked"
    offer = None
    for _ in range(40):
        offer = (await client.get(f"{API}/drivers/me/offer", headers=driver["headers"])).json()["data"]
        if offer:
            break
        await asyncio.sleep(0.25)
    assert offer and offer["request_id"] == rid
    r = await client.post(f"{API}/drivers/offers/{offer['offer_id']}/reject", headers=driver["headers"], json={"reason": "too far"})
    assert r.status_code == 200
    r = await client.post(f"{API}/rides/requests/{rid}/cancel", headers=fay["headers"])
    assert r.status_code == 200
    r = await client.get(f"{API}/rides/requests/{rid}/timeline", headers=fay["headers"])
    events = [e["event"] for e in r.json()["data"]]
    assert "driver_cancelled" in events and "no_driver" in events and "offer_rejected" in events and events[-1] == "cancelled"
