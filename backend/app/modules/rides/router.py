from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.core.deps import DB, Current, VerifiedStudent
from app.core.geo import LatLng
from app.models.enums import VehicleType
from app.modules.rides.schemas import CancelIn, CreateRideRequestIn, JoinRideIn, RoutePreviewIn
from app.modules.rides.service import RideService
from app.schemas.common import ok
from app.services.events import timeline

router = APIRouter(prefix="/rides", tags=["Rides (students)"])


@router.post("/preview", summary="Route, ETA and fare options for a trip")
async def preview(body: RoutePreviewIn, db: DB):
    data = await RideService(db).route_preview(None, body.origin, body.destination)
    return ok(data.model_dump(mode="json"))


@router.post("/requests", summary="Create a ride request (publishes to your college feed)")
async def create_request(body: CreateRideRequestIn, db: DB, current: VerifiedStudent):
    data = await RideService(db).create_request(current, body)
    return ok(data.model_dump(mode="json"), message="Ride published to your college feed")


@router.get("/feed", summary="Open rides from your college that fit your trip")
async def feed(
    db: DB,
    current: VerifiedStudent,
    pickup_lat: float | None = Query(default=None),
    pickup_lng: float | None = Query(default=None),
    drop_lat: float | None = Query(default=None),
    drop_lng: float | None = Query(default=None),
    departure_at: datetime | None = None,
    vehicle_type: VehicleType | None = None,
):
    pickup = LatLng(pickup_lat, pickup_lng) if pickup_lat is not None and pickup_lng is not None else None
    drop = LatLng(drop_lat, drop_lng) if drop_lat is not None and drop_lng is not None else None
    items = await RideService(db).feed(current, pickup=pickup, drop=drop, departure_at=departure_at, vehicle_type=vehicle_type)
    return ok(items, meta={"count": len(items)})


@router.get("/active", summary="My current ride (as creator or member)")
async def active(db: DB, current: Current):
    data = await RideService(db).active(current)
    return ok(data.model_dump(mode="json") if data else None)


@router.get("/history")
async def history(db: DB, current: Current, limit: int = Query(20, le=50), offset: int = 0):
    rows = await RideService(db).history(current, limit, offset)
    return ok([r.model_dump(mode="json") for r in rows])


@router.get("/requests/{request_id}")
async def detail(request_id: str, db: DB, current: Current):
    data = await RideService(db).detail(current, request_id)
    return ok(data.model_dump(mode="json"))


@router.get("/requests/{request_id}/timeline")
async def request_timeline(request_id: str, db: DB, current: Current):
    await RideService(db).detail(current, request_id)  # authorization
    return ok(await timeline(db, request_id))


@router.post("/requests/{request_id}/join", summary="Accept a ride from the feed (join the group)")
async def join(request_id: str, body: JoinRideIn, db: DB, current: VerifiedStudent):
    data = await RideService(db).join(current, request_id, body)
    return ok(data.model_dump(mode="json"), message="You're in! The creator has been notified")


@router.post("/requests/{request_id}/leave", summary="Leave a ride you joined")
async def leave(request_id: str, db: DB, current: Current):
    data = await RideService(db).leave(current, request_id)
    return ok(data.model_dump(mode="json") if data else None, message="You left the ride")


@router.post("/requests/{request_id}/hide", summary="Reject (hide) a feed request")
async def hide(request_id: str, db: DB, current: VerifiedStudent):
    await RideService(db).hide(current, request_id)
    return ok(message="Hidden from your feed")


@router.delete("/requests/{request_id}/members/{user_id}", summary="Creator removes a co-rider")
async def remove_member(request_id: str, user_id: str, db: DB, current: VerifiedStudent):
    data = await RideService(db).remove_member(current, request_id, user_id)
    return ok(data.model_dump(mode="json"))


@router.post("/requests/{request_id}/lock", summary="Creator: stop waiting and find a driver now")
async def lock(request_id: str, db: DB, current: VerifiedStudent):
    data = await RideService(db).lock(current, request_id)
    return ok(data.model_dump(mode="json"), message="Searching for drivers")


@router.post("/requests/{request_id}/retry", summary="Creator: retry driver search")
async def retry(request_id: str, db: DB, current: VerifiedStudent):
    data = await RideService(db).retry_dispatch(current, request_id)
    return ok(data.model_dump(mode="json"), message="Searching again")


@router.post("/requests/{request_id}/reopen", summary="Creator: reopen for more co-riders")
async def reopen(request_id: str, db: DB, current: VerifiedStudent):
    data = await RideService(db).reopen(current, request_id)
    return ok(data.model_dump(mode="json"), message="Ride reopened")


@router.post("/requests/{request_id}/cancel", summary="Creator: cancel the ride for the whole group")
async def cancel(request_id: str, db: DB, current: VerifiedStudent, body: CancelIn | None = None):
    await RideService(db).cancel(current, request_id, body.reason if body else None)
    return ok(message="Ride cancelled")
