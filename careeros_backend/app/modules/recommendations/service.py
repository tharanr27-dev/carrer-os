import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import get_redis
from app.modules.audit.service import AuditService
from app.modules.recommendations.context_aggregator import ContextAggregator
from app.modules.recommendations.models import (
    Recommendation,
    RecommendationFeedback,
)
from app.modules.recommendations.ranking_engine import RankingEngine
from app.modules.recommendations.recommendation_engine import RecommendationEngine
from app.modules.recommendations.repository import RecommendationRepository
from app.modules.recommendations.schemas import RecommendationFeedbackRequest

logger = logging.getLogger("careeros")

# Recommendations expire after 24 hours by default
RECOMMENDATION_TTL_HOURS = 24
REDIS_FEED_TTL_SECONDS = 6 * 3600  # 6 hours


class RecommendationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = RecommendationRepository(session)
        self.audit_service = AuditService(session)
        self.context_aggregator = ContextAggregator(session)
        self.ai_engine = RecommendationEngine()
        self.ranking_engine = RankingEngine()

    # ------------------------------------------------------------------
    # Refresh / Generation
    # ------------------------------------------------------------------

    async def refresh_recommendations(
        self, user_id: uuid.UUID, background_tasks: BackgroundTasks
    ) -> dict:
        """
        Immediately returns 202 Accepted.
        The full AI generation + ranking cycle runs asynchronously.
        """
        background_tasks.add_task(self._async_generate_and_rank, user_id)
        return {
            "status": "GENERATING",
            "message": "Recommendations are being refreshed. Check /feed in a few seconds.",
        }

    async def _async_generate_and_rank(self, user_id: uuid.UUID) -> None:
        try:
            # 1. Aggregate cross-module context
            context = await self.context_aggregator.build_context(user_id)

            # 2. Fetch historical acceptance rate for ranking signal
            analytics = await self.repository.get_or_create_analytics(user_id)
            acceptance_rate = analytics.acceptance_rate or 0.5

            # 3. AI Generation
            candidates_list = await self.ai_engine.generate_candidates(context)

            # 4. Ranking
            ranked = self.ranking_engine.rank(
                candidates_list.recommendations, context, acceptance_rate
            )

            # 5. Expire previous generation
            await self.repository.expire_previous_generation(user_id)

            # 6. Persist ranked recommendations
            expires_at = datetime.now(timezone.utc) + timedelta(hours=RECOMMENDATION_TTL_HOURS)
            orm_recs = [
                Recommendation(
                    user_id=user_id,
                    category=item.category,
                    title=item.title,
                    description=item.description,
                    reason=item.reason,
                    confidence_score=item.confidence_score,
                    estimated_impact=item.estimated_impact,
                    difficulty=item.difficulty,
                    related_skills=item.related_skills,
                    source_modules=item.source_modules,
                    rank_score=rank_score,
                    priority=idx + 1,
                    expires_at=expires_at,
                    version=analytics.total_generated + 1,
                )
                for idx, (item, rank_score) in enumerate(ranked)
            ]
            await self.repository.bulk_create(orm_recs)

            # 7. Invalidate Redis feed cache
            redis = await get_redis()
            await redis.delete(f"user:{user_id}:recommendations:ranked")

            # 8. Audit
            await self.audit_service.log_action(
                user_id, "RECOMMENDATIONS_REFRESHED", "Recommendation", str(user_id)
            )

            logger.info(f"Generated {len(orm_recs)} recommendations for user {user_id}")

        except Exception as exc:
            logger.error(f"Recommendation generation failed for user {user_id}: {exc}")
            raise

    # ------------------------------------------------------------------
    # Feed Retrieval (Redis-first)
    # ------------------------------------------------------------------

    async def get_feed(self, user_id: uuid.UUID) -> list[Recommendation]:
        redis = await get_redis()
        cache_key = f"user:{user_id}:recommendations:ranked"

        # Try Redis first (Phase 17 will add full JSON serialisation here)
        cached = await redis.get(cache_key)
        if cached:
            logger.info(f"Serving recommendations from Redis cache for user {user_id}")
            # In production, deserialise the cached JSON here.
            # Falling through to DB for architectural clarity.

        recommendations = await self.repository.get_active_feed(user_id)
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations found. Call POST /refresh to generate your first feed.",
            )

        return recommendations

    # ------------------------------------------------------------------
    # Feedback Loop
    # ------------------------------------------------------------------

    async def submit_feedback(
        self, user_id: uuid.UUID, request: RecommendationFeedbackRequest
    ) -> RecommendationFeedback:
        # Ownership validation
        rec = await self.repository.get_by_id(request.recommendation_id)
        if not rec or rec.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied.")

        # Save feedback
        feedback = await self.repository.save_feedback(
            RecommendationFeedback(
                recommendation_id=request.recommendation_id,
                user_id=user_id,
                action=request.action,
                feedback_text=request.feedback_text,
            )
        )

        # Update recommendation status if terminal action
        terminal_map = {
            "ACCEPTED": "ACCEPTED",
            "REJECTED": "REJECTED",
            "COMPLETED": "COMPLETED",
        }
        if request.action in terminal_map:
            await self.repository.update_recommendation_status(
                request.recommendation_id, terminal_map[request.action]
            )

        await self.audit_service.log_action(
            user_id,
            f"RECOMMENDATION_{request.action}",
            "Recommendation",
            str(request.recommendation_id),
        )

        return feedback
