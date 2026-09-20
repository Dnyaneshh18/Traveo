import asyncio
from app.core.database import async_session_factory
from app.models import DriverProfile
from app.models.enums import VerificationStatus
from sqlalchemy import update

async def run():
    async with async_session_factory() as db:
        await db.execute(update(DriverProfile).values(verification_status=VerificationStatus.APPROVED))
        await db.commit()
        print('Updated drivers')

if __name__ == "__main__":
    asyncio.run(run())
