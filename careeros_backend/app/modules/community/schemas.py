from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TagSchema(BaseModel):
    name: str


class TagResponse(TagSchema):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = []


class PostResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: str
    category: str
    status: str
    views_count: int
    reactions_count: int
    comments_count: int
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[UUID] = None


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    content: str
    parent_id: Optional[UUID]
    status: str
    reactions_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReactionCreate(BaseModel):
    entity_type: str  # 'post' or 'comment'
    entity_id: UUID
    reaction_type: str = "like"


class FeedItem(BaseModel):
    post: PostResponse
    relevance_score: Optional[float] = None
