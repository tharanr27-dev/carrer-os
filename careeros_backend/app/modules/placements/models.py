from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import AuditableBase


class College(AuditableBase):
    __tablename__ = "placement_colleges"

    name = Column(String, index=True, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=False)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    departments = relationship("Department", back_populates="college", cascade="all, delete-orphan")
    drives = relationship("PlacementDrive", back_populates="college", cascade="all, delete-orphan")
    officers = relationship(
        "PlacementOfficer", back_populates="college", cascade="all, delete-orphan"
    )


class Department(AuditableBase):
    __tablename__ = "placement_departments"

    college_id = Column(UUID(as_uuid=True), ForeignKey("placement_colleges.id"), nullable=False)
    name = Column(String, nullable=False)

    college = relationship("College", back_populates="departments")
    batches = relationship(
        "AcademicBatch", back_populates="department", cascade="all, delete-orphan"
    )


class AcademicBatch(AuditableBase):
    __tablename__ = "placement_batches"

    department_id = Column(
        UUID(as_uuid=True), ForeignKey("placement_departments.id"), nullable=False
    )
    graduation_year = Column(Integer, nullable=False)

    department = relationship("Department", back_populates="batches")


class PlacementOfficer(AuditableBase):
    __tablename__ = "placement_officers"

    user_id = Column(
        UUID(as_uuid=True), index=True, unique=True, nullable=False
    )  # Maps to users.id
    college_id = Column(UUID(as_uuid=True), ForeignKey("placement_colleges.id"), nullable=False)
    role_scope = Column(String, default="admin")  # 'admin', 'coordinator'

    college = relationship("College", back_populates="officers")


class PlacementDrive(AuditableBase):
    __tablename__ = "placement_drives"

    college_id = Column(
        UUID(as_uuid=True), ForeignKey("placement_colleges.id"), index=True, nullable=False
    )
    company_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # Optional link to recruiter_companies.id

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    drive_type = Column(String, default="Campus")  # 'Campus', 'Virtual', 'Off-Campus', 'Internship'
    status = Column(String, default="Upcoming")  # 'Upcoming', 'Ongoing', 'Completed', 'Cancelled'

    date_of_drive = Column(Date, nullable=True)

    requirements = Column(JSONB, nullable=True)  # e.g. {"min_cgpa": 7.0, "max_backlogs": 0}

    college = relationship("College", back_populates="drives")
    registrations = relationship(
        "DriveRegistration", back_populates="drive", cascade="all, delete-orphan"
    )
    eligibilities = relationship(
        "DriveEligibility", back_populates="drive", cascade="all, delete-orphan"
    )


class DriveEligibility(AuditableBase):
    __tablename__ = "placement_drive_eligibility"

    drive_id = Column(
        UUID(as_uuid=True), ForeignKey("placement_drives.id"), index=True, nullable=False
    )
    student_id = Column(UUID(as_uuid=True), index=True, nullable=False)  # Maps to users.id

    is_eligible = Column(Boolean, default=False)
    reason = Column(String, nullable=True)  # e.g. "CGPA below 7.0"

    ranking_score = Column(Float, nullable=True)

    drive = relationship("PlacementDrive", back_populates="eligibilities")


class DriveRegistration(AuditableBase):
    __tablename__ = "placement_drive_registrations"

    drive_id = Column(
        UUID(as_uuid=True), ForeignKey("placement_drives.id"), index=True, nullable=False
    )
    student_id = Column(UUID(as_uuid=True), index=True, nullable=False)  # Maps to users.id

    status = Column(
        String, default="Registered"
    )  # 'Registered', 'Shortlisted', 'Interviewing', 'Offered', 'Rejected'

    drive = relationship("PlacementDrive", back_populates="registrations")
    offer = relationship(
        "OfferLetter", back_populates="registration", uselist=False, cascade="all, delete-orphan"
    )


class OfferLetter(AuditableBase):
    __tablename__ = "placement_offer_letters"

    registration_id = Column(
        UUID(as_uuid=True),
        ForeignKey("placement_drive_registrations.id"),
        unique=True,
        nullable=False,
    )

    package_details = Column(String, nullable=True)  # E.g. "12 LPA"
    status = Column(String, default="Pending")  # 'Pending', 'Accepted', 'Declined'

    registration = relationship("DriveRegistration", back_populates="offer")
