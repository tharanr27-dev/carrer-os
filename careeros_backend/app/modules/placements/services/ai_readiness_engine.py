import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.repository import PlacementRepository


class AIPlacementReadinessEngine:
    """Batch readiness report.

    The platform does not record which students belong to which academic batch, so a batch-level figure cannot be
    computed from real data. This returns that fact instead of an invented percentage. Per-student readiness is
    available through drive rankings (StudentRankingService), which use real records.
    """

    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    async def analyze_batch_readiness(self, batch_id: uuid.UUID) -> Dict[str, Any]:
        return {
            "available": False,
            "overall_readiness": None,
            "top_skills": [],
            "skill_gaps": [],
            "suggested_interventions": [],
            "reason": "Students are not linked to academic batches in the data model, so batch readiness cannot be computed.",
        }
