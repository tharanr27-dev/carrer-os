from sqlalchemy import Boolean, Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class Resume(AuditableBase):
    __tablename__ = "resumes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    s3_key = Column(String, unique=True, nullable=False)
    content_type = Column(String, default="application/pdf")
    is_primary = Column(Boolean, default=False)
    status = Column(String, default="PROCESSING")  # PROCESSING, COMPLETED, FAILED

    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    metadata_record = relationship(
        "ResumeMetadata", uselist=False, back_populates="resume", cascade="all, delete-orphan"
    )
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")


class ResumeVersion(AuditableBase):
    __tablename__ = "resume_versions"

    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    version_number = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    change_summary = Column(Text, nullable=True)

    resume = relationship("Resume", back_populates="versions")


class ResumeMetadata(AuditableBase):
    __tablename__ = "resume_metadata"

    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), unique=True, nullable=False)
    parsed_content = Column(JSONB, nullable=True)  # Extracted raw text/blocks
    extracted_skills = Column(JSONB, nullable=True)
    extracted_experience = Column(JSONB, nullable=True)

    resume = relationship("Resume", back_populates="metadata_record")


class ResumeAnalysis(AuditableBase):
    __tablename__ = "resume_analyses"

    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # If analyzed against specific job

    ats_score = Column(Float, nullable=False)
    grammar_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    keyword_analysis = Column(JSONB, nullable=True)

    suggestions = relationship(
        "ResumeSuggestion", back_populates="analysis", cascade="all, delete-orphan"
    )
    resume = relationship("Resume", back_populates="analyses")


class ResumeSuggestion(AuditableBase):
    __tablename__ = "resume_suggestions"

    analysis_id = Column(UUID(as_uuid=True), ForeignKey("resume_analyses.id"), nullable=False)
    category = Column(
        String, nullable=False
    )  # e.g., "Formatting", "Action Verbs", "Missing Skills"
    suggestion_text = Column(Text, nullable=False)
    impact = Column(String, default="MEDIUM")  # HIGH, MEDIUM, LOW

    analysis = relationship("ResumeAnalysis", back_populates="suggestions")
