"""Safe, non-destructive Supabase PostgreSQL connection-only verification script.

This script:
1. Connects to the configured database using SQLAlchemy 2.0+ asyncpg.
2. Performs a read-only ping test (SELECT 1).
3. Retrieves PostgreSQL version, current database, and current user.
4. Inspects existing tables in the 'public' schema (read-only inspection).
5. Does NOT create tables, alter schema, run migrations, or seed data.
6. Does NOT print passwords, secret keys, or unmasked credentials.

Usage:
    python -m scripts.test_supabase_connection
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


def sanitize_uri(uri: str) -> str:
    """Mask credentials in connection URI for safe logging."""
    if not uri or "@" not in uri:
        return uri or ""
    scheme_and_auth, host_part = uri.split("@", 1)
    if "://" in scheme_and_auth:
        scheme, _ = scheme_and_auth.split("://", 1)
        return f"{scheme}://***:***@{host_part}"
    return f"***:***@{host_part}"


async def test_connection():
    db_uri = settings.sqlalchemy_database_uri
    masked_uri = sanitize_uri(db_uri)
    print("=" * 70)
    print("CAREEROS SUPABASE POSTGRESQL CONNECTION TEST (READ-ONLY)")
    print("=" * 70)
    print(f"Target: {masked_uri}")

    if "sqlite" in db_uri.lower():
        print("\n[WARNING] DATABASE_URL is currently pointing to local SQLite.")
        print("Please configure your Supabase PostgreSQL connection string in careeros_backend/.env first.")
        return False

    connect_args = {"statement_cache_size": 0}
    
    # Try connecting with the configured engine
    engine = create_async_engine(db_uri, echo=False, connect_args=connect_args)

    try:
        print("\n[Step 1/3] Establishing connection and executing ping...")
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1;"))
            val = res.scalar()
            if val == 1:
                print("  [SUCCESS] Database ping succeeded (SELECT 1 returned 1).")
            else:
                print(f"  [UNEXPECTED] SELECT 1 returned: {val}")

        print("\n[Step 2/3] Retrieving server metadata...")
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT version(), current_database(), current_user;"))
            row = res.fetchone()
            pg_version = row[0].split(",")[0] if row else "Unknown"
            db_name = row[1] if row else "Unknown"
            db_user = row[2] if row else "Unknown"
            print(f"  [SUCCESS] Connected to PostgreSQL!")
            print(f"  - Database: {db_name}")
            print(f"  - User:     {db_user}")
            print(f"  - Version:  {pg_version}")

        print("\n[Step 3/3] Inspecting existing tables (read-only)...")
        async with engine.connect() as conn:
            res = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
            )
            existing_tables = [r[0] for r in res.fetchall()]
            print(f"  [SUCCESS] Query completed. Found {len(existing_tables)} existing tables in 'public' schema.")
            if existing_tables:
                sample = existing_tables[:10]
                print(f"  - Existing tables sample: {sample}")
            else:
                print("  - 'public' schema is currently clean/empty.")

        print("\n" + "=" * 70)
        print("RESULT: CONNECTION TEST PASSED SUCCESSFULLY!")
        print("=" * 70)
        await engine.dispose()
        return True

    except Exception as exc:
        err_msg = str(exc)
        # Sanitize error message in case password was embedded in exception
        if "@" in err_msg:
            # Mask potential user:pass in exception
            import re
            err_msg = re.sub(r'://([^:]+):([^@]+)@', r'://***:***@', err_msg)
        print(f"\n[ERROR] Connection failed: {err_msg}")
        await engine.dispose()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
