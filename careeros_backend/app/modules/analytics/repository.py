import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.analytics.models import (
    AIUsageAnalytics,
    AnalyticsEvent,
    AnalyticsSnapshot,
    DailyMetric,
)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_event(self, event: AnalyticsEvent) -> AnalyticsEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def add_events_batch(self, events: List[AnalyticsEvent]) -> None:
        self.session.add_all(events)
        await self.session.commit()

    async def get_daily_metric(
        self, user_id: uuid.UUID, target_date: date
    ) -> Optional[DailyMetric]:
        stmt = select(DailyMetric).where(
            DailyMetric.user_id == user_id, DailyMetric.date == target_date
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert_daily_metric(self, metric: DailyMetric) -> DailyMetric:
        # Check if exists
        existing = await self.get_daily_metric(metric.user_id, metric.date)
        if existing:
            # Update fields
            existing.interviews_completed = metric.interviews_completed
            existing.communication_sessions = metric.communication_sessions
            existing.learning_tasks_completed = metric.learning_tasks_completed
            existing.resume_uploads = metric.resume_uploads
            existing.mentor_messages_sent = metric.mentor_messages_sent
            existing.recommendations_accepted = metric.recommendations_accepted
            existing.recommendations_rejected = metric.recommendations_rejected
            existing.ats_score = metric.ats_score
            existing.interview_score = metric.interview_score
            existing.communication_score = metric.communication_score
            existing.learning_completion_pct = metric.learning_completion_pct
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(metric)
            await self.session.commit()
            await self.session.refresh(metric)
            return metric

    async def add_ai_usage(self, usage: AIUsageAnalytics) -> AIUsageAnalytics:
        self.session.add(usage)
        await self.session.commit()
        await self.session.refresh(usage)
        return usage

    async def get_snapshot(self, user_id: uuid.UUID, period: str) -> Optional[AnalyticsSnapshot]:
        stmt = select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.user_id == user_id, AnalyticsSnapshot.period == period
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert_snapshot(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        existing = await self.get_snapshot(snapshot.user_id, snapshot.period)
        if existing:
            existing.career_readiness_score = snapshot.career_readiness_score
            existing.resume_strength = snapshot.resume_strength
            existing.interview_strength = snapshot.interview_strength
            existing.communication_strength = snapshot.communication_strength
            existing.learning_progress = snapshot.learning_progress
            existing.total_interviews = snapshot.total_interviews
            existing.total_tasks_completed = snapshot.total_tasks_completed
            existing.total_learning_hours = snapshot.total_learning_hours
            existing.total_ai_tokens = snapshot.total_ai_tokens
            existing.total_ai_cost_usd = snapshot.total_ai_cost_usd
            existing.ats_score_delta = snapshot.ats_score_delta
            existing.interview_score_delta = snapshot.interview_score_delta
            existing.communication_score_delta = snapshot.communication_score_delta
            existing.details = snapshot.details
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(snapshot)
            await self.session.commit()
            await self.session.refresh(snapshot)
            return snapshot
