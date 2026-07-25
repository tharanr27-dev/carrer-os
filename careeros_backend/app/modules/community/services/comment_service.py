import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import Comment
from app.modules.community.repository import CommunityRepository
from app.modules.community.schemas import CommentCreate


class CommentService:
    def __init__(self, db: AsyncSession):
        self.repo = CommunityRepository(db)
        self.db = db

    async def create_comment(
        self, user_id: uuid.UUID, post_id: uuid.UUID, comment_in: CommentCreate
    ) -> Comment:
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=comment_in.content,
            parent_id=comment_in.parent_id,
        )

        # Update post comment count
        post = await self.repo.get_post_by_id(post_id)
        if post:
            post.comments_count += 1
            await self.repo.update_post(post)

        return await self.repo.create_comment(comment)

    async def get_comments_for_post(self, post_id: uuid.UUID) -> List[Comment]:
        return await self.repo.get_comments_for_post(post_id)
