from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.users.schemas import ProfileResponse, ProfileUpdate
from app.modules.users.service import UserService

router = APIRouter()


@router.get("/me/profile", response_model=APIResponse[ProfileResponse])
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    profile = await service.get_or_create_profile(current_user.id)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=ProfileResponse.model_validate(profile), request_id=req_id)


@router.put("/me/profile", response_model=APIResponse[ProfileResponse])
async def update_my_profile(
    request: Request,
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    profile = await service.update_profile(current_user.id, profile_update)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=ProfileResponse.model_validate(profile), request_id=req_id)
