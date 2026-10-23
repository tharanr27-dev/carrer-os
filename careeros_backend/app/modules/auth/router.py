from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.login_throttle import login_throttle
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
async def login(credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    login_throttle.check(credentials.email, ip)  # 429 before any password check while blocked
    try:
        token = await AuthService(db).authenticate(credentials)
    except HTTPException as exc:
        if exc.status_code == 401:  # wrong credentials only; inactive accounts etc. are not guesses
            login_throttle.record_failure(credentials.email, ip)
        raise
    login_throttle.record_success(credentials.email, ip)
    return token


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
