import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.communication.evaluation_engine import CommunicationEvaluationEngine
from app.modules.communication.models import (
    CommunicationAnalysis,
    CommunicationMessage,
    CommunicationReport,
    CommunicationSession,
)
from app.modules.communication.repository import CommunicationRepository
from app.modules.communication.schemas import CommunicationSessionCreate
from app.modules.communication.websocket import manager


class CommunicationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CommunicationRepository(session)
        self.audit_service = AuditService(session)
        self.eval_engine = CommunicationEvaluationEngine()

    async def initialize_session(
        self, user_id: uuid.UUID, request: CommunicationSessionCreate
    ) -> CommunicationSession:
        return await self.repository.create_session(
            CommunicationSession(
                user_id=user_id, mode=request.mode, started_at=datetime.now(timezone.utc)
            )
        )

    async def handle_websocket_event(
        self, session_id: uuid.UUID, event: dict, background_tasks: BackgroundTasks
    ):
        event_type = event.get("event_type")
        payload = event.get("payload", {})

        if event_type == "START":
            await manager.send_json(
                {
                    "event_type": "SESSION_READY",
                    "payload": {"message": "You can begin speaking or typing."},
                },
                session_id,
            )

        elif event_type == "MESSAGE_SUBMITTED":
            text = payload.get("text")

            # Save the raw text immediately
            message = await self.repository.save_message(
                CommunicationMessage(session_id=session_id, speaker="USER", content_text=text)
            )

            # Send immediate ACK
            await manager.send_json({"event_type": "ANALYZING"}, session_id)

            # Offload linguistic analysis to background
            background_tasks.add_task(self._async_analyze_message, session_id, message.id, text)

        elif event_type == "FINISH":
            db_session = await self.repository.get_session(session_id)
            db_session.status = "COMPLETED"
            db_session.ended_at = datetime.now(timezone.utc)
            await self.session.commit()

            # Offload Final Report
            background_tasks.add_task(self._async_generate_report, session_id)
            await manager.send_json({"event_type": "SESSION_COMPLETED"}, session_id)

    async def _async_analyze_message(self, session_id: uuid.UUID, message_id: uuid.UUID, text: str):
        from app.db.session import AsyncSessionLocal
        # 1. AI Linguistic Evaluation
        analysis_data = await self.eval_engine.analyze_message(text)

        async with AsyncSessionLocal() as session:
            repository = CommunicationRepository(session)
            analysis = await repository.save_analysis(
                CommunicationAnalysis(
                    message_id=message_id,
                    grammar_score=analysis_data.grammar_score,
                    vocabulary_score=analysis_data.vocabulary_score,
                    tone_score=analysis_data.tone_score,
                    clarity_score=analysis_data.clarity_score,
                    feedbacks=[fb.model_dump() for fb in analysis_data.feedbacks],
                )
            )

        # 2. Push Live Feedback to WebSocket
        await manager.send_json(
            {
                "event_type": "LIVE_FEEDBACK",
                "payload": {
                    "message_id": str(message_id),
                    "grammar_score": analysis.grammar_score,
                    "feedbacks": analysis.feedbacks,
                },
            },
            session_id,
        )

    async def _async_generate_report(self, session_id: uuid.UUID):
        from app.db.session import AsyncSessionLocal
        report_data = await self.eval_engine.generate_final_report([])
        async with AsyncSessionLocal() as session:
            repository = CommunicationRepository(session)
            await repository.save_report(
                CommunicationReport(
                    session_id=session_id,
                    overall_score=report_data.overall_score,
                    grammar_score=report_data.grammar_score,
                    vocabulary_score=report_data.vocabulary_score,
                    tone_score=report_data.tone_score,
                    fluency_score=report_data.fluency_score,
                    strengths=report_data.strengths,
                    weaknesses=report_data.weaknesses,
                    improvement_suggestions=report_data.improvement_suggestions,
                )
            )
