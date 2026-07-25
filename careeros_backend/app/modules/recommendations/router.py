from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.recommendations.schemas import (
    RecommendationFeedbackRequest,
    RecommendationFeedResponse,
    RecommendationResponse,
)
from app.modules.recommendations.service import RecommendationService

router = APIRouter()


@router.post("/refresh", response_model=APIResponse, status_code=202)
async def refresh_recommendations(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers an async recommendation generation cycle.
    Returns 202 Accepted immediately.
    Poll GET /feed once the background task completes.
    """
    service = RecommendationService(db)
    result = await service.refresh_recommendations(current_user.id, background_tasks)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=result, request_id=req_id)


@router.get("/feed", response_model=APIResponse[RecommendationFeedResponse])
async def get_recommendation_feed(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the user's current ranked recommendation feed.
    Served from Redis cache when available; falls back to PostgreSQL.
    """
    service = RecommendationService(db)
    recommendations = await service.get_feed(current_user.id)
    req_id = getattr(request.state, "request_id", None)

    feed = RecommendationFeedResponse(
        user_id=current_user.id,
        generated_at=datetime.now(timezone.utc),
        recommendations=[RecommendationResponse.model_validate(r) for r in recommendations],
        total=len(recommendations),
    )
    return success_response(data=feed, request_id=req_id)


@router.post("/feedback", response_model=APIResponse)
async def submit_feedback(
    payload: RecommendationFeedbackRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Records the user's interaction with a recommendation (ACCEPTED, REJECTED, COMPLETED, etc.).
    Powers the historical acceptance-rate signal in the Ranking Engine.
    """
    service = RecommendationService(db)
    feedback = await service.submit_feedback(current_user.id, payload)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"feedback_id": str(feedback.id), "action": feedback.action},
        message="Feedback recorded. Your future recommendations will improve.",
        request_id=req_id,
    )
