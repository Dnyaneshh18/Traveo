"""
Traveo Backend — Passenger Ride API Router

Passenger-facing endpoints for ride booking, cancellation,
active ride tracking, ride history, and group voting.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies import get_current_user_id
from app.rides.schemas import (
    CreateRideRequest,
    CreateRideResponse,
    RideDetailResponse,
    RideHistoryResponse,
    RideRequestDetailResponse,
    VoteRequest,
    VoteResponse,
)
from app.rides.service import RideService

router = APIRouter()


# ── Book a Ride ────────────────────────────────────────────
@router.post("/book", response_model=CreateRideResponse)
async def book_ride(
    request: CreateRideRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Book a new shared ride. Triggers passenger matching immediately.
    Returns ride request ID, estimated fare, and matching status.
    """
    service = RideService(db)
    return await service.create_ride_request(user_id, request)


# ── Cancel Ride Request ────────────────────────────────────
@router.post("/{request_id}/cancel", status_code=204)
async def cancel_ride(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel a pending or matching ride request."""
    service = RideService(db)
    await service.cancel_ride_request(user_id, request_id)


# ── Ride Request Detail ───────────────────────────────────
@router.get("/request/{request_id}", response_model=RideRequestDetailResponse)
async def get_ride_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get details of a specific ride request."""
    service = RideService(db)
    return await service.get_ride_request_detail(user_id, request_id)


# ── Active Ride ────────────────────────────────────────────
@router.get("/active")
async def get_active_ride(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the passenger's currently active ride with group details."""
    service = RideService(db)
    ride = await service.get_active_ride_for_passenger(user_id)
    if not ride:
        return {"active_ride": None, "message": "No active ride."}
    return ride


# ── Ride History ───────────────────────────────────────────
@router.get("/history", response_model=RideHistoryResponse)
async def get_ride_history(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the passenger's ride history."""
    service = RideService(db)
    return await service.get_passenger_ride_history(user_id, limit, offset)


# ── Group Voting ───────────────────────────────────────────
@router.post("/group/{group_id}/vote", response_model=VoteResponse)
async def vote_in_group(
    group_id: str,
    request: VoteRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Submit a vote for the ride group decision (continue, wait, cancel)."""
    service = RideService(db)
    return await service.record_vote(user_id, group_id, request)
