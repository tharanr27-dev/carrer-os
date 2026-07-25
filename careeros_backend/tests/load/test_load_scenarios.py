"""Load-test scenario definitions for scheduled or manual enterprise runs."""

LOAD_SCENARIOS = [
    {
        "name": "100_users_dashboard",
        "users": 100,
        "endpoint": "/api/v1/analytics/dashboard/student",
    },
    {"name": "500_users_recommendations", "users": 500, "endpoint": "/api/v1/recommendations/feed"},
    {"name": "1000_users_auth", "users": 1000, "endpoint": "/api/v1/auth/login"},
    {"name": "5000_users_health", "users": 5000, "endpoint": "/health"},
    {"name": "concurrent_ai_requests", "users": 250, "module": "ai"},
    {"name": "concurrent_websockets", "users": 1000, "module": "websocket"},
    {"name": "concurrent_resume_uploads", "users": 500, "endpoint": "/api/v1/resumes/upload"},
    {"name": "concurrent_interviews", "users": 500, "module": "interviews"},
]


def test_load_scenarios_cover_required_enterprise_targets():
    names = {scenario["name"] for scenario in LOAD_SCENARIOS}

    assert "100_users_dashboard" in names
    assert "500_users_recommendations" in names
    assert "1000_users_auth" in names
    assert "5000_users_health" in names
    assert "concurrent_ai_requests" in names
    assert "concurrent_websockets" in names
    assert "concurrent_resume_uploads" in names
    assert "concurrent_interviews" in names
