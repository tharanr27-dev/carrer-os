import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.resumes.models import (
    Resume,
    ResumeAnalysis,
    ResumeMetadata,
    ResumeSuggestion,
)


class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_resume(self, resume: Resume) -> Resume:
        self.session.add(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def get_resume_by_id(self, resume_id: uuid.UUID) -> Resume | None:
        result = await self.session.execute(select(Resume).where(Resume.id == resume_id))
        return result.scalars().first()

    async def save_metadata(self, metadata: ResumeMetadata):
        self.session.add(metadata)
        await self.session.commit()

    async def save_analysis(
        self, analysis: ResumeAnalysis, suggestions: list[ResumeSuggestion]
    ) -> ResumeAnalysis:
        self.session.add(analysis)
        await self.session.commit()

        for sug in suggestions:
            sug.analysis_id = analysis.id
            self.session.add(sug)

        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def update_resume_status(self, resume_id: uuid.UUID, status: str):
        resume = await self.get_resume_by_id(resume_id)
        if resume:
            resume.status = status
            await self.session.commit()

    async def get_latest_analysis(self, resume_id: uuid.UUID) -> ResumeAnalysis | None:
        stmt = (
            select(ResumeAnalysis)
            .options(selectinload(ResumeAnalysis.suggestions))
            .where(ResumeAnalysis.resume_id == resume_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalars().first()
