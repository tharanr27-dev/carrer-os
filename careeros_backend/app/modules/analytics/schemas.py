from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Analytics Event Schema
class AnalyticsEventCreate(BaseModel):
    event_type: str
    module: str
    entity_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class AnalyticsEventResponse(AnalyticsEventCreate):
    id: UUID
    user_id: Optional[UUID]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Daily Metric Schema
class DailyMetricResponse(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    interviews_completed: int
    communication_sessions: int
    learning_tasks_completed: int
    resume_uploads: int
    mentor_messages_sent: int
    recommendations_accepted: int
    recommendations_rejected: int
    ats_score: Optional[float]
    interview_score: Optional[float]
    communication_score: Optional[float]
    learning_completion_pct: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# AI Usage Schema
class AIUsageAnalyticsCreate(BaseModel):
    module: str
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    retry_count: int = 0


class AIUsageAnalyticsResponse(AIUsageAnalyticsCreate):
    id: UUID
    user_id: Optional[UUID]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Snapshot Schema
class AnalyticsSnapshotResponse(BaseModel):
    id: UUID
    user_id: UUID
    period: str
    career_readiness_score: Optional[float]
    resume_strength: Optional[float]
    interview_strength: Optional[float]
    communication_strength: Optional[float]
    learning_progress: Optional[float]
    total_interviews: int
    total_tasks_completed: int
    total_learning_hours: float
    total_ai_tokens: int
    total_ai_cost_usd: float
    ats_score_delta: Optional[float]
    interview_score_delta: Optional[float]
    communication_score_delta: Optional[float]
    details: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
