from app.core.database import SessionFactory
from app.models import User, StudentProfile
from sqlalchemy import select
import asyncio

async def main():
    async with SessionFactory() as db:
        users = (await db.execute(select(User))).scalars().all()
        for u in users:
            print(f"User: id={u.id}, phone={u.phone}, name={u.full_name}, role={u.role}")

asyncio.run(main())
