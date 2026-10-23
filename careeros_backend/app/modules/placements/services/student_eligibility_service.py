import uuid
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placements.models import DriveEligibility
from app.modules.placements.repository import PlacementRepository
from app.modules.placements.services.student_metrics import student_metrics


class StudentEligibilityService:
    """Checks each REGISTERED student against the drive's requirements using their saved profile data.

    Supported requirement keys: `min_cgpa` (0-10 scale). Other keys (for example `max_backlogs`) cannot be verified
    because the platform stores no such data; they are reported in the reason and never silently passed or failed.
    A student with no CGPA on their profile is NOT marked eligible when the drive requires one.
    """

    def __init__(self, db: AsyncSession):
        self.repo = PlacementRepository(db)

    @staticmethod
    def evaluate(requirements: Optional[Dict[str, Any]], cgpa: Optional[float]) -> Tuple[bool, str]:
        requirements = requirements or {}
        reasons = []
        eligible = True
        min_cgpa = requirements.get("min_cgpa")
        if min_cgpa is not None:
            if cgpa is None:
                eligible = False
                reasons.append(f"CGPA required (min {min_cgpa}) but none is saved on the student's profile")
            elif cgpa < float(min_cgpa):
                eligible = False
                reasons.append(f"CGPA {cgpa} is below the minimum {min_cgpa}")
        unverifiable = [k for k in requirements if k != "min_cgpa"]
        if unverifiable:
            reasons.append("Could not verify: " + ", ".join(unverifiable) + " (no such data is stored)")
        return eligible, "; ".join(reasons) or "Meets the checked requirements"

    async def calculate_bulk_eligibility(self, drive_id: uuid.UUID) -> int:
        """Evaluates every registered student and stores the result. Returns how many students were evaluated."""
        drive = await self.repo.get_placement_drive(drive_id)
        if not drive:
            return 0
        registrations = await self.repo.get_drive_registrations(drive_id)
        for reg in registrations:
            metrics = await student_metrics(self.repo.session, reg.student_id)
            eligible, reason = self.evaluate(drive.requirements, metrics["cgpa"])
            row = await self.repo.get_drive_eligibility(drive_id, reg.student_id)
            if row is None:
                row = DriveEligibility(drive_id=drive_id, student_id=reg.student_id)
                self.repo.session.add(row)
            row.is_eligible, row.reason = eligible, reason[:250]
        await self.repo.session.commit()
        return len(registrations)
