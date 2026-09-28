from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.recruiters.dependencies import (
    get_application_service,
    get_company_service,
    get_job_service,
    verify_recruiter_access,
)
from app.modules.recruiters.schemas import (
    ApplicationResponse,
    ApplicationUpdate,
    CompanyCreate,
    CompanyResponse,
    JobCreate,
    JobResponse,
)
from app.modules.recruiters.services.application_service import ApplicationService
from app.modules.recruiters.services.company_service import CompanyService
from app.modules.recruiters.services.job_service import JobService
from app.modules.recruiters.tasks import generate_candidate_insights_background

router = APIRouter(tags=["recruiters"])


# Company Management (Simplified for this phase)
@router.post("/company", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_in: CompanyCreate,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    return await company_service.create_company(current_user.id, company_in)


# Jobs
@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    company_id: UUID = Depends(verify_recruiter_access),
    job_service: JobService = Depends(get_job_service),
):
    """
    Creates a job posting for the recruiter's company.
    """
    return await job_service.create_job(company_id, job_in)


@router.get("/jobs", response_model=List[JobResponse])
async def get_company_jobs(
    company_id: UUID = Depends(verify_recruiter_access),
    job_service: JobService = Depends(get_job_service),
):
    return await job_service.get_company_jobs(company_id)


# Applications (Candidate facing - applies to job)
@router.post(
    "/jobs/{job_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def apply_for_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    app = await application_service.apply_to_job(current_user.id, job_id)

    # Trigger AI parsing and deterministic matching in background
    try:
        generate_candidate_insights_background.delay(str(app.id))
    except Exception:
        pass

    return app


# Applications (Recruiter facing)
@router.get("/jobs/{job_id}/applications", response_model=List[ApplicationResponse])
async def get_job_applications(
    job_id: UUID,
    company_id: UUID = Depends(verify_recruiter_access),
    job_service: JobService = Depends(get_job_service),
    application_service: ApplicationService = Depends(get_application_service),
):
    # Verify job belongs to company
    job = await job_service.get_job(job_id)
    if not job or job.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these applications.")

    return await application_service.get_job_applications(job_id)


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: UUID,
    update_in: ApplicationUpdate,
    company_id: UUID = Depends(verify_recruiter_access),
    application_service: ApplicationService = Depends(get_application_service),
):
    """
    Updates candidate status in the recruitment pipeline (e.g. 'Shortlisted').
    """
    app = await application_service.update_application_status(application_id, update_in)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Example: If updated to 'Shortlisted', could fire a Celery notification task here.
    return app
