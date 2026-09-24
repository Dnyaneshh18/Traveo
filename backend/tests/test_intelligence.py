"""Unit tests for the pure Ride Intelligence Engine functions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.geo import LatLng, decode_polyline, encode_polyline, haversine_km, point_to_path_km
from app.intelligence.dispatch import DriverCandidate, rank_drivers, vehicle_compatible
from app.intelligence.fare import estimate_total, split_fare
from app.intelligence.identity import check_identity, name_similarity
from app.intelligence.matching import CandidateTrip, MatchingConfig, RequestSnapshot, evaluate_match
from app.intelligence.routing import MemberTrip, optimise_stops, sequence_numbers
from app.models.enums import VehicleType

COEP = LatLng(18.5293, 73.8567)
KOTHRUD = LatLng(18.5074, 73.8077)
HINJEWADI = LatLng(18.5912, 73.7389)
KATRAJ = LatLng(18.4480, 73.8580)
NAL_STOP = LatLng(18.5060, 73.8310)  # on the COEP→Kothrud corridor


def test_haversine_and_polyline_roundtrip():
    d = haversine_km(COEP.lat, COEP.lng, KOTHRUD.lat, KOTHRUD.lng)
    assert 5.0 < d < 6.5
    pts = [COEP, NAL_STOP, KOTHRUD]
    enc = encode_polyline(pts)
    dec = decode_polyline(enc)
    assert len(dec) == 3
    assert abs(dec[1].lat - NAL_STOP.lat) < 1e-5 and abs(dec[1].lng - NAL_STOP.lng) < 1e-5


def test_point_to_path_distance():
    d, pos = point_to_path_km(NAL_STOP, [COEP, KOTHRUD])
    assert d < 1.5  # real roads curve; straight-line corridor is ~1.2 km away
    assert 0.2 < pos < 0.9


def test_matching_accepts_corridor_and_rejects_opposite_direction():
    now = datetime.now(UTC)
    snapshot = RequestSnapshot(origin=COEP, destination=KOTHRUD, departure_at=now, seats_available=2, polyline=encode_polyline([COEP, KOTHRUD]), direction="from_college", route_distance_km=6.0)
    good = evaluate_match(CandidateTrip(pickup=COEP, drop=NAL_STOP, departure_at=now + timedelta(minutes=5)), snapshot)
    assert good.compatible and good.score > 0.5

    far = evaluate_match(CandidateTrip(pickup=COEP, drop=HINJEWADI, departure_at=now), snapshot)
    assert not far.compatible and far.reason == "too_far_from_route"

    late = evaluate_match(CandidateTrip(pickup=COEP, drop=NAL_STOP, departure_at=now + timedelta(hours=2)), snapshot, MatchingConfig(time_window_min=25))
    assert not late.compatible and late.reason == "time_window"

    full = evaluate_match(CandidateTrip(pickup=COEP, drop=NAL_STOP, departure_at=now, seats=3), snapshot)
    assert not full.compatible and full.reason == "no_seats"


def test_routing_respects_pickup_before_drop():
    driver = LatLng(18.5350, 73.8600)
    trips = [
        MemberTrip("a", COEP, "COEP", KOTHRUD, "Kothrud"),
        MemberTrip("b", COEP, "COEP", NAL_STOP, "Nal Stop"),
        MemberTrip("c", LatLng(18.5200, 73.8450), "Deccan", KATRAJ, "Katraj"),
    ]
    stops = optimise_stops(driver, trips)
    seen = set()
    for s in stops:
        if s.kind == "drop":
            assert s.member_id in seen
        else:
            seen.add(s.member_id)
    pickup_order, drop_order = sequence_numbers(stops)
    assert pickup_order["a"] == pickup_order["b"]  # same physical stop (campus)
    assert set(drop_order) == {"a", "b", "c"}


def test_driver_ranking_prefers_close_high_rated_exact_vehicle():
    pickup = COEP
    cands = [
        DriverCandidate("near_auto", LatLng(18.5310, 73.8580), VehicleType.AUTO, 3, 4.8, 0.9, 80),
        DriverCandidate("far_auto", LatLng(18.5500, 73.8800), VehicleType.AUTO, 3, 4.9, 0.9, 80),
        DriverCandidate("near_bike", LatLng(18.5300, 73.8570), VehicleType.BIKE, 1, 5.0, 1.0, 100),
        DriverCandidate("near_xl", LatLng(18.5300, 73.8570), VehicleType.CAR_XL, 6, 4.9, 0.9, 80),
    ]
    ranked = rank_drivers(pickup, cands, VehicleType.AUTO, 2, 3.0)
    ids = [r.candidate.user_id for r in ranked]
    assert "near_bike" not in ids
    assert ids[0] == "near_auto"
    assert vehicle_compatible(VehicleType.CAR, VehicleType.CAR_XL, 4)
    assert not vehicle_compatible(VehicleType.CAR_XL, VehicleType.CAR, 5)


def test_fare_split_is_distance_weighted_and_sums_to_total():
    total = estimate_total(VehicleType.CAR, 10.0, 30.0)
    assert total >= 70
    breakdown = split_fare(VehicleType.CAR, total, {"a": 10.0, "b": 5.0, "c": 2.0}, 8.0)
    assert sum(breakdown.shares.values()) == breakdown.total
    assert breakdown.shares["a"] > breakdown.shares["b"] >= breakdown.shares["c"]
    assert breakdown.driver_payout + breakdown.platform_fee == breakdown.total


def test_identity_name_matching_rules():
    assert name_similarity("College of Engineering, Pune", "COEP Technological University") < 0.8
    assert name_similarity("College of Engineering Pune", "College of Engineering Pune") == 1.0
    assert name_similarity("Pune Inst. of Computer Tech", "Pune Institute of Computer Technology") >= 0.8
    assert name_similarity("PICT", "Pune Institute of Computer Technology") >= 0.8  # acronym
    assert name_similarity("Fergusson College", "Symbiosis Institute of Technology") < 0.5

    ok = check_identity(typed_college_name="Pune Institute of Computer Technology", college_name="Pune Institute of Computer Technology", aliases=["PICT Pune"], college_id_number="C2K221234", id_pattern=r"^[CIEA]2K\d{2}[A-Z0-9]{3,8}$|^\d{5,8}$")
    assert ok.auto_verified
    bad_name = check_identity(typed_college_name="MIT World Peace University", college_name="Pune Institute of Computer Technology", aliases=[], college_id_number="C2K221234", id_pattern=None)
    assert not bad_name.name_matches
    bad_id = check_identity(typed_college_name="PICT Pune", college_name="Pune Institute of Computer Technology", aliases=["PICT Pune"], college_id_number="hello", id_pattern=r"^[CIEA]2K\d{2}[A-Z0-9]{3,8}$")
    assert bad_id.name_matches and not bad_id.id_format_valid
