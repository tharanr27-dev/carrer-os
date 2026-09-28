import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.career_discovery.models import CareerReport
from app.modules.communication.models import CommunicationReport, CommunicationSession
from app.modules.interviews.models import InterviewReport, InterviewSession
from app.modules.learning.models import LearningRoadmap, SkillProgress
from app.modules.mentor.models import CareerGoal
from app.modules.resumes.models import ResumeAnalysis

# Cross-module imports — read-only queries from prior phases
from app.modules.users.models import Profile

logger = logging.getLogger("careeros")


class ContextAggregator:
    """
    Queries all prior phase modules to assemble a single, unified
    user context snapshot for the Recommendation Engine.

    This is intentionally read-only — it never writes to any module.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build_context(self, user_id: uuid.UUID) -> dict:
        logger.info(f"Building cross-module context for user {user_id}")

        context: dict = {
            "user_id": str(user_id),
            "profile": {},
            "career_goals": [],
            "resume_weaknesses": [],
            "ats_score": None,
            "interview_scores": {},
            "communication_scores": {},
            "skill_progress": [],
            "roadmap_status": None,
        }

        # --- Phase 4: Profile ---
        profile_result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = profile_result.scalars().first()
        if profile:
            context["profile"] = {
                "headline": profile.headline,
                "completion": profile.completion_percentage,
            }

        # --- Phase 5: Career Report ---
        career_result = await self.session.execute(
            select(CareerReport)
            .where(CareerReport.user_id == user_id)
            .order_by(CareerReport.created_at.desc())
            .limit(1)
        )
        career_report = career_result.scalars().first()
        if career_report and career_report.skill_gaps:
            context["resume_weaknesses"].extend(career_report.skill_gaps.get("missing", []))

        # --- Phase 6: Resume ATS ---
        resume_result = await self.session.execute(
            select(ResumeAnalysis).order_by(ResumeAnalysis.created_at.desc()).limit(1)
        )
        resume_analysis = resume_result.scalars().first()
        if resume_analysis:
            context["ats_score"] = resume_analysis.ats_score
            context["resume_weaknesses"].extend(
                resume_analysis.keyword_analysis.get("missing", [])
                if resume_analysis.keyword_analysis
                else []
            )

        # --- Phase 7: Career Goals ---
        goals_result = await self.session.execute(
            select(CareerGoal)
            .where(CareerGoal.user_id == user_id, CareerGoal.status != "COMPLETED")
            .limit(5)
        )
        context["career_goals"] = [g.title for g in goals_result.scalars().all()]

        # --- Phase 8: Interview Performance ---
        interview_result = await self.session.execute(
            select(InterviewReport)
            .join(InterviewSession, InterviewReport.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewReport.created_at.desc())
            .limit(1)
        )
        interview_report = interview_result.scalars().first()
        if interview_report:
            context["interview_scores"] = {
                "overall": interview_report.overall_score,
                "technical": interview_report.technical_score,
                "communication": interview_report.communication_score,
            }

        # --- Phase 9: Communication Performance ---
        comm_result = await self.session.execute(
            select(CommunicationReport)
            .join(CommunicationSession, CommunicationReport.session_id == CommunicationSession.id)
            .where(CommunicationSession.user_id == user_id)
            .order_by(CommunicationReport.created_at.desc())
            .limit(1)
        )
        comm_report = comm_result.scalars().first()
        if comm_report:
            context["communication_scores"] = {
                "overall": comm_report.overall_score,
                "grammar": comm_report.grammar_score,
                "vocabulary": comm_report.vocabulary_score,
                "tone": comm_report.tone_score,
            }

        # --- Phase 10: Skill Progress ---
        skills_result = await self.session.execute(
            select(SkillProgress).where(SkillProgress.user_id == user_id)
        )
        context["skill_progress"] = [
            {"skill": s.skill_name, "level": s.current_level, "target": s.target_level}
            for s in skills_result.scalars().all()
        ]

        # --- Phase 10: Active Roadmap Status ---
        roadmap_result = await self.session.execute(
            select(LearningRoadmap)
            .where(LearningRoadmap.user_id == user_id, LearningRoadmap.status == "ACTIVE")
            .limit(1)
        )
        roadmap = roadmap_result.scalars().first()
        if roadmap:
            context["roadmap_status"] = {
                "title": roadmap.title,
                "target_role": roadmap.target_role,
                "version": roadmap.version,
            }

        logger.info(f"Context aggregation complete for user {user_id}")
        return context
