import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.career_discovery.models import (
    AssessmentTemplate,
    CareerMatch,
    CareerReport,
    UserAnswer,
    UserAssessment,
)


class DiscoveryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_templates(self):
        result = await self.session.execute(select(AssessmentTemplate))
        return result.scalars().all()

    async def create_user_assessment(self, assessment: UserAssessment) -> UserAssessment:
        self.session.add(assessment)
        await self.session.commit()
        await self.session.refresh(assessment)
        return assessment

    async def save_answers(self, answers: list[UserAnswer]):
        self.session.add_all(answers)
        await self.session.commit()

    async def mark_assessment_completed(self, assessment_id: uuid.UUID):
        stmt = select(UserAssessment).where(UserAssessment.id == assessment_id)
        result = await self.session.execute(stmt)
        assessment = result.scalars().first()
        if assessment:
            assessment.status = "COMPLETED"
            await self.session.commit()

    async def save_career_report(
        self, report: CareerReport, matches: list[CareerMatch]
    ) -> CareerReport:
        self.session.add(report)
        await self.session.commit()

        for match in matches:
            match.report_id = report.id
            self.session.add(match)

        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_report_by_id(self, report_id: uuid.UUID) -> CareerReport | None:
        stmt = (
            select(CareerReport)
            .options(selectinload(CareerReport.matches))
            .where(CareerReport.id == report_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
