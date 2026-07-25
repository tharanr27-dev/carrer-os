from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.repo = AnalyticsRepository(db)

    # General analytics methods can go here, e.g. cross-domain queries
    # For now, most logic is delegated to specific engines (EventAggregator, AIAnalytics, DashboardService)
