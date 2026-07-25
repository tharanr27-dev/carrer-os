"""Unit tests for mentor service using mocked dependencies."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.mentor.schemas import ChatMessageRequest
from app.modules.mentor.service import MentorService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    # Return a mock mentor session
    mock_mentor_session = MagicMock()
    mock_mentor_session.user_id = uuid.uuid4()
    mock_mentor_session.messages = []
    repo.get_session.return_value = mock_mentor_session
    repo.append_message.return_value = MagicMock(id=uuid.uuid4(), content="AI response")
    return repo


@pytest.fixture
def mock_audit():
    return AsyncMock()


@pytest.mark.asyncio
async def test_create_session(mock_session):
    """MentorService.create_session delegates to repository."""
    with (
        patch("app.modules.mentor.service.MentorRepository") as MockRepo,
        patch("app.modules.mentor.service.AuditService"),
    ):
        MockRepo.return_value.create_session = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
        service = MentorService(session=mock_session)
        user_id = uuid.uuid4()
        result = await service.create_session(user_id)
        MockRepo.return_value.create_session.assert_called_once_with(user_id)
        assert result.id


@pytest.mark.asyncio
async def test_send_message_access_denied(mock_session):
    """send_message raises 403 if session owner differs from requesting user."""
    from fastapi import HTTPException

    with (
        patch("app.modules.mentor.service.MentorRepository") as MockRepo,
        patch("app.modules.mentor.service.AuditService"),
    ):

        owner_id = uuid.uuid4()
        requester_id = uuid.uuid4()  # different user

        mock_mentor_session = MagicMock()
        mock_mentor_session.user_id = owner_id
        MockRepo.return_value.get_session = AsyncMock(return_value=mock_mentor_session)

        service = MentorService(session=mock_session)
        with pytest.raises(HTTPException) as exc_info:
            await service.send_message(
                user_id=requester_id,
                session_id=uuid.uuid4(),
                request=ChatMessageRequest(content="Hello"),
            )
        assert exc_info.value.status_code == 403
