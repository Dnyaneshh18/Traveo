"""Student onboarding & profile: identity-verified registration, ID card upload."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from pydantic import Field
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DB, Current, Student
from app.core.exceptions import (
    ConflictError,
    IdentityAlreadyUsed,
    IdentityMismatch,
    NotFoundError,
    ValidationFailed,
)
from app.core.logging import get_logger
from app.intelligence.identity import check_identity
from app.models import College, Gender, StudentProfile, UserRole, VerificationStatus
from app.modules.auth.service import serialize_user
from app.schemas.common import APIModel, ok
from app.services.storage import save_upload

router = APIRouter(prefix="/students", tags=["Students"])
settings = get_settings()
logger = get_logger(__name__)


class StudentRegisterIn(APIModel):
    full_name: str = Field(min_length=2, max_length=120)
    college_id: str
    college_name_on_id: str = Field(min_length=3, max_length=200, description="Institution name exactly as printed on the ID card")
    college_id_number: str = Field(min_length=3, max_length=60)
    gender: Gender | None = None
    course: str | None = Field(default=None, max_length=120)
    graduation_year: int | None = Field(default=None, ge=2020, le=2040)
    emergency_contact: str | None = Field(default=None, max_length=20)


class StudentUpdateIn(APIModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    gender: Gender | None = None
    course: str | None = None
    graduation_year: int | None = Field(default=None, ge=2020, le=2040)
    emergency_contact: str | None = None


class IdentityPreviewIn(APIModel):
    college_id: str
    college_name_on_id: str
    college_id_number: str


@router.post("/identity/preview", summary="Dry-run the identity rules before submitting")
async def identity_preview(body: IdentityPreviewIn, db: DB, current: Current):
    college = await db.get(College, body.college_id)
    if not college:
        raise NotFoundError("College not found")
    check = check_identity(
        typed_college_name=body.college_name_on_id,
        college_name=college.name,
        aliases=[a for a in (college.aliases or "").split("|") if a],
        college_id_number=body.college_id_number,
        id_pattern=college.id_pattern,
    )
    return ok(
        {
            "name_matches": check.name_matches,
            "name_score": check.name_score,
            "id_format_valid": check.id_format_valid,
            "auto_verified": check.auto_verified,
            "id_hint": college.id_hint,
        }
    )


@router.post("/register", summary="Complete student profile with college identity verification")
async def register_student(body: StudentRegisterIn, db: DB, current: Student):
    if current.student:
        raise ConflictError("Student profile already exists")
    college = await db.get(College, body.college_id)
    if not college or not college.is_active:
        raise NotFoundError("College not found")

    check = check_identity(
        typed_college_name=body.college_name_on_id,
        college_name=college.name,
        aliases=[a for a in (college.aliases or "").split("|") if a],
        college_id_number=body.college_id_number,
        id_pattern=college.id_pattern,
    )
    if not check.name_matches:
        raise IdentityMismatch(
            details={
                "name_score": check.name_score,
                "expected": college.name,
                "hint": "Type the institution name exactly as printed on your ID card.",
            }
        )

    id_number = body.college_id_number.strip().upper()
    dup = await db.scalar(
        select(StudentProfile).where(
            StudentProfile.college_id == college.id, StudentProfile.college_id_number == id_number
        )
    )
    if dup:
        raise IdentityAlreadyUsed()

    status = VerificationStatus.PENDING
    note = (
        f"Submitted for admin verification. Institution match: '{check.matched_alias}' ({check.name_score:.0%})."
        if check.matched_alias
        else "Submitted for admin verification."
    )
    profile = StudentProfile(
        user_id=current.id,
        college_id=college.id,
        college_id_number=id_number,
        college_name_on_id=body.college_name_on_id.strip(),
        identity_match_score=check.name_score,
        gender=body.gender,
        course=body.course,
        graduation_year=body.graduation_year,
        emergency_contact=body.emergency_contact,
        verification_status=status,
        verification_note=note,
        verified_at=None,
    )
    current.user.full_name = body.full_name.strip()
    current.user.profile_completed = True
    current.user.role = UserRole.STUDENT
    db.add(profile)
    await db.flush()
    await db.refresh(current.user)
    from app.core.deps import load_user

    user = await load_user(db, current.id)
    logger.info("student_registered", user_id=current.id, college=college.code, status=status)
    return ok(serialize_user(user).model_dump(), message="Welcome to Traveo" if status == VerificationStatus.VERIFIED else "Profile created – pending verification")  # type: ignore[arg-type]


@router.put("/me", summary="Update student profile")
async def update_student(body: StudentUpdateIn, db: DB, current: Student):
    if not current.student:
        raise NotFoundError("Complete registration first")
    if body.full_name:
        current.user.full_name = body.full_name.strip()
    for field in ("gender", "course", "graduation_year", "emergency_contact"):
        val = getattr(body, field)
        if val is not None:
            setattr(current.student, field, val)
    await db.flush()
    from app.core.deps import load_user

    user = await load_user(db, current.id)
    return ok(serialize_user(user).model_dump())  # type: ignore[arg-type]


@router.post("/me/id-card", summary="Upload ID card photo for verification")
async def upload_id_card(db: DB, current: Student, file: UploadFile = File(...)):
    if not current.student:
        raise NotFoundError("Complete registration first")
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise ValidationFailed("Upload a JPEG, PNG or WebP image")
    url = await save_upload(file, subdir="id-cards", owner_id=current.id)
    current.student.id_card_url = url
    if current.student.verification_status == VerificationStatus.REJECTED:
        current.student.verification_status = VerificationStatus.PENDING
        current.student.verification_note = "Re-submitted ID card – pending review"
    await db.flush()
    return ok({"id_card_url": url}, message="ID card uploaded")


@router.post("/me/avatar")
async def upload_avatar(db: DB, current: Current, file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise ValidationFailed("Upload a JPEG, PNG or WebP image")
    url = await save_upload(file, subdir="avatars", owner_id=current.id)
    current.user.avatar_url = url
    await db.flush()
    return ok({"avatar_url": url})


@router.get("/me/stats")
async def my_stats(current: Student):
    sp = current.student
    if not sp:
        raise NotFoundError("Complete registration first")
    return ok(
        {
            "completed_rides": sp.completed_rides,
            "cancelled_rides": sp.cancelled_rides,
            "total_saved_inr": sp.total_saved_inr,
            "average_rating": sp.average_rating,
            "rating_count": sp.rating_count,
            "co2_saved_kg": round(sp.completed_rides * 1.9, 1),
        }
    )


_ = Path  # keep import for type-checkers in some editors
