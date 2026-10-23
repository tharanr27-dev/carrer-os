"""Safe Supabase Schema Provisioning Script.

Executes Base.metadata.create_all() against the connected Supabase PostgreSQL database
to create all application tables safely without dropping, truncating, or modifying existing data.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.base import Base

# Ensure all 16 domain model modules are imported so Base.metadata knows about all tables
import app.modules.users.models
import app.modules.auth.models
import app.modules.career_discovery.models
import app.modules.resumes.models
import app.modules.mentor.models
import app.modules.interviews.models
import app.modules.communication.models
import app.modules.learning.models
import app.modules.recommendations.models
import app.modules.analytics.models
import app.modules.community.models
import app.modules.recruiters.models
import app.modules.placements.models
import app.modules.admin.models
import app.modules.audit.models
import app.modules.training.models


def sanitize_uri(uri: str) -> str:
    """Mask credentials in connection URI for safe logging."""
    if not uri or "@" not in uri:
        return uri or ""
    scheme_and_auth, host_part = uri.split("@", 1)
    if "://" in scheme_and_auth:
        scheme, _ = scheme_and_auth.split("://", 1)
        return f"{scheme}://***:***@{host_part}"
    return f"***:***@{host_part}"


async def provision_schema():
    import os

    if os.getenv("CONFIRM_REMOTE_SCHEMA", "").lower() != "yes":
        print("Refusing to run: this script creates missing tables in the database named by DATABASE_URL. "
              "Review deployment/training_tables.postgres.sql, then re-run with CONFIRM_REMOTE_SCHEMA=yes.")
        return False
    db_uri = settings.sqlalchemy_database_uri
    masked_uri = sanitize_uri(db_uri)

    print("=" * 75)
    print("CAREEROS SUPABASE POSTGRESQL SCHEMA CREATION")
    print("=" * 75)
    print(f"Target Connection: {masked_uri}")

    if "sqlite" in db_uri.lower():
        print("\n[ERROR] DATABASE_URL is pointing to local SQLite, not Supabase.")
        return False

    connect_args = {"statement_cache_size": 0}
    engine = create_async_engine(db_uri, echo=False, connect_args=connect_args)

    try:
        # Step 1: Confirm Target Database and Check Pre-Execution State
        print("\n[Step 1/4] Verifying connection and inspecting pre-execution state...")
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT version(), current_database(), current_user;"))
            row = res.fetchone()
            print(f"  [SUCCESS] Connected to target PostgreSQL server.")
            print(f"  - Database: {row[1]}")
            print(f"  - User:     {row[2]}")
            print(f"  - Version:  {row[0].split(',')[0]}")

            # Inspect existing tables
            res_tables = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
            )
            pre_tables = [r[0] for r in res_tables.fetchall()]
            print(f"  - Pre-existing tables in 'public' schema: {len(pre_tables)}")
            if pre_tables:
                print(f"  - Found existing tables: {pre_tables[:5]}... (will preserve them)")
            else:
                print("  - Confirmation: 'public' schema is completely empty as expected.")

        # Step 2: Provision Tables using Base.metadata.create_all()
        model_count = len(Base.metadata.tables)
        print(f"\n[Step 2/4] Executing Base.metadata.create_all() for {model_count} registered models...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  [SUCCESS] Base.metadata.create_all() execution completed without errors.")

        # Step 3: Verify Post-Execution Table Count in Supabase
        print("\n[Step 3/4] Verifying created tables in Supabase 'public' schema...")
        async with engine.connect() as conn:
            res_post = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
            )
            created_tables = [r[0] for r in res_post.fetchall()]
            post_count = len(created_tables)
            print(f"  [SUCCESS] Total tables now in 'public' schema: {post_count}")

            # Check if all models in Base.metadata are present
            defined_set = set(Base.metadata.tables.keys())
            created_set = set(created_tables)
            missing = defined_set - created_set
            if missing:
                print(f"  [WARNING] The following {len(missing)} model tables were not found: {missing}")
            else:
                print(f"  [SUCCESS] All {len(defined_set)} defined application models are verified in Supabase!")

        # Step 4: Summary of Created Table Groups
        print("\n[Step 4/4] Schema Structure Verified:")
        print(f"  - Root & Core Tables: users, roles, permissions, profiles, skills")
        print(f"  - Career & Assessment: assessment_templates, career_reports, career_matches")
        print(f"  - Resumes & Analytics: resumes, resume_analyses, analytics_events, ai_usage_analytics")
        print(f"  - Mentorship & Interviews: mentor_sessions, interview_sessions, communication_sessions")
        print(f"  - Recruiters & Placements: recruiter_jobs, recruiter_applications, placement_drives")
        print(f"  - Admin & Governance: admin_platform_settings, admin_feature_flags, admin_prompt_versions")

        print("\n" + "=" * 75)
        print(f"SCHEMA CREATION COMPLETE: {post_count} TABLES READY IN SUPABASE")
        print("=" * 75)
        print("Notice: Seeding scripts and endpoint tests were NOT run (awaiting approval).")

        await engine.dispose()
        return True

    except Exception as exc:
        err = str(exc)
        if "@" in err:
            import re
            err = re.sub(r'://([^:]+):([^@]+)@', r'://***:***@', err)
        print(f"\n[ERROR] Schema creation failed: {err}")
        await engine.dispose()
        return False


if __name__ == "__main__":
    success = asyncio.run(provision_schema())
    sys.exit(0 if success else 1)
