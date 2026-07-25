from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class CommunicationSession(AuditableBase):
    __tablename__ = "communication_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mode = Column(String, nullable=False)  # e.g., PRESENTATION, INTERVIEW, WORKPLACE
    status = Column(String, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED

    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    messages = relationship(
        "CommunicationMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CommunicationMessage.created_at.asc()",
    )
    report = relationship(
        "CommunicationReport", uselist=False, back_populates="session", cascade="all, delete-orphan"
    )


class CommunicationMessage(AuditableBase):
    __tablename__ = "communication_messages"

    session_id = Column(UUID(as_uuid=True), ForeignKey("communication_sessions.id"), nullable=False)
    speaker = Column(String, nullable=False)  # USER, SYSTEM
    content_text = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)  # Future voice integration

    analysis = relationship(
        "CommunicationAnalysis",
        uselist=False,
        back_populates="message",
        cascade="all, delete-orphan",
    )
    session = relationship("CommunicationSession", back_populates="messages")


class CommunicationAnalysis(AuditableBase):
    __tablename__ = "communication_analyses"

    message_id = Column(
        UUID(as_uuid=True), ForeignKey("communication_messages.id"), unique=True, nullable=False
    )

    grammar_score = Column(Float, nullable=False)
    vocabulary_score = Column(Float, nullable=False)
    tone_score = Column(Float, nullable=False)
    clarity_score = Column(Float, nullable=False)

    # Store actionable feedback points directly as JSONB array to reduce table sprawl
    feedbacks = Column(JSONB, nullable=True)

    message = relationship("CommunicationMessage", back_populates="analysis")


class CommunicationReport(AuditableBase):
    __tablename__ = "communication_reports"

    session_id = Column(
        UUID(as_uuid=True), ForeignKey("communication_sessions.id"), unique=True, nullable=False
    )

    overall_score = Column(Float, nullable=False)
    grammar_score = Column(Float, nullable=False)
    vocabulary_score = Column(Float, nullable=False)
    tone_score = Column(Float, nullable=False)
    fluency_score = Column(Float, nullable=False)  # Important for voice

    strengths = Column(JSONB, nullable=True)
    weaknesses = Column(JSONB, nullable=True)
    improvement_suggestions = Column(JSONB, nullable=True)

    session = relationship("CommunicationSession", back_populates="report")


class ImprovementPlan(AuditableBase):
    __tablename__ = "improvement_plans"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    daily_tasks = Column(JSONB, nullable=True)
    weekly_goals = Column(JSONB, nullable=True)
    recommended_reading = Column(JSONB, nullable=True)
    status = Column(String, default="ACTIVE")
