import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import get_redis
from app.modules.audit.service import AuditService
from app.modules.users.models import Profile
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import ProfileUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)
        self.audit_service = AuditService(session)

    def calculate_completion(self, profile: Profile) -> int:
        score = 0
        if profile.first_name and profile.last_name:
            score += 20
        if profile.headline:
            score += 10
        if profile.bio:
            score += 10
        if profile.profile_image_url:
            score += 10
        if profile.experiences:
            score += 20
        if profile.educations:
            score += 20
        if profile.profile_skills:
            score += 10
        return min(score, 100)

    async def get_or_create_profile(self, user_id: uuid.UUID) -> Profile:
        # In a full implementation, we'd check redis first:
        # cached = await redis.get(f"user:{user_id}:profile")

        profile = await self.repository.get_profile_by_user_id(user_id)
        if not profile:
            profile = await self.repository.create_profile(Profile(user_id=user_id))

        # Re-calc completion on fetch
        profile.completion_percentage = self.calculate_completion(profile)
        await self.session.commit()
        return profile

    async def update_profile(self, user_id: uuid.UUID, profile_update: ProfileUpdate) -> Profile:
        profile = await self.get_or_create_profile(user_id)

        update_data = profile_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "social_links" and value:
                profile.social_links = value
            else:
                setattr(profile, key, value)

        profile.completion_percentage = self.calculate_completion(profile)
        await self.session.commit()

        await self.audit_service.log_action(
            user_id=user_id,
            action="PROFILE_UPDATED",
            entity_type="Profile",
            entity_id=str(profile.id),
        )

        redis = await get_redis()
        await redis.delete(f"user:{user_id}:profile")

        return profile
