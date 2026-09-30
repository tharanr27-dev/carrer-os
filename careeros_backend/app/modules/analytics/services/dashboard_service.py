import json
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.repository import AnalyticsRepository
from app.modules.interviews.models import InterviewReport, InterviewSession
from app.modules.learning.models import LearningModule, LearningRoadmap, LearningTask
from app.modules.resumes.models import Resume, ResumeAnalysis

# Assuming a redis cache client is injected or available via infrastructure
# from app.infrastructure.redis import redis_client


class DashboardService:
    def __init__(self, db: AsyncSession, redis_client=None):
        self.repo = AnalyticsRepository(db)
        self.db = db
        self.redis = redis_client

    async def _latest_ats_scores(self, user_id: uuid.UUID) -> List[float]:
        stmt = (
            select(ResumeAnalysis.ats_score)
            .join(Resume, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.user_id == user_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(2)
        )
        return [float(v) for v in (await self.db.execute(stmt)).scalars().all()]

    async def _latest_interview_scores(self, user_id: uuid.UUID) -> List[float]:
        stmt = (
            select(InterviewReport.overall_score)
            .join(InterviewSession, InterviewSession.id == InterviewReport.session_id)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewReport.created_at.desc())
            .limit(2)
        )
        return [float(v) for v in (await self.db.execute(stmt)).scalars().all()]

    async def _learning_completion(self, user_id: uuid.UUID) -> Optional[float]:
        """Completed share (0-100) of tasks in the user's active roadmap; None without a roadmap."""
        base = (
            select(func.count(LearningTask.id))
            .join(LearningModule, LearningModule.id == LearningTask.module_id)
            .join(LearningRoadmap, LearningRoadmap.id == LearningModule.roadmap_id)
            .where(LearningRoadmap.user_id == user_id, LearningRoadmap.status == "ACTIVE")
        )
        total = (await self.db.execute(base)).scalar() or 0
        if not total:
            return None
        done = (
            await self.db.execute(base.where(LearningTask.status == "COMPLETED"))
        ).scalar() or 0
        return done / total * 100

    async def _today_counts(self, user_id: uuid.UUID) -> Dict[str, int]:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        interviews = (
            await self.db.execute(
                select(func.count(InterviewSession.id)).where(
                    InterviewSession.user_id == user_id,
                    InterviewSession.status == "COMPLETED",
                    InterviewSession.ended_at >= start,
                )
            )
        ).scalar() or 0
        # LearningTask has no completion timestamp; updated_at moves when a task is completed.
        tasks = (
            await self.db.execute(
                select(func.count(LearningTask.id))
                .join(LearningModule, LearningModule.id == LearningTask.module_id)
                .join(LearningRoadmap, LearningRoadmap.id == LearningModule.roadmap_id)
                .where(
                    LearningRoadmap.user_id == user_id,
                    LearningTask.status == "COMPLETED",
                    LearningTask.updated_at >= start,
                )
            )
        ).scalar() or 0
        return {"interviews": int(interviews), "tasks": int(tasks)}

    async def get_student_dashboard(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Fetches student dashboard metrics.
        Prefers Redis cache; otherwise computes them live from the source tables (latest resume
        analysis, latest interview report, roadmap progress). A pre-aggregated monthly snapshot,
        when one exists, takes precedence for the headline scores.
        """
        cache_key = f"dashboard:student:{user_id}"
        if self.redis:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

        today = date.today()
        current_period = f"{today.year}-{today.month:02d}"
        snapshot = await self.repo.get_snapshot(user_id, current_period)

        ats = await self._latest_ats_scores(user_id)
        interviews = await self._latest_interview_scores(user_id)
        learning_pct = await self._learning_completion(user_id)
        counts = await self._today_counts(user_id)

        resume_score = ats[0] if ats else 0.0
        interview_score = interviews[0] if interviews else 0.0
        # Readiness = mean of the components the user has data for.
        components = [v for v in (ats[0] if ats else None, interviews[0] if interviews else None, learning_pct) if v is not None]
        readiness = sum(components) / len(components) if components else 0.0

        def snap(value, live):
            return value if snapshot and value is not None else live

        dashboard_data = {
            "career_readiness": snap(snapshot.career_readiness_score if snapshot else None, readiness),
            "resume_score": snap(snapshot.resume_strength if snapshot else None, resume_score),
            "interview_score": snap(snapshot.interview_strength if snapshot else None, interview_score),
            "today_interviews": counts["interviews"],
            "today_tasks": counts["tasks"],
            "trends": {
                "ats_score_delta": snap(
                    snapshot.ats_score_delta if snapshot else None,
                    ats[0] - ats[1] if len(ats) > 1 else 0,
                ),
                "interview_score_delta": snap(
                    snapshot.interview_score_delta if snapshot else None,
                    interviews[0] - interviews[1] if len(interviews) > 1 else 0,
                ),
            },
        }
        if self.redis:
            # Cache for 1 hour
            await self.redis.setex(cache_key, 3600, json.dumps(dashboard_data))
        return dashboard_data
