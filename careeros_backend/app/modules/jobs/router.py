from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.jobs.schemas import RecommendedJobsResponse
from app.modules.jobs.service import (
    MAX_PAGE,
    HimalayasService,
    apply_matches,
    get_himalayas_service,
)
from app.modules.jobs.skills import load_student_skills
from app.modules.auth.models import User

router = APIRouter()


@router.get(
    "/recommended",
    response_model=RecommendedJobsResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommended remote IT jobs (Himalayas)",
    description=(
        "Live remote listings from the Himalayas public API (https://himalayas.app/jobs/api/search). "
        "`country` filters by the country candidates may work from; it does NOT mean the job is "
        "located there. Himalayas lists remote roles only, so no listing is labelled as being in a "
        "Tamil Nadu city. Page size is fixed at 20 by the upstream API. When the student has "
        "profile or resume skills, each job carries a keyword-overlap `match` estimate."
    ),
)
async def get_recommended_jobs(
    q: Annotated[Optional[str], Query(max_length=100, description="Keyword or role title")] = None,
    country: Annotated[
        Optional[str],
        Query(pattern="^[A-Za-z]{2}$", description="ISO 3166-1 alpha-2 candidate-eligibility country"),
    ] = None,
    page: Annotated[int, Query(ge=1, le=MAX_PAGE, description="1-based page number")] = 1,
    employment_type: Annotated[
        Optional[Literal["full-time", "part-time", "contractor", "temporary", "intern"]],
        Query(description="Employment type"),
    ] = None,
    seniority: Annotated[
        Optional[Literal["entry-level", "mid-level", "senior", "manager", "director", "executive"]],
        Query(description="Seniority level"),
    ] = None,
    worldwide: Annotated[Optional[bool], Query(description="Only worldwide-remote roles")] = None,
    exclude_worldwide: Annotated[
        Optional[bool], Query(description="With `country`, drop worldwide roles")
    ] = None,
    service: HimalayasService = Depends(get_himalayas_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendedJobsResponse:
    result = await service.fetch_recommended_jobs(
        q=q,
        country=country,
        page=page,
        employment_type=employment_type,
        seniority=seniority,
        worldwide=worldwide,
        exclude_worldwide=exclude_worldwide,
    )
    skills = await load_student_skills(db, current_user.id)
    return apply_matches(result, skills)
