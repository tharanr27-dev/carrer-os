from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class TrainingQuestion(AuditableBase):
    """Reviewed (curated) and AI-generated practice questions.

    Generated rows carry owner_user_id so one student's generated questions are never
    served to another student.
    """

    __tablename__ = "training_questions"

    round = Column(String, nullable=False, index=True)  # aptitude, technical, coding, ...
    topic = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True)  # e.g. Quantitative / Logical / Verbal
    difficulty = Column(String, nullable=False, default="medium")  # easy, medium, hard
    qtype = Column(String, nullable=False)  # mcq, text, code
    label = Column(String, nullable=True)  # foundational, commonly tested, scenario-based...
    prompt = Column(Text, nullable=False)
    options = Column(JSONB, nullable=True)  # list[str] for mcq
    correct_index = Column(Integer, nullable=True)  # mcq only
    explanation = Column(Text, nullable=True)
    model_answer = Column(Text, nullable=True)
    rubric = Column(JSONB, nullable=True)  # {"keywords": [[...]], "criteria": [...], "framework": "STAR"}
    follow_ups = Column(JSONB, nullable=True)
    extra = Column(JSONB, nullable=True)  # coding: constraints, examples, tests, hints, complexity
    roles = Column(JSONB, nullable=True)  # target roles this is relevant to (None = all)
    level = Column(String, nullable=True)  # fresher / junior / mid (None = all)
    source = Column(String, nullable=False, default="curated")  # curated | generated
    review_status = Column(String, nullable=False, default="reviewed")  # reviewed | unreviewed
    fingerprint = Column(String, nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    __table_args__ = (Index("ix_training_questions_round_topic", "round", "topic"),)


class TrainingProfile(AuditableBase):
    __tablename__ = "training_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    target_role = Column(String, nullable=True)
    level = Column(String, nullable=False, default="fresher")
    language = Column(String, nullable=False, default="en")  # explanations: en | ta
    # Student-corrected resume facts: {"projects": [...], "skills": [...]}
    resume_data = Column(JSONB, nullable=True)


class TrainingAttempt(AuditableBase):
    __tablename__ = "training_attempts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(String, nullable=False)  # practice | exam | mock
    round = Column(String, nullable=False)  # a round, or "mock"
    topic = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    status = Column(String, nullable=False, default="IN_PROGRESS")  # IN_PROGRESS | COMPLETED
    config = Column(JSONB, nullable=True)  # role, level, rounds, planned_count, adaptive, ...
    time_limit_sec = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(JSONB, nullable=True)

    items = relationship(
        "TrainingAttemptItem",
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="TrainingAttemptItem.position.asc()",
        lazy="selectin",
    )


class TrainingAttemptItem(AuditableBase):
    __tablename__ = "training_attempt_items"

    attempt_id = Column(
        UUID(as_uuid=True), ForeignKey("training_attempts.id"), nullable=False, index=True
    )
    question_id = Column(UUID(as_uuid=True), ForeignKey("training_questions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # denormalised for history
    position = Column(Integer, nullable=False)
    round = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    parent_item_id = Column(UUID(as_uuid=True), nullable=True)  # set for follow-up questions
    # Follow-ups and resume/project questions are personalised, so the text lives on the item.
    prompt_override = Column(Text, nullable=True)

    answer = Column(JSONB, nullable=True)  # {"index": n} | {"text": "..."} | {"text":..,"self_eval":..}
    answered_at = Column(DateTime(timezone=True), nullable=True)
    time_taken_sec = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)  # objective questions only
    score = Column(Float, nullable=True)  # 0..1
    score_kind = Column(String, nullable=True)  # objective | ai_estimate | keyword_estimate | self_assessed
    evaluation = Column(JSONB, nullable=True)

    attempt = relationship("TrainingAttempt", back_populates="items")
    question = relationship("TrainingQuestion", lazy="joined")
