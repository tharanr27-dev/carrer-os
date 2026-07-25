import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.repository import PlacementRepository


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
        In production, this fetches real profile data from the users/resumes/analytics modules.
        Returns a sorted list of {student_id, score, breakdown}.
        """
        active_weights = weights or self.DEFAULT_WEIGHTS

        registrations = await self.repo.get_drive_registrations(drive_id)

        rankings = []
        for reg in registrations:
            # In a real implementation, we'd query each student's profile,
            # resume analytics, interview scores, etc. from the respective modules.
            # Here we use placeholder logic to demonstrate the composite scoring model.
            breakdown = {
                "cgpa": 8.0,  # Would come from student profile
                "ats_score": 72.0,  # Would come from resume module
                "interview_score": 65.0,  # Would come from interview module
                "communication_score": 70.0,
                "learning_progress": 80.0,
                "certifications": 2,
                "projects": 3,
                "hackathons": 1,
                "recommendations": 4,
            }

            # Normalize all values to 0-100 scale
            normalized = {
                "cgpa": (breakdown["cgpa"] / 10.0) * 100,
                "ats_score": breakdown["ats_score"],
                "interview_score": breakdown["interview_score"],
                "communication_score": breakdown["communication_score"],
                "learning_progress": breakdown["learning_progress"],
                "certifications": min(breakdown["certifications"] * 20, 100),
                "projects": min(breakdown["projects"] * 20, 100),
                "hackathons": min(breakdown["hackathons"] * 25, 100),
                "recommendations": min(breakdown["recommendations"] * 20, 100),
            }

            composite_score = sum(
                normalized.get(k, 0) * active_weights.get(k, 0) for k in active_weights
            )

            rankings.append(
                {
                    "student_id": str(reg.student_id),
                    "score": round(composite_score, 2),
                    "breakdown": normalized,
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
