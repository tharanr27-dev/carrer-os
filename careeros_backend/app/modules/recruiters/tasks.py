import asyncio
import uuid

from celery import shared_task

from app.db.session import AsyncSessionLocal
from app.modules.recruiters.services.ai_insights_engine import AIInsightsEngine
from app.modules.recruiters.services.matching_engine import CandidateMatchingEngine


@shared_task
def generate_candidate_insights_background(application_id_str: str):
    application_id = uuid.UUID(application_id_str)

    async def _run():
        async with AsyncSessionLocal() as db:
            ai_engine = AIInsightsEngine(db)
            matching_engine = CandidateMatchingEngine(db)

            # Step 1: AI Insights
            await ai_engine.generate_candidate_insights(application_id)

            # Step 2: Deterministic Matching
            await matching_engine.calculate_deterministic_score(application_id)

    asyncio.run(_run())
