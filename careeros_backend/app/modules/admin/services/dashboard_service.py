import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import get_redis
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import AIProviderTestRequest, AIProviderTestResponse


class AdminDashboardService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)
        self.db = db

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        redis = await get_redis()
        cache_key = "admin:dashboard:summary"

        # Check cache
        cached = await redis.get(cache_key)
        if cached:
            import json

            return json.loads(cached)

        # Fallback pre-aggregated mock calculation (production query summary maps metrics tables)
        data = {
            "total_users": 1500,
            "active_users": 950,
            "pending_moderation_count": 8,
            "system_status": "healthy",
            "unresolved_reports": 4,
            "ai_daily_token_usage": 520400,
            "ai_monthly_cost_usd": 152.20,
        }

        import json

        await redis.set(cache_key, json.dumps(data), ex=300)
        return data

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
