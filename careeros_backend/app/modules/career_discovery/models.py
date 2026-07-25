from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class AssessmentTemplate(AuditableBase):
    __tablename__ = "assessment_templates"

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String, default="1.0")

    questions = relationship(
        "AssessmentQuestion", back_populates="template", cascade="all, delete-orphan"
    )


class AssessmentQuestion(AuditableBase):
    __tablename__ = "assessment_questions"

    template_id = Column(UUID(as_uuid=True), ForeignKey("assessment_templates.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="TEXT")  # e.g., TEXT, MULTIPLE_CHOICE, LIKERT
    options = Column(JSONB, nullable=True)  # Used if MULTIPLE_CHOICE
    order_index = Column(Integer, default=0)

    template = relationship("AssessmentTemplate", back_populates="questions")


class UserAssessment(AuditableBase):
    __tablename__ = "user_assessments"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("assessment_templates.id"), nullable=False)
    status = Column(String, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED

    answers = relationship("UserAnswer", back_populates="assessment", cascade="all, delete-orphan")
    report = relationship(
        "CareerReport", uselist=False, back_populates="assessment", cascade="all, delete-orphan"
    )


class UserAnswer(AuditableBase):
    __tablename__ = "user_answers"

    assessment_id = Column(UUID(as_uuid=True), ForeignKey("user_assessments.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("assessment_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    selected_options = Column(JSONB, nullable=True)

    assessment = relationship("UserAssessment", back_populates="answers")


class CareerReport(AuditableBase):
    __tablename__ = "career_reports"

    assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("user_assessments.id"), unique=True, nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    personality_analysis = Column(JSONB, nullable=True)
    interest_analysis = Column(JSONB, nullable=True)
    skill_gaps = Column(JSONB, nullable=True)
    career_timeline = Column(JSONB, nullable=True)

    matches = relationship("CareerMatch", back_populates="report", cascade="all, delete-orphan")
    assessment = relationship("UserAssessment", back_populates="report")


class CareerMatch(AuditableBase):
    __tablename__ = "career_matches"

    report_id = Column(UUID(as_uuid=True), ForeignKey("career_reports.id"), nullable=False)
    job_title = Column(String, nullable=False)
    suitability_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)

    report = relationship("CareerReport", back_populates="matches")
