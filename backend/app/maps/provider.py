"""
Traveo — Maps provider abstraction.

`MapsProvider` is the single interface the rest of the backend uses for
routing, distance matrices, place search and geocoding.  Two implementations:

* `MapplsProvider` – MapmyIndia / Mappls REST APIs (routing, distance matrix,
  autosuggest, reverse geocode).  Used automatically when `MAPPLS_REST_KEY`
  is configured.
* `LocalProvider`  – deterministic offline fallback (haversine + average
  urban speeds + built-in Pune place index).  Keeps the whole platform working
  with zero external dependencies, and acts as a graceful degradation path if
  Mappls is unreachable.

The mobile apps render the map with the Mappls React-Native SDK directly; the
backend only performs server-side computations (route geometry for groups,
ETA, fare, dispatch ranking).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.core.geo import LatLng, decode_polyline, encode_polyline, haversine_km, straight_polyline
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

AVERAGE_URBAN_SPEED_KMPH = 22.0
ROAD_FACTOR = 1.28  # haversine → typical road distance in Indian cities


@dataclass(slots=True)
class RouteResult:
    distance_km: float
    duration_min: float
    polyline: str  # encoded polyline (precision 5)
    legs: list[dict[str, float]] = field(default_factory=list)  # per leg distance/duration
    provider: str = "local"

    def points(self) -> list[LatLng]:
        return decode_polyline(self.polyline)


@dataclass(slots=True)
class PlaceSuggestion:
    name: str
    address: str
    lat: float | None
    lng: float | None
    place_id: str | None = None  # Mappls eLoc / pin
    category: str | None = None
    distance_km: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
            "place_id": self.place_id,
            "category": self.category,
            "distance_km": self.distance_km,
        }


class MapsProvider(Protocol):
    name: str

    async def route(self, waypoints: list[LatLng]) -> RouteResult: ...

    async def distance_matrix(self, origins: list[LatLng], destinations: list[LatLng]) -> list[list[tuple[float, float]]]:
        """Returns matrix[i][j] = (distance_km, duration_min)."""
        ...

    async def autosuggest(self, query: str, near: LatLng | None) -> list[PlaceSuggestion]: ...

    async def reverse_geocode(self, point: LatLng) -> str: ...


# ══════════════════════════════════════════════════════════════════
# Local (offline) provider
# ══════════════════════════════════════════════════════════════════
class LocalProvider:
    name = "local"

    async def route(self, waypoints: list[LatLng]) -> RouteResult:
        pts: list[LatLng] = []
        legs = []
        total_km = 0.0
        for i in range(len(waypoints) - 1):
            seg_km = haversine_km(*waypoints[i].as_tuple(), *waypoints[i + 1].as_tuple()) * ROAD_FACTOR
            seg_min = seg_km / AVERAGE_URBAN_SPEED_KMPH * 60
            legs.append({"distance_km": round(seg_km, 3), "duration_min": round(seg_min, 1)})
            total_km += seg_km
            seg_points = straight_polyline(waypoints[i], waypoints[i + 1], steps=8)
            pts.extend(seg_points if i == 0 else seg_points[1:])
        if len(waypoints) == 1:
            pts = [waypoints[0]]
        return RouteResult(
            distance_km=round(total_km, 3),
            duration_min=round(total_km / AVERAGE_URBAN_SPEED_KMPH * 60, 1),
            polyline=encode_polyline(pts),
            legs=legs,
            provider=self.name,
        )

    async def distance_matrix(self, origins: list[LatLng], destinations: list[LatLng]) -> list[list[tuple[float, float]]]:
        out = []
        for o in origins:
            row = []
            for d in destinations:
                km = haversine_km(o.lat, o.lng, d.lat, d.lng) * ROAD_FACTOR
                row.append((round(km, 3), round(km / AVERAGE_URBAN_SPEED_KMPH * 60, 1)))
            out.append(row)
        return out

    async def autosuggest(self, query: str, near: LatLng | None) -> list[PlaceSuggestion]:
        # 1. Try public Nominatim for precise real-time geocoding
        try:
            params: dict[str, Any] = {
                "q": f"{query}, Pune, Maharashtra",
                "format": "jsonv2",
                "addressdetails": "1",
                "limit": "8",
                "countrycodes": "in",
            }
            if near:
                # Viewbox around user or college (approx 35km box around near)
                delta = 0.35
                params["viewbox"] = f"{near.lng-delta},{near.lat+delta},{near.lng+delta},{near.lat-delta}"
                params["bounded"] = "0"
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://nominatim.openstreetmap.org/search", params=params, headers={"User-Agent": "TraveoCampusStudentRide/2.0"})
                if res.status_code == 200:
                    data = res.json()
                    results: list[PlaceSuggestion] = []
                    for item in data:
                        lat = float(item["lat"])
                        lng = float(item["lon"])
                        name = item.get("name") or item.get("display_name", "").split(",")[0]
                        address = item.get("display_name", "")
                        dist = haversine_km(near.lat, near.lng, lat, lng) if near else None
                        results.append(
                            PlaceSuggestion(
                                name=name,
                                address=address,
                                lat=lat,
                                lng=lng,
                                place_id=str(item.get("place_id")),
                                category=item.get("type"),
                                distance_km=round(dist, 1) if dist is not None else None,
                            )
                        )
                    if results:
                        return results
        except Exception:
            pass

        # 2. Fallback to offline Pune place index
        from app.maps.places_index import search_places

        return search_places(query, near)

    async def reverse_geocode(self, point: LatLng) -> str:
        from app.maps.places_index import nearest_place_label

        return nearest_place_label(point)


# ══════════════════════════════════════════════════════════════════
# Mappls / MapmyIndia provider
# ══════════════════════════════════════════════════════════════════
class MapplsProvider:
    name = "mappls"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.MAPS_HTTP_TIMEOUT_SECONDS)
        self._token: str | None = None
        self._token_expiry = 0.0
        self._token_lock = asyncio.Lock()
        self._fallback = LocalProvider()

    # ── auth for Atlas (OAuth2 client credentials) ─────────────────
    async def _bearer(self) -> str | None:
        if not (settings.MAPPLS_CLIENT_ID and settings.MAPPLS_CLIENT_SECRET):
            return None
        async with self._token_lock:
            if self._token and time.time() < self._token_expiry - 30:
                return self._token
            try:
                resp = await self._client.post(
                    settings.MAPPLS_OUTPOST_TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.MAPPLS_CLIENT_ID,
                        "client_secret": settings.MAPPLS_CLIENT_SECRET,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded", "accept": "application/json"},
                )
                resp.raise_for_status()
                body = resp.json()
                self._token = body["access_token"]
                self._token_expiry = time.time() + float(body.get("expires_in", 86000))
                return self._token
            except Exception as exc:  # pragma: no cover - network
                logger.warning("mappls_token_failed", error=str(exc))
                return None

    @staticmethod
    def _coords(points: list[LatLng]) -> str:
        return ";".join(f"{p.lng:.6f},{p.lat:.6f}" for p in points)

    # ── routing ────────────────────────────────────────────────────
    async def route(self, waypoints: list[LatLng]) -> RouteResult:
        if len(waypoints) < 2:
            return await self._fallback.route(waypoints)
        url = (
            f"{settings.MAPPLS_ROUTE_BASE_URL}/route/direction/route_adv/driving/"
            f"{self._coords(waypoints)}"
        )
        params = {
            "access_token": settings.MAPPLS_REST_KEY,
            "geometries": "polyline",
            "overview": "full",
            "steps": "false",
            "rtype": 0,
        }
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            body = resp.json()
            if body.get("code") != "Ok" or not body.get("routes"):
                raise ValueError(body.get("code", "no_route"))
            r = body["routes"][0]
            legs = [
                {"distance_km": round(leg["distance"] / 1000, 3), "duration_min": round(leg["duration"] / 60, 1)}
                for leg in r.get("legs", [])
            ]
            return RouteResult(
                distance_km=round(r["distance"] / 1000, 3),
                duration_min=round(r["duration"] / 60, 1),
                polyline=r["geometry"],
                legs=legs,
                provider=self.name,
            )
        except Exception as exc:
            logger.warning("mappls_route_failed_fallback", error=str(exc))
            return await self._fallback.route(waypoints)

    # ── distance matrix ────────────────────────────────────────────
    async def distance_matrix(self, origins: list[LatLng], destinations: list[LatLng]) -> list[list[tuple[float, float]]]:
        if not origins or not destinations:
            return []
        all_points = origins + destinations
        url = f"{settings.MAPPLS_ROUTE_BASE_URL}/route/dm/distance_matrix_eta/driving/{self._coords(all_points)}"
        params = {
            "access_token": settings.MAPPLS_REST_KEY,
            "sources": ";".join(str(i) for i in range(len(origins))),
            "destinations": ";".join(str(len(origins) + j) for j in range(len(destinations))),
        }
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            body = resp.json()
            results = body.get("results") or body
            distances = results["distances"]
            durations = results["durations"]
            return [
                [(round(distances[i][j] / 1000, 3), round(durations[i][j] / 60, 1)) for j in range(len(destinations))]
                for i in range(len(origins))
            ]
        except Exception as exc:
            logger.warning("mappls_matrix_failed_fallback", error=str(exc))
            return await self._fallback.distance_matrix(origins, destinations)

    # ── places ─────────────────────────────────────────────────────
    async def autosuggest(self, query: str, near: LatLng | None) -> list[PlaceSuggestion]:
        token = await self._bearer()
        headers = {"Authorization": f"bearer {token}"} if token else {}
        params: dict[str, Any] = {"query": query}
        if not token:
            params["access_token"] = settings.MAPPLS_REST_KEY
        if near:
            params["location"] = f"{near.lat},{near.lng}"
        url = f"{settings.MAPPLS_ATLAS_BASE_URL}/api/places/search/json"
        try:
            resp = await self._client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            body = resp.json()
            out: list[PlaceSuggestion] = []
            for s in body.get("suggestedLocations", [])[:10]:
                lat = s.get("latitude")
                lng = s.get("longitude")
                out.append(
                    PlaceSuggestion(
                        name=s.get("placeName", ""),
                        address=s.get("placeAddress", ""),
                        lat=float(lat) if lat is not None else None,
                        lng=float(lng) if lng is not None else None,
                        place_id=s.get("eLoc") or s.get("mapplsPin"),
                        category=s.get("type"),
                        distance_km=(float(s["distance"]) / 1000) if s.get("distance") else None,
                    )
                )
            if out:
                return out
        except Exception as exc:
            logger.warning("mappls_autosuggest_failed_fallback", error=str(exc))
        return await self._fallback.autosuggest(query, near)

    async def reverse_geocode(self, point: LatLng) -> str:
        token = await self._bearer()
        headers = {"Authorization": f"bearer {token}"} if token else {}
        params: dict[str, Any] = {"lat": point.lat, "lng": point.lng}
        if not token:
            params["access_token"] = settings.MAPPLS_REST_KEY
        url = f"{settings.MAPPLS_ATLAS_BASE_URL}/api/places/geocode"
        try:
            resp = await self._client.get(f"{settings.MAPPLS_ATLAS_BASE_URL}/api/places/rev_geocode", params=params, headers=headers)
            resp.raise_for_status()
            results = resp.json().get("results") or []
            if results:
                return results[0].get("formatted_address") or results[0].get("street") or "Selected location"
        except Exception as exc:
            logger.warning("mappls_revgeo_failed_fallback", error=str(exc), url=url)
        return await self._fallback.reverse_geocode(point)


_provider: MapsProvider | None = None


def get_maps_provider() -> MapsProvider:
    global _provider
    if _provider is None:
        if settings.mappls_enabled:
            _provider = MapplsProvider()
            logger.info("maps_provider", provider="mappls")
        else:
            _provider = LocalProvider()
            logger.info("maps_provider", provider="local")
    return _provider
