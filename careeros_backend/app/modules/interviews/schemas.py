from typing import Any, Dict, List, Optional

from pydantic import UUID4, BaseModel, Field

# --- API Input/Output Schemas ---


class SessionCreateRequest(BaseModel):
    interview_type: str = "TECHNICAL"
    company: Optional[str] = None
    difficulty: str = "MEDIUM"


class SessionResponse(BaseModel):
    id: UUID4
    interview_type: str
    status: str

    class Config:
        from_attributes = True


class SocketEvent(BaseModel):
    event_type: str  # e.g., ANSWER_SUBMITTED, FINISH_INTERVIEW
    payload: Dict[str, Any]


class SocketResponseEvent(BaseModel):
    event_type: str  # e.g., NEXT_QUESTION, INTERVIEW_COMPLETED
    payload: Dict[str, Any]


# --- AI Structured Output Schemas (LangChain Pydantic Parsers) ---


class AIEvaluationScore(BaseModel):
    overall_score: float = Field(description="Score out of 10")
    grammar_score: float = Field(description="Grammar score out of 10")
    confidence_score: float = Field(description="Confidence/Clarity out of 10")
    strengths: List[str] = Field(description="What they did well")
    improvements: List[str] = Field(description="Actionable areas to improve")


class AIFinalReport(BaseModel):
    overall_score: float
    technical_score: float
    communication_score: float
    detailed_analysis: Dict[str, Any]
    recommended_learning: List[str]
