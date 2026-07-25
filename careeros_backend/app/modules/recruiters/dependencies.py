from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.recruiters.services.application_service import ApplicationService
from app.modules.recruiters.services.company_service import CompanyService
from app.modules.recruiters.services.job_service import JobService


async def get_company_service(db: AsyncSession = Depends(get_db)):
    return CompanyService(db)


async def get_job_service(db: AsyncSession = Depends(get_db)):
    return JobService(db)


async def get_application_service(db: AsyncSession = Depends(get_db)):
    return ApplicationService(db)


async def verify_recruiter_access(
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    """
    Middleware-like dependency to ensure the user is an active recruiter
    and returns their company_id for multi-tenant isolation.
    """
    company_id = await company_service.get_recruiter_company_id(current_user.id)
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with any company."
        )
    return company_id
