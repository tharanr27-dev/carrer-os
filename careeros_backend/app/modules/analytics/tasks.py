import asyncio
import uuid

from celery import shared_task

from app.db.session import AsyncSessionLocal
from app.modules.analytics.services.metrics_calculator import MetricsCalculatorService
from app.modules.analytics.services.trend_analysis import TrendAnalysisService


@shared_task
def generate_monthly_snapshots(user_id_str: str, year: int, month: int):
    """
    Background task to generate a monthly snapshot for a user.
    """
    user_id = uuid.UUID(user_id_str)

    async def _run():
        async with AsyncSessionLocal() as db:
            calc_service = MetricsCalculatorService(db)
            trend_service = TrendAnalysisService(db)

            # Generate snapshot
            await calc_service.generate_monthly_snapshot(user_id, year, month)

            # Update trends
            await trend_service.calculate_monthly_trends(user_id, year, month)

    asyncio.run(_run())


@shared_task
def run_nightly_aggregations():
    """
    Cron-like task to trigger nightly rollups.
    In a real implementation, it would fetch all active users and enqueue snapshot generation.
    """
    pass
