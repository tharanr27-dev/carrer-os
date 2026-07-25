from sqlalchemy import BigInteger, Boolean, Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import AuditableBase


class AnalyticsEvent(AuditableBase):
    """
    Raw, append-only event log. One row per domain event across the platform.
    Will grow very large — partitioned by created_at month in production.
    Composite index on (user_id, event_type, created_at) is mandatory.
    """

    __tablename__ = "analytics_events"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)  # e.g., INTERVIEW_COMPLETED
    module = Column(String, nullable=False)  # e.g., interviews, resumes, learning
    entity_id = Column(String, nullable=True)  # ID of the related entity
    payload = Column(JSONB, nullable=True)  # Contextual event metadata


class DailyMetric(AuditableBase):
    """
    Pre-aggregated per-user daily counters.
    Upserted by Celery — never recalculated from scratch.
    """

    __tablename__ = "daily_metrics"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)

    # Activity counters
    interviews_completed = Column(Integer, default=0)
    communication_sessions = Column(Integer, default=0)
    learning_tasks_completed = Column(Integer, default=0)
    resume_uploads = Column(Integer, default=0)
    mentor_messages_sent = Column(Integer, default=0)
    recommendations_accepted = Column(Integer, default=0)
    recommendations_rejected = Column(Integer, default=0)

    # Score snapshots (latest value for that day)
    ats_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    learning_completion_pct = Column(Float, nullable=True)


class AIUsageAnalytics(AuditableBase):
    """
    One row per AI Pipeline invocation.
    Source of truth for cost tracking, latency monitoring, and token optimization.
    """

    __tablename__ = "ai_usage_analytics"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    module = Column(String, nullable=False)  # e.g., mentor, interviews, learning
    provider = Column(String, nullable=True)  # openai, gemini, claude
    model = Column(String, nullable=True)  # e.g., gpt-4-turbo
    prompt_version = Column(String, nullable=True)

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Integer, nullable=True)

    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


class AnalyticsSnapshot(AuditableBase):
    """
    Monthly point-in-time summary per user.
    What dashboard APIs actually read — never touches raw events.
    """

    __tablename__ = "analytics_snapshots"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period = Column(String, nullable=False)  # e.g., "2026-07" (YYYY-MM)

    # Career readiness composite
    career_readiness_score = Column(Float, nullable=True)
    resume_strength = Column(Float, nullable=True)
    interview_strength = Column(Float, nullable=True)
    communication_strength = Column(Float, nullable=True)
    learning_progress = Column(Float, nullable=True)

    # Usage totals for the period
    total_interviews = Column(Integer, default=0)
    total_tasks_completed = Column(Integer, default=0)
    total_learning_hours = Column(Float, default=0.0)
    total_ai_tokens = Column(BigInteger, default=0)
    total_ai_cost_usd = Column(Float, default=0.0)

    # Trend deltas (compared to previous period)
    ats_score_delta = Column(Float, nullable=True)
    interview_score_delta = Column(Float, nullable=True)
    communication_score_delta = Column(Float, nullable=True)
    details = Column(JSONB, nullable=True)
