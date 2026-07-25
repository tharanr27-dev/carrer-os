import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recruiters.repository import RecruiterRepository


class CandidateMatchingEngine:
    def __init__(self, db: AsyncSession):
        self.repo = RecruiterRepository(db)

    async def calculate_deterministic_score(self, application_id: uuid.UUID) -> str:
        """
        Calculate base fit score using explicit requirements.
        In a real app, this would compare job_requirements to candidate's profile skills.
        """
        app = await self.repo.get_application(application_id)
        if not app:
            return "0%"

        # Mock calculation
        base_score = 75

        # We save this deterministically
        app.fit_score = f"{base_score}%"
        await self.repo.update_application(app)

        return app.fit_score
