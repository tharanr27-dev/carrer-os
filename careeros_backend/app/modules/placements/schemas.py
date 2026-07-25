from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CollegeCreate(BaseModel):
    name: str
    domain: str
    address: Optional[str] = None


class CollegeResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    address: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PlacementDriveCreate(BaseModel):
    title: str
    description: Optional[str] = None
    drive_type: str = "Campus"
    date_of_drive: Optional[date] = None
    requirements: Optional[Dict[str, Any]] = None
    company_id: Optional[UUID] = None


class PlacementDriveResponse(BaseModel):
    id: UUID
    college_id: UUID
    company_id: Optional[UUID]
    title: str
    description: Optional[str]
    drive_type: str
    status: str
    date_of_drive: Optional[date]
    requirements: Optional[Dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DriveRegistrationCreate(BaseModel):
    student_id: UUID


class DriveRegistrationResponse(BaseModel):
    id: UUID
    drive_id: UUID
    student_id: UUID
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DriveRegistrationUpdate(BaseModel):
    status: str


class OfferLetterCreate(BaseModel):
    package_details: str


class OfferLetterResponse(BaseModel):
    id: UUID
    registration_id: UUID
    package_details: Optional[str]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OfferLetterUpdate(BaseModel):
    status: str
