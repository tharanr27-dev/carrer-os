"""Infrastructure adapter tests using deterministic in-memory behavior."""

import asyncio

import pytest

from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.storage.s3_client import S3Client


@pytest.mark.asyncio
async def test_redis_cache_create_read_invalidate_and_increment():
    redis = RedisClient("redis://test")

    await redis.set("dashboard:user-1", "cached", ex=60)
    assert await redis.get("dashboard:user-1") == "cached"
    assert await redis.incr("user:1:learning:streak") == 1
    assert await redis.incr("user:1:learning:streak") == 2

    await redis.delete("dashboard:user-1")
    assert await redis.get("dashboard:user-1") is None


@pytest.mark.asyncio
async def test_redis_ttl_expiration():
    redis = RedisClient("redis://test")

    await redis.set("ai:cache:key", "answer", ex=0)
    await asyncio.sleep(0)

    assert await redis.get("ai:cache:key") is None


@pytest.mark.asyncio
async def test_s3_client_upload_download_url_and_delete_contracts():
    s3 = S3Client(bucket_name="careeros-test")

    location = await s3.upload_file(b"resume", "resume.pdf", "users/u1/resume.pdf")
    url = await s3.generate_presigned_url("users/u1/resume.pdf", expires_in_seconds=300)
    deleted = await s3.delete_file("users/u1/resume.pdf")

    assert location == "s3://careeros-test/users/u1/resume.pdf"
    assert url.startswith("https://careeros-test.s3.amazonaws.com/users/u1/resume.pdf")
    assert "Expires=300" in url
    assert deleted is True
