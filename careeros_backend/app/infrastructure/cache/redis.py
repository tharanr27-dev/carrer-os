import os
import time
from typing import Optional

# Mock Redis client for architecture outline.
# Production should use aioredis / redis.asyncio


class RedisClient:
    def __init__(self, url: str):
        self.url = url
        self._store = {}  # Mock in-memory store
        self._expires_at = {}

    def _is_expired(self, key: str) -> bool:
        expires_at = self._expires_at.get(key)
        return expires_at is not None and expires_at <= time.time()

    async def get(self, key: str) -> Optional[str]:
        if self._is_expired(key):
            await self.delete(key)
            return None
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        self._store[key] = value
        if ex is not None:
            self._expires_at[key] = time.time() + ex
        else:
            self._expires_at.pop(key, None)

    async def delete(self, key: str):
        if key in self._store:
            del self._store[key]
        self._expires_at.pop(key, None)

    async def incr(self, key: str) -> int:
        current = await self.get(key)
        next_value = int(current or 0) + 1
        self._store[key] = str(next_value)
        return next_value


# We abstract the redis client so that the rest of the application
# doesn't depend directly on aioredis implementations.
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = RedisClient(redis_url)


async def get_redis():
    return redis_client
