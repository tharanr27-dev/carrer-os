import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.training.llm import TrainingLLM, get_llm
from app.modules.training.schemas import AnswerRequest, AttemptCreate, NextRequest, ProfileUpdate
from app.modules.training.service import TrainingService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db), llm: TrainingLLM = Depends(get_llm)) -> TrainingService:
    return TrainingService(db, llm)


def _rid(request: Request):
    return getattr(request.state, "request_id", None)


@router.get("/meta")
async def meta(request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)):
    return success_response(data=await svc.meta(user.id), request_id=_rid(request))


@router.get("/profile")
async def get_profile(request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)):
    return success_response(data=await svc.profile_view(user.id), request_id=_rid(request))


@router.put("/profile")
async def put_profile(
    payload: ProfileUpdate, request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)
):
    return success_response(data=await svc.update_profile(user.id, payload), request_id=_rid(request))


@router.get("/questions")
async def browse_questions(
    request: Request,
    round: Optional[str] = Query(default=None, max_length=30),
    topic: Optional[str] = Query(default=None, max_length=60),
    difficulty: Optional[str] = Query(default=None, pattern="^(easy|medium|hard)$"),
    page: int = Query(default=1, ge=1, le=1000),
    size: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    svc: TrainingService = Depends(_svc),
):
    """Question bank listing. Answers and explanations are never included here."""
    return success_response(data=await svc.browse(user.id, round, topic, difficulty, page, size), request_id=_rid(request))


@router.post("/attempts", status_code=201)
async def create_attempt(
    payload: AttemptCreate, request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)
):
    return success_response(data=await svc.create_attempt(user.id, payload), request_id=_rid(request))


@router.get("/attempts")
async def list_attempts(
    request: Request,
    page: int = Query(default=1, ge=1, le=1000),
    size: int = Query(default=10, ge=1, le=50),
    status: Optional[str] = Query(default=None, pattern="^(IN_PROGRESS|COMPLETED)$"),
    user: User = Depends(get_current_user),
    svc: TrainingService = Depends(_svc),
):
    return success_response(data=await svc.history(user.id, page, size, status), request_id=_rid(request))


@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: uuid.UUID, request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)
):
    return success_response(data=await svc.attempt_view(user.id, attempt_id), request_id=_rid(request))


@router.post("/attempts/{attempt_id}/answer")
async def answer(
    attempt_id: uuid.UUID, payload: AnswerRequest, request: Request,
    user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc),
):
    return success_response(data=await svc.answer(user.id, attempt_id, payload), request_id=_rid(request))


@router.post("/attempts/{attempt_id}/next")
async def next_questions(
    attempt_id: uuid.UUID, payload: NextRequest, request: Request,
    user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc),
):
    return success_response(data=await svc.next_questions(user.id, attempt_id, payload), request_id=_rid(request))


@router.post("/attempts/{attempt_id}/finish")
async def finish(
    attempt_id: uuid.UUID, request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)
):
    return success_response(data=await svc.finish(user.id, attempt_id), request_id=_rid(request))


@router.get("/progress")
async def progress(request: Request, user: User = Depends(get_current_user), svc: TrainingService = Depends(_svc)):
    return success_response(data=await svc.progress(user.id), request_id=_rid(request))
