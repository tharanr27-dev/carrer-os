from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.analytics.services.ai_analytics import AIAnalyticsService
from app.modules.analytics.services.analytics_service import AnalyticsService
from app.modules.analytics.services.dashboard_service import DashboardService
from app.modules.analytics.services.event_aggregator import EventAggregatorService
from app.modules.analytics.services.metrics_calculator import MetricsCalculatorService
from app.modules.analytics.services.trend_analysis import TrendAnalysisService

# Assuming Redis dependency if available
# from app.infrastructure.redis import get_redis


async def get_analytics_service(db: AsyncSession = Depends(get_db)):
    return AnalyticsService(db)


async def get_event_aggregator_service(db: AsyncSession = Depends(get_db)):
    return EventAggregatorService(db)


async def get_ai_analytics_service(db: AsyncSession = Depends(get_db)):
    return AIAnalyticsService(db)


async def get_metrics_calculator_service(db: AsyncSession = Depends(get_db)):
    return MetricsCalculatorService(db)


async def get_trend_analysis_service(db: AsyncSession = Depends(get_db)):
    return TrendAnalysisService(db)


async def get_dashboard_service(
    db: AsyncSession = Depends(get_db),
    # redis = Depends(get_redis)
):
    return DashboardService(db)
