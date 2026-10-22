from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.training.textutils import clean_text

PracticeRound = Literal["aptitude", "technical", "coding", "communication", "hr", "managerial", "resume"]
MockRound = PracticeRound
Difficulty = Literal["easy", "medium", "hard"]


class MockConfig(BaseModel):
    role: Optional[str] = Field(default=None, max_length=60)
    level: Literal["fresher", "junior", "mid"] = "fresher"
    rounds: List[MockRound] = Field(min_length=1, max_length=7)
    duration_min: int = Field(default=30, ge=10, le=180)
    difficulty: Optional[Difficulty] = None
    language: Literal["en", "ta"] = "en"

    @field_validator("rounds")
    @classmethod
    def _unique(cls, v):
        return list(dict.fromkeys(v))


class AttemptCreate(BaseModel):
    mode: Literal["practice", "exam", "mock"]
    round: Optional[PracticeRound] = None
    topic: Optional[str] = Field(default=None, max_length=60)
    difficulty: Optional[Difficulty] = None
    count: int = Field(default=10, ge=1, le=40)
    time_limit_sec: Optional[int] = Field(default=None, ge=60, le=10800)
    adaptive: bool = True
    generate: bool = False
    qtype: Optional[Literal["mcq", "text"]] = None
    mock: Optional[MockConfig] = None


class AnswerRequest(BaseModel):
    item_id: str
    index: Optional[int] = Field(default=None, ge=0, le=9)
    text: Optional[str] = Field(default=None, max_length=6000)
    self_passed: Optional[int] = Field(default=None, ge=0, le=50)
    self_total: Optional[int] = Field(default=None, ge=1, le=50)
    time_taken_sec: Optional[float] = Field(default=None, ge=0, le=7200)

    @field_validator("text")
    @classmethod
    def _clean(cls, v):
        return clean_text(v, 6000) if v is not None else v


class NextRequest(BaseModel):
    generate: bool = False
    count: int = Field(default=1, ge=1, le=5)
    qtype: Optional[Literal["mcq", "text"]] = None


class ResumeProject(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    tech_stack: Optional[str] = Field(default=None, max_length=200)

    @field_validator("title", "description", "tech_stack")
    @classmethod
    def _clean(cls, v):
        return clean_text(v, 1000) if v is not None else v


class ResumeData(BaseModel):
    projects: List[ResumeProject] = Field(default_factory=list, max_length=10)
    skills: List[str] = Field(default_factory=list, max_length=40)
    degree: Optional[str] = Field(default=None, max_length=120)

    @field_validator("skills")
    @classmethod
    def _skills(cls, v):
        return [s for s in (clean_text(x, 60) for x in v) if s]

    @field_validator("degree")
    @classmethod
    def _degree(cls, v):
        return clean_text(v, 120) if v else v


class ProfileUpdate(BaseModel):
    target_role: Optional[str] = Field(default=None, max_length=60)
    level: Optional[Literal["fresher", "junior", "mid"]] = None
    language: Optional[Literal["en", "ta"]] = None
    resume_data: Optional[ResumeData] = None
    reset_resume_data: bool = False

    @field_validator("target_role")
    @classmethod
    def _role(cls, v):
        return clean_text(v, 60) if v else v

