import logging
import os
import re
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# ─── SECRET_KEY startup policy ───────────────────────────────────────────────
# SECRET_KEY signs every login token. The placeholder below is public (it is committed to Git), so
# anyone who knows a user id could forge a valid token if it were ever used outside local development.
PUBLIC_PLACEHOLDER_SECRET_KEY = "super-secret-key-change-me-in-production"
MIN_SECRET_KEY_LENGTH = 32
# Only these environments may start with a weak key. Anything else (production, staging, or an
# unrecognised/empty name) fails closed.
_RELAXED_ENVIRONMENTS = {"development", "dev", "local", "test", "testing"}
_WARN_ENVIRONMENTS = {"development", "dev", "local"}
_KNOWN_PLACEHOLDERS = {
    PUBLIC_PLACEHOLDER_SECRET_KEY,
    "replace-with-a-secure-random-secret-key-min-32-chars",  # .env.example
    "change_me_in_production",  # deployment/k8s/secrets-example.yaml
    "changeme",
    "secret",
}
_PLACEHOLDER_HINT = re.compile(r"change[-_ ]?me|replace[-_ ]?with|placeholder|your[-_ ]?secret", re.IGNORECASE)


class InsecureConfigurationError(RuntimeError):
    """Raised at startup for an unsafe configuration. Messages never contain secret values."""


def secret_key_problems(secret_key: Optional[str]) -> List[str]:
    """Describes what is wrong with a key without ever echoing it."""
    key = (secret_key or "").strip()
    if not key:
        return ["SECRET_KEY is missing or empty"]
    problems = []
    if key.lower() in _KNOWN_PLACEHOLDERS or _PLACEHOLDER_HINT.search(key):
        problems.append("SECRET_KEY is a known public placeholder value")
    if len(key) < MIN_SECRET_KEY_LENGTH:
        problems.append(f"SECRET_KEY is shorter than {MIN_SECRET_KEY_LENGTH} characters")
    return problems


def enforce_secret_key_policy(
    environment: Optional[str], secret_key: Optional[str], logger: Optional[logging.Logger] = None
) -> None:
    """Refuse to start with an insecure key outside local development; only warn inside it."""
    problems = secret_key_problems(secret_key)
    if not problems:
        return
    env = (environment or "").strip().lower()
    if env in _RELAXED_ENVIRONMENTS:
        if env in _WARN_ENVIRONMENTS:
            (logger or logging.getLogger("careeros")).warning(
                "Insecure SECRET_KEY for local development (%s). Replace it with a random key of at least "
                "%d characters before sharing, staging or production use.",
                "; ".join(problems),
                MIN_SECRET_KEY_LENGTH,
            )
        return
    raise InsecureConfigurationError(
        f"Refusing to start in the '{env or 'unset'}' environment: {'; '.join(problems)}. "
        f"Set SECRET_KEY to a random value of at least {MIN_SECRET_KEY_LENGTH} characters in the "
        "deployment environment (for example from your host's secret manager)."
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "CareerOS AI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "*")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

    SECRET_KEY: str = os.getenv("SECRET_KEY", PUBLIC_PLACEHOLDER_SECRET_KEY)
    # Whether startup runs Base.metadata.create_all(): "auto" (default) = only for SQLite; "true" = always;
    # "false" = never. Non-SQLite databases are never written to at startup unless you opt in explicitly.
    AUTO_CREATE_TABLES: str = os.getenv("AUTO_CREATE_TABLES", "auto")

    # Private directory for uploaded files (git-ignored). Override in deployment, e.g. a mounted volume.
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "data" / "uploads"))

    # Failed-login throttling (see app/core/login_throttle.py)
    LOGIN_MAX_FAILURES_PER_ACCOUNT: int = int(os.getenv("LOGIN_MAX_FAILURES_PER_ACCOUNT", "5"))
    LOGIN_MAX_FAILURES_PER_IP: int = int(os.getenv("LOGIN_MAX_FAILURES_PER_IP", "30"))
    LOGIN_FAILURE_WINDOW_SECONDS: int = int(os.getenv("LOGIN_FAILURE_WINDOW_SECONDS", "900"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = "HS256"

    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "careeros")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"
    )

    DATABASE_URL: str | None = os.getenv("DATABASE_URL", None)

    # Optional: enables AI question generation / answer evaluation in the training module.
    # When unset, training falls back to the reviewed question bank and rule-based scoring.
    ANTHROPIC_API_KEY: str | None = None
    # Grok (xAI): takes priority over Anthropic when set. OpenAI-compatible chat completions API.
    XAI_API_KEY: str | None = None
    # Groq (groq.com, keys start with "gsk_"). The key may be placed in either GROQ_API_KEY or XAI_API_KEY.
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    XAI_MODEL: str = "grok-3-mini"
    XAI_API_URL: str = "https://api.x.ai/v1/chat/completions"
    TRAINING_LLM_MODEL: str = "claude-haiku-5-5"
    TRAINING_LLM_TIMEOUT_SECONDS: float = 25.0
    # AI Mentor chat (uses the same provider/model as above).
    MENTOR_HISTORY_MESSAGES: int = 10
    MENTOR_MAX_REPLY_TOKENS: int = 1500
    MENTOR_MESSAGES_PER_MINUTE: int = 12

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            uri = self.DATABASE_URL.strip()
            if uri.startswith("postgresql://"):
                uri = "postgresql+asyncpg://" + uri[len("postgresql://"):]
            elif uri.startswith("postgres://"):
                uri = "postgresql+asyncpg://" + uri[len("postgres://"):]
            return uri
        if self.ENVIRONMENT != "production" and self.POSTGRES_SERVER == "postgres":
            return "sqlite+aiosqlite:///./careeros.db"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
enforce_secret_key_policy(settings.ENVIRONMENT, settings.SECRET_KEY)
