import json
import uuid
from datetime import date
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.repository import AnalyticsRepository

# Assuming a redis cache client is injected or available via infrastructure
# from app.infrastructure.redis import redis_client


class DashboardService:
    def __init__(self, db: AsyncSession, redis_client=None):
        self.repo = AnalyticsRepository(db)
        self.redis = redis_client

    async def get_student_dashboard(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Fetches student dashboard metrics.
        Prefers Redis cache; falls back to DB snapshot/daily metrics.
        """
        cache_key = f"dashboard:student:{user_id}"

        if self.redis:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

        # Fallback to DB
        today = date.today()
        current_period = f"{today.year}-{today.month:02d}"

        snapshot = await self.repo.get_snapshot(user_id, current_period)
        daily = await self.repo.get_daily_metric(user_id, today)

        dashboard_data = {
            "career_readiness": snapshot.career_readiness_score if snapshot else 0,
            "resume_score": snapshot.resume_strength if snapshot else 0,
            "interview_score": snapshot.interview_strength if snapshot else 0,
            "today_interviews": daily.interviews_completed if daily else 0,
            "today_tasks": daily.learning_tasks_completed if daily else 0,
            "trends": {
                "ats_score_delta": snapshot.ats_score_delta if snapshot else 0,
                "interview_score_delta": snapshot.interview_score_delta if snapshot else 0,
            },
        }

        if self.redis:
            # Cache for 1 hour
            await self.redis.setex(cache_key, 3600, json.dumps(dashboard_data))

        return dashboard_data
