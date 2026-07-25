import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.recommendations.models import (
    Recommendation,
    RecommendationAnalytics,
    RecommendationFeedback,
)


class RecommendationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    async def bulk_create(self, recommendations: list[Recommendation]) -> None:
        """Persist an entire generation cycle in one transaction."""
        self.session.add_all(recommendations)
        await self.session.commit()

    async def get_active_feed(self, user_id: uuid.UUID, limit: int = 20) -> list[Recommendation]:
        """
        Fetch the latest ACTIVE recommendations ordered by rank_score desc.
        Filtered to exclude expired items.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.status == "ACTIVE",
                (Recommendation.expires_at == None) | (Recommendation.expires_at > now),  # noqa
            )
            .order_by(Recommendation.rank_score.desc().nullslast())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, recommendation_id: uuid.UUID) -> Recommendation | None:
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        return result.scalars().first()

    async def expire_previous_generation(self, user_id: uuid.UUID) -> None:
        """
        Mark all current ACTIVE recommendations as EXPIRED before inserting
        a fresh generation cycle.
        """
        stmt = select(Recommendation).where(
            Recommendation.user_id == user_id,
            Recommendation.status == "ACTIVE",
        )
        result = await self.session.execute(stmt)
        for rec in result.scalars().all():
            rec.status = "EXPIRED"
        await self.session.commit()

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    async def save_feedback(self, feedback: RecommendationFeedback) -> RecommendationFeedback:
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback

    async def update_recommendation_status(self, recommendation_id: uuid.UUID, status: str) -> None:
        rec = await self.get_by_id(recommendation_id)
        if rec:
            rec.status = status
            await self.session.commit()

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def get_or_create_analytics(self, user_id: uuid.UUID) -> RecommendationAnalytics:
        result = await self.session.execute(
            select(RecommendationAnalytics).where(RecommendationAnalytics.user_id == user_id)
        )
        analytics = result.scalars().first()
        if not analytics:
            analytics = RecommendationAnalytics(user_id=user_id)
            self.session.add(analytics)
            await self.session.commit()
            await self.session.refresh(analytics)
        return analytics
