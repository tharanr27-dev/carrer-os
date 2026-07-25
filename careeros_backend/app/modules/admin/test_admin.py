"""
Phase 16 — Enterprise Administration Platform
Unit Tests using stdlib unittest + asyncio

Tests:
  - FeatureFlagService.is_enabled (enabled, disabled, role-based, rollout)
  - AdminDashboardService.get_dashboard_summary (cache hit)
  - AdminDashboardService.test_ai_provider
  - MonitoringService.check_health (DB + Redis probes)
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Helpers ──────────────────────────────────────────────────────────────────


def async_test(coro):
    """Decorator to run async test methods. Compatible with Python 3.10+."""

    def wrapper(*args, **kwargs):
        asyncio.run(coro(*args, **kwargs))

    return wrapper


# ── Feature Flag Service Tests ────────────────────────────────────────────────


class TestFeatureFlagService(unittest.TestCase):

    def _make_service(self, redis_mock):
        """Build a FeatureFlagService with a mocked DB and injected redis."""
        # We import here to avoid top-level dependency errors in CI
        from app.modules.admin.services.feature_flag_service import FeatureFlagService

        db_mock = AsyncMock()
        service = FeatureFlagService(db_mock)
        return service, db_mock, redis_mock

    @async_test
    async def test_flag_enabled_via_cache(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(
            return_value=json.dumps(
                {
                    "is_enabled": True,
                    "allowed_roles": [],
                    "allowed_users": [],
                    "rollout_percentage": 100,
                }
            )
        )
        redis_mock.set = AsyncMock()

        with patch(
            "app.modules.admin.services.feature_flag_service.get_redis",
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=redis_mock)),
        ):
            with patch(
                "app.modules.admin.services.feature_flag_service.get_redis",
                AsyncMock(return_value=redis_mock),
            ):
                service, db_mock, _ = self._make_service(redis_mock)
                result = await service.is_enabled("test-flag")
                self.assertTrue(result)

    @async_test
    async def test_flag_disabled_via_cache(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(
            return_value=json.dumps(
                {
                    "is_enabled": False,
                    "allowed_roles": [],
                    "allowed_users": [],
                    "rollout_percentage": 100,
                }
            )
        )

        with patch(
            "app.modules.admin.services.feature_flag_service.get_redis",
            AsyncMock(return_value=redis_mock),
        ):
            service, _, _ = self._make_service(redis_mock)
            result = await service.is_enabled("test-flag-off")
            self.assertFalse(result)

    @async_test
    async def test_flag_role_restriction(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(
            return_value=json.dumps(
                {
                    "is_enabled": True,
                    "allowed_roles": ["recruiter"],
                    "allowed_users": [],
                    "rollout_percentage": 100,
                }
            )
        )

        with patch(
            "app.modules.admin.services.feature_flag_service.get_redis",
            AsyncMock(return_value=redis_mock),
        ):
            service, _, _ = self._make_service(redis_mock)
            # Student role should be denied
            result = await service.is_enabled("recruiter-only", role="student")
            self.assertFalse(result)
            # Recruiter role should be allowed
            result = await service.is_enabled("recruiter-only", role="recruiter")
            self.assertTrue(result)

    @async_test
    async def test_flag_rollout_percentage_deterministic(self):
        """Deterministic hash — same user_id must always yield consistent result."""
        import uuid

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(
            return_value=json.dumps(
                {
                    "is_enabled": True,
                    "allowed_roles": [],
                    "allowed_users": [],
                    "rollout_percentage": 50,
                }
            )
        )

        with patch(
            "app.modules.admin.services.feature_flag_service.get_redis",
            AsyncMock(return_value=redis_mock),
        ):
            service, _, _ = self._make_service(redis_mock)
            uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
            result_1 = await service.is_enabled("beta-feature", user_id=uid)
            result_2 = await service.is_enabled("beta-feature", user_id=uid)
            # Same user must always get the same flag value
            self.assertEqual(result_1, result_2)


# ── Admin Dashboard Service Tests ─────────────────────────────────────────────


class TestAdminDashboardService(unittest.TestCase):

    @async_test
    async def test_get_dashboard_summary_returns_dict(self):
        from app.modules.admin.services.dashboard_service import AdminDashboardService

        db_mock = AsyncMock()
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)  # Cache miss
        redis_mock.set = AsyncMock()

        with patch(
            "app.modules.admin.services.dashboard_service.get_redis",
            AsyncMock(return_value=redis_mock),
        ):
            service = AdminDashboardService(db_mock)
            summary = await service.get_dashboard_summary()

        self.assertIn("total_users", summary)
        self.assertIn("active_users", summary)
        self.assertIn("pending_moderation_count", summary)
        self.assertIn("system_status", summary)
        self.assertIn("ai_daily_token_usage", summary)
        self.assertEqual(summary["system_status"], "healthy")

    @async_test
    async def test_get_dashboard_summary_from_cache(self):
        from app.modules.admin.services.dashboard_service import AdminDashboardService

        db_mock = AsyncMock()
        cached_data = {
            "total_users": 999,
            "active_users": 500,
            "pending_moderation_count": 3,
            "system_status": "healthy",
            "unresolved_reports": 1,
            "ai_daily_token_usage": 100000,
            "ai_monthly_cost_usd": 50.0,
        }
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=json.dumps(cached_data))

        with patch(
            "app.modules.admin.services.dashboard_service.get_redis",
            AsyncMock(return_value=redis_mock),
        ):
            service = AdminDashboardService(db_mock)
            summary = await service.get_dashboard_summary()

        self.assertEqual(summary["total_users"], 999)

    @async_test
    async def test_ai_provider_test_returns_response(self):
        import uuid

        from app.modules.admin.schemas import AIProviderTestRequest
        from app.modules.admin.services.dashboard_service import AdminDashboardService

        db_mock = AsyncMock()
        service = AdminDashboardService(db_mock)

        test_request = AIProviderTestRequest(
            provider_name="openai",
            model_name="gpt-4-turbo",
            prompt_text="Hello AI",
            temperature=0.5,
        )
        admin_id = uuid.uuid4()
        response = await service.test_ai_provider(admin_id, test_request)

        self.assertEqual(response.status, "success")
        self.assertIn("openai", response.response_text)
        self.assertGreaterEqual(response.latency_ms, 0)
        self.assertGreater(response.tokens_used, 0)


# ── Monitoring Service Tests ──────────────────────────────────────────────────


class TestMonitoringService(unittest.TestCase):

    @async_test
    async def test_check_health_returns_response(self):
        from app.modules.admin.schemas import SystemHealthResponse
        from app.modules.admin.services.monitoring_service import MonitoringService

        db_mock = AsyncMock()
        # Mock DB execute to succeed
        db_mock.execute = AsyncMock(return_value=MagicMock())

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)

        # Mock admin repo snapshot save
        with patch(
            "app.modules.admin.services.monitoring_service.get_redis",
            AsyncMock(return_value=redis_mock),
        ):
            with patch(
                "app.modules.admin.repository.AdminRepository.save_health_snapshot", AsyncMock()
            ):
                with patch(
                    "app.modules.admin.repository.AdminRepository.save_resource_usage", AsyncMock()
                ):
                    service = MonitoringService(db_mock)
                    result = await service.check_health()

        self.assertIsInstance(result, SystemHealthResponse)
        self.assertIsNotNone(result.checked_at)

    @async_test
    async def test_get_resource_summary_returns_dict(self):
        from app.modules.admin.services.monitoring_service import MonitoringService

        db_mock = AsyncMock()
        service = MonitoringService(db_mock)

        summary = await service.get_resource_summary()

        # psutil should provide real values on Windows
        self.assertIn("cpu_percent", summary)
        self.assertIn("memory_percent", summary)
        self.assertIn("disk_percent", summary)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
