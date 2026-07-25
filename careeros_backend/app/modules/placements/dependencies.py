import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.placements.services.application_service import ApplicationService
from app.modules.placements.services.college_service import CollegeService, PlacementOfficerService
from app.modules.placements.services.placement_drive_service import PlacementDriveService
from app.modules.placements.services.student_ranking_service import StudentRankingService


async def get_college_service(db: AsyncSession = Depends(get_db)):
    return CollegeService(db)


async def get_placement_officer_service(db: AsyncSession = Depends(get_db)):
    return PlacementOfficerService(db)


async def get_placement_drive_service(db: AsyncSession = Depends(get_db)):
    return PlacementDriveService(db)


async def get_application_service(db: AsyncSession = Depends(get_db)):
    return ApplicationService(db)


async def get_student_ranking_service(db: AsyncSession = Depends(get_db)):
    return StudentRankingService(db)


async def verify_placement_officer_access(
    current_user: User = Depends(get_current_user),
    officer_service: PlacementOfficerService = Depends(get_placement_officer_service),
) -> uuid.UUID:
    """
    Multi-tenant isolation dependency.
    Ensures the current user is a registered placement officer and
    returns their college_id so downstream endpoints can scope queries.
    """
    college_id = await officer_service.get_officer_college_id(current_user.id)
    if not college_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a registered placement officer.",
        )
    return college_id
