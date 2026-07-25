from typing import Any, Dict, List, Optional

from pydantic import UUID4, BaseModel, Field


class ResumeUploadResponse(BaseModel):
    id: UUID4
    file_name: str
    status: str
    message: str


class ResumeAnalysisRequest(BaseModel):
    job_description_text: Optional[str] = None


class ResumeSuggestionResponse(BaseModel):
    category: str
    suggestion_text: str
    impact: str

    class Config:
        from_attributes = True


class ResumeAnalysisResponse(BaseModel):
    id: UUID4
    ats_score: float
    grammar_score: float
    quality_score: float
    keyword_analysis: Dict[str, Any]
    suggestions: List[ResumeSuggestionResponse]

    class Config:
        from_attributes = True


# --- AI Structured Output Schemas (LangChain Pydantic Parsers) ---


class AIResumeSuggestion(BaseModel):
    category: str = Field(description="Category of suggestion (Formatting, Action Verbs, etc)")
    suggestion_text: str = Field(description="Actionable advice")
    impact: str = Field(description="HIGH, MEDIUM, or LOW impact")


class AIResumeAnalysis(BaseModel):
    ats_score: float = Field(description="Score from 0.0 to 100.0 representing ATS parseability")
    grammar_score: float = Field(
        description="Score from 0.0 to 100.0 representing grammatical correctness"
    )
    quality_score: float = Field(description="Score from 0.0 to 100.0 representing overall impact")
    keyword_analysis: Dict[str, Any] = Field(
        description="Found and missing keywords against industry standards"
    )
    suggestions: List[AIResumeSuggestion] = Field(description="Actionable improvements")
    extracted_skills: List[str] = Field(description="List of raw skills found in text")
