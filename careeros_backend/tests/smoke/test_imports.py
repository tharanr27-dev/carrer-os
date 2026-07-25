"""Smoke tests: verify all major modules import without errors."""

import importlib

import pytest

MODULES_TO_IMPORT = [
    "app.main",
    "app.core.config",
    "app.core.security",
    "app.core.exceptions",
    "app.core.dependencies",
    "app.db.session",
    "app.db.base",
    "app.modules.ai.gateway",
    "app.modules.ai.orchestrator",
    "app.modules.ai.dependencies",
    "app.modules.ai.providers.echo_gateway",
    "app.modules.auth.router",
    "app.modules.auth.schemas",
    "app.modules.auth.models",
    "app.modules.users.router",
    "app.modules.users.schemas",
    "app.modules.career_discovery.router",
    "app.modules.career_discovery.schemas",
    "app.modules.resumes.router",
    "app.modules.resumes.schemas",
    "app.modules.mentor.router",
    "app.modules.mentor.schemas",
    "app.modules.interviews.router",
    "app.modules.interviews.schemas",
    "app.modules.interviews.evaluation_engine",
    "app.modules.recommendations.router",
    "app.modules.analytics.router",
    "app.modules.community.router",
    "app.modules.recruiters.router",
    "app.modules.placements.router",
    "app.modules.admin.router",
]


@pytest.mark.parametrize("module_path", MODULES_TO_IMPORT)
def test_module_imports_clean(module_path: str):
    """Every module in the application must import without raising an error."""
    mod = importlib.import_module(module_path)
    assert mod is not None
