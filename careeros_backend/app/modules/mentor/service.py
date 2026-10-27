import time
import uuid
from collections import defaultdict, deque

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.audit.service import AuditService
from app.modules.mentor.models import CareerGoal, GoalMilestone, MentorSession
from app.modules.mentor.repository import MentorRepository
from app.modules.mentor.prompt import build_system
from app.modules.mentor.schemas import CareerGoalCreate, ChatMessageRequest


# Provider failure reason -> (HTTP status, user-facing message). Provider text and credentials are never relayed.
_FAILURES = {
    "not_configured": (
        503,
        "The AI Mentor is not set up on this server yet. An administrator needs to set GROQ_API_KEY in the "
        "backend environment and restart the server.",
    ),
    "timeout": (504, "The AI Mentor took too long to answer. Please try again."),
    "network": (503, "The AI Mentor could not reach its AI provider. Please try again shortly."),
    "auth": (502, "The server's AI provider credentials were rejected. An administrator needs to check the AI provider API key."),
    "rate_limited": (429, "The AI provider is busy right now. Please wait a moment and try again."),
    "quota": (503, "The AI provider's usage limit has been reached. An administrator needs to check the account."),
    "model_unavailable": (502, "The configured AI model is unavailable. An administrator needs to check the model name (GROQ_MODEL)."),
    "overloaded": (503, "The AI provider is temporarily overloaded. Please try again shortly."),
    "bad_output": (502, "The AI Mentor returned an unreadable answer. Please try again."),
    "error": (502, "The AI Mentor could not answer right now. Please try again."),
}


class _MessageLimiter:
    """Sliding one-minute window per user (in-memory, per process)."""

    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= settings.MENTOR_MESSAGES_PER_MINUTE:
            return False
        hits.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()


mentor_limiter = _MessageLimiter()


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

        # 2. Per-user throttle (checked before any provider call so it also bounds cost)
        if not mentor_limiter.allow(str(user_id)):
            raise HTTPException(status_code=429, detail="You are sending messages too quickly. Please wait a moment.")

        # 3. Ask the provider. Nothing is saved unless a genuine answer comes back, so a failed request leaves no
        #    orphaned user message (a retry does not duplicate it) and never stores a fake assistant reply.
        content, tokens = await self._reply(user_id, mentor_session, request.content)

        await self.repository.append_message(session_id, "USER", request.content)
        ai_msg = await self.repository.append_message(
            session_id=session_id, role="AI", content=content, tokens=tokens
        )

        # 4. Audit Event
        await self.audit_service.log_action(
            user_id, "MENTOR_INTERACTION", "MentorSession", str(session_id)
        )

        return ai_msg

    async def status(self) -> dict:
        from app.modules.training.llm import get_llm

        return {"ai_available": get_llm().available}

    async def suggestions(self, user_id: uuid.UUID) -> list[dict]:
        """Next steps derived from this user's own saved activity. Shown separately from chat answers."""
        from app.modules.recommendations.context_aggregator import ContextAggregator
        from app.modules.recommendations.recommendation_engine import RecommendationEngine

        context = await ContextAggregator(self.session).build_context(user_id)
        recs = (await RecommendationEngine().generate_candidates(context)).recommendations
        return [{"title": r.title, "reason": r.reason} for r in recs[:4]]

    async def _reply(self, user_id: uuid.UUID, mentor_session: MentorSession, message: str):
        from app.modules.recommendations.context_aggregator import ContextAggregator
        from app.modules.training.llm import LLMUnavailable, get_llm

        llm = get_llm()
        if not llm.available:
            raise HTTPException(status_code=503, detail=_FAILURES["not_configured"][1])

        context = await ContextAggregator(self.session).build_context(user_id)
        history = [
            {"role": "assistant" if m.role == "AI" else "user", "content": m.content[:4000]}
            for m in list(mentor_session.messages)[-settings.MENTOR_HISTORY_MESSAGES :]
            if m.role in ("USER", "AI")
        ]
        history.append({"role": "user", "content": message})
        try:
            reply = await llm.complete_text(build_system(context), history, max_tokens=settings.MENTOR_MAX_REPLY_TOKENS)
        except LLMUnavailable as exc:
            status, text = _FAILURES.get(getattr(exc, "reason", "error"), _FAILURES["error"])
            raise HTTPException(status_code=status, detail=text)
        return reply[:6000], {"provider": "llm", "model": llm.model}

    async def create_goal(self, user_id: uuid.UUID, request: CareerGoalCreate) -> CareerGoal:
        goal = CareerGoal(
            user_id=user_id,
            title=request.title,
            description=request.description,
            source=request.source,
        )
        milestones = [GoalMilestone(title=m.title) for m in request.milestones]

        return await self.repository.create_goal(goal, milestones)
