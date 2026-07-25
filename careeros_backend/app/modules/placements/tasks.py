import asyncio
import uuid

from celery import shared_task

from app.db.session import AsyncSessionLocal
from app.modules.placements.services.ai_readiness_engine import AIPlacementReadinessEngine
from app.modules.placements.services.student_eligibility_service import StudentEligibilityService
from app.modules.placements.services.student_ranking_service import StudentRankingService


@shared_task
def calculate_drive_eligibility_background(drive_id_str: str):
    """
    Heavy background task that iterates through every student in a batch
    and evaluates their eligibility against a drive's requirements.
    Triggered by a placement officer via the API.
    """
    drive_id = uuid.UUID(drive_id_str)

    async def _run():
        async with AsyncSessionLocal() as db:
            eligibility_service = StudentEligibilityService(db)
            await eligibility_service.calculate_bulk_eligibility(drive_id)

    asyncio.run(_run())


@shared_task
def rank_students_for_drive_background(drive_id_str: str):
    """
    Background task to rank all registered students for a drive.
    """
    drive_id = uuid.UUID(drive_id_str)

    async def _run():
        async with AsyncSessionLocal() as db:
            ranking_service = StudentRankingService(db)
            await ranking_service.rank_students_for_drive(drive_id)

    asyncio.run(_run())


@shared_task
def analyze_batch_readiness_background(batch_id_str: str):
    """
    Background task to generate an AI readiness report for an academic batch.
    """
    batch_id = uuid.UUID(batch_id_str)

    async def _run():
        async with AsyncSessionLocal() as db:
            ai_engine = AIPlacementReadinessEngine(db)
            await ai_engine.analyze_batch_readiness(batch_id)

    asyncio.run(_run())
