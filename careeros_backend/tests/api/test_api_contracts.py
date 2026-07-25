"""API contract tests that do not require external infrastructure."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_uses_standard_response_envelope():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Request-ID": "phase-18"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "System is healthy"
    assert payload["data"] == {"status": "ok"}
    assert payload["errors"] is None
    assert "timestamp" in payload
    assert response.headers["X-Request-ID"] == "phase-18"


@pytest.mark.asyncio
async def test_security_headers_are_applied_to_http_responses():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"


def test_expected_enterprise_router_tags_are_registered():
    expected_tags = {
        "auth",
        "users",
        "career_discovery",
        "resumes",
        "mentor",
        "interviews",
        "communication",
        "learning",
        "recommendations",
        "analytics",
        "community",
        "recruiters",
        "placements",
        "admin",
    }
    route_tags = set()
    for route in app.routes:
        route_tags.update(getattr(route, "tags", []) or [])
        include_context = getattr(route, "include_context", None)
        if include_context is not None:
            route_tags.update(getattr(include_context, "tags", []) or [])

    assert expected_tags.issubset(route_tags)


def test_openapi_schema_exposes_registered_api_paths():
    schema = app.openapi()
    paths = schema["paths"]

    assert "/health" in paths
    assert any(path.endswith("/auth/login") for path in paths)
    assert any(path.endswith("/resumes/upload") for path in paths)
    assert any(path.endswith("/admin/health/check") for path in paths)
