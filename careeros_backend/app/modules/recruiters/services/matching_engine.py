import uuid
from typing import Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.text_analysis import extract_skills
from app.modules.jobs.skills import load_student_skills
from app.modules.recruiters.repository import RecruiterRepository

METHOD = "skill_overlap_v1"


def job_required_skills(job) -> List[str]:
    """Skills the job asks for: found in its requirement lines, else (fallback) in title and description."""
    req_text = "\n".join(str(r) for r in (job.requirements or []))
    skills = extract_skills(req_text)
    return skills or extract_skills(f"{job.title}\n{job.description or ''}")


async def compute_match(db: AsyncSession, job, candidate_id: uuid.UUID) -> Tuple[List[str], List[str], List[str]]:
    """(required, matched, missing) comparing the job's skills with the candidate's saved skills."""
    required = job_required_skills(job)
    have = {s.lower() for s in await load_student_skills(db, candidate_id)}
    matched = [s for s in required if s.lower() in have]
    return required, matched, [s for s in required if s.lower() not in have]


class CandidateMatchingEngine:
    """Skill-overlap fit score: matched required skills / required skills. Only skills the candidate has saved on their
    profile or that were found in their uploaded résumé count, and only skills literally named by the job count."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RecruiterRepository(db)

    async def calculate_deterministic_score(self, application_id: uuid.UUID) -> str:
        app = await self.repo.get_application(application_id)
        if not app:
            return "0%"
        job = await self.repo.get_job(app.job_id)
        required, matched, missing = await compute_match(self.db, job, app.candidate_id)
        details: Dict = {"method": METHOD, "required_skills": required, "matched_skills": matched, "missing_skills": missing}
        if required:
            app.fit_score = f"{round(100 * len(matched) / len(required))}%"
        else:
            app.fit_score = "N/A"
            details["note"] = "The job text names no recognisable skills, so no fit score can be computed."
        app.match_details = details
        await self.repo.update_application(app)
        return app.fit_score
