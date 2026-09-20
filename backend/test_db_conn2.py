"""Test connection with explicit password parameter."""
import asyncio
import asyncpg


async def test():
    print("Connecting with explicit params...")
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
        print(f"[OK] Connected!\n   PostgreSQL: {ver}")
        
        # List tables
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        )
        if tables:
            print(f"\n   Public tables ({len(tables)}):")
            for t in tables:
                print(f"     - {t['table_name']}")
        else:
            print("\n   No tables in public schema yet.")
        
        await conn.close()
    except asyncpg.InvalidPasswordError:
        print("[AUTH FAILED] Wrong password.")
    except asyncio.TimeoutError:
        print("[TIMEOUT] Could not reach database in 15s.")
    except Exception as e:
        print(f"[FAILED] {type(e).__name__}: {e}")


asyncio.run(test())
