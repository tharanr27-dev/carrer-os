import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.community.models import Comment, CommunityPost, CommunityTag, Reaction


class CommunityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_tag_by_name(self, name: str) -> Optional[CommunityTag]:
        stmt = select(CommunityTag).where(CommunityTag.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_create_tags(self, tag_names: List[str]) -> List[CommunityTag]:
        tags = []
        for name in tag_names:
            tag = await self.get_tag_by_name(name)
            if not tag:
                tag = CommunityTag(name=name)
                self.session.add(tag)
            tags.append(tag)
        await self.session.commit()
        return tags

    async def create_post(self, post: CommunityPost) -> CommunityPost:
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_post_by_id(self, post_id: uuid.UUID) -> Optional[CommunityPost]:
        stmt = (
            select(CommunityPost)
            .options(selectinload(CommunityPost.tags))
            .where(CommunityPost.id == post_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_recent_posts(self, limit: int = 20, offset: int = 0) -> List[CommunityPost]:
        stmt = (
            select(CommunityPost)
            .options(selectinload(CommunityPost.tags))
            .order_by(CommunityPost.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_post(self, post: CommunityPost) -> CommunityPost:
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def create_comment(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def get_comments_for_post(self, post_id: uuid.UUID) -> List[Comment]:
        stmt = select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_reaction(self, reaction: Reaction) -> Reaction:
        # Check if already reacted
        stmt = select(Reaction).where(
            Reaction.user_id == reaction.user_id,
            Reaction.entity_id == reaction.entity_id,
            Reaction.entity_type == reaction.entity_type,
        )
        existing = (await self.session.execute(stmt)).scalars().first()
        if not existing:
            self.session.add(reaction)
            await self.session.commit()
            await self.session.refresh(reaction)
            return reaction
        return existing
