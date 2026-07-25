from typing import List, Optional

from pydantic import UUID4, BaseModel, Field

# ---------------------------------------------------------------------------
# API Request / Response Schemas
# ---------------------------------------------------------------------------


class RoadmapGenerateRequest(BaseModel):
    target_role: Optional[str] = None
    target_company: Optional[str] = None


class LearningTaskResponse(BaseModel):
    id: UUID4
    title: str
    description: Optional[str] = None
    resource_url: Optional[str] = None
    resource_type: Optional[str] = None
    estimated_minutes: Optional[int] = None
    difficulty: str
    status: str

    class Config:
        from_attributes = True


class LearningModuleResponse(BaseModel):
    id: UUID4
    title: str
    description: Optional[str] = None
    order_index: int
    estimated_hours: Optional[float] = None
    status: str
    tasks: List[LearningTaskResponse] = []

    class Config:
        from_attributes = True


class LearningRoadmapResponse(BaseModel):
    id: UUID4
    title: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    version: int
    status: str
    modules: List[LearningModuleResponse] = []

    class Config:
        from_attributes = True


class TaskCompleteRequest(BaseModel):
    task_id: UUID4


# ---------------------------------------------------------------------------
# AI Structured Output Schemas (for LangChain Pydantic Parser enforcement)
# ---------------------------------------------------------------------------


class AILearningTask(BaseModel):
    title: str = Field(description="Short, actionable task title")
    description: str = Field(description="Detailed instructions for the task")
    resource_type: str = Field(description="VIDEO, ARTICLE, EXERCISE, BOOK, or PROJECT")
    resource_url: Optional[str] = Field(description="URL if applicable", default=None)
    estimated_minutes: int = Field(description="Estimated time to complete in minutes")
    difficulty: str = Field(description="EASY, MEDIUM, or HARD")


class AILearningModule(BaseModel):
    title: str = Field(description="Module theme, e.g., 'System Design Fundamentals'")
    description: str = Field(description="What this module covers and why it matters")
    estimated_hours: float = Field(description="Total estimated hours for the module")
    tasks: List[AILearningTask] = Field(description="Ordered list of tasks in this module")


class AILearningRoadmap(BaseModel):
    title: str = Field(description="Personalized roadmap title")
    description: str = Field(description="Overview of the roadmap and expected outcomes")
    modules: List[AILearningModule] = Field(description="Ordered list of learning modules (max 5)")
