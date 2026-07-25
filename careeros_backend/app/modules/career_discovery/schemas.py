from typing import Any, Dict, List, Optional

from pydantic import UUID4, BaseModel, Field

# --- API Input/Output Schemas ---


class AnswerSubmission(BaseModel):
    question_id: UUID4
    answer_text: Optional[str] = None
    selected_options: Optional[List[str]] = None


class AssessmentSubmitRequest(BaseModel):
    answers: List[AnswerSubmission]


class CareerMatchResponse(BaseModel):
    job_title: str
    suitability_score: float
    confidence_score: float
    reasoning: str

    class Config:
        from_attributes = True


class CareerReportResponse(BaseModel):
    id: UUID4
    personality_analysis: Dict[str, Any]
    interest_analysis: Dict[str, Any]
    skill_gaps: Dict[str, Any]
    career_timeline: Dict[str, Any]
    matches: List[CareerMatchResponse]

    class Config:
        from_attributes = True


# --- AI Structured Output Schemas (LangChain Pydantic Parsers) ---


class AICareerMatch(BaseModel):
    job_title: str = Field(description="The recommended job title")
    suitability_score: float = Field(description="Score from 0.0 to 100.0 representing fit")
    confidence_score: float = Field(
        description="Score from 0.0 to 100.0 representing AI confidence"
    )
    reasoning: str = Field(description="Detailed explanation of why this matches the user profile")


class AICareerAnalysis(BaseModel):
    personality_analysis: Dict[str, Any] = Field(
        description="Structured breakdown of personality traits"
    )
    interest_analysis: Dict[str, Any] = Field(
        description="Structured breakdown of professional interests"
    )
    skill_gaps: Dict[str, Any] = Field(description="Identified missing skills for top careers")
    career_timeline: Dict[str, Any] = Field(description="Suggested 1, 3, and 5 year timeline")
    recommended_matches: List[AICareerMatch] = Field(
        description="Top 3 to 5 career recommendations"
    )
