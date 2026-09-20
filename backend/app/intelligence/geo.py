"""
Traveo Ride Intelligence Engine — Geospatial Math & Route Helpers

Pure mathematical functions for Haversine distance, bounding box calculations,
bearing vectors, and detour distance estimations.
No database or I/O dependencies.
"""

from __future__ import annotations

import math


EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on the Earth
    in kilometers using the Haversine formula.
    """
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def haversine_distance_meters(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate distance in meters."""
    return haversine_distance_km(lat1, lon1, lat2, lon2) * 1000.0


def calculate_bounding_box(
    lat: float, lon: float, radius_km: float
) -> tuple[float, float, float, float]:
    """
    Calculate a bounding box (min_lat, max_lat, min_lon, max_lon)
    around a point for efficient database index filtering before Haversine refinement.
    """
    lat_delta = radius_km / EARTH_RADIUS_KM
    # Account for longitude contraction at higher latitudes
    lat_rad = math.radians(lat)
    lon_delta = radius_km / (EARTH_RADIUS_KM * math.cos(lat_rad))

    min_lat = lat - math.degrees(lat_delta)
    max_lat = lat + math.degrees(lat_delta)
    min_lon = lon - math.degrees(lon_delta)
    max_lon = lon + math.degrees(lon_delta)

    return min_lat, max_lat, min_lon, max_lon


def calculate_bearing(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate compass bearing from point 1 to point 2 in degrees (0-360).
    Used to check if two ride requests are heading in a similar direction.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(
        phi2
    ) * math.cos(delta_lambda)

    theta = math.atan2(y, x)
    bearing = (math.degrees(theta) + 360.0) % 360.0
    return bearing


def bearing_difference(bearing1: float, bearing2: float) -> float:
    """
    Calculate angular difference between two bearings in degrees (0-180).
    A difference close to 0 indicates identical direction.
    """
    diff = abs(bearing1 - bearing2) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def estimate_travel_time_minutes(
    distance_km: float, average_speed_kmh: float = 30.0
) -> float:
    """Estimate travel time in minutes based on average urban speed."""
    if average_speed_kmh <= 0:
        return 0.0
    return (distance_km / average_speed_kmh) * 60.0
