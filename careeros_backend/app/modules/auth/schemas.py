from typing import List, Optional

from pydantic import UUID4, BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(UserResponse):
    """Current session identity: RBAC roles/permissions plus org linkage."""

    roles: List[str] = []
    permissions: List[str] = []
    company_id: Optional[UUID4] = None
    college_id: Optional[UUID4] = None
