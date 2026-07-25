from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.repository import CommunityRepository
from app.modules.community.schemas import FeedItem, PostResponse


class FeedService:
    def __init__(self, db: AsyncSession):
        self.repo = CommunityRepository(db)

    async def get_latest_feed(self, limit: int = 20, offset: int = 0) -> List[FeedItem]:
        posts = await self.repo.get_recent_posts(limit, offset)
        feed = []
        for p in posts:
            post_resp = PostResponse.model_validate(p)
            feed.append(FeedItem(post=post_resp, relevance_score=1.0))
        return feed

    async def get_trending_feed(self, limit: int = 20, offset: int = 0) -> List[FeedItem]:
        # In a real implementation, this would fetch from Redis ZSET.
        # Fallback to recent posts for now.
        return await self.get_latest_feed(limit, offset)
