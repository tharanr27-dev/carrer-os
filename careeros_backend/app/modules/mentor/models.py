from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class MentorSession(AuditableBase):
    __tablename__ = "mentor_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Conversation")
    status = Column(String, default="ACTIVE")  # ACTIVE, ARCHIVED

    messages = relationship(
        "MentorMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MentorMessage.created_at.asc()",
    )


class MentorMessage(AuditableBase):
    __tablename__ = "mentor_messages"

    session_id = Column(UUID(as_uuid=True), ForeignKey("mentor_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # SYSTEM, USER, AI
    content = Column(Text, nullable=False)

    # Track cost/usage directly on the message
    token_usage = Column(JSONB, nullable=True)

    session = relationship("MentorSession", back_populates="messages")


class CareerGoal(AuditableBase):
    __tablename__ = "career_goals"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, COMPLETED
    source = Column(String, default="USER")  # USER, AI_SUGGESTED

    milestones = relationship(
        "GoalMilestone",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="GoalMilestone.created_at.asc()",
    )


class GoalMilestone(AuditableBase):
    __tablename__ = "goal_milestones"

    goal_id = Column(UUID(as_uuid=True), ForeignKey("career_goals.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, COMPLETED

    goal = relationship("CareerGoal", back_populates="milestones")
