"""
Traveo — Geospatial utilities used by the Ride Intelligence Engine.

Pure functions, no I/O:  haversine distance, bearings, polyline encoding,
point-to-route distance and detour estimation.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True, slots=True)
class LatLng:
    lat: float
    lng: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.lat, self.lng)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two WGS-84 points in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def distance_km(a: LatLng, b: LatLng) -> float:
    return haversine_km(a.lat, a.lng, b.lat, b.lng)


def bearing_deg(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial bearing from point 1 to point 2 (0° = north, clockwise)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlmb = math.radians(lng2 - lng1)
    x = math.sin(dlmb) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlmb)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def bearing_difference(b1: float, b2: float) -> float:
    d = abs(b1 - b2) % 360.0
    return 360.0 - d if d > 180.0 else d


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """(min_lat, min_lng, max_lat, max_lng) square around a point – cheap DB pre-filter."""
    dlat = radius_km / 110.574
    dlng = radius_km / (111.320 * max(0.01, math.cos(math.radians(lat))))
    return (lat - dlat, lng - dlng, lat + dlat, lng + dlng)


def path_length_km(points: Sequence[LatLng]) -> float:
    return sum(distance_km(points[i], points[i + 1]) for i in range(len(points) - 1))


def interpolate(a: LatLng, b: LatLng, fraction: float) -> LatLng:
    return LatLng(a.lat + (b.lat - a.lat) * fraction, a.lng + (b.lng - a.lng) * fraction)


def point_to_segment_km(p: LatLng, a: LatLng, b: LatLng) -> tuple[float, float]:
    """
    Distance from P to segment AB (km) using an equirectangular projection –
    accurate for the city-scale distances Traveo works with.
    Returns (distance_km, t) where t∈[0,1] is the projection position along AB.
    """
    lat0 = math.radians((a.lat + b.lat + p.lat) / 3)
    kx = 111.320 * math.cos(lat0)
    ky = 110.574
    ax, ay = a.lng * kx, a.lat * ky
    bx, by = b.lng * kx, b.lat * ky
    px, py = p.lng * kx, p.lat * ky
    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return math.hypot(px - ax, py - ay), 0.0
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy), t


def point_to_path_km(p: LatLng, path: Sequence[LatLng]) -> tuple[float, float]:
    """
    Minimum distance from P to a polyline and the fractional position (0..1)
    along the polyline of the closest point.
    """
    if not path:
        return float("inf"), 0.0
    if len(path) == 1:
        return distance_km(p, path[0]), 0.0
    total = path_length_km(path) or 1e-9
    best_d, best_pos, walked = float("inf"), 0.0, 0.0
    for i in range(len(path) - 1):
        seg_len = distance_km(path[i], path[i + 1])
        d, t = point_to_segment_km(p, path[i], path[i + 1])
        if d < best_d:
            best_d, best_pos = d, (walked + t * seg_len) / total
        walked += seg_len
    return best_d, best_pos


def detour_km(origin: LatLng, destination: LatLng, via: LatLng) -> float:
    """Extra distance incurred by visiting `via` between origin and destination."""
    direct = distance_km(origin, destination)
    return max(0.0, distance_km(origin, via) + distance_km(via, destination) - direct)


# ── Google/OSRM encoded polylines ─────────────────────────────────
def encode_polyline(points: Iterable[LatLng], precision: int = 5) -> str:
    factor = 10**precision
    output: list[str] = []
    prev_lat = prev_lng = 0
    for p in points:
        lat, lng = round(p.lat * factor), round(p.lng * factor)
        for delta in (lat - prev_lat, lng - prev_lng):
            v = ~(delta << 1) if delta < 0 else delta << 1
            while v >= 0x20:
                output.append(chr((0x20 | (v & 0x1F)) + 63))
                v >>= 5
            output.append(chr(v + 63))
        prev_lat, prev_lng = lat, lng
    return "".join(output)


def decode_polyline(encoded: str, precision: int = 5) -> list[LatLng]:
    factor = 10**precision
    points: list[LatLng] = []
    index = lat = lng = 0
    while index < len(encoded):
        for coord in ("lat", "lng"):
            shift = result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if coord == "lat":
                lat += delta
            else:
                lng += delta
        points.append(LatLng(lat / factor, lng / factor))
    return points


def straight_polyline(a: LatLng, b: LatLng, steps: int = 12) -> list[LatLng]:
    """Fallback route geometry when no routing provider is configured."""
    return [interpolate(a, b, i / steps) for i in range(steps + 1)]
