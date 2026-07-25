import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.users.models import Profile, UserPreference


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> Profile | None:
        stmt = (
            select(Profile)
            .options(
                selectinload(Profile.experiences),
                selectinload(Profile.educations),
                selectinload(Profile.projects),
                selectinload(Profile.certifications),
                selectinload(Profile.profile_skills),
            )
            .where(Profile.user_id == user_id)
        )

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_profile(self, profile: Profile) -> Profile:
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_preferences(self, user_id: uuid.UUID) -> UserPreference | None:
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_preferences(self, prefs: UserPreference) -> UserPreference:
        self.session.add(prefs)
        await self.session.commit()
        await self.session.refresh(prefs)
        return prefs
