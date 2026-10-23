"""Real per-student metrics for placement ranking and eligibility.

Every value comes from a saved record. A metric with no record is None (never a default or an estimate), and the
callers either skip it or report it as missing.
"""

import re
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication.models import CommunicationReport, CommunicationSession
from app.modules.interviews.models import InterviewReport, InterviewSession
from app.modules.learning.models import LearningModule, LearningRoadmap, LearningTask
from app.modules.resumes.models import Resume, ResumeAnalysis
from app.modules.users.models import Certification, Education, Profile, Project


def parse_cgpa(raw: Optional[str]) -> Optional[float]:
    """Normalises '8.4', '8.4/10', '3.6/4.0', '84%' to a 0-10 scale. Anything unparseable -> None."""
    if not raw:
        return None
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?)|%)?\s*", str(raw))
    if not m:
        return None
    value = float(m.group(1))
    if m.group(2):
        scale = float(m.group(2))
        return round(value / scale * 10, 2) if 0 < scale and value <= scale else None
    if str(raw).strip().endswith("%"):
        return round(value / 10, 2) if value <= 100 else None
    return value if value <= 10 else (round(value / 10, 2) if value <= 100 else None)


async def student_metrics(db: AsyncSession, student_id: uuid.UUID) -> Dict[str, Any]:
    profile = (await db.execute(select(Profile).where(Profile.user_id == student_id))).scalars().first()
    cgpa = certs = projects = None
    if profile is not None:
        edus = (
            await db.execute(select(Education.gpa).where(Education.profile_id == profile.id).order_by(Education.end_date.desc().nullslast()))
        ).scalars().all()
        cgpa = next((c for c in (parse_cgpa(g) for g in edus) if c is not None), None)
        certs = (await db.execute(select(func.count()).select_from(Certification).where(Certification.profile_id == profile.id))).scalar_one()
        projects = (await db.execute(select(func.count()).select_from(Project).where(Project.profile_id == profile.id))).scalar_one()

    ats = (
        await db.execute(
            select(ResumeAnalysis.ats_score).join(Resume, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.user_id == student_id, Resume.status == "COMPLETED").order_by(ResumeAnalysis.created_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    interview = (
        await db.execute(
            select(InterviewReport.overall_score).join(InterviewSession, InterviewSession.id == InterviewReport.session_id)
            .where(InterviewSession.user_id == student_id).order_by(InterviewReport.created_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    comm = (
        await db.execute(
            select(CommunicationReport.overall_score).join(CommunicationSession, CommunicationSession.id == CommunicationReport.session_id)
            .where(CommunicationSession.user_id == student_id).order_by(CommunicationReport.created_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    total = (
        await db.execute(
            select(func.count()).select_from(LearningTask).join(LearningModule, LearningModule.id == LearningTask.module_id)
            .join(LearningRoadmap, LearningRoadmap.id == LearningModule.roadmap_id)
            .where(LearningRoadmap.user_id == student_id, LearningRoadmap.status == "ACTIVE")
        )
    ).scalar_one()
    done = (
        await db.execute(
            select(func.count()).select_from(LearningTask).join(LearningModule, LearningModule.id == LearningTask.module_id)
            .join(LearningRoadmap, LearningRoadmap.id == LearningModule.roadmap_id)
            .where(LearningRoadmap.user_id == student_id, LearningRoadmap.status == "ACTIVE", LearningTask.status == "COMPLETED")
        )
    ).scalar_one()
    return {
        "cgpa": cgpa,  # 0-10
        "ats_score": ats,  # 0-100, rule-based résumé readiness
        "interview_score": interview,  # 0-100, rule-based estimate
        "communication_score": comm * 10 if comm is not None else None,  # stored 0-10 -> 0-100
        "learning_progress": round(100 * done / total, 1) if total else None,
        "certifications": certs if certs else None,  # 0 certificates is "no data", not a negative signal
        "projects": projects if projects else None,
        "hackathons": None,  # not recorded anywhere in the platform
        "recommendations": None,  # not recorded anywhere in the platform
    }
