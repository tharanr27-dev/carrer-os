import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.mentor.models import CareerGoal, GoalMilestone, MentorSession
from app.modules.mentor.repository import MentorRepository
from app.modules.mentor.schemas import CareerGoalCreate, ChatMessageRequest


class MentorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = MentorRepository(session)
        self.audit_service = AuditService(session)

    async def create_session(self, user_id: uuid.UUID) -> MentorSession:
        return await self.repository.create_session(user_id)

    async def send_message(
        self, user_id: uuid.UUID, session_id: uuid.UUID, request: ChatMessageRequest
    ):
        # 1. Fetch Session & Validate Ownership
        mentor_session = await self.repository.get_session(session_id)
        if not mentor_session or mentor_session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 2. Append User Message
        await self.repository.append_message(session_id, "USER", request.content)

        # 3. Reply. A real conversation needs an AI provider; without one the mentor says so plainly and gives
        #    guidance derived from the student's own saved data instead of pretending to chat.
        content, tokens = await self._reply(user_id, mentor_session, request.content)

        # 4. Append the reply
        ai_msg = await self.repository.append_message(
            session_id=session_id, role="AI", content=content, tokens=tokens
        )

        # 5. Audit Event
        await self.audit_service.log_action(
            user_id, "MENTOR_INTERACTION", "MentorSession", str(session_id)
        )

        return ai_msg

    async def _reply(self, user_id: uuid.UUID, mentor_session: MentorSession, message: str):
        from app.modules.recommendations.context_aggregator import ContextAggregator
        from app.modules.recommendations.recommendation_engine import RecommendationEngine
        from app.modules.training.llm import LLMUnavailable, get_llm

        context = await ContextAggregator(self.session).build_context(user_id)
        recs = (await RecommendationEngine().generate_candidates(context)).recommendations
        llm = get_llm()
        if llm.available:
            history = [
                {"role": "assistant" if m.role == "AI" else "user", "content": m.content[:1500]}
                for m in list(mentor_session.messages)[-10:]
                if m.role in ("USER", "AI")
            ]
            history.append({"role": "user", "content": message})
            facts = "; ".join(f"{r.title} ({r.reason})" for r in recs[:4]) or "no saved activity yet"
            system = (
                "You are a concise, honest career mentor for an IT student. Use ONLY these facts about the student "
                f"and never invent achievements, scores or experience: {facts}. If you do not know something, say so. "
                "Reply in under 150 words, plain text."
            )
            try:
                return (await llm.complete_text(system, history, max_tokens=500))[:2000], {"provider": "llm"}
            except LLMUnavailable:
                pass  # fall through to the honest local reply
        steps = "\n".join(f"{i}. {r.title}: {r.reason}" for i, r in enumerate(recs[:3], 1))
        reply = (
            "The AI mentor chat is not available: no AI provider is configured on this server, so I cannot hold a real "
            "conversation or answer free-form questions."
            + "\n\nHere is what your saved activity suggests as next steps:\n"
            + steps
        )
        return reply, {"provider": "none"}

    async def create_goal(self, user_id: uuid.UUID, request: CareerGoalCreate) -> CareerGoal:
        goal = CareerGoal(
            user_id=user_id,
            title=request.title,
            description=request.description,
            source=request.source,
        )
        milestones = [GoalMilestone(title=m.title) for m in request.milestones]

        return await self.repository.create_goal(goal, milestones)
