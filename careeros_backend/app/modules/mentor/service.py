import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.pipeline import AIGlobalPipeline
from app.modules.audit.service import AuditService
from app.modules.mentor.models import CareerGoal, GoalMilestone, MentorSession
from app.modules.mentor.repository import MentorRepository
from app.modules.mentor.schemas import CareerGoalCreate, ChatMessageRequest


class MentorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = MentorRepository(session)
        self.audit_service = AuditService(session)
        self.ai_pipeline = AIGlobalPipeline()

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

        # 3. Build Chat History for Memory
        chat_history = [
            {"role": msg.role, "content": msg.content} for msg in mentor_session.messages
        ]

        # 4. Context Builder (Stubbed for Phase 7, dynamic in Phase 17)
        system_prompt = (
            "You are a professional AI Career Mentor. Keep responses concise and actionable."
        )

        # 5. Route to AI Platform Orchestrator
        from app.modules.ai.dependencies import get_ai_orchestrator

        orchestrator = get_ai_orchestrator()

        request_payload = {
            "provider_name": "mock",
            "model_name": "gpt-4",
            "task": "conversational_mentor",
            "system_prompt": system_prompt,
            "chat_history": chat_history,
            "new_message": request.content,
        }

        ai_response = await orchestrator.process_request("mock", request_payload)
        # Assuming the orchestrator mock returns the message in response_text
        content = ai_response.get("response_text", "I'm sorry, I could not process that.")
        tokens = ai_response.get("tokens_used", 0)

        # 6. Append AI Message
        ai_msg = await self.repository.append_message(
            session_id=session_id, role="AI", content=content, tokens=tokens
        )

        # 7. Audit Event
        await self.audit_service.log_action(
            user_id, "MENTOR_INTERACTION", "MentorSession", str(session_id)
        )

        return ai_msg

    async def create_goal(self, user_id: uuid.UUID, request: CareerGoalCreate) -> CareerGoal:
        goal = CareerGoal(
            user_id=user_id,
            title=request.title,
            description=request.description,
            source=request.source,
        )
        milestones = [GoalMilestone(title=m.title) for m in request.milestones]

        return await self.repository.create_goal(goal, milestones)
