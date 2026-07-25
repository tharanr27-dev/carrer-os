from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class LearningRoadmap(AuditableBase):
    """
    Top-level AI-generated personalized roadmap for a user.
    Versioned to allow progressive updates without destroying active progress.
    """

    __tablename__ = "learning_roadmaps"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    target_role = Column(String, nullable=True)
    target_company = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, COMPLETED, ARCHIVED

    # AI context snapshot at the time of generation (for auditability)
    generation_context = Column(JSONB, nullable=True)

    modules = relationship(
        "LearningModule",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="LearningModule.order_index.asc()",
    )
    report = relationship(
        "LearningReport", uselist=False, back_populates="roadmap", cascade="all, delete-orphan"
    )


class LearningModule(AuditableBase):
    """
    A thematic chapter within a roadmap (e.g., 'System Design', 'Communication Basics').
    """

    __tablename__ = "learning_modules"

    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("learning_roadmaps.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    estimated_hours = Column(Float, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED

    roadmap = relationship("LearningRoadmap", back_populates="modules")
    tasks = relationship(
        "LearningTask",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="LearningTask.order_index.asc()",
    )


class LearningTask(AuditableBase):
    """
    An atomic, actionable learning item within a module.
    """

    __tablename__ = "learning_tasks"

    module_id = Column(UUID(as_uuid=True), ForeignKey("learning_modules.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    resource_url = Column(String, nullable=True)
    resource_type = Column(String, nullable=True)  # VIDEO, ARTICLE, EXERCISE, BOOK
    estimated_minutes = Column(Integer, nullable=True)
    difficulty = Column(String, default="MEDIUM")  # EASY, MEDIUM, HARD
    order_index = Column(Integer, default=0, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED

    module = relationship("LearningModule", back_populates="tasks")


class Course(AuditableBase):
    """
    System-wide catalog of internal and external courses.
    Reusable across multiple user roadmaps.
    """

    __tablename__ = "courses"

    title = Column(String, nullable=False)
    provider = Column(String, nullable=True)  # e.g., YouTube, Coursera, Internal
    url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    difficulty = Column(String, default="BEGINNER")
    estimated_hours = Column(Float, nullable=True)
    skills_covered = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    is_free = Column(Boolean, default=True)


class SkillProgress(AuditableBase):
    """
    Tracks a user's growing proficiency in a specific skill over time.
    """

    __tablename__ = "skill_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    current_level = Column(Float, default=0.0)  # 0 to 100
    target_level = Column(Float, default=80.0)
    required_level = Column(Float, nullable=True)  # For a specific role
    learning_hours = Column(Float, default=0.0)
    history = Column(JSONB, nullable=True)  # Array of {date, level} snapshots


class LearningReport(AuditableBase):
    """
    Periodic aggregated performance snapshot for a roadmap.
    """

    __tablename__ = "learning_reports"

    roadmap_id = Column(
        UUID(as_uuid=True), ForeignKey("learning_roadmaps.id"), unique=True, nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    completion_percentage = Column(Float, default=0.0)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    total_hours = Column(Float, default=0.0)
    streak_days = Column(Integer, default=0)

    strengths = Column(JSONB, nullable=True)
    weak_areas = Column(JSONB, nullable=True)
    next_priorities = Column(JSONB, nullable=True)

    roadmap = relationship("LearningRoadmap", back_populates="report")
