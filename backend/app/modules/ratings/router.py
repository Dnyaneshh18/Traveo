"""Ratings + payments (cash / UPI acknowledgement)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import Field
from sqlalchemy import func, select

from app.core.deps import DB, Current
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, RideStateError
from app.models import (
    DriverProfile,
    MemberStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Rating,
    Ride,
    RideStatus,
    StudentProfile,
)
from app.modules.rides.repository import RideRepository
from app.schemas.common import APIModel, ok

router = APIRouter(tags=["Ratings & Payments"])


class RatingIn(APIModel):
    ride_id: str
    ratee_id: str
    stars: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=300)


class PaymentIn(APIModel):
    method: PaymentMethod = PaymentMethod.CASH
    reference: str | None = None


async def _recalculate(db, ratee_id: str) -> None:
    avg, count = (
        await db.execute(select(func.avg(Rating.stars), func.count(Rating.id)).where(Rating.ratee_id == ratee_id))
    ).one()
    for model in (StudentProfile, DriverProfile):
        profile = await db.scalar(select(model).where(model.user_id == ratee_id))
        if profile:
            profile.average_rating = round(float(avg or 5.0), 2)
            profile.rating_count = int(count or 0)


@router.post("/ratings", summary="Rate a driver or co-rider after a completed ride")
async def rate(body: RatingIn, db: DB, current: Current):
    ride = await RideRepository(db).get_ride(body.ride_id)
    if not ride:
        raise NotFoundError("Ride not found")
    if ride.status != RideStatus.COMPLETED:
        raise RideStateError("You can rate once the ride is completed")
    participants = {m.user_id for m in ride.request.members if m.status == MemberStatus.DROPPED} | {ride.driver_user_id}
    if current.id not in participants or body.ratee_id not in participants or body.ratee_id == current.id:
        raise ForbiddenError("You can only rate people who shared this ride with you")
    existing = await db.scalar(
        select(Rating).where(Rating.ride_id == body.ride_id, Rating.rater_id == current.id, Rating.ratee_id == body.ratee_id)
    )
    if existing:
        raise ConflictError("Already rated")
    db.add(Rating(ride_id=body.ride_id, rater_id=current.id, ratee_id=body.ratee_id, stars=body.stars, comment=body.comment, created_at=datetime.now(UTC)))
    await db.flush()
    await _recalculate(db, body.ratee_id)
    return ok(message="Thanks for the feedback")


@router.get("/rides/{ride_id}/payments", summary="Payment status for each passenger")
async def payments(ride_id: str, db: DB, current: Current):
    ride = await db.get(Ride, ride_id)
    if not ride:
        raise NotFoundError("Ride not found")
    rows = (await db.execute(select(Payment).where(Payment.ride_id == ride_id))).scalars().all()
    if current.id != ride.driver_user_id and current.id not in {p.payer_id for p in rows} and current.role != "admin":
        raise ForbiddenError()
    return ok([
        {"id": p.id, "payer_id": p.payer_id, "amount_inr": p.amount_inr, "method": p.method, "status": p.status, "paid_at": p.paid_at}
        for p in rows
    ])


@router.post("/rides/{ride_id}/payments/confirm", summary="Passenger marks their share as paid (cash/UPI)")
async def confirm_payment(ride_id: str, body: PaymentIn, db: DB, current: Current):
    payment = await db.scalar(select(Payment).where(Payment.ride_id == ride_id, Payment.payer_id == current.id))
    if not payment:
        raise NotFoundError("No payment due for this ride")
    payment.method = body.method
    payment.reference = body.reference
    payment.status = PaymentStatus.PAID
    payment.paid_at = datetime.now(UTC)
    await db.flush()
    return ok({"status": payment.status}, message="Payment recorded")
