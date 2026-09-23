from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import DB, Driver, VerifiedDriver, load_user
from app.modules.auth.service import serialize_user
from app.modules.drivers.schemas import (
    CancelRideIn,
    DriverRegisterIn,
    DriverStatusIn,
    LocationIn,
    MemberActionIn,
    OfferRespondIn,
    VerifyCodeIn,
)
from app.modules.drivers.service import DriverService
from app.schemas.common import ok

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post("/register", summary="Complete driver profile + vehicle")
async def register(body: DriverRegisterIn, db: DB, current: Driver):
    await DriverService(db).register(current, body)
    db.expire_all()
    user = await load_user(db, current.id)
    return ok(serialize_user(user).model_dump(), message="Driver profile created")  # type: ignore[arg-type]


@router.put("/me/status", summary="Go online / offline")
async def set_status(body: DriverStatusIn, db: DB, current: Driver):
    data = await DriverService(db).set_online(current, body.online, body.lat, body.lng)
    return ok(data)


@router.post("/me/location", summary="Push a GPS fix (REST fallback for the WebSocket stream)")
async def update_location(body: LocationIn, db: DB, current: Driver):
    await DriverService(db).update_location(current, body)
    return ok()


@router.get("/me/offer", summary="Pending ride offer, if any")
async def current_offer(db: DB, current: VerifiedDriver):
    return ok(await DriverService(db).current_offer(current))


@router.post("/offers/{offer_id}/accept")
async def accept_offer(offer_id: str, db: DB, current: VerifiedDriver):
    data = await DriverService(db).accept(current, offer_id)
    return ok(data, message="Ride accepted – head to the first pickup")


@router.post("/offers/{offer_id}/reject")
async def reject_offer(offer_id: str, db: DB, current: VerifiedDriver, body: OfferRespondIn | None = None):
    await DriverService(db).reject(current, offer_id, body.reason if body else None)
    return ok(message="Offer declined")


@router.get("/me/trip", summary="Active trip with ordered stops")
async def active_trip(db: DB, current: VerifiedDriver):
    return ok(await DriverService(db).active_trip(current))


@router.post("/trips/{ride_id}/arrived", summary="Notify waiting passengers at the next stop")
async def arrived(ride_id: str, db: DB, current: VerifiedDriver):
    return ok(await DriverService(db).arrived(current, ride_id))


@router.post("/trips/{ride_id}/verify", summary="Board a passenger with OTP (creator) or matching code (member)")
async def verify(ride_id: str, body: VerifyCodeIn, db: DB, current: VerifiedDriver):
    return ok(await DriverService(db).verify_pickup(current, ride_id, body.code), message="Passenger boarded")


@router.post("/trips/{ride_id}/no-show")
async def no_show(ride_id: str, body: MemberActionIn, db: DB, current: VerifiedDriver):
    return ok(await DriverService(db).no_show(current, ride_id, body.member_id))


@router.post("/trips/{ride_id}/drop", summary="Drop a passenger at their stop")
async def drop(ride_id: str, body: MemberActionIn, db: DB, current: VerifiedDriver):
    return ok(await DriverService(db).drop(current, ride_id, body.member_id))


@router.post("/trips/{ride_id}/cancel")
async def cancel(ride_id: str, body: CancelRideIn, db: DB, current: VerifiedDriver):
    await DriverService(db).cancel_by_driver(current, ride_id, body.reason)
    return ok(message="Ride released – passengers are being re-matched")


@router.get("/me/earnings")
async def earnings(db: DB, current: Driver):
    return ok(await DriverService(db).earnings(current))


@router.get("/me/history")
async def history(db: DB, current: Driver, limit: int = Query(20, le=50), offset: int = 0):
    return ok(await DriverService(db).history(current, limit, offset))
