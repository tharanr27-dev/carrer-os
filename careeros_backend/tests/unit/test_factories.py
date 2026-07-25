"""Unit tests for test factories and Faker integration."""

import uuid

from tests.factories.base_factories import (
    AIResponseFactory,
    CollegeFactory,
    CommunicationSessionFactory,
    CompanyFactory,
    InterviewSessionFactory,
    JobFactory,
    MentorSessionFactory,
    RecommendationFactory,
    RecruiterFactory,
    ResumeFactory,
    UserFactory,
)


def test_user_factory_generates_unique_ids():
    u1 = UserFactory()
    u2 = UserFactory()
    assert u1["id"] != u2["id"]
    assert "@" in u1["email"]
    assert u1["is_active"] is True


def test_user_factory_build_batch():
    users = UserFactory.build_batch(5)
    assert len(users) == 5
    ids = {u["id"] for u in users}
    assert len(ids) == 5


def test_resume_factory():
    resume = ResumeFactory()
    assert resume["version"] == 1
    assert isinstance(resume["user_id"], uuid.UUID)
    assert len(resume["content"]) > 0


def test_job_factory():
    job = JobFactory()
    assert job["is_active"] is True
    assert len(job["title"]) > 0


def test_mentor_session_factory():
    session = MentorSessionFactory()
    assert session["is_active"] is True


def test_interview_factory():
    interview = InterviewSessionFactory()
    assert interview["interview_type"] == "technical"
    assert interview["status"] == "in_progress"


def test_enterprise_factories_cover_phase_entities():
    assert RecruiterFactory()["role"] == "recruiter"
    assert CollegeFactory()["domain"]
    assert CompanyFactory()["industry"] == "Technology"
    assert CommunicationSessionFactory()["session_type"] == "presentation"
    assert RecommendationFactory()["score"] > 0
    assert AIResponseFactory()["tokens_used"] == 42
