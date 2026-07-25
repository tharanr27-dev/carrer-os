import uuid
from datetime import date
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsEvent, DailyMetric
from app.modules.analytics.repository import AnalyticsRepository


class EventAggregatorService:
    """
    Consumes raw events and immediately or periodically updates metrics.
    In a real event-driven architecture, this might listen to a message queue.
    """

    def __init__(self, db: AsyncSession):
        self.repo = AnalyticsRepository(db)
        self.db = db

    async def log_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        module: str,
        entity_id: str = None,
        payload: Dict[str, Any] = None,
    ):
        """
        Logs a raw event to the database.
        """
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            module=module,
            entity_id=entity_id,
            payload=payload,
        )
        await self.repo.add_event(event)

        # In a fully async system, we'd fire a Celery task here to update metrics
        # For simplicity in this service method, we might update DailyMetric immediately
        # or rely on a cron job. Let's do a lightweight immediate update for critical counters.
        await self._update_daily_metric_for_event(user_id, event_type, payload)

    async def _update_daily_metric_for_event(
        self, user_id: uuid.UUID, event_type: str, payload: Dict[str, Any]
    ):
        today = date.today()
        metric = await self.repo.get_daily_metric(user_id, today)
        if not metric:
            metric = DailyMetric(user_id=user_id, date=today)

        # Update counters based on event type
        if event_type == "INTERVIEW_COMPLETED":
            metric.interviews_completed += 1
            if payload and "score" in payload:
                metric.interview_score = payload["score"]
        elif event_type == "RESUME_UPLOADED":
            metric.resume_uploads += 1
        elif event_type == "RESUME_ANALYZED":
            if payload and "ats_score" in payload:
                metric.ats_score = payload["ats_score"]
        elif event_type == "LEARNING_TASK_COMPLETED":
            metric.learning_tasks_completed += 1
        elif event_type == "RECOMMENDATION_ACCEPTED":
            metric.recommendations_accepted += 1
        elif event_type == "RECOMMENDATION_REJECTED":
            metric.recommendations_rejected += 1

        await self.repo.upsert_daily_metric(metric)
