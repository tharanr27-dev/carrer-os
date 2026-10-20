import logging
from typing import Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resumes.models import Resume, ResumeMetadata
from app.modules.users.models import Profile, ProfileSkill, Skill

logger = logging.getLogger("careeros")


def _skill_names(raw: Any) -> List[str]:
    """Resume extraction may store strings or {"name": ...} objects; accept both."""
    names: List[str] = []
    items = list(raw.values()) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return names
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            value = item.get("name") or item.get("skill")
            if isinstance(value, str):
                names.append(value)
    return names


async def load_student_skills(db: AsyncSession, user_id: UUID) -> List[str]:
    """Skills from the student's profile and resume. Never raises: matching is optional."""
    try:
        rows = await db.execute(
            select(Skill.name)
            .join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
            .join(Profile, Profile.id == ProfileSkill.profile_id)
            .where(Profile.user_id == user_id)
        )
        skills = [r[0] for r in rows.all() if r[0]]

        rows = await db.execute(
            select(ResumeMetadata.extracted_skills)
            .join(Resume, Resume.id == ResumeMetadata.resume_id)
            .where(Resume.user_id == user_id)
        )
        for (extracted,) in rows.all():
            skills.extend(_skill_names(extracted))

        seen, unique = set(), []
        for s in skills:
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(s.strip())
        return unique
    except Exception:
        logger.warning("Could not load student skills for job matching", exc_info=True)
        return []
