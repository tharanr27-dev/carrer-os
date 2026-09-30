"""Idempotent development seed: RBAC roles/permissions, an admin user, and one assessment.

Run from careeros_backend/:  python -m scripts.seed_dev
Admin credentials come from SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD (dev defaults below).
"""

import asyncio
import os

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.modules.auth.models import Permission, Role, User, UserStatus
from app.modules.career_discovery.models import AssessmentQuestion, AssessmentTemplate

ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@careeros.ai")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "AdminPass123!")

ADMIN_PERMISSIONS = [
    "admin:read",
    "admin:write",
    "admin:moderator",
    "manage:users",
    "manage:roles",
    "manage:settings",
    "view:audit_logs",
    "view:health",
    "view:metrics",
]

ASSESSMENT_TITLE = "General Tech Career Assessment"
ASSESSMENT_QUESTIONS = [
    ("Which programming languages or tools do you enjoy working with?", "TEXT", None),
    (
        "Which kind of work energises you most?",
        "MULTIPLE_CHOICE",
        ["Building products", "Analysing data", "Designing experiences", "Leading teams"],
    ),
    ("Describe a project you are proud of and your role in it.", "TEXT", None),
    (
        "How do you prefer to work?",
        "MULTIPLE_CHOICE",
        ["Independently", "In a small team", "In a large team", "It depends on the task"],
    ),
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        perms = []
        for name in ADMIN_PERMISSIONS:
            perm = (
                await session.execute(select(Permission).where(Permission.name == name))
            ).scalars().first()
            if not perm:
                perm = Permission(name=name, description=f"Permission for {name}")
                session.add(perm)
                await session.flush()
            perms.append(perm)

        admin_role = (
            await session.execute(select(Role).where(Role.name == "admin_super"))
        ).scalars().first()
        if not admin_role:
            admin_role = Role(name="admin_super", description="Super Admin", permissions=perms)
            session.add(admin_role)
            await session.flush()
        for perm in perms:
            if perm not in admin_role.permissions:
                admin_role.permissions.append(perm)

        for role_name in ("student", "recruiter", "placement_officer"):
            exists = (
                await session.execute(select(Role).where(Role.name == role_name))
            ).scalars().first()
            if not exists:
                session.add(Role(name=role_name, description=f"{role_name} role"))

        admin = (
            await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        ).scalars().first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                status=UserStatus.ACTIVE,
                roles=[admin_role],
            )
            session.add(admin)
        elif admin_role not in admin.roles:
            admin.roles.append(admin_role)

        template = (
            await session.execute(
                select(AssessmentTemplate).where(AssessmentTemplate.title == ASSESSMENT_TITLE)
            )
        ).scalars().first()
        if not template:
            template = AssessmentTemplate(
                title=ASSESSMENT_TITLE,
                description="Evaluates technical and interpersonal interests",
            )
            session.add(template)
            await session.flush()
            for idx, (text, q_type, options) in enumerate(ASSESSMENT_QUESTIONS, start=1):
                session.add(
                    AssessmentQuestion(
                        template_id=template.id,
                        question_text=text,
                        question_type=q_type,
                        options=options,
                        order_index=idx,
                    )
                )

        await session.commit()
    print(f"Seed complete. Admin: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed())
