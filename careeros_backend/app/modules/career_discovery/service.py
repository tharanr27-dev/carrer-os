import uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.modules.audit.service import AuditService
from app.modules.career_discovery.ai_engine import CareerDiscoveryAIEngine
from app.modules.career_discovery.models import (
    CareerMatch,
    CareerReport,
    UserAnswer,
    UserAssessment,
)
from app.modules.career_discovery.repository import DiscoveryRepository
from app.modules.career_discovery.schemas import AssessmentSubmitRequest


class DiscoveryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = DiscoveryRepository(session)
        self.audit_service = AuditService(session)
        self.ai_engine = CareerDiscoveryAIEngine()

    async def submit_assessment(
        self,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        submission: AssessmentSubmitRequest,
        background_tasks: BackgroundTasks,
    ) -> UserAssessment:

        assessment = await self.repository.create_user_assessment(
            UserAssessment(user_id=user_id, template_id=template_id)
        )

        answers = []
        for ans in submission.answers:
            answers.append(
                UserAnswer(
                    assessment_id=assessment.id,
                    question_id=ans.question_id,
                    answer_text=ans.answer_text,
                    selected_options=ans.selected_options,
                )
            )

        await self.repository.save_answers(answers)
        await self.repository.mark_assessment_completed(assessment.id)

        # Domain Event: Log Audit
        await self.audit_service.log_action(
            user_id=user_id,
            action="CAREER_ASSESSMENT_COMPLETED",
            entity_type="UserAssessment",
            entity_id=str(assessment.id),
        )

        # Offload AI processing to background to prevent blocking HTTP response.
        # We pass only primitive/serialisable data so the background coroutine
        # can open its own DB session (the request-scoped session will be closed
        # by the time this background task actually runs).
        raw_answers = [
            {"q_id": str(a.question_id), "text": a.answer_text} for a in answers
        ]
        background_tasks.add_task(
            self._process_ai_report_isolated, user_id, assessment.id, raw_answers
        )

        return assessment

    async def _process_ai_report_isolated(
        self,
        user_id: uuid.UUID,
        assessment_id: uuid.UUID,
        raw_answers: list[dict],
    ):
        """
        Background task that opens its OWN DB session so it doesn't depend on
        the closed request-scoped session.
        """
        async with AsyncSessionLocal() as session:
            ai_engine = CareerDiscoveryAIEngine()
            ai_analysis = await ai_engine.generate_career_report(raw_answers)

            report = CareerReport(
                assessment_id=assessment_id,
                user_id=user_id,
                personality_analysis=ai_analysis.personality_analysis,
                interest_analysis=ai_analysis.interest_analysis,
                skill_gaps=ai_analysis.skill_gaps,
                career_timeline=ai_analysis.career_timeline,
            )

            matches = [
                CareerMatch(
                    job_title=m.job_title,
                    suitability_score=m.suitability_score,
                    confidence_score=m.confidence_score,
                    reasoning=m.reasoning,
                )
                for m in ai_analysis.recommended_matches
            ]

            repository = DiscoveryRepository(session)
            await repository.save_career_report(report, matches)

