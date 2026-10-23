import uuid
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recruiters.repository import RecruiterRepository
from app.modules.recruiters.services.matching_engine import METHOD, compute_match
from app.modules.training.models import TrainingQuestion
from app.modules.users.models import Certification, Profile, Project

# skill -> reviewed Interview Prep topic used to suggest questions
SKILL_TOPIC = {
    "Python": "python", "Java": "java", "C": "c", "C++": "cpp", "JavaScript": "javascript", "TypeScript": "typescript",
    "SQL": "sql", "PostgreSQL": "databases", "MySQL": "databases", "MongoDB": "databases", "React": "react-next",
    "Next.js": "react-next", "Git": "git", "REST APIs": "rest-api", "OOP": "oop", "Data Structures": "dsa",
    "Algorithms": "dsa", "Machine Learning": "machine-learning", "Deep Learning": "deep-learning", "NLP": "nlp-llm",
    "LLMs": "nlp-llm", "RAG": "rag", "Testing": "testing", "Operating Systems": "os", "Computer Networks": "networks",
    "DBMS": "dbms", "JWT": "authentication", "OAuth": "authentication", "HTML": "web-basics", "CSS": "web-basics",
}


class AIInsightsEngine:
    """Candidate insights built from facts only: skills the job names versus skills the candidate has saved, counts of
    saved projects and certificates, and interview questions drawn from the reviewed bank for the job's skills.
    Despite the historical class name this is rule-based, not AI."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RecruiterRepository(db)

    async def generate_candidate_insights(self, application_id: uuid.UUID) -> Dict[str, Any]:
        app = await self.repo.get_application(application_id)
        if not app:
            return {}
        job = await self.repo.get_job(app.job_id)
        required, matched, missing = await compute_match(self.db, job, app.candidate_id)

        strengths: List[str] = []
        gaps: List[str] = []
        if matched:
            strengths.append(f"Saved skills match {len(matched)} of {len(required)} skills the job names: {', '.join(matched)}.")
        profile = (await self.db.execute(select(Profile).where(Profile.user_id == app.candidate_id))).scalars().first()
        if profile is not None:
            projects = (await self.db.execute(select(func.count()).select_from(Project).where(Project.profile_id == profile.id))).scalar_one()
            certs = (await self.db.execute(select(func.count()).select_from(Certification).where(Certification.profile_id == profile.id))).scalar_one()
            if projects:
                strengths.append(f"{projects} project(s) listed on the profile.")
            if certs:
                strengths.append(f"{certs} certification(s) listed on the profile.")
        if missing:
            gaps.append(f"Skills the job names that are not on the candidate's profile or résumé: {', '.join(missing)}. They may still have them.")
        if not required:
            gaps.append("The job text names no recognisable skills, so skill matching was not possible.")

        topics = list(dict.fromkeys(SKILL_TOPIC[s] for s in matched + missing if s in SKILL_TOPIC))[:4]
        questions: List[str] = []
        if topics:
            rows = (
                await self.db.execute(
                    select(TrainingQuestion.prompt).where(
                        TrainingQuestion.round == "technical", TrainingQuestion.qtype == "text",
                        TrainingQuestion.source == "curated", TrainingQuestion.topic.in_(topics),
                    ).limit(6)
                )
            ).scalars().all()
            questions = list(rows)[:5]

        insights = {
            "method": METHOD,
            "disclaimer": "Built from saved profile/résumé data and the job text, not an AI assessment. Absence of a skill here means it was not recorded, not that the candidate lacks it.",
            "strengths": strengths,
            "gaps": gaps,
            "suggested_interview_questions": questions,
        }
        app.ai_insights = insights
        await self.repo.update_application(app)
        return insights
