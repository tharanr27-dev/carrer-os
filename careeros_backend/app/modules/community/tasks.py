import asyncio
import uuid

from celery import shared_task

from app.db.session import AsyncSessionLocal
from app.modules.community.repository import CommunityRepository
from app.modules.community.services.ai_moderation import AIContentModerationEngine


@shared_task
def moderate_post_background(post_id_str: str):
    """
    Background task to moderate a newly created post.
    """
    post_id = uuid.UUID(post_id_str)

    async def _run():
        async with AsyncSessionLocal() as db:
            repo = CommunityRepository(db)
            moderator = AIContentModerationEngine(db)

            post = await repo.get_post_by_id(post_id)
            if not post:
                return

            is_safe, scores = await moderator.moderate_content(post.content)

            post.is_ai_moderated = True
            post.moderation_score = scores

            if not is_safe:
                post.status = "flagged"

            await repo.update_post(post)

    asyncio.run(_run())
