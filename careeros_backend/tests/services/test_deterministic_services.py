"""Service-layer tests with mocked persistence and deterministic engines."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.security import get_password_hash
from app.modules.auth.schemas import UserCreate, UserLogin
from app.modules.auth.service import AuthService
from app.modules.placements.services.student_ranking_service import StudentRankingService
from app.modules.recommendations.ranking_engine import RankingEngine
from app.modules.recommendations.schemas import AIRecommendationItem
from app.modules.users.service import UserService


def test_user_profile_completion_scores_complete_profile_at_100():
    profile = SimpleNamespace(
        first_name="Alex",
        last_name="Morgan",
        headline="Backend Engineer",
        bio="Builds reliable systems",
        profile_image_url="https://example.com/avatar.png",
        experiences=[object()],
        educations=[object()],
        profile_skills=[object()],
    )

    assert UserService(session=AsyncMock()).calculate_completion(profile) == 100


def test_recommendation_ranking_prefers_goal_aligned_high_confidence_items():
    engine = RankingEngine()
    backend_item = AIRecommendationItem(
        category="SKILL",
        title="Practice backend system design",
        description="Work on distributed systems exercises",
        reason="Matches career goal",
        confidence_score=0.95,
        estimated_impact=0.9,
        difficulty="MEDIUM",
        related_skills=["Backend"],
        source_modules=["mentor"],
    )
    unrelated_item = AIRecommendationItem(
        category="COURSE",
        title="Try watercolor basics",
        description="Creative optional course",
        reason="Exploration",
        confidence_score=0.5,
        estimated_impact=0.2,
        difficulty="EASY",
        related_skills=["Art"],
        source_modules=["learning"],
    )

    ranked = engine.rank(
        [unrelated_item, backend_item],
        {"career_goals": ["Backend"], "skill_progress": [{"level": 80}]},
    )

    assert ranked[0][0].title == "Practice backend system design"
    assert ranked[0][1] > ranked[1][1]


@pytest.mark.asyncio
async def test_student_ranking_service_sorts_and_persists_scores():
    drive_id = uuid.uuid4()
    student_a = uuid.uuid4()
    student_b = uuid.uuid4()
    registrations = [
        SimpleNamespace(student_id=student_a),
        SimpleNamespace(student_id=student_b),
    ]
    eligibility = SimpleNamespace(ranking_score=None)

    with patch(
        "app.modules.placements.services.student_ranking_service.PlacementRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        repo.get_drive_registrations = AsyncMock(return_value=registrations)
        repo.get_drive_eligibility = AsyncMock(return_value=eligibility)
        repo.session.commit = AsyncMock()

        rankings = await StudentRankingService(AsyncMock()).rank_students_for_drive(drive_id)

    assert [entry["student_id"] for entry in rankings] == [str(student_a), str(student_b)]
    assert rankings[0]["score"] >= rankings[1]["score"]
    assert repo.session.commit.await_count == 2
    assert eligibility.ranking_score == rankings[-1]["score"]


@pytest.mark.asyncio
async def test_auth_service_rejects_duplicate_registration():
    with patch("app.modules.auth.service.AuthRepository") as repo_cls:
        repo_cls.return_value.get_user_by_email = AsyncMock(return_value=object())
        service = AuthService(session=AsyncMock())

        with pytest.raises(HTTPException) as exc_info:
            await service.register(UserCreate(email="alex@example.com", password="StrongPass123!"))

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_auth_service_authenticates_active_user():
    user_id = uuid.uuid4()
    user = SimpleNamespace(
        id=user_id,
        email="alex@example.com",
        hashed_password=get_password_hash("StrongPass123!"),
        is_active=True,
    )

    with patch("app.modules.auth.service.AuthRepository") as repo_cls:
        repo_cls.return_value.get_user_by_email = AsyncMock(return_value=user)
        service = AuthService(session=AsyncMock())
        token = await service.authenticate(
            UserLogin(email="alex@example.com", password="StrongPass123!")
        )

    assert token.token_type == "bearer"
    assert token.access_token
    assert token.refresh_token
