import logging
import uuid
from typing import Dict

from fastapi import WebSocket

logger = logging.getLogger("careeros")


class ConnectionManager:
    def __init__(self):
        # In a multi-worker production deployment, this local dict is insufficient.
        # It must be backed by Redis Pub/Sub to route messages to the correct Uvicorn worker.
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, session_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: uuid.UUID):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: str, session_id: uuid.UUID):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

    async def send_json(self, payload: dict, session_id: uuid.UUID):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(payload)


manager = ConnectionManager()
