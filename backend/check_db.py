import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect(
        host="db.toqvohzccqziphjjsiil.supabase.co",
        port=5432, user="postgres",
        password="Nandupatil@123", database="postgres"
    )
    # Check blocked locks
    locks = await conn.fetch(
        "SELECT pid, mode, granted, relation::regclass FROM pg_locks WHERE NOT granted"
    )
    print(f"Blocked locks: {len(locks)}")
    for l in locks:
        print(f"  pid={l['pid']}, mode={l['mode']}, relation={l['relation']}")

    # Check tables created
    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    )
    print(f"\nTables created so far: {len(tables)}")
    for t in tables:
        print(f"  - {t['table_name']}")

    # Check alembic version
    try:
        ver = await conn.fetch("SELECT * FROM alembic_version")
        print(f"\nAlembic version: {ver}")
    except Exception as e:
        print(f"\nAlembic version table: {e}")

    await conn.close()

asyncio.run(check())
