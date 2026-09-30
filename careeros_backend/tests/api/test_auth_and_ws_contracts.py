"""Auth/RBAC/WebSocket contract checks that fail before touching any database."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token, create_refresh_token
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/auth/me",
        "/api/v1/admin/users",
        "/api/v1/resumes",
        "/api/v1/recruiters/jobs/open",
        "/api/v1/placements/drives/available",
        "/api/v1/mentor/goals",
        "/api/v1/discovery/templates",
    ],
)
async def test_new_endpoints_require_authentication(client, path):
    assert (await client.get(path)).status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_garbage_and_access_tokens(client):
    assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": "junk"})).status_code == 401
    access = create_access_token(subject=uuid.uuid4())
    assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": access})).status_code == 401


@pytest.mark.asyncio
async def test_refresh_requires_a_body(client):
    assert (await client.post("/api/v1/auth/refresh", json={})).status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_cannot_authenticate_api_calls(client):
    refresh = create_refresh_token(subject=uuid.uuid4())
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 401


@pytest.mark.parametrize("kind", ["interviews", "communication"])
@pytest.mark.parametrize("query", ["", "?token=junk"])
def test_websocket_refuses_missing_or_bad_token(kind, query):
    client = TestClient(app)  # not used as a context manager: no lifespan / DB needed
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/api/v1/{kind}/ws/{uuid.uuid4()}{query}"):
            pass
    assert exc.value.code == 4401


def test_cors_origins_come_from_settings():
    from app.main import CORS_ORIGINS

    assert "http://localhost:3000" in CORS_ORIGINS
    assert "*" not in CORS_ORIGINS
