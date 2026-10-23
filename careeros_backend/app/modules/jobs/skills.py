import logging
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resumes.models import Resume, ResumeMetadata
from app.modules.users.models import Profile, ProfileSkill, Skill

logger = logging.getLogger("careeros")


async def load_student_skills(db: AsyncSession, user_id: UUID) -> List[str]:
    """Skills from the student's profile and (real) résumé extraction. Never raises: matching is optional."""
    try:
        rows = await db.execute(
            select(Skill.name)
            .join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
            .join(Profile, Profile.id == ProfileSkill.profile_id)
            .where(Profile.user_id == user_id)
        )
        skills = [r[0] for r in rows.all() if r[0]]

        # Skills read from the student's latest completed résumé, but ONLY from analyses carrying the
        # "text_match_v1" marker (real extraction). Older rows were written by a simulated pipeline that stored the
        # same canned skills for every upload; those are ignored so nobody is credited with skills they lack.
        latest = await db.execute(
            select(ResumeMetadata.extracted_skills)
            .join(Resume, Resume.id == ResumeMetadata.resume_id)
            .where(Resume.user_id == user_id, Resume.status == "COMPLETED")
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        row = latest.first()
        extracted = row[0] if row else None
        if isinstance(extracted, dict) and extracted.get("method") == "text_match_v1":
            skills.extend(str(s) for s in extracted.get("skills", []) if isinstance(s, str))

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
