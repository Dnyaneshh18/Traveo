"""
Seed data — colleges/schools registry (Pune pilot), admin account, and demo
drivers so the platform can be exercised end-to-end immediately.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import (
    VEHICLE_CAPACITY,
    College,
    DriverProfile,
    DriverStatus,
    InstitutionType,
    User,
    UserRole,
    Vehicle,
    VehicleType,
    VerificationStatus,
)

settings = get_settings()
logger = get_logger(__name__)

COLLEGES: list[dict] = [
    dict(code="COEP", name="COEP Technological University", short_name="COEP", aliases=["College of Engineering Pune", "COEP Tech", "COEP Pune"], city="Pune", state="Maharashtra", address="Wellesley Rd, Shivajinagar, Pune 411005", latitude=18.5293, longitude=73.8567, id_pattern=r"^(C|MIS)?\d{9,12}$|^\d{2}[A-Z]{2,4}\d{3,4}$", id_hint="e.g. 112003045 or 21CS1234"),
    dict(code="PICT", name="Pune Institute of Computer Technology", short_name="PICT", aliases=["PICT Pune", "SCTR's PICT"], city="Pune", state="Maharashtra", address="Survey No. 27, Dhankawadi, Pune 411043", latitude=18.4575, longitude=73.8508, id_pattern=r"^[CIEA]2K\d{2}[A-Z0-9]{3,8}$|^\d{5,8}$", id_hint="e.g. C2K221234 or 42325"),
    dict(code="VIT", name="Vishwakarma Institute of Technology", short_name="VIT Pune", aliases=["VIT Pune", "Vishwakarma Institute of Tech", "BRACT's VIT"], city="Pune", state="Maharashtra", address="666, Upper Indiranagar, Bibwewadi, Pune 411037", latitude=18.4636, longitude=73.8682, id_pattern=r"^\d{8,9}$|^[A-Z]{2,4}\d{6,8}$", id_hint="e.g. 12210123"),
    dict(code="MITWPU", name="MIT World Peace University", short_name="MIT-WPU", aliases=["MIT WPU", "MIT Pune", "Maharashtra Institute of Technology"], city="Pune", state="Maharashtra", address="Survey No. 124, Paud Rd, Kothrud, Pune 411038", latitude=18.5183, longitude=73.8152, id_pattern=r"^\d{10}$|^[A-Z]{3,5}\d{6,9}$", id_hint="e.g. 1032210123"),
    dict(code="SPPU", name="Savitribai Phule Pune University", short_name="SPPU", aliases=["Pune University", "University of Pune", "SPPU Main Campus"], city="Pune", state="Maharashtra", address="Ganeshkhind, Pune 411007", latitude=18.5529, longitude=73.8248, id_pattern=r"^[A-Z0-9]{6,14}$", id_hint="PRN e.g. 72123456M"),
    dict(code="SYMBIOSIS", name="Symbiosis Institute of Technology", short_name="SIT Pune", aliases=["Symbiosis Institute of Tech", "SIT Lavale", "Symbiosis International University"], city="Pune", state="Maharashtra", address="Lavale, Mulshi, Pune 412115", latitude=18.5324, longitude=73.7288, id_pattern=r"^\d{11}$|^[A-Z]{2,4}\d{6,9}$", id_hint="e.g. 22070122001"),
    dict(code="FERGUSSON", name="Fergusson College", short_name="Fergusson", aliases=["Fergusson College Pune", "DES Fergusson College", "FC Pune"], city="Pune", state="Maharashtra", address="FC Road, Shivajinagar, Pune 411004", latitude=18.5228, longitude=73.8395, id_pattern=r"^[A-Z]{1,3}\d{5,8}$|^\d{6,9}$", id_hint="e.g. F2312345"),
    dict(code="DYPIT", name="D. Y. Patil Institute of Technology", short_name="DYPIT Pimpri", aliases=["DY Patil Pimpri", "DYPIT", "Dr. D. Y. Patil Institute of Technology"], city="Pune", state="Maharashtra", address="Sant Tukaram Nagar, Pimpri, Pune 411018", latitude=18.6228, longitude=73.8161, id_pattern=r"^[A-Z]{2,4}\d{5,9}$|^\d{6,10}$", id_hint="e.g. TE12345"),
    dict(code="PCCOE", name="Pimpri Chinchwad College of Engineering", short_name="PCCOE", aliases=["PCCOE Nigdi", "PCCOE Pune", "Pimpri Chinchwad College of Engg"], city="Pune", state="Maharashtra", address="Sector 26, Pradhikaran, Nigdi, Pune 411044", latitude=18.6517, longitude=73.7615, id_pattern=r"^\d{6,10}$|^[A-Z]{2,4}\d{5,8}$", id_hint="e.g. 122B1A0123"),
    dict(code="IISER", name="Indian Institute of Science Education and Research Pune", short_name="IISER Pune", aliases=["IISER", "IISER Pune"], city="Pune", state="Maharashtra", address="Dr. Homi Bhabha Rd, Pashan, Pune 411008", latitude=18.5468, longitude=73.8062, id_pattern=r"^\d{8}$", id_hint="e.g. 20221234"),
    dict(code="AIT", name="Army Institute of Technology", short_name="AIT Pune", aliases=["AIT Dighi", "Army Institute of Tech"], city="Pune", state="Maharashtra", address="Dighi Hills, Pune 411015", latitude=18.6136, longitude=73.8760, id_pattern=r"^[A-Z]{2,4}\d{4,8}$|^\d{6,10}$", id_hint="e.g. IT2021001"),
    dict(code="SCOE", name="Sinhgad College of Engineering", short_name="SCOE Vadgaon", aliases=["Sinhgad COE", "SCOE", "Sinhgad College of Engg Vadgaon"], city="Pune", state="Maharashtra", address="Vadgaon Budruk, Pune 411041", latitude=18.4690, longitude=73.8352, id_pattern=r"^[A-Z]{1,4}\d{5,9}$|^\d{6,10}$", id_hint="e.g. S1234567"),
    dict(code="DPS", name="Delhi Public School Pune", short_name="DPS Pune", aliases=["DPS Nyati County", "Delhi Public School Mohammadwadi"], institution_type=InstitutionType.SCHOOL, city="Pune", state="Maharashtra", address="Nyati County, Mohammadwadi, Pune 411060", latitude=18.4670, longitude=73.9230, id_pattern=r"^\d{4,8}$", id_hint="Admission no. e.g. 20231"),
    dict(code="BISHOPS", name="The Bishop's School", short_name="Bishop's Camp", aliases=["Bishops School Camp", "Bishop's School Pune"], institution_type=InstitutionType.SCHOOL, city="Pune", state="Maharashtra", address="General Bhagat Marg, Camp, Pune 411001", latitude=18.5127, longitude=73.8807, id_pattern=r"^[A-Z]?\d{4,8}$", id_hint="e.g. B12345"),
    dict(code="TRAVEO_DEMO", name="Traveo Demo College", short_name="Demo College", aliases=["Traveo Demo", "Demo College Pune"], city="Pune", state="Maharashtra", address="Hinjewadi Phase 1, Pune 411057", latitude=18.5912, longitude=73.7389, id_pattern=r"^DEMO\d{3,6}$", id_hint="e.g. DEMO1001"),
]

DEMO_DRIVERS: list[dict] = [
    dict(phone="+919900000001", name="Ramesh Pawar", vehicle=VehicleType.AUTO, reg="MH12AB1234", model="Bajaj RE", color="Yellow-Black", lat=18.5320, lng=73.8520),
    dict(phone="+919900000002", name="Suresh Jadhav", vehicle=VehicleType.CAR, reg="MH12CD5678", model="Maruti Dzire", color="White", lat=18.5250, lng=73.8600),
    dict(phone="+919900000003", name="Imran Shaikh", vehicle=VehicleType.CAR_XL, reg="MH14EF9012", model="Toyota Innova", color="Silver", lat=18.5400, lng=73.8450),
    dict(phone="+919900000004", name="Vikas More", vehicle=VehicleType.AUTO, reg="MH12GH3456", model="Piaggio Ape", color="Green", lat=18.4600, lng=73.8500),
    dict(phone="+919900000005", name="Amit Kulkarni", vehicle=VehicleType.CAR, reg="MH12JK7890", model="Hyundai Aura", color="Grey", lat=18.5900, lng=73.7400),
    dict(phone="+919900000006", name="Santosh Gaikwad", vehicle=VehicleType.BIKE, reg="MH12LM2345", model="Honda Activa", color="Blue", lat=18.5200, lng=73.8300),
]


async def seed(db: AsyncSession) -> None:
    now = datetime.now(UTC)
    existing_codes = set((await db.execute(select(College.code))).scalars().all())
    added = 0
    for c in COLLEGES:
        if c["code"] in existing_codes:
            continue
        db.add(
            College(
                code=c["code"],
                name=c["name"],
                short_name=c.get("short_name"),
                aliases="|".join(c.get("aliases", [])),
                institution_type=c.get("institution_type", InstitutionType.COLLEGE),
                city=c["city"],
                state=c.get("state"),
                address=c.get("address"),
                latitude=c["latitude"],
                longitude=c["longitude"],
                id_pattern=c.get("id_pattern"),
                id_hint=c.get("id_hint"),
            )
        )
        added += 1

    admin = await db.scalar(select(User).where(User.email == settings.ADMIN_EMAIL.lower()))
    if not admin:
        db.add(
            User(
                email=settings.ADMIN_EMAIL.lower(),
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                full_name="Traveo Ops",
                profile_completed=True,
            )
        )

    if settings.SEED_DEMO_DATA:
        driver_count = int(await db.scalar(select(func.count()).select_from(DriverProfile)) or 0)
        if driver_count == 0:
            for d in DEMO_DRIVERS:
                user = User(phone=d["phone"], role=UserRole.DRIVER, full_name=d["name"], profile_completed=True)
                db.add(user)
                await db.flush()
                profile = DriverProfile(
                    user_id=user.id,
                    license_number=f"MH12{d['reg'][-4:]}2019{d['reg'][2:4]}",
                    verification_status=VerificationStatus.VERIFIED,
                    status=DriverStatus.ONLINE,
                    average_rating=4.6 + (hash(d["phone"]) % 4) / 10,
                    rating_count=25,
                    completed_rides=40 + hash(d["phone"]) % 90,
                    offers_received=60,
                    offers_accepted=52,
                    latitude=d["lat"],
                    longitude=d["lng"],
                    location_updated_at=now,
                )
                db.add(profile)
                await db.flush()
                db.add(
                    Vehicle(
                        driver_id=profile.id,
                        vehicle_type=d["vehicle"],
                        registration_number=d["reg"],
                        make_model=d["model"],
                        color=d["color"],
                        seat_capacity=VEHICLE_CAPACITY[d["vehicle"]],
                        is_verified=True,
                    )
                )
    await db.flush()
    if added:
        logger.info("seed_colleges", added=added)
