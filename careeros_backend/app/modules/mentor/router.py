import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.mentor.schemas import (
    CareerGoalCreate,
    CareerGoalResponse,
    ChatMessageRequest,
    MentorMessageResponse,
    MentorSessionResponse,
)
from app.modules.mentor.service import MentorService

router = APIRouter()


@router.post("/sessions", response_model=APIResponse[MentorSessionResponse])
async def create_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MentorService(db)
    session = await service.create_session(current_user.id)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=MentorSessionResponse.model_validate(session), request_id=req_id)


@router.get("/sessions/latest", response_model=APIResponse[MentorSessionResponse])
async def get_latest_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The user's most recent active conversation with its history (404 if none yet)."""
    session = await MentorService(db).repository.get_latest_session(current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="No mentor conversation yet")
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=MentorSessionResponse.model_validate(session), request_id=req_id)


@router.get("/goals", response_model=APIResponse[list[CareerGoalResponse]])
async def list_goals(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goals = await MentorService(db).repository.list_goals(current_user.id)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data=[CareerGoalResponse.model_validate(g) for g in goals], request_id=req_id
    )


@router.post("/sessions/{session_id}/message", response_model=APIResponse[MentorMessageResponse])
async def send_message(
    session_id: uuid.UUID,
    payload: ChatMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MentorService(db)
    ai_msg = await service.send_message(current_user.id, session_id, payload)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=MentorMessageResponse.model_validate(ai_msg), request_id=req_id)


@router.post("/goals", response_model=APIResponse[CareerGoalResponse])
async def create_goal(
    payload: CareerGoalCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MentorService(db)
    goal = await service.create_goal(current_user.id, payload)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=CareerGoalResponse.model_validate(goal), request_id=req_id)
