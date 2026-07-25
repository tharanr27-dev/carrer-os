from typing import List, Optional

from pydantic import UUID4, BaseModel


class ChatMessageRequest(BaseModel):
    content: str


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
