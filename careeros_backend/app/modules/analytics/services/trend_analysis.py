import uuid
from datetime import date
from typing import Any, Dict

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.repository import AnalyticsRepository


class TrendAnalysisService:
    def __init__(self, db: AsyncSession):
        self.repo = AnalyticsRepository(db)

    async def calculate_monthly_trends(
        self, user_id: uuid.UUID, year: int, month: int
    ) -> Dict[str, Any]:
        """
        Calculates trends by comparing the current month to the previous month.
        """
        current_period = f"{year}-{month:02d}"

        # Calculate previous month string
        current_date = date(year, month, 1)
        prev_date = current_date - relativedelta(months=1)
        prev_period = f"{prev_date.year}-{prev_date.month:02d}"

        current_snapshot = await self.repo.get_snapshot(user_id, current_period)
        prev_snapshot = await self.repo.get_snapshot(user_id, prev_period)

        if not current_snapshot:
            return {}

        trends = {}

        # Helper to calculate delta
        def calc_delta(curr, prev):
            if curr is None:
                return None
            if prev is None:
                return curr
            return curr - prev

        trends["ats_score_delta"] = calc_delta(
            current_snapshot.resume_strength,
            prev_snapshot.resume_strength if prev_snapshot else None,
        )
        trends["interview_score_delta"] = calc_delta(
            current_snapshot.interview_strength,
            prev_snapshot.interview_strength if prev_snapshot else None,
        )
        trends["communication_score_delta"] = calc_delta(
            current_snapshot.communication_strength,
            prev_snapshot.communication_strength if prev_snapshot else None,
        )

        # Update current snapshot with trends
        current_snapshot.ats_score_delta = trends["ats_score_delta"]
        current_snapshot.interview_score_delta = trends["interview_score_delta"]
        current_snapshot.communication_score_delta = trends["communication_score_delta"]

        await self.repo.upsert_snapshot(current_snapshot)
        return trends
