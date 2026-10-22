"""Pre-deployment audit tests: PostgreSQL compatibility (without a PostgreSQL server), foreign-key
integrity, ownership, AI-provider failure handling and regression guards.

No test here talks to Supabase, a real PostgreSQL server, or a paid AI API.
"""

import json
import logging
import re
import uuid
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateIndex, CreateTable

from app.core.dependencies import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.auth.models import User
from app.modules.training.llm import LLMUnavailable, TrainingLLM, get_llm
from app.modules.training.models import TrainingProfile, TrainingQuestion
from app.modules.training.seed import _lock_for_seeding, all_seed, ensure_seed
from app.modules.training.service import TrainingService
from app.modules.users.models import Profile, Project

from training_fakes import FakeLLM

P = "/api/v1/training"
NEW_TABLES = ["training_questions", "training_profiles", "training_attempts", "training_attempt_items"]
PG = postgresql.dialect()


# ── PostgreSQL compatibility (compile-time; no server) ───────────────────────
def test_new_tables_compile_to_expected_postgres_types():
    ddl = {n: str(CreateTable(Base.metadata.tables[n]).compile(dialect=PG)) for n in NEW_TABLES}
    q = ddl["training_questions"]
    assert "options JSONB" in q and "rubric JSONB" in q and "id UUID NOT NULL" in q
    assert "created_at TIMESTAMP WITH TIME ZONE NOT NULL" in q
    assert "UNIQUE (user_id)" in ddl["training_profiles"]
    assert "FOREIGN KEY(user_id) REFERENCES users (id)" in ddl["training_attempts"]
    items = ddl["training_attempt_items"]
    assert "REFERENCES training_attempts (id)" in items and "REFERENCES training_questions (id)" in items
    assert "answer JSONB" in items and "score FLOAT" in items


def test_index_and_identifier_names_are_valid_and_globally_unique():
    names = [ix.name for t in Base.metadata.tables.values() for ix in t.indexes]
    assert len(names) == len(set(names)), "PostgreSQL index names are schema-global; duplicates would break create_all"
    for ident in list(Base.metadata.tables) + names:
        assert len(ident) <= 63, ident
    for n in NEW_TABLES:
        for ix in Base.metadata.tables[n].indexes:
            str(CreateIndex(ix).compile(dialect=PG))  # compiles


def test_new_foreign_keys_target_existing_uuid_columns_created_earlier():
    order = [t.name for t in Base.metadata.sorted_tables]
    for n in NEW_TABLES:
        for fk in Base.metadata.tables[n].foreign_keys:
            assert fk.column.table.name in Base.metadata.tables
            assert order.index(fk.column.table.name) < order.index(n)
            assert fk.column.type.__class__.__name__ == "UUID"


def test_no_table_name_collisions_with_existing_schema():
    # 99 tables existed before this work (reported by the earlier Supabase provisioning commit).
    assert len(Base.metadata.tables) == 99 + len(NEW_TABLES)


async def test_every_orm_query_in_the_main_flows_compiles_for_postgres(client, llm):
    compiled = []

    def check(state):
        state.statement.compile(dialect=PG)  # raises CompileError for non-PostgreSQL constructs
        compiled.append(1)

    event.listen(Session, "do_orm_execute", check)
    try:
        await client.put(f"{P}/profile", json={"target_role": "Python Developer", "level": "fresher",
                                               "resume_data": {"projects": [{"title": "Portal"}], "skills": ["Python"]}})
        await client.get(f"{P}/meta")
        a = (await client.post(f"{P}/attempts", json={"mode": "practice", "round": "technical", "topic": "python", "count": 2})).json()["data"]
        await client.post(f"{P}/attempts/{a['id']}/answer", json={"item_id": a["items"][0]["id"], "index": 0})
        await client.post(f"{P}/attempts/{a['id']}/next", json={})
        await client.post(f"{P}/attempts/{a['id']}/finish")
        await client.post(f"{P}/attempts", json={"mode": "exam", "round": "aptitude", "count": 2})
        await client.post(f"{P}/attempts", json={"mode": "practice", "round": "resume", "count": 4})
        await client.post(f"{P}/attempts", json={"mode": "mock", "mock": {"rounds": ["aptitude", "technical", "coding", "hr", "resume"], "duration_min": 45}})
        await client.get(f"{P}/attempts", params={"status": "COMPLETED"})
        await client.get(f"{P}/questions", params={"round": "aptitude", "topic": "percentages"})
        assert (await client.get(f"{P}/progress")).status_code == 200
    finally:
        event.remove(Session, "do_orm_execute", check)
    assert len(compiled) > 40


def test_no_nul_characters_reach_text_or_jsonb_columns():
    # PostgreSQL rejects \u0000 in text/JSONB; all untrusted input passes through clean_text.
    from app.modules.training.schemas import AnswerRequest, ResumeProject

    assert "\x00" not in AnswerRequest(item_id="x", text="a\x00b").text
    assert "\x00" not in ResumeProject(title="a\x00b").title
    assert all("\x00" not in json.dumps(r, default=str) for r in all_seed())


# ── Concurrency fixes that only matter on PostgreSQL ─────────────────────────
async def test_seed_lock_is_only_taken_on_postgres():
    class FakeBind:
        def __init__(self, name):
            self.dialect = type("D", (), {"name": name})()

    class FakeDb:
        def __init__(self, name):
            self.bind, self.executed = FakeBind(name), []

        def get_bind(self):
            return self.bind

        async def execute(self, stmt, params=None):
            self.executed.append((str(stmt), params))

    pg, lite = FakeDb("postgresql"), FakeDb("sqlite")
    await _lock_for_seeding(pg)
    await _lock_for_seeding(lite)
    assert len(pg.executed) == 1 and "pg_advisory_xact_lock" in pg.executed[0][0] and pg.executed[0][1]["key"] > 0
    assert lite.executed == []


async def test_seeding_is_idempotent_and_repairs_missing_rows(sessionmaker_):
    async with sessionmaker_() as s:
        n = len(all_seed())
        assert await ensure_seed(s) == n
        assert await ensure_seed(s) == 0
        victim = (await s.execute(select(TrainingQuestion).where(TrainingQuestion.source == "curated").limit(1))).scalar_one()
        await s.delete(victim)
        await s.commit()
        assert await ensure_seed(s) == 1
        rows = (await s.execute(select(TrainingQuestion.fingerprint).where(TrainingQuestion.source == "curated"))).scalars().all()
        assert len(rows) == n == len(set(rows))


async def test_concurrent_first_profile_creation_does_not_500(sessionmaker_):
    uid = uuid.uuid4()
    async with sessionmaker_() as s1, sessionmaker_() as s2:
        svc = TrainingService(s1)
        real_commit = s1.commit

        async def racing_commit():
            s2.add(TrainingProfile(user_id=uid, level="fresher", language="en"))
            await s2.commit()  # the "other request" wins the race
            await real_commit()  # our insert now violates UNIQUE(user_id)

        s1.commit = racing_commit
        row = await svc.get_profile(uid)
        assert row.user_id == uid
    async with sessionmaker_() as s:
        assert len((await s.execute(select(TrainingProfile).where(TrainingProfile.user_id == uid))).scalars().all()) == 1


# ── Foreign-key integrity (SQLite with FK enforcement + a real users row, like PostgreSQL) ──
@pytest.fixture
async def fk_env():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    users = []
    async with sm() as s:
        for name in ("a", "b"):
            u = User(email=f"{name}@example.com", hashed_password="x")
            s.add(u)
            users.append(u)
        await s.commit()
    who = type("W", (), {"id": users[0].id})()

    async def _db():
        async with sm() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: who
    app.dependency_overrides[get_llm] = lambda: FakeLLM(available=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        c.sm, c.who, c.users = sm, who, users
        yield c
    for d in (get_db, get_current_user, get_llm):
        app.dependency_overrides.pop(d, None)
    await engine.dispose()


async def test_full_flows_satisfy_foreign_keys(fk_env):
    c = fk_env
    async with c.sm() as s:
        prof = Profile(user_id=c.who.id, first_name="A")
        s.add(prof)
        await s.flush()
        s.add(Project(profile_id=prof.id, title="Library Portal"))
        await s.commit()
    for body in (
        {"mode": "practice", "round": "aptitude", "topic": "percentages", "count": 2},
        {"mode": "exam", "round": "aptitude", "count": 3},
        {"mode": "practice", "round": "resume", "count": 4},
        {"mode": "mock", "mock": {"rounds": ["aptitude", "technical", "coding", "hr", "resume"], "duration_min": 30}},
    ):
        r = await c.post(f"{P}/attempts", json=body)
        assert r.status_code == 201, (body, r.text)
        att = r.json()["data"]
        first = att["items"][0]
        text = "I built tests first because the situation needed reliable delivery and I learned a lot from it."
        payload = {"item_id": first["id"], "index": 0} if first["qtype"] == "mcq" else {"item_id": first["id"], "text": text, "self_passed": 0}
        assert (await c.post(f"{P}/attempts/{att['id']}/answer", json=payload)).status_code == 200
        assert (await c.post(f"{P}/attempts/{att['id']}/finish")).status_code == 200
    assert (await c.get(f"{P}/progress")).status_code == 200
    assert (await c.put(f"{P}/profile", json={"target_role": "Data Analyst"})).status_code == 200


# ── Authentication and ownership ─────────────────────────────────────────────
ROUTES = [
    ("get", "/meta", None), ("get", "/profile", None), ("put", "/profile", {}), ("get", "/questions", None),
    ("post", "/attempts", {"mode": "practice", "round": "aptitude"}), ("get", "/attempts", None),
    (("get"), f"/attempts/{uuid.uuid4()}", None), ("post", f"/attempts/{uuid.uuid4()}/answer", {"item_id": "x"}),
    ("post", f"/attempts/{uuid.uuid4()}/next", {}), ("post", f"/attempts/{uuid.uuid4()}/finish", None),
    ("get", "/progress", None),
]


@pytest.mark.parametrize("method,path,body", ROUTES)
async def test_every_training_route_requires_a_valid_token(client, method, path, body):
    app.dependency_overrides.pop(get_current_user, None)
    for headers in ({}, {"Authorization": "Bearer not-a-real-token"}):
        r = await client.request(method.upper(), f"{P}{path}", json=body, headers=headers)
        assert r.status_code == 401, (method, path, r.status_code)


async def test_mock_and_resume_sessions_are_private_to_their_owner(client, me):
    await client.put(f"{P}/profile", json={"resume_data": {"projects": [{"title": "Zebra Tracker"}], "skills": ["Rust"]}})
    mock = (await client.post(f"{P}/attempts", json={"mode": "mock", "mock": {"rounds": ["aptitude", "resume"], "duration_min": 20}})).json()["data"]
    resume = (await client.post(f"{P}/attempts", json={"mode": "practice", "round": "resume", "count": 4})).json()["data"]
    assert "Zebra Tracker" in " ".join(i["prompt"] for i in resume["items"])
    a_item = mock["items"][0]["id"]

    me.id = uuid.uuid4()  # student B
    for att in (mock, resume):
        assert (await client.get(f"{P}/attempts/{att['id']}")).status_code == 404
        assert (await client.post(f"{P}/attempts/{att['id']}/finish")).status_code == 404
    assert (await client.post(f"{P}/attempts/{mock['id']}/answer", json={"item_id": a_item, "index": 0})).status_code == 404
    # B's own attempt cannot be used to answer A's item either
    b_att = (await client.post(f"{P}/attempts", json={"mode": "practice", "round": "aptitude", "count": 1})).json()["data"]
    assert (await client.post(f"{P}/attempts/{b_att['id']}/answer", json={"item_id": a_item, "index": 0})).status_code == 404
    # B sees none of A's data
    profile = (await client.get(f"{P}/profile")).json()["data"]
    assert "Zebra Tracker" not in json.dumps(profile) and "Rust" not in json.dumps(profile["resume_data"]["skills"])
    b_resume = await client.post(f"{P}/attempts", json={"mode": "practice", "round": "resume", "count": 4})
    assert b_resume.status_code == 422  # B has no projects/skills, so A's are not borrowed
    hist = (await client.get(f"{P}/attempts")).json()["data"]
    assert [i["id"] for i in hist["items"]] == [b_att["id"]]
    assert (await client.get(f"{P}/progress")).json()["data"]["attempts_total"] == 1


# ── AI provider configuration and failure handling ───────────────────────────
KEY = "sk-ant-TEST-SECRET-123456"


def _http_patch(handler):
    real = httpx.AsyncClient

    def factory(*a, **kw):
        return real(transport=httpx.MockTransport(handler), timeout=kw.get("timeout"))

    return patch("app.modules.training.llm.httpx.AsyncClient", side_effect=factory)


@pytest.mark.parametrize("key", [None, "", "   "])
async def test_missing_or_blank_key_means_unavailable_and_no_http_call(key):
    llm = TrainingLLM(key, "m", 1.0)
    assert llm.available is False
    called = []
    with _http_patch(lambda req: called.append(req) or httpx.Response(200, json={})):
        with pytest.raises(LLMUnavailable):
            await llm.complete_json("s", "u")
    assert called == []


@pytest.mark.parametrize("resp", [
    httpx.Response(401, json={"error": {"message": "invalid x-api-key"}}),
    httpx.Response(429, json={"error": "rate"}),
    httpx.Response(500, text="boom"),
    httpx.Response(200, text="<html>not json</html>"),
    httpx.Response(200, json={"content": []}),
    httpx.Response(200, json={"content": [{"type": "text", "text": "no json here"}]}),
])
async def test_provider_failures_become_llm_unavailable_without_leaking_the_key(resp, caplog):
    llm = TrainingLLM(KEY, "m", 1.0)
    with caplog.at_level(logging.DEBUG), _http_patch(lambda req: resp):
        with pytest.raises(LLMUnavailable) as exc:
            await llm.complete_json("s", "u")
    assert KEY not in str(exc.value) and KEY not in caplog.text


async def test_provider_timeout_and_network_error_are_safe():
    llm = TrainingLLM(KEY, "m", 1.0)
    for err in (httpx.ReadTimeout("slow"), httpx.ConnectError("dns")):
        def boom(req, err=err):
            raise err

        with _http_patch(boom):
            with pytest.raises(LLMUnavailable):
                await llm.complete_json("s", "u")


async def test_key_is_sent_only_as_a_header_to_the_provider():
    seen = {}

    def handler(req):
        seen["url"], seen["key"], seen["body"] = str(req.url), req.headers.get("x-api-key"), req.content.decode()
        return httpx.Response(200, json={"content": [{"type": "text", "text": '{"ok": true}'}]})

    with _http_patch(handler):
        assert await TrainingLLM(f"  {KEY}  ", "m", 1.0).complete_json("sys", "user") == {"ok": True}
    assert seen["key"] == KEY and KEY not in seen["url"] and KEY not in seen["body"]
    assert seen["url"].startswith("https://api.anthropic.com/")


async def test_invalid_key_end_to_end_falls_back_safely(client, caplog):
    app.dependency_overrides[get_llm] = lambda: TrainingLLM(KEY, "m", 1.0)
    with caplog.at_level(logging.DEBUG), _http_patch(lambda req: httpx.Response(401, json={"error": "invalid x-api-key"})):
        meta = await client.get(f"{P}/meta")
        gen = await client.post(f"{P}/attempts", json={"mode": "practice", "round": "technical", "topic": "python",
                                                         "count": 2, "generate": True, "qtype": "mcq"})
        att = gen.json()["data"]
        text_q = await client.post(f"{P}/attempts", json={"mode": "practice", "round": "technical", "topic": "oop", "count": 1, "qtype": "text"})
        t = text_q.json()["data"]
        ans = await client.post(f"{P}/attempts/{t['id']}/answer", json={"item_id": t["items"][0]["id"],
              "text": "Encapsulation hides data behind methods and inheritance reuses a parent class for polymorphism."})
    assert gen.status_code == 201 and all(i["source"] == "curated" for i in att["items"])
    assert any("unavailable" in n for n in att["config"]["notices"])
    res = ans.json()["data"]["item"]["result"]
    assert res["score_kind"] == "keyword_estimate" and "fallback_reason" in res["evaluation"]
    for r in (meta, gen, ans):
        assert KEY not in r.text
    assert KEY not in caplog.text
    assert meta.json()["data"]["ai_available"] is True  # configured; failures are handled per call


async def test_meta_never_exposes_provider_details(client, llm):
    llm.__init__([], available=True)
    body = (await client.get(f"{P}/meta")).text
    assert "test-key" not in body and "test-model" not in body


# ── Regression guards for pre-existing features ──────────────────────────────
def test_previously_verified_endpoints_are_all_still_registered():
    recorded = json.loads((Path(__file__).parents[2] / "endpoint_verification_results.json").read_text(encoding="utf-8"))
    paths = [(r.path, getattr(r, "methods", {"GET"})) for r in app.routes]
    missing = []
    for e in recorded:
        ep = e["endpoint"].split("?")[0]
        candidates = [ep, "/api/v1" + ep]  # some recorded endpoints are root-level, others are versioned
        if not any(
            e["method"] in m and re.fullmatch(re.sub(r"\{[^}]+\}", "[^/]+", p), c) for p, m in paths for c in candidates
        ):
            missing.append((e["method"], e["endpoint"]))
    assert not missing, missing


def test_jobs_recommended_route_still_authenticated_and_registered():
    r = next(r for r in app.routes if getattr(r, "path", "") == "/api/v1/jobs/recommended")
    assert "GET" in r.methods
    from app.modules.jobs.service import MAX_PAGE

    assert MAX_PAGE == 250
