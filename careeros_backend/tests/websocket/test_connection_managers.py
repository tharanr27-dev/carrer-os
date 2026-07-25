"""WebSocket connection manager tests for interview and communication sessions."""

import uuid

import pytest

from app.modules.communication.websocket import ConnectionManager as CommunicationConnectionManager
from app.modules.interviews.websocket import ConnectionManager as InterviewConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.text_messages = []
        self.json_messages = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        self.text_messages.append(message)

    async def send_json(self, payload: dict):
        self.json_messages.append(payload)


@pytest.mark.parametrize(
    "manager_cls",
    [InterviewConnectionManager, CommunicationConnectionManager],
)
@pytest.mark.asyncio
async def test_websocket_manager_connect_send_and_disconnect(manager_cls):
    manager = manager_cls()
    session_id = uuid.uuid4()
    websocket = FakeWebSocket()

    await manager.connect(session_id, websocket)
    await manager.send_personal_message("hello", session_id)
    await manager.send_json({"sequence": 1, "event": "feedback"}, session_id)
    manager.disconnect(session_id)

    assert websocket.accepted is True
    assert websocket.text_messages == ["hello"]
    assert websocket.json_messages == [{"sequence": 1, "event": "feedback"}]
    assert session_id not in manager.active_connections


@pytest.mark.parametrize(
    "manager_cls",
    [InterviewConnectionManager, CommunicationConnectionManager],
)
@pytest.mark.asyncio
async def test_websocket_manager_ignores_messages_for_disconnected_sessions(manager_cls):
    manager = manager_cls()

    await manager.send_personal_message("lost", uuid.uuid4())
    await manager.send_json({"event": "lost"}, uuid.uuid4())

    assert manager.active_connections == {}
