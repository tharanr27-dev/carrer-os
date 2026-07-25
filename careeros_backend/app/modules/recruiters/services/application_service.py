import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recruiters.models import Application
from app.modules.recruiters.repository import RecruiterRepository
from app.modules.recruiters.schemas import ApplicationUpdate


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.repo = RecruiterRepository(db)

    async def apply_to_job(self, candidate_id: uuid.UUID, job_id: uuid.UUID) -> Application:
        # Check if already applied
        apps = await self.repo.get_applications_by_job(job_id)
        for app in apps:
            if app.candidate_id == candidate_id:
                return app

        application = Application(job_id=job_id, candidate_id=candidate_id, status="Applied")
        return await self.repo.create_application(application)

    async def update_application_status(
        self, application_id: uuid.UUID, update_in: ApplicationUpdate
    ) -> Optional[Application]:
        app = await self.repo.get_application(application_id)
        if app:
            app.status = update_in.status
            return await self.repo.update_application(app)
        return None

    async def get_job_applications(
        self, job_id: uuid.UUID, status: Optional[str] = None
    ) -> List[Application]:
        return await self.repo.get_applications_by_job(job_id, status)
