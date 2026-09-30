import uuid
from typing import Any, Dict

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import ModerationQueue
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import AIProviderTestRequest, AIProviderTestResponse
from app.modules.analytics.models import AIUsageAnalytics
from app.modules.auth.models import User, UserStatus


class AdminDashboardService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)
        self.db = db

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Live aggregates straight from the database (cheap indexed counts/sums)."""
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = day_start.replace(day=1)

        async def scalar(stmt):
            return (await self.db.execute(stmt)).scalar() or 0

        total_users = await scalar(select(func.count(User.id)))
        active_users = await scalar(
            select(func.count(User.id)).where(User.status == UserStatus.ACTIVE)
        )
        pending = await scalar(
            select(func.count(ModerationQueue.id)).where(ModerationQueue.status == "pending")
        )
        unresolved = await scalar(
            select(func.count(ModerationQueue.id)).where(
                ModerationQueue.status.in_(["pending", "escalated"])
            )
        )
        tokens_today = await scalar(
            select(func.coalesce(func.sum(AIUsageAnalytics.total_tokens), 0)).where(
                AIUsageAnalytics.created_at >= day_start
            )
        )
        cost_month = await scalar(
            select(func.coalesce(func.sum(AIUsageAnalytics.estimated_cost_usd), 0.0)).where(
                AIUsageAnalytics.created_at >= month_start
            )
        )

        return {
            "total_users": int(total_users),
            "active_users": int(active_users),
            "pending_moderation_count": int(pending),
            "system_status": "healthy",  # the query above succeeding proves the database is up
            "unresolved_reports": int(unresolved),
            "ai_daily_token_usage": int(tokens_today),
            "ai_monthly_cost_usd": round(float(cost_month), 2),
        }

    async def test_ai_provider(
        self, admin_id: uuid.UUID, test_in: AIProviderTestRequest
    ) -> AIProviderTestResponse:
        from app.modules.ai.dependencies import get_ai_orchestrator

        orchestrator = get_ai_orchestrator()

        request_payload = {"provider_name": test_in.provider_name, "model_name": test_in.model_name}

        try:
            # Route request through orchestrator to the appropriate provider gateway
            result = await orchestrator.process_request(
                test_in.provider_name.lower(), request_payload
            )

            return AIProviderTestResponse(
                status=result.get("status", "success"),
                response_text=result.get("response_text", "Success"),
                latency_ms=result.get("latency_ms", 0),
                tokens_used=result.get("tokens_used", 0),
            )
        except ValueError as e:
            return AIProviderTestResponse(
                status="error", response_text=str(e), latency_ms=0, tokens_used=0
            )
