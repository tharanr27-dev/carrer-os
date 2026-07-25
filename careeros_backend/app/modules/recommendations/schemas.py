from datetime import datetime
from typing import List, Optional

from pydantic import UUID4, BaseModel, Field

# ---------------------------------------------------------------------------
# REST API Schemas
# ---------------------------------------------------------------------------


class RecommendationFeedbackRequest(BaseModel):
    recommendation_id: UUID4
    action: str  # ACCEPTED | REJECTED | IGNORED | COMPLETED | DISMISSED | SAVED | BOOKMARKED
    feedback_text: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: UUID4
    category: str
    title: str
    description: Optional[str]
    confidence_score: float
    estimated_impact: float
    difficulty: str
    priority: int
    reason: Optional[str]
    related_skills: Optional[List[str]]
    source_modules: Optional[List[str]]
    status: str
    expires_at: Optional[datetime]
    version: int

    class Config:
        from_attributes = True


class RecommendationFeedResponse(BaseModel):
    """The ranked feed returned to the client."""

    user_id: UUID4
    generated_at: datetime
    recommendations: List[RecommendationResponse]
    total: int


# ---------------------------------------------------------------------------
# AI Structured Output Schemas (enforced via LangChain Pydantic Parser)
# ---------------------------------------------------------------------------


class AIRecommendationItem(BaseModel):
    category: str = Field(
        description="One of: JOB, SKILL, COURSE, RESUME, INTERVIEW, "
        "COMMUNICATION, COMPANY, CERTIFICATION, PROJECT, PRACTICE"
    )
    title: str = Field(description="Short, actionable recommendation title")
    description: str = Field(description="Detailed explanation and next steps")
    reason: str = Field(description="Why this recommendation was chosen for this specific user")
    confidence_score: float = Field(description="AI confidence 0.0 to 1.0")
    estimated_impact: float = Field(description="Expected career impact if acted upon, 0.0 to 1.0")
    difficulty: str = Field(description="EASY, MEDIUM, or HARD")
    related_skills: List[str] = Field(description="Skills addressed by this recommendation")
    source_modules: List[str] = Field(
        description="Which CareerOS modules surfaced this need (e.g., Phase 8 Interview)"
    )


class AIRecommendationList(BaseModel):
    recommendations: List[AIRecommendationItem] = Field(
        description="Ordered list of 10–15 personalized recommendations"
    )
