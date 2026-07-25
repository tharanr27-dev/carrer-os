import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import Reaction
from app.modules.community.repository import CommunityRepository
from app.modules.community.schemas import ReactionCreate


class ReactionService:
    def __init__(self, db: AsyncSession):
        self.repo = CommunityRepository(db)
        self.db = db

    async def add_reaction(self, user_id: uuid.UUID, reaction_in: ReactionCreate) -> Reaction:
        reaction = Reaction(
            user_id=user_id,
            entity_type=reaction_in.entity_type,
            entity_id=reaction_in.entity_id,
            reaction_type=reaction_in.reaction_type,
        )

        created = await self.repo.add_reaction(reaction)

        # Update counts
        if created:
            if reaction_in.entity_type == "post":
                post = await self.repo.get_post_by_id(reaction_in.entity_id)
                if post:
                    post.reactions_count += 1
                    await self.repo.update_post(post)
            # Add logic for comment reaction count updates if needed

        return created
