"""Repository contract tests with mocked async sessions."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.analytics.models import AnalyticsEvent, DailyMetric
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.resumes.models import Resume, ResumeAnalysis, ResumeSuggestion
from app.modules.resumes.repository import ResumeRepository
from app.modules.users.models import Profile
from app.modules.users.repository import UserRepository


def _mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_user_repository_create_profile_commits_and_refreshes():
    session = _mock_session()
    profile = Profile(user_id=uuid.uuid4())

    result = await UserRepository(session).create_profile(profile)

    session.add.assert_called_once_with(profile)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(profile)
    assert result is profile


@pytest.mark.asyncio
async def test_analytics_repository_batch_insert_uses_bulk_session_operation():
    session = _mock_session()
    events = [
        AnalyticsEvent(user_id=uuid.uuid4(), event_type="click", module="mentor"),
        AnalyticsEvent(user_id=uuid.uuid4(), event_type="view", module="resume"),
    ]

    await AnalyticsRepository(session).add_events_batch(events)

    session.add_all.assert_called_once_with(events)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_analytics_repository_upsert_updates_existing_metric():
    session = _mock_session()
    repo = AnalyticsRepository(session)
    user_id = uuid.uuid4()
    existing = DailyMetric(user_id=user_id, date=date.today(), interviews_completed=1)
    incoming = DailyMetric(
        user_id=user_id,
        date=date.today(),
        interviews_completed=2,
        communication_sessions=3,
    )
    repo.get_daily_metric = AsyncMock(return_value=existing)

    result = await repo.upsert_daily_metric(incoming)

    assert result is existing
    assert existing.interviews_completed == 2
    assert existing.communication_sessions == 3
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_resume_repository_save_analysis_persists_suggestions_after_analysis():
    session = _mock_session()
    analysis = ResumeAnalysis(
        resume_id=uuid.uuid4(),
        ats_score=80,
        grammar_score=75,
        quality_score=82,
    )
    analysis.id = uuid.uuid4()
    suggestions = [ResumeSuggestion(category="Summary", suggestion_text="Improve summary")]

    result = await ResumeRepository(session).save_analysis(analysis, suggestions)

    assert result is analysis
    assert suggestions[0].analysis_id == analysis.id
    assert session.commit.await_count == 2
    session.refresh.assert_awaited_once_with(analysis)


@pytest.mark.asyncio
async def test_resume_repository_update_status_commits_when_resume_exists():
    session = _mock_session()
    repo = ResumeRepository(session)
    resume = Resume(
        user_id=uuid.uuid4(),
        file_name="resume.pdf",
        s3_key="users/u1/resume.pdf",
    )
    repo.get_resume_by_id = AsyncMock(return_value=resume)

    await repo.update_resume_status(uuid.uuid4(), "PROCESSED")

    assert resume.status == "PROCESSED"
    session.commit.assert_awaited_once()
