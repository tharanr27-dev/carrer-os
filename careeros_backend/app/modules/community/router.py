from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.community.dependencies import (
    get_comment_service,
    get_feed_service,
    get_post_service,
    get_reaction_service,
    get_search_service,
)
from app.modules.community.schemas import (
    CommentCreate,
    CommentResponse,
    FeedItem,
    PostCreate,
    PostResponse,
    ReactionCreate,
)
from app.modules.community.services.analytics_publisher import AnalyticsPublisher
from app.modules.community.services.comment_service import CommentService
from app.modules.community.services.feed_service import FeedService
from app.modules.community.services.post_service import PostService
from app.modules.community.services.reaction_service import ReactionService
from app.modules.community.services.search_service import SearchService
from app.modules.community.tasks import moderate_post_background

router = APIRouter(tags=["community"])


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service),
):
    post = await post_service.create_post(current_user.id, post_in)

    # Trigger background AI moderation safely
    try:
        moderate_post_background.delay(str(post.id))
    except Exception:
        pass

    # Trigger Analytics
    AnalyticsPublisher.publish_event(
        user_id=current_user.id, event_type="POST_CREATED", entity_id=str(post.id)
    )

    return post


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service),
):
    post = await post_service.get_post(post_id)
    # Analytics
    AnalyticsPublisher.publish_event(
        user_id=current_user.id, event_type="POST_VIEWED", entity_id=str(post.id)
    )
    return post


@router.post(
    "/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    post_id: UUID,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    comment = await comment_service.create_comment(current_user.id, post_id, comment_in)
    AnalyticsPublisher.publish_event(
        user_id=current_user.id, event_type="COMMENT_CREATED", entity_id=str(comment.id)
    )
    return comment


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    return await comment_service.get_comments_for_post(post_id)


@router.post("/reactions", status_code=status.HTTP_201_CREATED)
async def add_reaction(
    reaction_in: ReactionCreate,
    current_user: User = Depends(get_current_user),
    reaction_service: ReactionService = Depends(get_reaction_service),
):
    await reaction_service.add_reaction(current_user.id, reaction_in)
    AnalyticsPublisher.publish_event(
        user_id=current_user.id, event_type="REACTION_ADDED", entity_id=str(reaction_in.entity_id)
    )
    return {"status": "success"}


@router.get("/feed/trending", response_model=List[FeedItem])
async def get_trending_feed(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    return await feed_service.get_trending_feed(limit, offset)


@router.get("/feed/latest", response_model=List[FeedItem])
async def get_latest_feed(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    return await feed_service.get_latest_feed(limit, offset)


@router.get("/search", response_model=List[PostResponse])
async def search_posts(
    q: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    return await search_service.search_posts(q, limit, offset)
