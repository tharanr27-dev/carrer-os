import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recruiters.models import Job
from app.modules.recruiters.repository import RecruiterRepository
from app.modules.recruiters.schemas import JobCreate


class JobService:
    def __init__(self, db: AsyncSession):
        self.repo = RecruiterRepository(db)

    async def create_job(self, company_id: uuid.UUID, job_in: JobCreate) -> Job:
        job = Job(
            company_id=company_id,
            title=job_in.title,
            description=job_in.description,
            location=job_in.location,
            requirements=job_in.requirements,
            benefits=job_in.benefits,
            pipeline_stages=job_in.pipeline_stages,
            status="open",
        )
        return await self.repo.create_job(job)

    async def get_job(self, job_id: uuid.UUID) -> Optional[Job]:
        return await self.repo.get_job(job_id)

    async def get_company_jobs(
        self, company_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[Job]:
        return await self.repo.get_jobs_by_company(company_id, limit, offset)
