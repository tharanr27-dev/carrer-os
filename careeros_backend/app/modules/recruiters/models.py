from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase

job_skills = Table(
    "job_skills_assoc",
    AuditableBase.metadata,
    Column("job_id", UUID(as_uuid=True), ForeignKey("recruiter_jobs.id"), primary_key=True),
    Column("skill_name", String, primary_key=True),
)


class Company(AuditableBase):
    __tablename__ = "recruiter_companies"

    name = Column(String, index=True, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    recruiters = relationship(
        "RecruiterProfile", back_populates="company", cascade="all, delete-orphan"
    )
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class RecruiterProfile(AuditableBase):
    __tablename__ = "recruiter_profiles"

    user_id = Column(UUID(as_uuid=True), index=True, unique=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("recruiter_companies.id"), nullable=False)
    role = Column(String, default="recruiter")  # 'admin', 'recruiter', 'hiring_manager'
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="recruiters")


class Job(AuditableBase):
    __tablename__ = "recruiter_jobs"

    company_id = Column(
        UUID(as_uuid=True), ForeignKey("recruiter_companies.id"), index=True, nullable=False
    )
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    status = Column(String, index=True, default="draft")  # 'draft', 'open', 'closed'

    requirements = Column(
        JSONB, nullable=True
    )  # E.g., ["3+ years Python", "Experience with FastAPI"]
    benefits = Column(JSONB, nullable=True)

    # Custom pipeline for this job (optional)
    pipeline_stages = Column(
        JSONB, nullable=True
    )  # e.g. ["Applied", "Screening", "Interview", "Offer"]

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Application(AuditableBase):
    __tablename__ = "recruiter_applications"

    job_id = Column(UUID(as_uuid=True), ForeignKey("recruiter_jobs.id"), index=True, nullable=False)
    candidate_id = Column(UUID(as_uuid=True), index=True, nullable=False)  # Refers to users.id

    status = Column(String, index=True, default="Applied")  # Must match one of pipeline_stages

    # AI and Matching Scores
    fit_score = Column(String, nullable=True)  # E.g., '85%' or a float
    match_details = Column(JSONB, nullable=True)  # Breakdowns of skills, gaps
    ai_insights = Column(JSONB, nullable=True)  # E.g. suggested questions

    job = relationship("Job", back_populates="applications")
    notes = relationship(
        "CandidateNote", back_populates="application", cascade="all, delete-orphan"
    )


class CandidateNote(AuditableBase):
    __tablename__ = "recruiter_candidate_notes"

    application_id = Column(
        UUID(as_uuid=True), ForeignKey("recruiter_applications.id"), index=True, nullable=False
    )
    recruiter_id = Column(UUID(as_uuid=True), nullable=False)  # Refers to users.id of recruiter
    note = Column(Text, nullable=False)

    application = relationship("Application", back_populates="notes")
