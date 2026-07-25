from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase

post_tags = Table(
    "post_tags",
    AuditableBase.metadata,
    Column("post_id", UUID(as_uuid=True), ForeignKey("community_posts.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("community_tags.id"), primary_key=True),
)


class CommunityPost(AuditableBase):
    __tablename__ = "community_posts"

    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(
        String, index=True, nullable=False
    )  # e.g., 'discussion', 'interview_experience', 'resource'
    status = Column(
        String, index=True, default="published"
    )  # 'draft', 'published', 'flagged', 'hidden'

    views_count = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)

    # Moderation flags
    is_ai_moderated = Column(Boolean, default=False)
    moderation_score = Column(JSONB, nullable=True)  # E.g. {"toxicity": 0.1, "spam": 0.05}

    tags = relationship("CommunityTag", secondary=post_tags, lazy="selectin")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship(
        "Reaction",
        cascade="all, delete-orphan",
        foreign_keys="Reaction.entity_id",
        primaryjoin="and_(CommunityPost.id == foreign(Reaction.entity_id), Reaction.entity_type == 'post')",
        overlaps="reactions",
    )


class CommunityTag(AuditableBase):
    __tablename__ = "community_tags"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)


class Comment(AuditableBase):
    __tablename__ = "community_comments"

    post_id = Column(UUID(as_uuid=True), ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("community_comments.id"), nullable=True
    )  # Threaded replies
    status = Column(String, default="published")

    reactions_count = Column(Integer, default=0)

    post = relationship("CommunityPost", back_populates="comments")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Comment", back_populates="replies", remote_side="Comment.id")
    reactions = relationship(
        "Reaction",
        cascade="all, delete-orphan",
        foreign_keys="Reaction.entity_id",
        primaryjoin="and_(Comment.id == foreign(Reaction.entity_id), Reaction.entity_type == 'comment')",
        overlaps="reactions",
    )


class Reaction(AuditableBase):
    __tablename__ = "community_reactions"

    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    entity_type = Column(String, index=True, nullable=False)  # 'post' or 'comment'
    entity_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    reaction_type = Column(String, nullable=False, default="like")  # 'like', 'upvote', 'celebrate'


class Bookmark(AuditableBase):
    __tablename__ = "community_bookmarks"

    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("community_posts.id"), nullable=False)


class ModerationAction(AuditableBase):
    __tablename__ = "community_moderation_actions"

    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String, nullable=False)  # 'flagged_by_ai', 'hidden_by_admin', 'approved'
    reason = Column(String, nullable=True)
    performed_by = Column(UUID(as_uuid=True), nullable=True)  # None if AI
