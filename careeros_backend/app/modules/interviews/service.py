import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tasks import spawn
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
        self.eval_engine = InterviewEvaluationEngine(session)

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

    async def _asked(self, session_id: uuid.UUID, db: AsyncSession) -> List[str]:
        rows = await db.execute(
            select(InterviewQuestion.question_text)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.created_at.asc())
        )
        return [r[0] for r in rows.all()]

    async def handle_websocket_event(
        self, session_id: uuid.UUID, event: dict, background_tasks: BackgroundTasks
    ):
        event_type = event.get("event_type")
        payload = event.get("payload", {})

        if event_type == "START":
            db_session = await self.repository.get_session(session_id)
            question_text, skills = await self.eval_engine.next_question(
                db_session.user_id, db_session.interview_type, db_session.difficulty, asked=[]
            )
            q = await self.repository.create_question(
                InterviewQuestion(session_id=session_id, question_text=question_text, expected_skills=skills)
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

            spawn(self._async_evaluate_and_continue(session_id, answer.id, text))

        elif event_type == "FINISH":
            db_session = await self.repository.get_session(session_id)
            db_session.status = "COMPLETED"
            db_session.ended_at = datetime.now(timezone.utc)
            await self.session.commit()

            spawn(self._async_generate_report(session_id))
            await manager.send_json({"event_type": "INTERVIEW_COMPLETED"}, session_id)

    async def _async_evaluate_and_continue(
        self, session_id: uuid.UUID, answer_id: uuid.UUID, answer_text: str
    ):
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            engine = InterviewEvaluationEngine(session)
            repository = InterviewRepository(session)

            # 1. Score the answer against the question it answers (rule-based rubric).
            question_text = (
                await session.execute(
                    select(InterviewQuestion.question_text)
                    .join(InterviewAnswer, InterviewAnswer.question_id == InterviewQuestion.id)
                    .where(InterviewAnswer.id == answer_id)
                )
            ).scalar_one()
            evaluation = await engine.evaluate_answer(question_text, answer_text)
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

            # 2. Choose the next question: a probing follow-up when one exists, otherwise a fresh reviewed question.
            db_session = await repository.get_session(session_id)
            asked = await self._asked(session_id, session)
            next_text, skills = await engine.next_question(
                db_session.user_id, db_session.interview_type, db_session.difficulty, asked, last_answer=answer_text
            )
            q = await repository.create_question(
                InterviewQuestion(session_id=session_id, question_text=next_text, expected_skills=skills)
            )

        # 3. Push to WebSocket
        await manager.send_json(
            {
                "event_type": "NEXT_QUESTION",
                "payload": {"question_id": str(q.id), "text": next_text},
            },
            session_id,
        )

    async def _async_generate_report(self, session_id: uuid.UUID):
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            report_data = await InterviewEvaluationEngine(session).generate_final_report(session_id)
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
