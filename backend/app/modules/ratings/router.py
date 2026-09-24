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
    RideMember,
    RideRequest,
    RideRequestStatus,
    RideStatus,
    StudentProfile,
    User,
)
from app.modules.rides.repository import RideRepository
from app.schemas.common import APIModel, ok

router = APIRouter(tags=["Ratings & Payments"])


class RatingIn(APIModel):
    ride_id: str
    ratee_id: str | None = None
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

    is_driver = (current.id == ride.driver_user_id)
    dropped_members = [m for m in ride.request.members if m.status == MemberStatus.DROPPED]
    participants = {m.user_id for m in dropped_members} | {ride.driver_user_id}

    if current.id not in participants:
        raise ForbiddenError("You did not participate in this ride")

    # If rater is the driver -> rate all dropped passengers in this ride in common
    if is_driver:
        if not dropped_members:
            raise NotFoundError("No dropped passengers to rate")
        rated_any = False
        for m in dropped_members:
            target_id = m.user_id
            existing = await db.scalar(
                select(Rating).where(
                    Rating.ride_id == body.ride_id,
                    Rating.rater_id == current.id,
                    Rating.ratee_id == target_id,
                )
            )
            if not existing:
                db.add(
                    Rating(
                        ride_id=body.ride_id,
                        rater_id=current.id,
                        ratee_id=target_id,
                        stars=body.stars,
                        comment=body.comment,
                        created_at=datetime.now(UTC),
                    )
                )
                rated_any = True
        await db.flush()
        for m in dropped_members:
            await _recalculate(db, m.user_id)
        return ok(message="Thanks for rating the passengers!")
    else:
        target_id = body.ratee_id or ride.driver_user_id
        if target_id == current.id:
            raise ForbiddenError("You cannot rate yourself")
        existing = await db.scalar(
            select(Rating).where(
                Rating.ride_id == body.ride_id,
                Rating.rater_id == current.id,
            )
        )
        if existing:
            raise ConflictError("You have already rated this ride")
        db.add(
            Rating(
                ride_id=body.ride_id,
                rater_id=current.id,
                ratee_id=target_id,
                stars=body.stars,
                comment=body.comment,
                created_at=datetime.now(UTC),
            )
        )
        await db.flush()
        db.expire_all()
        await _recalculate(db, target_id)
        return ok(message="Thanks for your feedback!")


@router.get("/ratings/pending", summary="Check if current user has an unrated completed ride")
async def pending_rating(db: DB, current: Current):
    if current.role == "driver":
        # Find latest completed ride where driver hasn't rated yet
        res = await db.execute(
            select(Ride)
            .where(Ride.driver_user_id == current.id, Ride.status == RideStatus.COMPLETED)
            .order_by(Ride.completed_at.desc())
            .limit(5)
        )
        rides = res.scalars().all()
        for r in rides:
            has_rated = await db.scalar(
                select(Rating.id).where(Rating.ride_id == r.id, Rating.rater_id == current.id)
            )
            if not has_rated:
                members_res = [m for m in r.request.members if m.status == MemberStatus.DROPPED]
                if members_res:
                    return ok({
                        "ride_id": r.id,
                        "request_id": r.request_id,
                        "role": "driver",
                        "passenger_count": len(members_res),
                        "origin_address": r.request.origin_address.split(",")[0],
                        "destination_address": r.request.destination_address.split(",")[0],
                        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                    })
        return ok(None)
    else:
        # Find latest completed ride where passenger hasn't rated driver yet
        res = await db.execute(
            select(RideMember)
            .join(RideRequest, RideMember.request_id == RideRequest.id)
            .where(
                RideMember.user_id == current.id,
                RideMember.status == MemberStatus.DROPPED,
                RideRequest.status == RideRequestStatus.COMPLETED,
            )
            .order_by(RideMember.dropped_at.desc())
            .limit(5)
        )
        members = res.scalars().all()
        for m in members:
            req = await db.get(RideRequest, m.request_id)
            if req and req.ride and req.ride.status == RideStatus.COMPLETED:
                driver_id = req.ride.driver_user_id
                has_rated = await db.scalar(
                    select(Rating.id).where(
                        Rating.ride_id == req.ride.id,
                        Rating.rater_id == current.id,
                    )
                )
                if not has_rated:
                    driver_user = await db.get(User, driver_id)
                    return ok({
                        "ride_id": req.ride.id,
                        "request_id": req.id,
                        "role": "passenger",
                        "driver_name": driver_user.full_name if driver_user else "Your Driver",
                        "driver_id": driver_id,
                        "origin_address": m.pickup_address.split(",")[0],
                        "destination_address": m.drop_address.split(",")[0],
                        "fare_share_inr": m.fare_share_inr,
                        "completed_at": req.ride.completed_at.isoformat() if req.ride.completed_at else None,
                    })
        return ok(None)


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
