import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.models import College, PlacementOfficer
from app.modules.placements.repository import PlacementRepository
from app.modules.placements.schemas import CollegeCreate


class CollegeService:
    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    async def create_college(self, user_id: uuid.UUID, college_in: CollegeCreate) -> College:
        college = College(
            name=college_in.name, domain=college_in.domain, address=college_in.address
        )
        created_college = await self.repo.create_college(college)

        # Assign user as Placement Officer (Admin)
        officer = PlacementOfficer(
            user_id=user_id, college_id=created_college.id, role_scope="admin"
        )
        self.repo.session.add(officer)
        await self.repo.session.commit()

        return created_college

    async def get_college(self, college_id: uuid.UUID) -> Optional[College]:
        return await self.repo.get_college(college_id)


class PlacementOfficerService:
    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    async def get_officer_college_id(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        officer = await self.repo.get_placement_officer(user_id)
        return officer.college_id if officer else None
