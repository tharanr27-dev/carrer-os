from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.community.models import CommunityPost


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_posts(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> List[CommunityPost]:
        # Simple ILIKE search for now. Prepare for full-text or vector search.
        stmt = (
            select(CommunityPost)
            .options(selectinload(CommunityPost.tags))
            .where(
                CommunityPost.title.ilike(f"%{query}%") | CommunityPost.content.ilike(f"%{query}%")
            )
            .order_by(CommunityPost.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
