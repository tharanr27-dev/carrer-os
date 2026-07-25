import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import CommunityPost
from app.modules.community.repository import CommunityRepository
from app.modules.community.schemas import PostCreate


class PostService:
    def __init__(self, db: AsyncSession):
        self.repo = CommunityRepository(db)

    async def create_post(self, user_id: uuid.UUID, post_in: PostCreate) -> CommunityPost:
        post = CommunityPost(
            user_id=user_id, title=post_in.title, content=post_in.content, category=post_in.category
        )
        if post_in.tags:
            tags = await self.repo.get_or_create_tags(post_in.tags)
            post.tags = tags

        # Optional: trigger AI moderation here synchronously or asynchronously

        return await self.repo.create_post(post)

    async def get_post(self, post_id: uuid.UUID) -> Optional[CommunityPost]:
        post = await self.repo.get_post_by_id(post_id)
        if post:
            # Increment view count
            post.views_count += 1
            await self.repo.update_post(post)
        return post

    async def get_recent_posts(self, limit: int = 20, offset: int = 0) -> List[CommunityPost]:
        return await self.repo.get_recent_posts(limit, offset)
