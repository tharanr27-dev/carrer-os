import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.models import PlacementDrive
from app.modules.placements.repository import PlacementRepository
from app.modules.placements.schemas import PlacementDriveCreate


class PlacementDriveService:
    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    async def create_drive(
        self, college_id: uuid.UUID, drive_in: PlacementDriveCreate
    ) -> PlacementDrive:
        drive = PlacementDrive(
            college_id=college_id,
            company_id=drive_in.company_id,
            title=drive_in.title,
            description=drive_in.description,
            drive_type=drive_in.drive_type,
            date_of_drive=drive_in.date_of_drive,
            requirements=drive_in.requirements,
            status="Upcoming",
        )
        return await self.repo.create_placement_drive(drive)

    async def get_drive(self, drive_id: uuid.UUID) -> Optional[PlacementDrive]:
        return await self.repo.get_placement_drive(drive_id)

    async def get_college_drives(
        self, college_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[PlacementDrive]:
        return await self.repo.get_college_drives(college_id, limit, offset)
