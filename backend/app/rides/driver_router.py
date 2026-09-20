"""
Traveo Backend — Driver API Router

All driver-facing endpoints: go online/offline, location updates,
accept/reject rides, OTP verification, pickup/drop management,
ride lifecycle, and ride history.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies import RequireDriver
from app.rides.schemas import (
    AcceptRejectResponse,
    DriverActiveRideResponse,
    DriverLocationUpdate,
    DriverOnlineResponse,
    DropPassengerRequest,
    PickupPassengerRequest,
    RideHistoryResponse,
    VerifyOTPRequest,
)
from app.rides.service import RideService

driver_router = APIRouter()


def _get_driver_id(user: tuple = Depends(RequireDriver)) -> str:
    return user[0]


# ── Go Online / Offline ────────────────────────────────────
@driver_router.post("/go-online", response_model=DriverOnlineResponse)
async def go_online(
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Set driver status to online — start receiving ride requests."""
    driver_id = user[0]
    service = RideService(db)
    return await service.go_online(driver_id)


@driver_router.post("/go-offline", response_model=DriverOnlineResponse)
async def go_offline(
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Set driver status to offline — stop receiving ride requests."""
    driver_id = user[0]
    service = RideService(db)
    return await service.go_offline(driver_id)


# ── Location Updates ───────────────────────────────────────
@driver_router.post("/update-location", status_code=204)
async def update_location(
    location: DriverLocationUpdate,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Update driver's real-time GPS location."""
    driver_id = user[0]
    service = RideService(db)
    await service.update_driver_location(driver_id, location)


# ── Accept / Reject Ride ───────────────────────────────────
@driver_router.post("/accept-ride", response_model=AcceptRejectResponse)
async def accept_ride(
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Accept the pending ride assignment."""
    driver_id = user[0]
    service = RideService(db)
    return await service.accept_ride(driver_id)


@driver_router.post("/reject-ride", response_model=AcceptRejectResponse)
async def reject_ride(
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Reject the pending ride assignment."""
    driver_id = user[0]
    service = RideService(db)
    return await service.reject_ride(driver_id)


# ── OTP Verification ──────────────────────────────────────
@driver_router.post("/rides/{ride_id}/verify-otp")
async def verify_otp(
    ride_id: str,
    request: VerifyOTPRequest,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Verify passenger OTP at pickup point."""
    driver_id = user[0]
    service = RideService(db)
    result = await service.verify_ride_otp(driver_id, ride_id, request.otp)
    return {"verified": result, "message": "OTP verified successfully."}


# ── Pickup & Drop ─────────────────────────────────────────
@driver_router.post("/rides/{ride_id}/pickup")
async def pickup_passenger(
    ride_id: str,
    request: PickupPassengerRequest,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Confirm a passenger has boarded the vehicle."""
    driver_id = user[0]
    service = RideService(db)
    await service.pickup_passenger(driver_id, ride_id, request.passenger_id)
    return {"status": "boarded", "message": "Passenger boarded successfully."}


@driver_router.post("/rides/{ride_id}/drop")
async def drop_passenger(
    ride_id: str,
    request: DropPassengerRequest,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Confirm a passenger has been dropped off."""
    driver_id = user[0]
    service = RideService(db)
    await service.drop_passenger(driver_id, ride_id, request.passenger_id)
    return {"status": "dropped", "message": "Passenger dropped off successfully."}


# ── Ride Lifecycle ─────────────────────────────────────────
@driver_router.post("/rides/{ride_id}/start")
async def start_ride(
    ride_id: str,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Start the ride after all passengers have boarded."""
    driver_id = user[0]
    service = RideService(db)
    await service.start_ride(driver_id, ride_id)
    return {"status": "started", "message": "Ride started."}


@driver_router.post("/rides/{ride_id}/complete")
async def complete_ride(
    ride_id: str,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Complete the ride after all passengers have been dropped off."""
    driver_id = user[0]
    service = RideService(db)
    await service.complete_ride(driver_id, ride_id)
    return {"status": "completed", "message": "Ride completed."}


# ── Active Ride ────────────────────────────────────────────
@driver_router.get("/active-ride")
async def get_active_ride(
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the driver's currently active ride."""
    driver_id = user[0]
    service = RideService(db)
    ride = await service.get_active_ride_for_driver(driver_id)
    if not ride:
        return {"active_ride": None, "message": "No active ride."}
    return ride


# ── Ride History ───────────────────────────────────────────
@driver_router.get("/ride-history", response_model=RideHistoryResponse)
async def get_ride_history(
    limit: int = 20,
    offset: int = 0,
    user: tuple = Depends(RequireDriver),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the driver's ride history."""
    driver_id = user[0]
    service = RideService(db)
    return await service.get_driver_ride_history(driver_id, limit, offset)
