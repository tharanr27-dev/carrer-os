import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.interviews.models import (
    InterviewAnswer,
    InterviewFeedback,
    InterviewQuestion,
    InterviewReport,
    InterviewSession,
)


class InterviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, session: InterviewSession) -> InterviewSession:
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> InterviewSession | None:
        stmt = (
            select(InterviewSession)
            .options(selectinload(InterviewSession.questions))
            .where(InterviewSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_question(self, question: InterviewQuestion) -> InterviewQuestion:
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def save_answer(self, answer: InterviewAnswer) -> InterviewAnswer:
        self.session.add(answer)
        await self.session.commit()
        await self.session.refresh(answer)
        return answer

    async def save_feedback(self, feedback: InterviewFeedback):
        self.session.add(feedback)
        await self.session.commit()

    async def save_report(self, report: InterviewReport):
        self.session.add(report)
        await self.session.commit()
