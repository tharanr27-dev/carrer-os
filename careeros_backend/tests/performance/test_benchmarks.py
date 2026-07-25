"""Performance benchmarks for core operations (no external services required)."""

import time

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

# ── Benchmarks ─────────────────────────────────────────────────────────────────


def test_password_hash_performance():
    """get_password_hash should complete in under 500ms (bcrypt cost factor check)."""
    start = time.perf_counter()
    get_password_hash("TestPassword123!")
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"Password hashing too slow: {elapsed:.3f}s"


def test_password_verify_performance():
    """verify_password should complete in under 500ms."""
    hashed = get_password_hash("TestPassword123!")
    start = time.perf_counter()
    verify_password("TestPassword123!", hashed)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"Password verification too slow: {elapsed:.3f}s"


def test_access_token_creation_performance():
    """Creating 100 access tokens should complete in under 500ms total."""
    start = time.perf_counter()
    for i in range(100):
        create_access_token(subject=f"user-{i}")
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"100 token creations took {elapsed:.3f}s"


def test_refresh_token_creation_performance():
    """Creating 100 refresh tokens should complete in under 500ms total."""
    start = time.perf_counter()
    for i in range(100):
        create_refresh_token(subject=f"user-{i}")
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"100 refresh token creations took {elapsed:.3f}s"
