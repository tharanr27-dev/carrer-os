import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recruiters.models import Company, RecruiterProfile
from app.modules.recruiters.repository import RecruiterRepository
from app.modules.recruiters.schemas import CompanyCreate


class CompanyService:
    def __init__(self, db: AsyncSession):
        self.repo = RecruiterRepository(db)

    async def create_company(self, user_id: uuid.UUID, company_in: CompanyCreate) -> Company:
        company = Company(
            name=company_in.name, domain=company_in.domain, description=company_in.description
        )
        created_company = await self.repo.create_company(company)

        # Link user as admin for this company
        existing_profile = await self.repo.get_recruiter_profile(user_id)
        if existing_profile:
            existing_profile.company_id = created_company.id
            existing_profile.role = "admin"
        else:
            profile = RecruiterProfile(user_id=user_id, company_id=created_company.id, role="admin")
            self.repo.session.add(profile)
        await self.repo.session.commit()

        return created_company

    async def get_company(self, company_id: uuid.UUID) -> Optional[Company]:
        return await self.repo.get_company(company_id)

    async def get_recruiter_company_id(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        profile = await self.repo.get_recruiter_profile(user_id)
        return profile.company_id if profile else None
