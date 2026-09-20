"""Quick script to test Supabase database connectivity."""
import asyncio
import asyncpg


async def test():
    print("Connecting to: db.toqvohzccqziphjjsiil.supabase.co:5432 ...")
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(
                host="db.toqvohzccqziphjjsiil.supabase.co",
                port=5432,
                user="postgres",
                password="Nandupatil@123",
                database="postgres",
            ),
            timeout=15,
        )
        ver = await conn.fetchval("SELECT version()")
        print(f"[OK] SUCCESS -- Connected!\n   PostgreSQL: {ver}")
        await conn.close()
    except asyncio.TimeoutError:
        print("[TIMEOUT] Could not reach the database in 15 seconds.")
        print("   Possible causes:")
        print("   1. Supabase project is PAUSED (free tier pauses after inactivity)")
        print("   2. Network/firewall blocking port 5432")
    except asyncpg.InvalidPasswordError:
        print("[AUTH FAILED] Wrong password.")
        print("   Update DATABASE_URL in .env with the correct password.")
    except Exception as e:
        print(f"[FAILED] {type(e).__name__}: {e}")


asyncio.run(test())
