"""Admin & operations API: dashboard metrics, verification queues, live map, rides, config."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.deps import DB, Admin
from app.core.exceptions import NotFoundError
from app.models import (
    College,
    DriverProfile,
    DriverStatus,
    Ride,
    RideRequest,
    RideRequestStatus,
    RideStatus,
    StudentProfile,
    User,
    UserRole,
    VerificationStatus,
)
from app.modules.rides.repository import RideRepository
from app.modules.rides.service import RideService
from app.realtime.hub import hub
from app.schemas.common import APIModel, ok
from app.services import runtime_config
from app.services.events import timeline
from app.services.notifications import notify

router = APIRouter(prefix="/admin", tags=["Admin"])
settings = get_settings()


class VerifyIn(APIModel):
    status: VerificationStatus
    note: str | None = Field(default=None, max_length=300)


class ConfigIn(APIModel):
    key: str
    value: Any


class ToggleActiveIn(APIModel):
    is_active: bool


# ── dashboard ──────────────────────────────────────────────────────
@router.get("/dashboard")
async def dashboard(db: DB, _: Admin):
    now = datetime.now(UTC)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = today - timedelta(days=7)

    async def count(stmt):
        return int(await db.scalar(stmt) or 0)

    students_total = await count(select(func.count()).select_from(StudentProfile))
    students_pending = await count(select(func.count()).select_from(StudentProfile).where(StudentProfile.verification_status == VerificationStatus.PENDING))
    drivers_total = await count(select(func.count()).select_from(DriverProfile))
    drivers_pending = await count(select(func.count()).select_from(DriverProfile).where(DriverProfile.verification_status == VerificationStatus.PENDING))
    drivers_online = await count(select(func.count()).select_from(DriverProfile).where(DriverProfile.status.in_((DriverStatus.ONLINE, DriverStatus.ON_TRIP))))
    open_requests = await count(select(func.count()).select_from(RideRequest).where(RideRequest.status == RideRequestStatus.OPEN))
    dispatching = await count(select(func.count()).select_from(RideRequest).where(RideRequest.status == RideRequestStatus.LOCKED))
    live_rides = await count(select(func.count()).select_from(Ride).where(Ride.status.in_((RideStatus.DRIVER_ASSIGNED, RideStatus.IN_PROGRESS))))
    rides_today = await count(select(func.count()).select_from(Ride).where(Ride.status == RideStatus.COMPLETED, Ride.completed_at >= today))
    rides_week = await count(select(func.count()).select_from(Ride).where(Ride.status == RideStatus.COMPLETED, Ride.completed_at >= week))
    gmv_week = float(await db.scalar(select(func.coalesce(func.sum(Ride.total_fare_inr), 0.0)).where(Ride.status == RideStatus.COMPLETED, Ride.completed_at >= week)) or 0.0)
    fees_week = float(await db.scalar(select(func.coalesce(func.sum(Ride.platform_fee_inr), 0.0)).where(Ride.status == RideStatus.COMPLETED, Ride.completed_at >= week)) or 0.0)
    avg_group = float(await db.scalar(select(func.coalesce(func.avg(RideRequest.seats_taken), 0.0)).where(RideRequest.status == RideRequestStatus.COMPLETED)) or 0.0)

    # 7-day series
    series = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        c = await count(select(func.count()).select_from(Ride).where(Ride.status == RideStatus.COMPLETED, Ride.completed_at >= day, Ride.completed_at < day + timedelta(days=1)))
        series.append({"date": day.date().isoformat(), "rides": c})

    per_college = (
        await db.execute(
            select(College.short_name, College.name, func.count(RideRequest.id))
            .join(RideRequest, RideRequest.college_id == College.id, isouter=True)
            .group_by(College.id)
            .order_by(func.count(RideRequest.id).desc())
            .limit(8)
        )
    ).all()

    return ok(
        {
            "students": {"total": students_total, "pending": students_pending},
            "drivers": {"total": drivers_total, "pending": drivers_pending, "online": drivers_online},
            "rides": {"open_requests": open_requests, "dispatching": dispatching, "live": live_rides, "today": rides_today, "week": rides_week},
            "revenue": {"gmv_week_inr": gmv_week, "platform_fees_week_inr": fees_week},
            "avg_group_size": round(avg_group, 2),
            "realtime_connections": hub.online_count(),
            "series": series,
            "per_college": [{"college": s or n, "requests": c} for s, n, c in per_college],
            "maps_provider": "mappls" if settings.mappls_enabled else "local",
        }
    )


# ── live map ───────────────────────────────────────────────────────
@router.get("/live")
async def live(db: DB, _: Admin):
    drivers = (
        await db.execute(
            select(DriverProfile)
            .options(selectinload(DriverProfile.user), selectinload(DriverProfile.vehicle))
            .where(DriverProfile.status.in_((DriverStatus.ONLINE, DriverStatus.ON_TRIP)), DriverProfile.latitude.is_not(None))
        )
    ).scalars().all()
    requests = (
        await db.execute(
            select(RideRequest)
            .options(selectinload(RideRequest.members), selectinload(RideRequest.rides))
            .where(RideRequest.status.in_((RideRequestStatus.OPEN, RideRequestStatus.LOCKED, RideRequestStatus.DRIVER_ASSIGNED, RideRequestStatus.IN_PROGRESS)))
            .order_by(RideRequest.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return ok(
        {
            "drivers": [
                {
                    "user_id": d.user_id,
                    "name": d.user.full_name,
                    "status": d.status,
                    "vehicle_type": d.vehicle.vehicle_type if d.vehicle else None,
                    "registration": d.vehicle.registration_number if d.vehicle else None,
                    "lat": (hub.get_position(d.user_id).lat if hub.get_position(d.user_id) else d.latitude),
                    "lng": (hub.get_position(d.user_id).lng if hub.get_position(d.user_id) else d.longitude),
                    "heading": d.heading,
                    "updated_at": d.location_updated_at,
                    "current_ride_id": d.current_ride_id,
                }
                for d in drivers
            ],
            "requests": [
                {
                    "id": r.id,
                    "status": r.status,
                    "college_id": r.college_id,
                    "direction": r.direction,
                    "vehicle_type": r.vehicle_type,
                    "seats_taken": r.seats_taken,
                    "seat_capacity": r.seat_capacity,
                    "origin": {"lat": r.origin_lat, "lng": r.origin_lng, "address": r.origin_address},
                    "destination": {"lat": r.destination_lat, "lng": r.destination_lng, "address": r.destination_address},
                    "polyline": r.route_polyline,
                    "departure_at": r.departure_at,
                    "dispatch_radius_km": r.dispatch_radius_km,
                    "driver_user_id": r.ride.driver_user_id if r.ride else None,
                    "members": [{"user_id": m.user_id, "status": m.status, "pickup": {"lat": m.pickup_lat, "lng": m.pickup_lng}} for m in r.members],
                }
                for r in requests
            ],
            "rider_positions": [p.to_dict() for p in hub.positions(role="student", max_age_seconds=120)],
        }
    )


# ── students ───────────────────────────────────────────────────────
@router.get("/students")
async def students(db: DB, _: Admin, status: VerificationStatus | None = None, q: str | None = None, college_id: str | None = None, limit: int = Query(50, le=200), offset: int = 0):
    stmt = select(StudentProfile).options(selectinload(StudentProfile.user), selectinload(StudentProfile.college))
    if status:
        stmt = stmt.where(StudentProfile.verification_status == status)
    if college_id:
        stmt = stmt.where(StudentProfile.college_id == college_id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.join(User, User.id == StudentProfile.user_id).where(
            func.lower(User.full_name).like(like) | User.phone.like(like) | func.lower(StudentProfile.college_id_number).like(like)
        )
    rows = (await db.execute(stmt.order_by(StudentProfile.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return ok(
        [
            {
                "id": s.id,
                "user_id": s.user_id,
                "full_name": s.user.full_name,
                "phone": s.user.phone,
                "college": {"id": s.college.id, "name": s.college.name, "short_name": s.college.short_name},
                "college_id_number": s.college_id_number,
                "college_name_on_id": s.college_name_on_id,
                "identity_match_score": s.identity_match_score,
                "id_card_url": s.id_card_url,
                "verification_status": s.verification_status,
                "verification_note": s.verification_note,
                "gender": s.gender,
                "course": s.course,
                "completed_rides": s.completed_rides,
                "average_rating": s.average_rating,
                "is_active": s.user.is_active,
                "created_at": s.created_at,
            }
            for s in rows
        ]
    )


@router.post("/students/{profile_id}/verify")
async def verify_student(profile_id: str, body: VerifyIn, db: DB, admin: Admin):
    sp = await db.get(StudentProfile, profile_id)
    if not sp:
        raise NotFoundError("Student not found")
    sp.verification_status = body.status
    sp.verification_note = body.note or f"{body.status.title()} by {admin.user.full_name or 'admin'}"
    sp.verified_at = datetime.now(UTC) if body.status == VerificationStatus.VERIFIED else None
    await db.flush()
    from app.models import NotificationType

    await notify(
        db,
        [sp.user_id],
        type=NotificationType.SYSTEM,
        title="Identity verified ✅" if body.status == VerificationStatus.VERIFIED else "Verification update",
        body="You can now create and join rides with your classmates." if body.status == VerificationStatus.VERIFIED else (body.note or "Your ID could not be verified. Please re-upload a clear photo."),
        data={"screen": "profile"},
    )
    await hub.send_to_user(sp.user_id, "profile.updated", {"verification_status": body.status})
    return ok(message="Updated")


# ── drivers ────────────────────────────────────────────────────────
@router.get("/drivers")
async def drivers(db: DB, _: Admin, status: VerificationStatus | None = None, limit: int = Query(50, le=200), offset: int = 0):
    stmt = select(DriverProfile).options(selectinload(DriverProfile.user), selectinload(DriverProfile.vehicle))
    if status:
        stmt = stmt.where(DriverProfile.verification_status == status)
    rows = (await db.execute(stmt.order_by(DriverProfile.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return ok(
        [
            {
                "id": d.id,
                "user_id": d.user_id,
                "full_name": d.user.full_name,
                "phone": d.user.phone,
                "license_number": d.license_number,
                "license_url": d.license_url,
                "verification_status": d.verification_status,
                "verification_note": d.verification_note,
                "status": d.status,
                "vehicle": {"type": d.vehicle.vehicle_type, "registration": d.vehicle.registration_number, "make_model": d.vehicle.make_model, "color": d.vehicle.color} if d.vehicle else None,
                "completed_rides": d.completed_rides,
                "average_rating": d.average_rating,
                "acceptance_rate": round(d.acceptance_rate, 2),
                "total_earnings_inr": d.total_earnings_inr,
                "is_active": d.user.is_active,
                "created_at": d.created_at,
            }
            for d in rows
        ]
    )


@router.post("/drivers/{profile_id}/verify")
async def verify_driver(profile_id: str, body: VerifyIn, db: DB, admin: Admin):
    dp = await db.get(DriverProfile, profile_id)
    if not dp:
        raise NotFoundError("Driver not found")
    dp.verification_status = body.status
    dp.verification_note = body.note or f"{body.status.title()} by {admin.user.full_name or 'admin'}"
    if dp.vehicle:
        dp.vehicle.is_verified = (body.status == VerificationStatus.VERIFIED)
    await db.flush()
    from app.models import NotificationType

    await notify(db, [dp.user_id], type=NotificationType.SYSTEM, title="Driver verification", body=body.note or f"Your driver profile is now {body.status}.", data={"screen": "home"})
    await hub.send_to_user(dp.user_id, "profile.updated", {"verification_status": body.status})
    return ok(message="Updated")


@router.post("/users/{user_id}/active")
async def toggle_user(user_id: str, body: ToggleActiveIn, db: DB, _: Admin):
    user = await db.get(User, user_id)
    if not user or user.role == UserRole.ADMIN:
        raise NotFoundError("User not found")
    user.is_active = body.is_active
    await db.flush()
    return ok(message="Updated")


# ── rides ──────────────────────────────────────────────────────────
@router.get("/rides")
async def rides(db: DB, admin: Admin, status: RideRequestStatus | None = None, college_id: str | None = None, limit: int = Query(50, le=200), offset: int = 0):
    stmt = select(RideRequest).options(selectinload(RideRequest.members), selectinload(RideRequest.rides))
    if status:
        stmt = stmt.where(RideRequest.status == status)
    if college_id:
        stmt = stmt.where(RideRequest.college_id == college_id)
    rows = (await db.execute(stmt.order_by(RideRequest.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    svc = RideService(db)
    return ok([(await svc.serialize(r, viewer_id=None, light=True)).model_dump(mode="json") for r in rows])


@router.get("/rides/{request_id}")
async def ride_detail(request_id: str, db: DB, admin: Admin):
    req = await RideRepository(db).get_request(request_id)
    if not req:
        raise NotFoundError("Ride not found")
    data = (await RideService(db).serialize(req, viewer_id=None)).model_dump(mode="json")
    data["timeline"] = await timeline(db, request_id)
    data["otp"] = req.otp_plain
    data["offers"] = [
        {"id": o.id, "driver_user_id": o.driver_user_id, "status": o.status, "radius_km": o.radius_km, "eta_min": o.eta_min, "score": o.score, "created_at": o.created_at}
        for o in req.offers
    ]
    return ok(data)


@router.post("/rides/{request_id}/cancel")
async def cancel_ride(request_id: str, db: DB, admin: Admin):
    req = await RideRepository(db).get_request(request_id)
    if not req:
        raise NotFoundError("Ride not found")
    await RideService(db)._cancel(req, actor_id=admin.id, reason="admin_cancelled")
    return ok(message="Cancelled")


# ── config ─────────────────────────────────────────────────────────
@router.get("/config")
async def get_config(db: DB, _: Admin):
    values = await runtime_config.load_config(db, force=True)
    return ok([{**d, "value": values.get(d["key"], d["default"])} for d in runtime_config.describe()])


@router.put("/config")
async def set_config(body: ConfigIn, db: DB, _: Admin):
    if body.key not in runtime_config.DEFAULTS:
        raise NotFoundError("Unknown config key")
    await runtime_config.set_value(db, body.key, body.value)
    return ok(message="Saved")
