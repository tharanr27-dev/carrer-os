import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.recruiters.models import Application, Company, Job, RecruiterProfile


class RecruiterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_company(self, company: Company) -> Company:
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def get_company(self, company_id: uuid.UUID) -> Optional[Company]:
        stmt = select(Company).where(Company.id == company_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def create_job(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, job_id: uuid.UUID) -> Optional[Job]:
        stmt = select(Job).where(Job.id == job_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_jobs_by_company(
        self, company_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[Job]:
        stmt = select(Job).where(Job.company_id == company_id).offset(offset).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_open_jobs(self, limit: int = 100, offset: int = 0) -> list:
        """Open jobs across all companies, joined with the company name (candidate-facing)."""
        stmt = (
            select(Job, Company.name)
            .join(Company, Company.id == Job.company_id)
            .where(Job.status == "open")
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return (await self.session.execute(stmt)).all()

    async def get_applications_by_candidate(self, candidate_id: uuid.UUID) -> list:
        stmt = (
            select(Application, Job.title, Company.name)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Job.company_id)
            .where(Application.candidate_id == candidate_id)
            .order_by(Application.created_at.desc())
        )
        return (await self.session.execute(stmt)).all()

    async def create_application(self, application: Application) -> Application:
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def get_application(self, application_id: uuid.UUID) -> Optional[Application]:
        stmt = select(Application).where(Application.id == application_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def update_application(self, application: Application) -> Application:
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def get_applications_by_job(
        self, job_id: uuid.UUID, status: Optional[str] = None
    ) -> List[Application]:
        stmt = select(Application).where(Application.job_id == job_id)
        if status:
            stmt = stmt.where(Application.status == status)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_recruiter_profile(self, user_id: uuid.UUID) -> Optional[RecruiterProfile]:
        stmt = select(RecruiterProfile).where(RecruiterProfile.user_id == user_id)
        return (await self.session.execute(stmt)).scalars().first()
