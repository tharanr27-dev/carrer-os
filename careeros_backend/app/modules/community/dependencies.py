from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.community.services.comment_service import CommentService
from app.modules.community.services.feed_service import FeedService
from app.modules.community.services.post_service import PostService
from app.modules.community.services.reaction_service import ReactionService
from app.modules.community.services.search_service import SearchService


async def get_post_service(db: AsyncSession = Depends(get_db)):
    return PostService(db)


async def get_comment_service(db: AsyncSession = Depends(get_db)):
    return CommentService(db)


async def get_reaction_service(db: AsyncSession = Depends(get_db)):
    return ReactionService(db)


async def get_feed_service(db: AsyncSession = Depends(get_db)):
    return FeedService(db)


async def get_search_service(db: AsyncSession = Depends(get_db)):
    return SearchService(db)
