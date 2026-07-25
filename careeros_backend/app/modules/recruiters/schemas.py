from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    name: str
    domain: str
    description: Optional[str] = None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    requirements: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    pipeline_stages: Optional[List[str]] = [
        "Applied",
        "Screening",
        "Interview",
        "Offer",
        "Hired",
        "Rejected",
    ]


class JobResponse(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    description: str
    location: Optional[str]
    status: str
    requirements: Optional[List[str]]
    benefits: Optional[List[str]]
    pipeline_stages: Optional[List[str]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdate(BaseModel):
    status: str


class ApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    status: str
    fit_score: Optional[str]
    match_details: Optional[Dict[str, Any]]
    ai_insights: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateNoteCreate(BaseModel):
    note: str


class CandidateNoteResponse(BaseModel):
    id: UUID
    application_id: UUID
    recruiter_id: UUID
    note: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
