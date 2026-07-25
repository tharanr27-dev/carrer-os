import uuid
from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.analytics.models import AnalyticsSnapshot, DailyMetric
from app.modules.analytics.repository import AnalyticsRepository


class MetricsCalculatorService:
    def __init__(self, db: AsyncSession):
        self.repo = AnalyticsRepository(db)
        self.db = db

    async def generate_monthly_snapshot(
        self, user_id: uuid.UUID, year: int, month: int
    ) -> AnalyticsSnapshot:
        """
        Rolls up daily metrics for a given user and month into an AnalyticsSnapshot.
        """
        start_date = date(year, month, 1)
        end_date = start_date + relativedelta(months=1)

        stmt = select(DailyMetric).where(
            DailyMetric.user_id == user_id,
            DailyMetric.date >= start_date,
            DailyMetric.date < end_date,
        )
        result = await self.db.execute(stmt)
        dailies = result.scalars().all()

        # Aggregate
        total_interviews = sum(d.interviews_completed for d in dailies)
        total_tasks = sum(d.learning_tasks_completed for d in dailies)

        # For scores, we can take the average of the non-null scores during the month,
        # or the latest one. Let's take the latest (max date) for simplicity.
        latest_daily = None
        if dailies:
            latest_daily = max(dailies, key=lambda d: d.date)

        period = f"{year}-{month:02d}"
        snapshot = AnalyticsSnapshot(
            user_id=user_id,
            period=period,
            total_interviews=total_interviews,
            total_tasks_completed=total_tasks,
            # Assuming these are updated incrementally in DailyMetric, we can just take the latest
            career_readiness_score=latest_daily.ats_score if latest_daily else None,  # Simplified
            resume_strength=latest_daily.ats_score if latest_daily else None,
            interview_strength=latest_daily.interview_score if latest_daily else None,
            communication_strength=latest_daily.communication_score if latest_daily else None,
            learning_progress=latest_daily.learning_completion_pct if latest_daily else None,
        )

        return await self.repo.upsert_snapshot(snapshot)
