from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    MeResponse,
    RefreshRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.modules.auth.service import AuthService
from app.modules.placements.models import PlacementOfficer
from app.modules.recruiters.models import RecruiterProfile

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.authenticate(credentials)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.register(user_in)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges a valid refresh token for a fresh access/refresh token pair."""
    return await AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Returns the authenticated identity with roles, permissions and org linkage."""
    recruiter = (
        await db.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == current_user.id))
    ).scalars().first()
    officer = (
        await db.execute(select(PlacementOfficer).where(PlacementOfficer.user_id == current_user.id))
    ).scalars().first()
    permissions = sorted({p.name for role in current_user.roles for p in role.permissions})
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=sorted(r.name for r in current_user.roles),
        permissions=permissions,
        company_id=recruiter.company_id if recruiter else None,
        college_id=officer.college_id if officer else None,
    )
