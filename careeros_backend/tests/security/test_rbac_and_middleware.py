"""Security regression tests for RBAC and middleware behavior."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import require_permissions
from app.core.middleware.rate_limit import RateLimitMiddleware
from app.main import app


def _user_with_permissions(*permission_names: str):
    permissions = [SimpleNamespace(name=name) for name in permission_names]
    return SimpleNamespace(roles=[SimpleNamespace(permissions=permissions)])


@pytest.mark.asyncio
async def test_require_permissions_allows_user_with_required_permission():
    checker = require_permissions(["admin:read"])
    user = _user_with_permissions("admin:read", "users:update")

    assert await checker(current_user=user) is user


@pytest.mark.asyncio
async def test_require_permissions_rejects_permission_escalation():
    checker = require_permissions(["admin:write"])
    user = _user_with_permissions("admin:read")

    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=user)

    assert exc_info.value.status_code == 403
    assert "admin:write" in exc_info.value.detail


@pytest.mark.asyncio
async def test_rate_limiter_returns_standard_error_response():
    limited_app = RateLimitMiddleware(app, max_requests=1, window_seconds=60)
    transport = ASGITransport(app=limited_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get("/health")
        second = await client.get("/health")

    assert first.status_code == 200
    assert second.status_code == 429
    payload = second.json()
    assert payload["success"] is False
    assert payload["message"] == "Rate limit exceeded"
    assert payload["errors"] == ["Too Many Requests"]
