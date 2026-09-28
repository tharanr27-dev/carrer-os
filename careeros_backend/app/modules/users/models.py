from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class Profile(AuditableBase):
    __tablename__ = "profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    headline = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String, nullable=True)

    social_links = Column(JSONB, nullable=True)  # LinkedIn, GitHub, Portfolio
    role_specific_data = Column(
        JSONB, nullable=True
    )  # specific fields for recruiter/placement officer

    completion_percentage = Column(Integer, default=0)

    user = relationship("User", backref="profile", lazy="selectin")
    educations = relationship(
        "Education", back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    experiences = relationship(
        "Experience", back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    projects = relationship(
        "Project", back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    certifications = relationship(
        "Certification", back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    profile_skills = relationship(
        "ProfileSkill", back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )


class UserPreference(AuditableBase):
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    theme = Column(String, default="light")
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    privacy_settings = Column(JSONB, nullable=True)  # e.g. "public_profile": True

    user = relationship("User", backref="preferences", lazy="selectin")


class Education(AuditableBase):
    __tablename__ = "educations"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    institution = Column(String, nullable=False)
    degree = Column(String, nullable=True)
    field_of_study = Column(String, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    gpa = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    profile = relationship("Profile", back_populates="educations")


class Experience(AuditableBase):
    __tablename__ = "experiences"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    profile = relationship("Profile", back_populates="experiences")


class Project(AuditableBase):
    __tablename__ = "projects"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile", back_populates="projects")


class Certification(AuditableBase):
    __tablename__ = "certifications"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    issuing_organization = Column(String, nullable=True)
    issue_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    credential_id = Column(String, nullable=True)
    credential_url = Column(String, nullable=True)

    profile = relationship("Profile", back_populates="certifications")


class Skill(AuditableBase):
    __tablename__ = "skills"

    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=True)  # e.g. "Hard", "Soft", "Tool"


class ProfileSkill(AuditableBase):
    __tablename__ = "profile_skills"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    proficiency = Column(String, nullable=True)  # "Beginner", "Intermediate", "Expert"

    profile = relationship("Profile", back_populates="profile_skills")
    skill = relationship("Skill", lazy="joined")
