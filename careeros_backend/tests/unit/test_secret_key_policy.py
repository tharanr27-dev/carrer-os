"""Startup guard for SECRET_KEY. No secrets from .env are used: every key below is made up in the test."""

import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import (
    MIN_SECRET_KEY_LENGTH,
    PUBLIC_PLACEHOLDER_SECRET_KEY,
    InsecureConfigurationError,
    enforce_secret_key_policy,
    secret_key_problems,
)

ROOT = Path(__file__).parents[2]
STRONG = secrets.token_urlsafe(48)  # generated per run, never printed
SHORT_MARKER = "short-KEY-abc123"  # distinctive, so we can prove it never appears in messages


# ── what counts as a bad key ─────────────────────────────────────────────────
@pytest.mark.parametrize("key", [None, "", "   ", "\n\t"])
def test_missing_or_blank_key_is_rejected(key):
    assert secret_key_problems(key) == ["SECRET_KEY is missing or empty"]


@pytest.mark.parametrize("key", [
    PUBLIC_PLACEHOLDER_SECRET_KEY,
    f"  {PUBLIC_PLACEHOLDER_SECRET_KEY}  ",
    PUBLIC_PLACEHOLDER_SECRET_KEY.upper(),
    "replace-with-a-secure-random-secret-key-min-32-chars",  # .env.example (long enough, still public)
    "change_me_in_production",
    "please-change-me-to-something-really-long-123456",
    "your-secret-goes-here-your-secret-goes-here",
])
def test_known_placeholders_are_rejected_even_if_long(key):
    assert "SECRET_KEY is a known public placeholder value" in secret_key_problems(key)


def test_length_boundary():
    assert secret_key_problems("x" * (MIN_SECRET_KEY_LENGTH - 1)) == [f"SECRET_KEY is shorter than {MIN_SECRET_KEY_LENGTH} characters"]
    assert secret_key_problems("k" * MIN_SECRET_KEY_LENGTH) == []
    assert secret_key_problems(f" {'k' * 31} ") != []  # surrounding whitespace does not count toward length


def test_generated_key_is_valid():
    assert len(STRONG) >= 60 and secret_key_problems(STRONG) == []


# ── enforcement by environment ───────────────────────────────────────────────
@pytest.mark.parametrize("bad", [None, "", PUBLIC_PLACEHOLDER_SECRET_KEY, SHORT_MARKER, "change_me_in_production"])
@pytest.mark.parametrize("env", ["production", "Production ", "PRODUCTION", "prod", "staging", "", None, "something-new"])
def test_non_development_environments_reject_insecure_keys(env, bad):
    with pytest.raises(InsecureConfigurationError) as exc:
        enforce_secret_key_policy(env, bad)
    msg = str(exc.value)
    assert "Refusing to start" in msg and "SECRET_KEY" in msg
    assert SHORT_MARKER not in msg and PUBLIC_PLACEHOLDER_SECRET_KEY not in msg  # the key is never echoed


@pytest.mark.parametrize("env", ["production", "prod", "staging", "something-new", "development", "local", "test"])
def test_every_environment_accepts_a_strong_key_silently(env, caplog):
    with caplog.at_level(logging.DEBUG):
        enforce_secret_key_policy(env, STRONG)
    assert caplog.records == []


@pytest.mark.parametrize("env", ["development", "dev", "local", "Development "])
def test_development_keeps_working_but_warns_without_logging_the_key(env, caplog):
    with caplog.at_level(logging.DEBUG, logger="careeros"):
        enforce_secret_key_policy(env, PUBLIC_PLACEHOLDER_SECRET_KEY)
        enforce_secret_key_policy(env, SHORT_MARKER)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 2
    text = " ".join(r.getMessage() for r in warnings)
    assert "local development" in text
    assert PUBLIC_PLACEHOLDER_SECRET_KEY not in text and SHORT_MARKER not in text


@pytest.mark.parametrize("env", ["test", "testing"])
def test_test_environment_is_quiet_and_allowed(env, caplog):
    with caplog.at_level(logging.DEBUG):
        enforce_secret_key_policy(env, PUBLIC_PLACEHOLDER_SECRET_KEY)
    assert caplog.records == []


# ── real process startup (isolated: empty working dir, so the real .env is never read) ──
def _start(tmp_path, **env):
    base = {k: v for k, v in os.environ.items() if k not in ("SECRET_KEY", "ENVIRONMENT", "DATABASE_URL")}
    base.update({"PYTHONPATH": str(ROOT), "DATABASE_URL": "sqlite+aiosqlite://"})
    base.update(env)
    return subprocess.run(
        [sys.executable, "-c", "import app.core.config as c; print('started', c.settings.ENVIRONMENT)"],
        cwd=tmp_path, env=base, capture_output=True, text=True, timeout=60,
    )


@pytest.mark.parametrize("key", [PUBLIC_PLACEHOLDER_SECRET_KEY, SHORT_MARKER])
def test_production_process_refuses_to_start_with_insecure_key(tmp_path, key):
    r = _start(tmp_path, ENVIRONMENT="production", SECRET_KEY=key)
    assert r.returncode != 0 and "started" not in r.stdout
    assert "InsecureConfigurationError" in r.stderr and "Refusing to start" in r.stderr
    assert key not in r.stdout + r.stderr  # not in the message, the traceback, or anywhere else


def test_production_process_refuses_to_start_with_missing_key(tmp_path):
    r = _start(tmp_path, ENVIRONMENT="production")  # no SECRET_KEY at all: falls back to the placeholder
    assert r.returncode != 0 and "Refusing to start" in r.stderr
    assert PUBLIC_PLACEHOLDER_SECRET_KEY not in r.stderr.replace("is a known public placeholder", "")


def test_production_process_starts_with_a_strong_key(tmp_path):
    r = _start(tmp_path, ENVIRONMENT="production", SECRET_KEY=STRONG)
    assert r.returncode == 0, r.stderr[-500:]
    assert "started production" in r.stdout
    assert STRONG not in r.stdout + r.stderr


def test_development_process_still_starts_with_the_placeholder_and_warns(tmp_path):
    r = _start(tmp_path, ENVIRONMENT="development", SECRET_KEY=PUBLIC_PLACEHOLDER_SECRET_KEY)
    assert r.returncode == 0 and "started development" in r.stdout
    assert "Insecure SECRET_KEY for local development" in r.stderr
    assert PUBLIC_PLACEHOLDER_SECRET_KEY not in r.stderr  # the warning names the problem, not the value


def test_default_environment_is_development_and_keeps_working(tmp_path):
    r = _start(tmp_path)  # nothing set: defaults to development + placeholder, as before
    assert r.returncode == 0 and "started development" in r.stdout
