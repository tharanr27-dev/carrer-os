from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.learning.schemas import (
    LearningRoadmapResponse,
    RoadmapGenerateRequest,
    TaskCompleteRequest,
)
from app.modules.learning.service import LearningService

router = APIRouter()


@router.post("/roadmaps/generate", response_model=APIResponse, status_code=202)
async def generate_roadmap(
    payload: RoadmapGenerateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates AI-powered personalised learning roadmap generation.
    Returns 202 Accepted immediately; the roadmap is built asynchronously.
    Poll GET /roadmaps/active to check when status transitions from GENERATING to ACTIVE.
    """
    service = LearningService(db)
    result = await service.generate_roadmap(current_user.id, payload, background_tasks)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data=result,
        message="Roadmap generation started. Check /roadmaps/active for progress.",
        request_id=req_id,
    )


@router.get("/roadmaps/active", response_model=APIResponse[LearningRoadmapResponse])
async def get_active_roadmap(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetches the user's current active learning roadmap with all modules and tasks."""
    service = LearningService(db)
    roadmap = await service.get_active_roadmap(current_user.id)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data=LearningRoadmapResponse.model_validate(roadmap),
        request_id=req_id,
    )


@router.post("/tasks/complete", response_model=APIResponse)
async def complete_task(
    payload: TaskCompleteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks a learning task as COMPLETED and increments the user's learning streak in Redis.
    Publishes a LEARNING_TASK_COMPLETED domain event for future achievement integration.
    """
    service = LearningService(db)
    task = await service.complete_task(current_user.id, payload.task_id)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"task_id": str(task.id), "status": task.status},
        message="Task marked as completed.",
        request_id=req_id,
    )
