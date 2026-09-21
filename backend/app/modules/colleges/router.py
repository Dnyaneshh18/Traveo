"""College registry – public search used during registration, admin CRUD."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import Field
from sqlalchemy import func, or_, select

from app.core.deps import DB, Admin
from app.core.exceptions import NotFoundError
from app.models import College, InstitutionType
from app.schemas.common import APIModel, ok

router = APIRouter(prefix="/colleges", tags=["Colleges"])


class CollegeOut(APIModel):
    id: str
    code: str
    name: str
    short_name: str | None = None
    aliases: list[str] = []
    institution_type: str
    city: str
    state: str | None = None
    address: str | None = None
    latitude: float
    longitude: float
    id_hint: str | None = None
    id_pattern: str | None = None
    is_active: bool


class CollegeIn(APIModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=3, max_length=200)
    short_name: str | None = None
    aliases: list[str] = []
    institution_type: InstitutionType = InstitutionType.COLLEGE
    city: str
    state: str | None = None
    address: str | None = None
    latitude: float
    longitude: float
    id_pattern: str | None = None
    id_hint: str | None = None
    email_domain: str | None = None
    is_active: bool = True


def serialize_college(c: College) -> dict:
    return CollegeOut(
        id=c.id,
        code=c.code,
        name=c.name,
        short_name=c.short_name,
        aliases=[a for a in (c.aliases or "").split("|") if a],
        institution_type=c.institution_type,
        city=c.city,
        state=c.state,
        address=c.address,
        latitude=c.latitude,
        longitude=c.longitude,
        id_hint=c.id_hint,
        id_pattern=c.id_pattern,
        is_active=c.is_active,
    ).model_dump()


@router.get("", summary="Search colleges & schools (public)")
async def search_colleges(
    db: DB,
    q: str | None = Query(default=None, min_length=1, max_length=80),
    city: str | None = None,
    institution_type: InstitutionType | None = None,
    limit: int = Query(default=25, le=100),
):
    stmt = select(College).where(College.is_active.is_(True))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(College.name).like(like),
                func.lower(College.short_name).like(like),
                func.lower(College.code).like(like),
                func.lower(College.aliases).like(like),
            )
        )
    if city:
        stmt = stmt.where(func.lower(College.city) == city.lower())
    if institution_type:
        stmt = stmt.where(College.institution_type == institution_type)
    rows = (await db.execute(stmt.order_by(College.name).limit(limit))).scalars().all()
    return ok([serialize_college(c) for c in rows])


@router.get("/{college_id}")
async def get_college(college_id: str, db: DB):
    c = await db.get(College, college_id)
    if not c:
        raise NotFoundError("College not found")
    return ok(serialize_college(c))


@router.post("", summary="Create college (admin)")
async def create_college(body: CollegeIn, db: DB, _: Admin):
    c = College(**body.model_dump(exclude={"aliases"}), aliases="|".join(body.aliases))
    db.add(c)
    await db.flush()
    return ok(serialize_college(c), message="College created")


@router.put("/{college_id}", summary="Update college (admin)")
async def update_college(college_id: str, body: CollegeIn, db: DB, _: Admin):
    c = await db.get(College, college_id)
    if not c:
        raise NotFoundError("College not found")
    for k, v in body.model_dump(exclude={"aliases"}).items():
        setattr(c, k, v)
    c.aliases = "|".join(body.aliases)
    await db.flush()
    return ok(serialize_college(c), message="College updated")
