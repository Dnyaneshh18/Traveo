"""Maps proxy — keeps Mappls REST keys server-side; apps call these endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.core.deps import Current
from app.core.geo import LatLng
from app.maps.provider import get_maps_provider
from app.schemas.common import APIModel, GeoPoint, ok

router = APIRouter(prefix="/maps", tags=["Maps"])
settings = get_settings()


class RouteIn(APIModel):
    waypoints: list[GeoPoint]


@router.get("/autosuggest", summary="Place search (Mappls Atlas / offline index)")
async def autosuggest(
    q: str = Query(min_length=2, max_length=80),
    lat: float | None = None,
    lng: float | None = None,
):
    near = LatLng(lat, lng) if lat is not None and lng is not None else None
    results = await get_maps_provider().autosuggest(q, near)
    return ok([r.to_dict() for r in results], meta={"provider": get_maps_provider().name})


@router.get("/reverse-geocode")
async def reverse_geocode(lat: float, lng: float):
    address = await get_maps_provider().reverse_geocode(LatLng(lat, lng))
    return ok({"lat": lat, "lng": lng, "address": address})


@router.post("/route", summary="Route geometry through waypoints")
async def route(body: RouteIn):
    if len(body.waypoints) < 2:
        return ok(None)
    r = await get_maps_provider().route([LatLng(p.lat, p.lng) for p in body.waypoints])
    return ok({"distance_km": r.distance_km, "duration_min": r.duration_min, "polyline": r.polyline, "legs": r.legs, "provider": r.provider})


@router.get("/config", summary="Client map configuration")
async def map_config():
    return ok(
        {
            "provider": "mappls" if settings.mappls_enabled else "local",
            "default_center": {"lat": 18.5204, "lng": 73.8567},
            "default_zoom": 12,
            "attribution": "© Mappls (MapmyIndia)" if settings.mappls_enabled else "© OpenStreetMap contributors",
        }
    )
