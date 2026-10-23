"""Placement ranking/eligibility, recruiter matching, admin background tasks, and the safety guards.

Isolated in-memory SQLite; no remote database; no network."""

import asyncio
import logging
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.modules.placements.models import College, DriveEligibility, DriveRegistration, PlacementDrive
from app.modules.placements.services.ai_readiness_engine import AIPlacementReadinessEngine
from app.modules.placements.services.student_eligibility_service import StudentEligibilityService
from app.modules.placements.services.student_metrics import parse_cgpa, student_metrics
from app.modules.placements.services.student_ranking_service import StudentRankingService
from app.modules.recruiters.models import Application, Company, Job
from app.modules.recruiters.services.ai_insights_engine import AIInsightsEngine
from app.modules.recruiters.services.matching_engine import CandidateMatchingEngine
from app.modules.resumes.models import Resume, ResumeAnalysis
from app.modules.training.seed import ensure_seed
from app.modules.users.models import Certification, Education, Profile, ProfileSkill, Project, Skill


# ── placements ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,expected", [("8.4", 8.4), ("8.4/10", 8.4), ("3.6/4.0", 9.0), ("84%", 8.4), ("84", 8.4), (" 9 ", 9.0),
                                          ("abc", None), ("", None), (None, None), ("11/10", None), ("120%", None)])
def test_cgpa_parsing_normalises_to_ten_or_gives_up(raw, expected):
    assert parse_cgpa(raw) == expected


async def _student(db, gpa=None, ats=None, certs=0, projects=0):
    uid = uuid.uuid4()
    prof = Profile(user_id=uid, first_name="S")
    db.add(prof)
    await db.flush()
    if gpa:
        db.add(Education(profile_id=prof.id, institution="Uni", gpa=gpa))
    for i in range(certs):
        db.add(Certification(profile_id=prof.id, name=f"c{i}"))
    for i in range(projects):
        db.add(Project(profile_id=prof.id, title=f"p{i}"))
    if ats is not None:
        r = Resume(user_id=uid, file_name="a.pdf", s3_key=f"k-{uuid.uuid4()}", status="COMPLETED")
        db.add(r)
        await db.flush()
        db.add(ResumeAnalysis(resume_id=r.id, ats_score=ats, grammar_score=80, quality_score=70, keyword_analysis={"method": "rule_based_v1"}))
    await db.commit()
    return uid


async def _drive(db, students, requirements=None):
    c = College(name="Uni", domain=f"{uuid.uuid4().hex[:6]}.edu")
    db.add(c)
    await db.flush()
    d = PlacementDrive(college_id=c.id, title="Drive", requirements=requirements)
    db.add(d)
    await db.flush()
    for s in students:
        db.add(DriveRegistration(drive_id=d.id, student_id=s))
    await db.commit()
    return d.id


async def test_student_metrics_come_from_saved_records_and_missing_data_stays_none(sessionmaker_):
    async with sessionmaker_() as db:
        full = await _student(db, gpa="8.2", ats=80.0, certs=2, projects=3)
        empty = await _student(db)
        m, e = await student_metrics(db, full), await student_metrics(db, empty)
    assert m["cgpa"] == 8.2 and m["ats_score"] == 80.0 and m["certifications"] == 2 and m["projects"] == 3
    assert e == {k: None for k in e}  # nothing recorded -> nothing invented (the old code gave everyone cgpa 8.0, ats 72, ...)
    assert m["hackathons"] is None and m["recommendations"] is None


async def test_ranking_orders_students_by_their_own_records_and_lists_what_is_missing(sessionmaker_):
    async with sessionmaker_() as db:
        strong = await _student(db, gpa="9.0", ats=90.0, certs=3, projects=4)
        mid = await _student(db, gpa="7.0", ats=60.0)
        nothing = await _student(db)
        drive = await _drive(db, [mid, nothing, strong])
        ranking = await StudentRankingService(db).rank_students_for_drive(drive)
        stored = {r.student_id: r.ranking_score for r in (await db.execute(select(DriveEligibility))).scalars()}
    order = [r["student_id"] for r in ranking]
    assert order == [str(strong), str(mid), str(nothing)]
    scores = [r["score"] for r in ranking]
    assert scores[0] > scores[1] > scores[2] == 0.0
    assert ranking[2]["missing_data"] and ranking[2]["weight_coverage_pct"] == 0.0
    assert "hackathons" in ranking[0]["missing_data"] and ranking[0]["weight_coverage_pct"] < 100
    assert scores[0] != 74.0  # the old identical fabricated composite
    assert stored == {}  # no eligibility rows existed, so nothing to update (ranking never invents rows)


async def test_eligibility_checks_cgpa_and_never_silently_passes_unverifiable_requirements(sessionmaker_):
    ev = StudentEligibilityService.evaluate
    assert ev({"min_cgpa": 7.0}, 8.0) == (True, "Meets the checked requirements")
    ok, why = ev({"min_cgpa": 7.0}, 6.5)
    assert not ok and "below the minimum" in why
    ok, why = ev({"min_cgpa": 7.0}, None)
    assert not ok and "none is saved" in why
    ok, why = ev({"min_cgpa": 7.0, "max_backlogs": 0}, 8.0)
    assert ok and "Could not verify: max_backlogs" in why
    assert ev(None, None)[0] is True
    async with sessionmaker_() as db:
        good = await _student(db, gpa="8.5")
        low = await _student(db, gpa="6.0")
        unknown = await _student(db)
        drive = await _drive(db, [good, low, unknown], {"min_cgpa": 7.0})
        n = await StudentEligibilityService(db).calculate_bulk_eligibility(drive)
        rows = {r.student_id: r.is_eligible for r in (await db.execute(select(DriveEligibility))).scalars()}
        assert n == 3 and rows == {good: True, low: False, unknown: False}  # was a constant 150
        assert await StudentEligibilityService(db).calculate_bulk_eligibility(uuid.uuid4()) == 0
        again = await StudentEligibilityService(db).calculate_bulk_eligibility(drive)
        assert again == 3 and len((await db.execute(select(DriveEligibility))).scalars().all()) == 3  # idempotent


async def test_batch_readiness_admits_it_cannot_be_computed():
    r = await AIPlacementReadinessEngine(AsyncMock()).analyze_batch_readiness(uuid.uuid4())
    assert r["available"] is False and r["overall_readiness"] is None and "not linked" in r["reason"]
    assert "75%" not in str(r) and "AWS workshop" not in str(r)


# ── recruiters ───────────────────────────────────────────────────────────────
async def _job_and_candidate(db, requirements, skills):
    uid = uuid.uuid4()
    prof = Profile(user_id=uid, first_name="C")
    db.add(prof)
    await db.flush()
    for name in skills:
        sk = (await db.execute(select(Skill).where(Skill.name == name))).scalars().first() or Skill(name=name)
        db.add(sk)
        await db.flush()
        db.add(ProfileSkill(profile_id=prof.id, skill_id=sk.id))
    co = Company(name="Co", domain=f"{uuid.uuid4().hex[:6]}.com")
    db.add(co)
    await db.flush()
    job = Job(company_id=co.id, title="Backend Engineer", description="Build services", requirements=requirements)
    db.add(job)
    await db.flush()
    app = Application(job_id=job.id, candidate_id=uid)
    db.add(app)
    await db.commit()
    return app.id


async def test_fit_score_is_the_real_skill_overlap_not_a_constant(sessionmaker_):
    async with sessionmaker_() as db:
        a = await _job_and_candidate(db, ["3+ years Python", "SQL experience", "Docker", "Redis"], ["Python", "SQL"])
        b = await _job_and_candidate(db, ["3+ years Python", "SQL experience", "Docker", "Redis"], [])
        c = await _job_and_candidate(db, ["Be a good team player"], ["Python"])  # names no skill; description names none either
        fits = [await CandidateMatchingEngine(db).calculate_deterministic_score(x) for x in (a, b, c)]
        apps = [(await db.execute(select(Application).where(Application.id == x))).scalars().one() for x in (a, b, c)]
    assert fits == ["50%", "0%", "N/A"]  # the old stub returned "75%" for everyone
    assert sorted(apps[0].match_details["matched_skills"]) == ["Python", "SQL"] and sorted(apps[0].match_details["missing_skills"]) == ["Docker", "Redis"]
    assert apps[2].match_details["note"] and apps[0].match_details["method"] == "skill_overlap_v1"


async def test_insights_contain_only_facts_and_reviewed_questions(sessionmaker_):
    async with sessionmaker_() as db:
        await ensure_seed(db)
        app_id = await _job_and_candidate(db, ["Python", "SQL", "Docker"], ["Python"])
        ins = await AIInsightsEngine(db).generate_candidate_insights(app_id)
        stored = (await db.execute(select(Application).where(Application.id == app_id))).scalars().one().ai_insights
    assert stored == ins and ins["method"] == "skill_overlap_v1"
    assert "1 of 3" in ins["strengths"][0] and "Python" in ins["strengths"][0]
    assert "SQL" in ins["gaps"][0] and "Docker" in ins["gaps"][0] and "may still have them" in ins["gaps"][0]
    assert 1 <= len(ins["suggested_interview_questions"]) <= 5
    text = str(ins)
    for invented in ("startup", "Django", "transitioned", "FastAPI, though"):
        assert invented not in text  # strings from the old canned insights
    assert await AIInsightsEngine(db).generate_candidate_insights(uuid.uuid4()) == {}


# ── admin background tasks ───────────────────────────────────────────────────
def test_scheduled_admin_tasks_no_longer_record_invented_figures():
    from app.modules.admin import tasks

    with patch.object(tasks, "_redis_set_sync") as redis, patch.object(tasks, "_record_system_metric") as metric, patch.object(tasks, "_record_job_history"):
        a = tasks.refresh_dashboard_cache.run()
        b = tasks.aggregate_ai_tokens.run()
    assert a["status"] == b["status"] == "skipped"
    redis.assert_not_called()
    metric.assert_not_called()
    assert not hasattr(tasks, "_query_total_users")  # the 1500/950 stub helpers are gone


# ── safety guards ────────────────────────────────────────────────────────────
def test_scripts_refuse_a_non_sqlite_database_without_explicit_permission(monkeypatch):
    from app.core import safety

    monkeypatch.delenv("ALLOW_REMOTE_DB_SCRIPTS", raising=False)
    fake = MagicMock(sqlalchemy_database_uri="postgresql+asyncpg://user:SECRETPW@db.example.com/postgres")
    monkeypatch.setattr(safety, "settings", fake)
    with pytest.raises(SystemExit) as exc:
        safety.require_local_database("seed")
    assert "SECRETPW" not in str(exc.value) and "db.example.com" not in str(exc.value)  # the URL is never echoed
    monkeypatch.setenv("ALLOW_REMOTE_DB_SCRIPTS", "yes")
    safety.require_local_database("seed")
    monkeypatch.delenv("ALLOW_REMOTE_DB_SCRIPTS")
    monkeypatch.setattr(safety, "settings", MagicMock(sqlalchemy_database_uri="sqlite+aiosqlite:///./x.db"))
    safety.require_local_database("seed")


def test_seed_script_has_no_default_admin_password_and_requires_a_strong_one(monkeypatch):
    import ast
    import pathlib

    src = (pathlib.Path(__file__).parents[2] / "scripts" / "seed_dev.py").read_text(encoding="utf-8")
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "SEED_ADMIN_PASSWORD":
            assert len(n.args) == 1  # os.getenv("SEED_ADMIN_PASSWORD") with no fallback value
    import importlib

    monkeypatch.setenv("ALLOW_REMOTE_DB_SCRIPTS", "yes")  # only bypasses the DB guard; the password check exits before any connection
    seed = importlib.import_module("scripts.seed_dev")
    monkeypatch.setattr(seed, "ADMIN_PASSWORD", None)
    with pytest.raises(SystemExit) as e1:
        asyncio.run(seed.seed())
    assert "SEED_ADMIN_PASSWORD" in str(e1.value)
    monkeypatch.setattr(seed, "ADMIN_PASSWORD", "short")
    with pytest.raises(SystemExit):
        asyncio.run(seed.seed())


def test_no_tracked_script_or_doc_carries_a_literal_admin_password():
    import pathlib
    import re

    root = pathlib.Path(__file__).parents[3]
    pat = re.compile(r"""(?:ADMIN_PASSWORD|admin[_-]?pass\w*)\s*[:=]\s*["'][^"'$<{]{6,}["']""", re.I)
    for rel in ("README.md", "careeros_backend/scripts/seed_dev.py", "careeros_backend/scripts/e2e_live.py",
                "careeros_backend/verify_all_endpoints.py", "e2e/roles.e2e.mjs"):
        assert not pat.search((root / rel).read_text(encoding="utf-8")), rel


async def _lifespan_calls(monkeypatch, uri, mode):
    from app import main

    created = []

    class Conn:
        async def run_sync(self, fn):
            created.append(fn)

    class Begin:
        async def __aenter__(self):
            return Conn()

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(main, "engine", MagicMock(begin=lambda: Begin()))
    monkeypatch.setattr(main, "settings", MagicMock(AUTO_CREATE_TABLES=mode, sqlalchemy_database_uri=uri))
    async with main.lifespan(main.app):
        pass
    return created


@pytest.mark.parametrize("uri,mode,creates", [
    ("sqlite+aiosqlite:///./x.db", "auto", True),
    ("postgresql+asyncpg://u:p@h/db", "auto", False),   # the safety default: starting the app never writes to a remote DB
    ("postgresql+asyncpg://u:p@h/db", "false", False),
    ("postgresql+asyncpg://u:p@h/db", "true", True),    # explicit opt-in
    ("sqlite+aiosqlite:///./x.db", "false", False),
])
async def test_startup_creates_tables_only_for_sqlite_or_on_explicit_opt_in(monkeypatch, caplog, uri, mode, creates):
    with caplog.at_level(logging.WARNING, logger="careeros"):
        calls = await _lifespan_calls(monkeypatch, uri, mode)
    assert bool(calls) is creates
    if not creates:
        assert any("Not creating tables at startup" in r.getMessage() for r in caplog.records)
        assert "postgresql" not in caplog.text


def test_remote_schema_script_refuses_without_explicit_confirmation(monkeypatch, capsys):
    import importlib.util
    import pathlib

    monkeypatch.delenv("CONFIRM_REMOTE_SCHEMA", raising=False)
    spec = importlib.util.spec_from_file_location("prov_check", pathlib.Path(__file__).parents[2] / "scripts" / "create_supabase_schema.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    boom = MagicMock(side_effect=AssertionError("must not even build an engine"))
    monkeypatch.setattr(mod, "create_async_engine", boom)
    assert asyncio.run(mod.provision_schema()) is False
    boom.assert_not_called()
    assert "CONFIRM_REMOTE_SCHEMA=yes" in capsys.readouterr().out
    assert os.environ.get("CONFIRM_REMOTE_SCHEMA") is None
