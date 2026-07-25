import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.models import DriveRegistration, OfferLetter
from app.modules.placements.repository import PlacementRepository
from app.modules.placements.schemas import DriveRegistrationUpdate, OfferLetterCreate


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    async def register_student(
        self, drive_id: uuid.UUID, student_id: uuid.UUID
    ) -> DriveRegistration:
        # Note: In a real system, we'd check if student is eligible first via DriveEligibility
        registration = DriveRegistration(
            drive_id=drive_id, student_id=student_id, status="Registered"
        )
        return await self.repo.create_drive_registration(registration)

    async def update_registration_status(
        self, registration_id: uuid.UUID, update_in: DriveRegistrationUpdate
    ) -> Optional[DriveRegistration]:
        reg = await self.repo.get_drive_registration(registration_id)
        if reg:
            reg.status = update_in.status
            return await self.repo.update_drive_registration(reg)
        return None

    async def get_drive_registrations(self, drive_id: uuid.UUID) -> List[DriveRegistration]:
        return await self.repo.get_drive_registrations(drive_id)

    async def add_offer_letter(
        self, registration_id: uuid.UUID, offer_in: OfferLetterCreate
    ) -> OfferLetter:
        offer = OfferLetter(
            registration_id=registration_id,
            package_details=offer_in.package_details,
            status="Pending",
        )
        return await self.repo.create_offer_letter(offer)
