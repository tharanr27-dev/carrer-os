import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.core.middleware.rate_limit import RateLimitMiddleware
from app.main import app
from app.modules.training.llm import get_llm

from training_fakes import FakeLLM


def _reset_rate_limiter():
    """The app rate-limits per IP in memory; a long test run would otherwise trip it (HTTP 429)."""
    node = getattr(app, "middleware_stack", None)
    while node is not None:
        if isinstance(node, RateLimitMiddleware):
            node._cache.clear()
            return
        node = getattr(node, "app", None)


@pytest.fixture(autouse=True)
def _fresh_rate_limit():
    _reset_rate_limiter()
    yield
    _reset_rate_limiter()


class Who:
    id = uuid.uuid4()


@pytest.fixture
async def sessionmaker_():
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def llm():
    return FakeLLM(available=False)


@pytest.fixture
def me():
    w = Who()
    w.id = uuid.uuid4()
    return w


@pytest.fixture
async def client(sessionmaker_, me, llm):
    async def _db():
        async with sessionmaker_() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: me
    app.dependency_overrides[get_llm] = lambda: llm
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        c.sessionmaker = sessionmaker_
        yield c
    for dep in (get_db, get_current_user, get_llm):
        app.dependency_overrides.pop(dep, None)
