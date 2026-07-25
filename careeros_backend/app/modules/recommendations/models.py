from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class Recommendation(AuditableBase):
    """
    A single AI-generated, ranked recommendation for a user.
    Versioned per generation cycle; expires after a configurable TTL.
    """

    __tablename__ = "recommendations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Classification
    category = Column(
        String, nullable=False
    )  # JOB, SKILL, COURSE, RESUME, INTERVIEW, COMPANY, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # AI-generated scores (raw, before ranking)
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0–1
    estimated_impact = Column(Float, nullable=False, default=0.0)  # 0–1
    difficulty = Column(String, default="MEDIUM")  # EASY, MEDIUM, HARD

    # Ranking output
    rank_score = Column(Float, nullable=True)  # Calculated by Ranking Engine
    priority = Column(Integer, default=5)  # 1 (highest) to 10 (lowest)

    # Metadata
    reason = Column(Text, nullable=True)  # Human-readable explanation
    source_modules = Column(JSONB, nullable=True)  # e.g., ["Phase 8", "Phase 10"]
    related_skills = Column(JSONB, nullable=True)
    version = Column(Integer, default=1)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Lifecycle
    status = Column(String, default="ACTIVE")  # ACTIVE, ACCEPTED, REJECTED, COMPLETED, EXPIRED

    feedbacks = relationship(
        "RecommendationFeedback", back_populates="recommendation", cascade="all, delete-orphan"
    )


class RecommendationFeedback(AuditableBase):
    """
    Records every explicit user interaction with a recommendation.
    Powers the historical acceptance-rate signal in the Ranking Engine.
    """

    __tablename__ = "recommendation_feedbacks"

    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # ACCEPTED | REJECTED | IGNORED | COMPLETED | DISMISSED | SAVED | BOOKMARKED
    action = Column(String, nullable=False)
    feedback_text = Column(Text, nullable=True)

    recommendation = relationship("Recommendation", back_populates="feedbacks")


class RecommendationAnalytics(AuditableBase):
    """
    Aggregated per-user recommendation performance metrics.
    Refreshed by Celery on a nightly schedule.
    """

    __tablename__ = "recommendation_analytics"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    total_generated = Column(Integer, default=0)
    total_accepted = Column(Integer, default=0)
    total_rejected = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    acceptance_rate = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)

    # AI cost tracking — feeds Phase 17 dashboards
    total_tokens_used = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
