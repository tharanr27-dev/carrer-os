from typing import List, Optional

from pydantic import BaseModel, Field


class JobFilters(BaseModel):
    query: Optional[str] = None
    country: Optional[str] = None
    page: int = 1
    seniority: Optional[str] = None
    employment_type: Optional[str] = None
    worldwide: Optional[bool] = None
    exclude_worldwide: Optional[bool] = None


class JobMatch(BaseModel):
    """Transparent keyword-overlap estimate. Not a hiring probability."""

    score: int = Field(ge=0, le=100)
    matched_skills: List[str] = Field(default_factory=list)
    reason: str = ""


class RecommendedJobItem(BaseModel):
    id: str
    title: str
    company: str
    company_slug: Optional[str] = None
    company_logo: Optional[str] = None
    # Himalayas only lists remote roles, so this is always "Remote"; it is never a city.
    location: str = "Remote"
    remote: bool = True
    eligible_countries: List[str] = Field(default_factory=list)
    employment_type: Optional[str] = None
    seniority: List[str] = Field(default_factory=list)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    description: str = ""
    posted_at: Optional[str] = None
    expires_at: Optional[str] = None
    apply_url: str
    source: str = "Himalayas"
    match: Optional[JobMatch] = None


class Attribution(BaseModel):
    name: str = "Himalayas"
    url: str = "https://himalayas.app"


class RecommendedJobsResponse(BaseModel):
    success: bool = True
    source: str = "Himalayas"
    attribution: Attribution = Field(default_factory=Attribution)
    filters: JobFilters
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    match_method: Optional[str] = None
    jobs: List[RecommendedJobItem] = Field(default_factory=list)
