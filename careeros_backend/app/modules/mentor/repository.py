import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.mentor.models import CareerGoal, GoalMilestone, MentorMessage, MentorSession


class MentorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self, user_id: uuid.UUID, title: str = "New Conversation"
    ) -> MentorSession:
        session = MentorSession(user_id=user_id, title=title)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> MentorSession | None:
        stmt = (
            select(MentorSession)
            .options(selectinload(MentorSession.messages))
            .where(MentorSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_latest_session(self, user_id: uuid.UUID) -> MentorSession | None:
        stmt = (
            select(MentorSession)
            .options(selectinload(MentorSession.messages))
            .where(MentorSession.user_id == user_id, MentorSession.status == "ACTIVE")
            .order_by(MentorSession.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def list_goals(self, user_id: uuid.UUID) -> list[CareerGoal]:
        stmt = (
            select(CareerGoal)
            .options(selectinload(CareerGoal.milestones))
            .where(CareerGoal.user_id == user_id)
            .order_by(CareerGoal.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def append_message(
        self, session_id: uuid.UUID, role: str, content: str, tokens: dict = None
    ) -> MentorMessage:
        msg = MentorMessage(session_id=session_id, role=role, content=content, token_usage=tokens)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def create_goal(self, goal: CareerGoal, milestones: list[GoalMilestone]) -> CareerGoal:
        self.session.add(goal)
        await self.session.commit()

        for m in milestones:
            m.goal_id = goal.id
            self.session.add(m)

        await self.session.commit()
        await self.session.refresh(goal)
        return goal
