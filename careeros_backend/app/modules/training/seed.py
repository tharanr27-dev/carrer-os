"""Idempotent loader for the reviewed question bank."""

from typing import Any, Dict, List

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.training.bank.aptitude import APTITUDE
from app.modules.training.bank.behavioural import COMMUNICATION, HR, MANAGERIAL
from app.modules.training.bank.catalog import TOPIC_INDEX
from app.modules.training.bank.coding import CODING
from app.modules.training.bank.technical import TECHNICAL
from app.modules.training.models import TrainingQuestion
from app.modules.training.textutils import fingerprint


def all_seed() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for q in [*APTITUDE, *TECHNICAL, *CODING, *COMMUNICATION, *HR, *MANAGERIAL]:
        meta = TOPIC_INDEX[f"{q['round']}:{q['topic']}"]  # KeyError => bad seed topic (caught by tests)
        row = dict(q)
        row["category"] = meta["group"]
        row["source"] = "curated"
        row["review_status"] = "reviewed"
        row["fingerprint"] = fingerprint(q["prompt"])
        row["owner_user_id"] = None
        rows.append(row)
    return rows


SEED_LOCK_KEY = 727_001_001  # arbitrary app-specific key for pg_advisory_xact_lock


async def _lock_for_seeding(db: AsyncSession) -> None:
    """Serialise concurrent first-time seeding on PostgreSQL.

    `fingerprint` is intentionally not UNIQUE (generated questions may legitimately repeat across
    students), so without a lock two simultaneous first requests could both insert the whole bank.
    The lock is transaction-scoped, so it is released by the commit and is safe behind PgBouncer.
    SQLite (tests/dev) has a single writer and needs no lock.
    """
    if db.get_bind().dialect.name == "postgresql":
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SEED_LOCK_KEY})


async def ensure_seed(db: AsyncSession) -> int:
    """Insert any curated questions that are missing. Returns the number inserted."""
    seed = all_seed()
    count_stmt = select(func.count()).select_from(TrainingQuestion).where(TrainingQuestion.source == "curated")
    if (await db.execute(count_stmt)).scalar_one() >= len(seed):
        return 0  # fast path: no lock taken on normal requests
    await _lock_for_seeding(db)
    # Re-read under the lock: another request may have finished seeding while we waited.
    existing = set(
        (await db.execute(select(TrainingQuestion.fingerprint).where(TrainingQuestion.source == "curated"))).scalars()
    )
    new = [TrainingQuestion(**r) for r in seed if r["fingerprint"] not in existing]
    if new:
        db.add_all(new)
    await db.commit()
    return len(new)
