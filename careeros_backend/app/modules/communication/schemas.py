from typing import Any, Dict, List

from pydantic import UUID4, BaseModel, Field

# --- API Input/Output Schemas ---


class CommunicationSessionCreate(BaseModel):
    mode: str = "WORKPLACE"


class CommunicationSessionResponse(BaseModel):
    id: UUID4
    mode: str
    status: str

    class Config:
        from_attributes = True


class CommunicationSocketEvent(BaseModel):
    event_type: str  # e.g., MESSAGE_SUBMITTED, FINISH_SESSION
    payload: Dict[str, Any]


# --- AI Structured Output Schemas (LangChain Pydantic Parsers) ---


class AILinguisticFeedback(BaseModel):
    category: str = Field(description="E.g., Grammar, Vocabulary, Filler Word")
    original_text: str = Field(description="The exact text to be corrected")
    suggested_correction: str = Field(description="How it should be said")
    reasoning: str = Field(description="Why this is a better choice")


class AICommunicationAnalysis(BaseModel):
    grammar_score: float = Field(description="Score out of 10")
    vocabulary_score: float = Field(description="Score out of 10")
    tone_score: float = Field(description="Professional Tone out of 10")
    clarity_score: float = Field(description="Clarity out of 10")
    feedbacks: List[AILinguisticFeedback] = Field(description="Specific actionable corrections")


class AICommunicationReport(BaseModel):
    overall_score: float
    grammar_score: float
    vocabulary_score: float
    tone_score: float
    fluency_score: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
