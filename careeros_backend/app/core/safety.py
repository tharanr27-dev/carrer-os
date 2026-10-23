"""Guards that stop development scripts from touching a remote database by accident."""

import os

from app.core.config import settings


def is_sqlite() -> bool:
    return "sqlite" in settings.sqlalchemy_database_uri.lower()


def require_local_database(action: str) -> None:
    """Exit unless the configured database is SQLite, or the operator explicitly allowed remote scripts.

    The message never contains the database URL.
    """
    if is_sqlite() or os.getenv("ALLOW_REMOTE_DB_SCRIPTS", "").lower() == "yes":
        return
    raise SystemExit(
        f"Refusing to {action}: DATABASE_URL points to a non-SQLite (possibly remote) database. "
        "Use a local SQLite URL (for example DATABASE_URL=sqlite+aiosqlite:///./local.db), or set "
        "ALLOW_REMOTE_DB_SCRIPTS=yes if you really intend to change that database."
    )


def require_env(name: str, hint: str = "") -> str:
    value = os.getenv(name, "")
    if not value:
        raise SystemExit(f"{name} must be set in the environment. {hint}".strip())
    return value
