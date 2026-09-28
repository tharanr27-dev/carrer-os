import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.interviews.evaluation_engine import InterviewEvaluationEngine
from app.modules.interviews.models import (
    InterviewAnswer,
    InterviewFeedback,
    InterviewQuestion,
    InterviewReport,
    InterviewSession,
)
from app.modules.interviews.repository import InterviewRepository
from app.modules.interviews.schemas import SessionCreateRequest
from app.modules.interviews.websocket import manager


class InterviewService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = InterviewRepository(session)
        self.audit_service = AuditService(session)
        self.eval_engine = InterviewEvaluationEngine()

    async def initialize_session(
        self, user_id: uuid.UUID, request: SessionCreateRequest
    ) -> InterviewSession:
        return await self.repository.create_session(
            InterviewSession(
                user_id=user_id,
                interview_type=request.interview_type,
                company=request.company,
                difficulty=request.difficulty,
            )
        )

    async def handle_websocket_event(
        self, session_id: uuid.UUID, event: dict, background_tasks: BackgroundTasks
    ):
        event_type = event.get("event_type")
        payload = event.get("payload", {})

        if event_type == "START":
            # Send the very first question
            question_text = "Let's begin. Could you please introduce yourself and your background?"
            q = await self.repository.create_question(
                InterviewQuestion(session_id=session_id, question_text=question_text)
            )
            await manager.send_json(
                {
                    "event_type": "NEXT_QUESTION",
                    "payload": {"question_id": str(q.id), "text": question_text},
                },
                session_id,
            )

        elif event_type == "ANSWER_SUBMITTED":
            q_id = uuid.UUID(payload.get("question_id"))
            text = payload.get("answer_text")

            answer = await self.repository.save_answer(
                InterviewAnswer(question_id=q_id, answer_text=text)
            )

            # Send immediate ACK so client knows we got it
            await manager.send_json({"event_type": "EVALUATING"}, session_id)

            # Offload heavy AI processing to background
            background_tasks.add_task(
                self._async_evaluate_and_continue, session_id, answer.id, text
            )

        elif event_type == "FINISH":
            db_session = await self.repository.get_session(session_id)
            db_session.status = "COMPLETED"
            db_session.ended_at = datetime.now(timezone.utc)
            await self.session.commit()

            # Offload Final Report Generation
            background_tasks.add_task(self._async_generate_report, session_id)
            await manager.send_json({"event_type": "INTERVIEW_COMPLETED"}, session_id)

    async def _async_evaluate_and_continue(
        self, session_id: uuid.UUID, answer_id: uuid.UUID, answer_text: str
    ):
        from app.db.session import AsyncSessionLocal
        # 1. Evaluate
        evaluation = await self.eval_engine.evaluate_answer("dummy_q", answer_text)
        async with AsyncSessionLocal() as session:
            repository = InterviewRepository(session)
            await repository.save_feedback(
                InterviewFeedback(
                    answer_id=answer_id,
                    score=evaluation.overall_score,
                    grammar_score=evaluation.grammar_score,
                    confidence_score=evaluation.confidence_score,
                    strengths=evaluation.strengths,
                    improvements=evaluation.improvements,
                )
            )

            # 2. Generate Next Question
            next_q_text = await self.eval_engine.generate_next_question([], "TECHNICAL")
            q = await repository.create_question(
                InterviewQuestion(session_id=session_id, question_text=next_q_text)
            )

        # 3. Push to WebSocket
        await manager.send_json(
            {
                "event_type": "NEXT_QUESTION",
                "payload": {"question_id": str(q.id), "text": next_q_text},
            },
            session_id,
        )

    async def _async_generate_report(self, session_id: uuid.UUID):
        from app.db.session import AsyncSessionLocal
        report_data = await self.eval_engine.generate_final_report([])
        async with AsyncSessionLocal() as session:
            repository = InterviewRepository(session)
            await repository.save_report(
                InterviewReport(
                    session_id=session_id,
                    overall_score=report_data.overall_score,
                    technical_score=report_data.technical_score,
                    communication_score=report_data.communication_score,
                    detailed_analysis=report_data.detailed_analysis,
                    recommended_learning=report_data.recommended_learning,
                )
            )
