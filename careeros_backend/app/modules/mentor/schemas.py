from typing import List, Optional

from pydantic import UUID4, BaseModel, Field, field_validator


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class MentorStatusResponse(BaseModel):
    ai_available: bool


class MentorSuggestion(BaseModel):
    title: str
    reason: str


class MentorMessageResponse(BaseModel):
    id: UUID4
    role: str
    content: str

    class Config:
        from_attributes = True


class MentorSessionResponse(BaseModel):
    id: UUID4
    title: str
    status: str
    messages: List[MentorMessageResponse] = []

    class Config:
        from_attributes = True


class GoalMilestoneCreate(BaseModel):
    title: str


class CareerGoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    source: str = "USER"
    milestones: List[GoalMilestoneCreate] = []


class GoalMilestoneResponse(GoalMilestoneCreate):
    id: UUID4
    status: str

    class Config:
        from_attributes = True


class CareerGoalResponse(BaseModel):
    id: UUID4
    title: str
    description: Optional[str] = None
    status: str
    source: str
    milestones: List[GoalMilestoneResponse] = []

    class Config:
        from_attributes = True
