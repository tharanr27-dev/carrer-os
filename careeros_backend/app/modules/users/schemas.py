from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import UUID4, AnyHttpUrl, BaseModel, ConfigDict, field_validator


class SocialLinks(BaseModel):
    """Social link fields are stored as plain strings in a JSONB column."""

    model_config = ConfigDict(populate_by_name=True)

    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    twitter: Optional[str] = None

    @field_validator("linkedin", "github", "portfolio", "twitter", mode="before")
    @classmethod
    def coerce_url_to_str(cls, v: Any) -> Optional[str]:
        """Accept both str and Pydantic HttpUrl objects; always store as str."""
        if v is None:
            return None
        return str(v)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    # Store as plain str so SQLAlchemy can write to a String column.
    profile_image_url: Optional[str] = None
    social_links: Optional[SocialLinks] = None
    role_specific_data: Optional[Dict[str, Any]] = None

    @field_validator("profile_image_url", mode="before")
    @classmethod
    def coerce_image_url_to_str(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v)


class ExperienceCreate(BaseModel):
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False
    description: Optional[str] = None


class ExperienceResponse(ExperienceCreate):
    id: UUID4

    class Config:
        from_attributes = True


class ProfileResponse(ProfileUpdate):
    id: UUID4
    user_id: UUID4
    completion_percentage: int
    experiences: List[ExperienceResponse] = []

    class Config:
        from_attributes = True


class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class UserPreferenceResponse(UserPreferenceUpdate):
    id: UUID4

    class Config:
        from_attributes = True

