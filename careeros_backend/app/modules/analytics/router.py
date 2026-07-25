from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.modules.analytics.dependencies import (
    get_ai_analytics_service,
    get_dashboard_service,
    get_event_aggregator_service,
)
from app.modules.analytics.schemas import (
    AIUsageAnalyticsCreate,
    AIUsageAnalyticsResponse,
    AnalyticsEventCreate,
)
from app.modules.analytics.services.ai_analytics import AIAnalyticsService
from app.modules.analytics.services.dashboard_service import DashboardService
from app.modules.analytics.services.event_aggregator import EventAggregatorService
from app.modules.auth.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def log_event(
    event_in: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    event_service: EventAggregatorService = Depends(get_event_aggregator_service),
):
    """
    Log a new domain event.
    """
    await event_service.log_event(
        user_id=current_user.id,
        event_type=event_in.event_type,
        module=event_in.module,
        entity_id=event_in.entity_id,
        payload=event_in.payload,
    )
    return {"status": "accepted"}


@router.post(
    "/ai-usage", status_code=status.HTTP_201_CREATED, response_model=AIUsageAnalyticsResponse
)
async def log_ai_usage(
    usage_in: AIUsageAnalyticsCreate,
    current_user: User = Depends(get_current_user),
    ai_service: AIAnalyticsService = Depends(get_ai_analytics_service),
):
    """
    Log AI pipeline usage (tokens, latency).
    """
    usage = await ai_service.log_ai_usage(
        module=usage_in.module,
        provider=usage_in.provider,
        model=usage_in.model,
        prompt_version=usage_in.prompt_version,
        prompt_tokens=usage_in.prompt_tokens,
        completion_tokens=usage_in.completion_tokens,
        total_tokens=usage_in.total_tokens,
        estimated_cost_usd=usage_in.estimated_cost_usd,
        execution_time_ms=usage_in.latency_ms,
        success=usage_in.success,
        error_message=usage_in.error_message,
        user_id=current_user.id,
    )
    return usage


@router.get("/dashboard/student", response_model=Dict[str, Any])
async def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """
    Get aggregated dashboard data for the student.
    """
    return await dashboard_service.get_student_dashboard(current_user.id)
