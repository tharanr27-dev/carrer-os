import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.placements.models import (
    College,
    DriveEligibility,
    DriveRegistration,
    OfferLetter,
    PlacementDrive,
    PlacementOfficer,
)


class PlacementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_college(self, college: College) -> College:
        self.session.add(college)
        await self.session.commit()
        await self.session.refresh(college)
        return college

    async def get_college(self, college_id: uuid.UUID) -> Optional[College]:
        stmt = select(College).where(College.id == college_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_placement_officer(self, user_id: uuid.UUID) -> Optional[PlacementOfficer]:
        stmt = select(PlacementOfficer).where(PlacementOfficer.user_id == user_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def create_placement_drive(self, drive: PlacementDrive) -> PlacementDrive:
        self.session.add(drive)
        await self.session.commit()
        await self.session.refresh(drive)
        return drive

    async def get_placement_drive(self, drive_id: uuid.UUID) -> Optional[PlacementDrive]:
        stmt = select(PlacementDrive).where(PlacementDrive.id == drive_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_college_drives(
        self, college_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[PlacementDrive]:
        stmt = (
            select(PlacementDrive)
            .where(PlacementDrive.college_id == college_id)
            .offset(offset)
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def create_drive_registration(self, registration: DriveRegistration) -> DriveRegistration:
        self.session.add(registration)
        await self.session.commit()
        await self.session.refresh(registration)
        return registration

    async def get_drive_registration(
        self, registration_id: uuid.UUID
    ) -> Optional[DriveRegistration]:
        stmt = select(DriveRegistration).where(DriveRegistration.id == registration_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def update_drive_registration(self, registration: DriveRegistration) -> DriveRegistration:
        await self.session.commit()
        await self.session.refresh(registration)
        return registration

    async def get_drive_registrations(self, drive_id: uuid.UUID) -> List[DriveRegistration]:
        stmt = select(DriveRegistration).where(DriveRegistration.drive_id == drive_id)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_drive_eligibility(
        self, drive_id: uuid.UUID, student_id: uuid.UUID
    ) -> Optional[DriveEligibility]:
        stmt = select(DriveEligibility).where(
            DriveEligibility.drive_id == drive_id, DriveEligibility.student_id == student_id
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def create_offer_letter(self, offer: OfferLetter) -> OfferLetter:
        self.session.add(offer)
        await self.session.commit()
        await self.session.refresh(offer)
        return offer
