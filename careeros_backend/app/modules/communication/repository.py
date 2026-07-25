import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.communication.models import (
    CommunicationAnalysis,
    CommunicationMessage,
    CommunicationReport,
    CommunicationSession,
    ImprovementPlan,
)


class CommunicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, session: CommunicationSession) -> CommunicationSession:
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> CommunicationSession | None:
        stmt = (
            select(CommunicationSession)
            .options(selectinload(CommunicationSession.messages))
            .where(CommunicationSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save_message(self, message: CommunicationMessage) -> CommunicationMessage:
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def save_analysis(self, analysis: CommunicationAnalysis) -> CommunicationAnalysis:
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def save_report(self, report: CommunicationReport) -> CommunicationReport:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def save_improvement_plan(self, plan: ImprovementPlan) -> ImprovementPlan:
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
