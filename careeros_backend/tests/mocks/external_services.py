"""Mock singletons for external services used in tests."""

import time
from unittest.mock import AsyncMock, MagicMock


def make_mock_orchestrator(response_text: str = "Mocked AI response"):
    """Return a mock AIOrchestrator that always returns a successful response."""
    mock = MagicMock()
    mock.process_request = AsyncMock(
        return_value={
            "status": "success",
            "response_text": response_text,
            "tokens_used": 42,
            "latency_ms": 10,
            "provider": "mock",
        }
    )
    return mock


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.expires_at = {}

    def _expired(self, key: str) -> bool:
        expires_at = self.expires_at.get(key)
        return expires_at is not None and expires_at <= time.time()

    async def get(self, key: str):
        if self._expired(key):
            await self.delete(key)
            return None
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value
        if ex is not None:
            self.expires_at[key] = time.time() + ex
        else:
            self.expires_at.pop(key, None)
        return True

    async def delete(self, key: str):
        existed = key in self.store
        self.store.pop(key, None)
        self.expires_at.pop(key, None)
        return int(existed)

    async def incr(self, key: str):
        current = int(await self.get(key) or 0) + 1
        self.store[key] = str(current)
        return current


def make_mock_redis():
    """Return a mock Redis client with standard async operations."""
    return FakeRedis()


def make_mock_s3_client():
    """Return a mock boto3 S3 client."""
    mock = MagicMock()
    mock.upload_fileobj = MagicMock(return_value=None)
    mock.generate_presigned_url = MagicMock(
        return_value="https://s3.example.com/file.pdf?signed=true"
    )
    mock.delete_object = MagicMock(return_value={"ResponseMetadata": {"HTTPStatusCode": 204}})
    return mock


def make_mock_celery_task():
    """Return a mock Celery task that captures delay() calls."""
    mock = MagicMock()
    mock.delay = MagicMock(return_value=MagicMock(id="mock-task-id"))
    return mock


def make_mock_db_session():
    """Return a mock async database session."""
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    mock.execute = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    return mock


class FailingAIGateway:
    async def handle(self, request):
        raise RuntimeError(request.get("failure", "provider unavailable"))


class DeterministicAIGateway:
    def __init__(self, response_text: str = "Deterministic AI response"):
        self.response_text = response_text

    async def handle(self, request):
        return {
            "status": "success",
            "response_text": self.response_text,
            "tokens_used": request.get("tokens_used", 7),
            "latency_ms": request.get("latency_ms", 5),
            "provider": request.get("provider_name", "deterministic"),
        }
