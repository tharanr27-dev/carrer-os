import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AIUsageAnalytics
from app.modules.analytics.repository import AnalyticsRepository


class AIAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.repo = AnalyticsRepository(db)

    async def log_ai_usage(
        self,
        module: str,
        provider: str,
        model: str,
        execution_time_ms: int,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        prompt_version: Optional[str] = None,
    ) -> AIUsageAnalytics:
        usage = AIUsageAnalytics(
            module=module,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            latency_ms=execution_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            success=success,
            error_message=error_message,
            user_id=user_id,
        )
        return await self.repo.add_ai_usage(usage)
