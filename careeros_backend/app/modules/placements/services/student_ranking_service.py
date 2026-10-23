import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.repository import PlacementRepository
from app.modules.placements.services.student_metrics import student_metrics


class StudentRankingService:
    """
    Deterministic ranking engine for placement drives.
    Ranks students using configurable weighted scores pulled from
    existing platform data (Resume ATS, Interview, Communication, Learning modules).
    """

    # Default weights (configurable per drive)
    DEFAULT_WEIGHTS = {
        "cgpa": 0.25,
        "ats_score": 0.20,
        "interview_score": 0.15,
        "communication_score": 0.10,
        "learning_progress": 0.10,
        "certifications": 0.05,
        "projects": 0.05,
        "hackathons": 0.05,
        "recommendations": 0.05,
    }

    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    async def rank_students_for_drive(
        self, drive_id: uuid.UUID, weights: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks all eligible students for a given drive.
        Uses real saved records (education, résumé analysis, reports, roadmap progress); see student_metrics.
        Returns a sorted list of {student_id, score, breakdown}.
        """
        active_weights = weights or self.DEFAULT_WEIGHTS

        registrations = await self.repo.get_drive_registrations(drive_id)

        rankings = []
        for reg in registrations:
            # Real saved records only. Score = points earned out of the full weight (100): a metric with no
            # record earns 0 and is listed under missing_data, so students with fuller records are not out-ranked
            # by someone with a single strong number.
            metrics = await student_metrics(self.repo.session, reg.student_id)
            normalized = {
                k: v
                for k, v in {
                    "cgpa": metrics["cgpa"] * 10 if metrics["cgpa"] is not None else None,
                    "ats_score": metrics["ats_score"],
                    "interview_score": metrics["interview_score"],
                    "communication_score": metrics["communication_score"],
                    "learning_progress": metrics["learning_progress"],
                    "certifications": min(metrics["certifications"] * 20, 100) if metrics["certifications"] else None,
                    "projects": min(metrics["projects"] * 20, 100) if metrics["projects"] else None,
                    "hackathons": None,
                    "recommendations": None,
                }.items()
                if v is not None
            }
            used = sum(active_weights.get(k, 0) for k in normalized)
            total_weight = sum(active_weights.values()) or 1
            composite_score = sum(normalized[k] * active_weights.get(k, 0) for k in normalized) / total_weight
            rankings.append(
                {
                    "student_id": str(reg.student_id),
                    "score": round(composite_score, 2),
                    "breakdown": normalized,
                    "missing_data": [k for k in active_weights if k not in normalized],
                    "weight_coverage_pct": round(100 * used / total_weight, 1),
                }
            )

        # Sort descending by score
        rankings.sort(key=lambda r: r["score"], reverse=True)

        # Persist ranking scores into DriveEligibility for dashboard queries
        for _rank_idx, entry in enumerate(rankings):
            elig = await self.repo.get_drive_eligibility(drive_id, uuid.UUID(entry["student_id"]))
            if elig:
                elig.ranking_score = entry["score"]
                await self.repo.session.commit()

        return rankings
