import logging
import uuid
from typing import Dict

from fastapi import WebSocket

logger = logging.getLogger("careeros")


class CommunicationConnectionManager:
    def __init__(self):
        # Redis Pub/Sub abstraction needed for multi-worker scaling
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, session_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"Communication WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: uuid.UUID):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Communication WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: str, session_id: uuid.UUID):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

    async def send_json(self, payload: dict, session_id: uuid.UUID):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(payload)


ConnectionManager = CommunicationConnectionManager

manager = CommunicationConnectionManager()
