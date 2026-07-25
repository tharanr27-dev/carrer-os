from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class InterviewSession(AuditableBase):
    __tablename__ = "interview_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    interview_type = Column(String, nullable=False)  # HR, TECHNICAL, BEHAVIORAL
    company = Column(String, nullable=True)
    difficulty = Column(String, default="MEDIUM")
    status = Column(String, default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED

    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    questions = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.created_at.asc()",
    )
    report = relationship(
        "InterviewReport", uselist=False, back_populates="session", cascade="all, delete-orphan"
    )


class InterviewQuestion(AuditableBase):
    __tablename__ = "interview_questions"

    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    expected_skills = Column(JSONB, nullable=True)  # e.g., ["System Design", "Scalability"]

    answer = relationship(
        "InterviewAnswer", uselist=False, back_populates="question", cascade="all, delete-orphan"
    )
    session = relationship("InterviewSession", back_populates="questions")


class InterviewAnswer(AuditableBase):
    __tablename__ = "interview_answers"

    question_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_questions.id"), unique=True, nullable=False
    )
    answer_text = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)  # Future voice capability

    feedback = relationship(
        "InterviewFeedback", uselist=False, back_populates="answer", cascade="all, delete-orphan"
    )
    question = relationship("InterviewQuestion", back_populates="answer")


class InterviewFeedback(AuditableBase):
    __tablename__ = "interview_feedbacks"

    answer_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_answers.id"), unique=True, nullable=False
    )

    score = Column(Float, nullable=False)  # 0 to 10
    grammar_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)

    strengths = Column(JSONB, nullable=True)
    improvements = Column(JSONB, nullable=True)

    answer = relationship("InterviewAnswer", back_populates="feedback")


class InterviewReport(AuditableBase):
    __tablename__ = "interview_reports"

    session_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), unique=True, nullable=False
    )

    overall_score = Column(Float, nullable=False)
    technical_score = Column(Float, nullable=False)
    communication_score = Column(Float, nullable=False)

    detailed_analysis = Column(JSONB, nullable=True)
    recommended_learning = Column(JSONB, nullable=True)

    session = relationship("InterviewSession", back_populates="report")
