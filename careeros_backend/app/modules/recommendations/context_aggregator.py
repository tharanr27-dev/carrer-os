import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.career_discovery.models import CareerReport
from app.modules.communication.models import CommunicationReport, CommunicationSession
from app.modules.interviews.models import InterviewReport, InterviewSession
from app.modules.learning.models import LearningRoadmap, SkillProgress
from app.modules.mentor.models import CareerGoal
from app.modules.resumes.models import Resume, ResumeAnalysis, ResumeSuggestion

# Cross-module imports — read-only queries from prior phases
from app.modules.training.models import TrainingAttempt, TrainingAttemptItem, TrainingProfile
from app.modules.training.progress import compute_progress
from app.modules.users.models import Profile, Project

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
            "has_career_report": False,
            "target_role": None,
            "training": None,
            "resume_suggestions": [],
            "resume_method": None,
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
        context["has_career_report"] = career_report is not None
        if career_report and career_report.skill_gaps:
            context["resume_weaknesses"].extend(career_report.skill_gaps.get("missing", []))

        # --- Phase 6: Resume analysis (this user's latest COMPLETED résumé only) ---
        resume_result = await self.session.execute(
            select(ResumeAnalysis)
            .join(Resume, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.user_id == user_id, Resume.status == "COMPLETED")
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(1)
        )
        resume_analysis = resume_result.scalars().first()
        if resume_analysis:
            context["ats_score"] = resume_analysis.ats_score
            kw = resume_analysis.keyword_analysis or {}
            context["resume_method"] = kw.get("method")
            context["resume_weaknesses"].extend(kw.get("missing", []))
            suggestion_rows = (
                await self.session.execute(
                    select(ResumeSuggestion).where(ResumeSuggestion.analysis_id == resume_analysis.id)
                )
            ).scalars().all()
            context["resume_suggestions"] = [
                {"category": s.category, "text": s.suggestion_text, "impact": s.impact}
                for s in sorted(suggestion_rows, key=lambda x: {"HIGH": 0, "MEDIUM": 1}.get(x.impact, 2))[:3]
            ]

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

        # --- Interview Prep (training): real saved attempts only ---
        tprof = (
            await self.session.execute(select(TrainingProfile).where(TrainingProfile.user_id == user_id))
        ).scalars().first()
        context["target_role"] = tprof.target_role if tprof else None
        item_rows = (
            await self.session.execute(
                select(TrainingAttemptItem).where(
                    TrainingAttemptItem.user_id == user_id, TrainingAttemptItem.score.is_not(None)
                ).limit(4000)
            )
        ).scalars().all()
        attempt_rows = (
            await self.session.execute(
                select(TrainingAttempt).where(TrainingAttempt.user_id == user_id).order_by(TrainingAttempt.started_at.desc()).limit(200)
            )
        ).scalars().all()
        has_projects = bool(
            profile
            and (await self.session.execute(select(Project.id).where(Project.profile_id == profile.id).limit(1))).first()
        )
        items = [
            {"round": i.round, "topic": i.topic, "difficulty": i.difficulty, "score": i.score, "score_kind": i.score_kind,
             "time_taken_sec": i.time_taken_sec, "answered_at": i.answered_at.isoformat() if i.answered_at else None}
            for i in item_rows
        ]
        attempts = [
            {"id": str(a.id), "status": a.status, "round": a.round, "topic": a.topic, "mode": a.mode,
             "ended_at": a.ended_at.isoformat() if a.ended_at else None, "summary": a.summary,
             "started_at": a.started_at.isoformat() if a.started_at else None}
            for a in attempt_rows
        ]
        context["training"] = compute_progress(items, attempts, has_projects=has_projects)

        logger.info(f"Context aggregation complete for user {user_id}")
        return context
