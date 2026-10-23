"""Fixes from the full-project audit: password policy, failed-login throttling, upload validation and the
fabricated-skills leak. Uses the isolated in-memory SQLite fixtures; no remote database, no network."""

import io
import uuid
import zipfile
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.login_throttle import LoginThrottle, login_throttle
from app.core.security import get_password_hash
from app.modules.auth.models import User, UserStatus
from app.modules.jobs.skills import load_student_skills
from app.modules.resumes.models import Resume, ResumeMetadata
from app.modules.resumes.service import ResumeService
from app.modules.resumes.upload_validation import (
    DOCX_MIME,
    MAX_RESUME_BYTES,
    safe_filename,
    validate_resume_upload,
)
from app.modules.training.service import TrainingService
from app.modules.users.models import Profile, ProfileSkill, Skill

A = "/api/v1/auth"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture(autouse=True)
def _clean_throttle():
    login_throttle.reset()
    yield
    login_throttle.reset()


def _docx(with_document=True) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml" if with_document else "other.xml", "<w:document/>")
    return buf.getvalue()


# ── password policy ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("pw", ["", "a", "1234567", "x" * 129])
async def test_registration_rejects_weak_or_oversized_passwords(client, pw):
    r = await client.post(f"{A}/register", json={"email": f"{uuid.uuid4().hex[:8]}@test.com", "password": pw})
    assert r.status_code == 422, pw


async def test_registration_accepts_a_reasonable_password_and_can_log_in(client):
    email = f"{uuid.uuid4().hex[:8]}@test.com"
    assert (await client.post(f"{A}/register", json={"email": email, "password": "12345678"})).status_code == 201
    assert (await client.post(f"{A}/login", json={"email": email, "password": "12345678"})).status_code == 200


async def test_existing_accounts_with_short_passwords_can_still_sign_in(client):
    async with client.sessionmaker() as s:
        s.add(User(email="legacy@test.com", hashed_password=get_password_hash("abc"), status=UserStatus.ACTIVE))
        await s.commit()
    assert (await client.post(f"{A}/login", json={"email": "legacy@test.com", "password": "abc"})).status_code == 200


# ── failed-login throttling ──────────────────────────────────────────────────
async def _register(client, pw="Correct-Pass-1"):
    email = f"{uuid.uuid4().hex[:8]}@test.com"
    assert (await client.post(f"{A}/register", json={"email": email, "password": pw})).status_code == 201
    return email


async def test_account_is_throttled_after_five_failures_even_for_the_right_password(client):
    email = await _register(client)
    for _ in range(5):
        assert (await client.post(f"{A}/login", json={"email": email, "password": "wrong-pass"})).status_code == 401
    blocked = await client.post(f"{A}/login", json={"email": email, "password": "wrong-pass"})
    assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0
    # The correct password is refused too, so a guesser can't tell when they hit the right one.
    assert (await client.post(f"{A}/login", json={"email": email, "password": "Correct-Pass-1"})).status_code == 429
    other = await _register(client)
    assert (await client.post(f"{A}/login", json={"email": other, "password": "Correct-Pass-1"})).status_code == 200


async def test_success_resets_the_counter_and_inactive_accounts_are_not_counted(client):
    email = await _register(client)
    for _ in range(4):
        await client.post(f"{A}/login", json={"email": email, "password": "wrong-pass"})
    assert (await client.post(f"{A}/login", json={"email": email, "password": "Correct-Pass-1"})).status_code == 200
    for _ in range(4):
        assert (await client.post(f"{A}/login", json={"email": email, "password": "wrong-pass"})).status_code == 401
    async with client.sessionmaker() as s:
        u = (await s.execute(select(User).where(User.email == email))).scalar_one()
        u.status = UserStatus.SUSPENDED
        await s.commit()
    login_throttle.reset()
    for _ in range(8):  # correct password on a suspended account -> 400 each time, never counted as a guess
        assert (await client.post(f"{A}/login", json={"email": email, "password": "Correct-Pass-1"})).status_code == 400


async def test_unknown_emails_are_throttled_too(client):
    for _ in range(5):
        assert (await client.post(f"{A}/login", json={"email": "ghost@test.com", "password": "whatever1"})).status_code == 401
    assert (await client.post(f"{A}/login", json={"email": "GHOST@test.com", "password": "whatever1"})).status_code == 429  # case-insensitive


def test_throttle_window_expiry_ip_limit_and_retry_after():
    now = [1000.0]
    t = LoginThrottle(max_per_account=3, max_per_ip=5, window_seconds=60, clock=lambda: now[0])
    for _ in range(3):
        t.record_failure("a@x.com", "1.1.1.1")
    with pytest.raises(HTTPException) as exc:
        t.check("a@x.com", "1.1.1.1")
    assert exc.value.status_code == 429 and exc.value.headers["Retry-After"] == "60"
    t.check("a@x.com", "2.2.2.2")  # same account from another address is not blocked by the (email, ip) counter
    now[0] += 30
    with pytest.raises(HTTPException) as exc:
        t.check("a@x.com", "1.1.1.1")
    assert exc.value.headers["Retry-After"] == "30"
    now[0] += 31  # oldest failures aged out
    t.check("a@x.com", "1.1.1.1")
    for i in range(5):  # per-IP limit across many accounts (credential stuffing)
        t.record_failure(f"user{i}@x.com", "9.9.9.9")
    with pytest.raises(HTTPException):
        t.check("brand-new@x.com", "9.9.9.9")


def test_throttle_memory_is_bounded():
    t = LoginThrottle(max_per_account=5, max_per_ip=5, window_seconds=60, max_keys=50)
    for i in range(500):
        t.record_failure(f"u{i}@x.com", f"10.0.{i % 250}.{i % 200}")
    assert len(t._accounts) <= 50 and len(t._ips) <= 50


# ── upload validation ────────────────────────────────────────────────────────
def test_safe_filename():
    assert safe_filename("../../../etc/passwd.pdf", ".pdf") == "passwd.pdf"
    assert safe_filename("C:\\Users\\me\\My CV (final).pdf", ".pdf") == "My CV (final).pdf"
    assert safe_filename("cv.exe", ".pdf") == "cv.pdf"  # extension always matches the verified type
    assert safe_filename("<script>alert(1)</script>.pdf", ".pdf") == "script.pdf"  # "/" starts a path component
    assert safe_filename("a<b>c|d?.pdf", ".pdf") == "abcd.pdf"
    assert safe_filename("....", ".docx") == "resume.docx" and safe_filename(None, ".pdf") == "resume.pdf"
    assert len(safe_filename("a" * 500 + ".pdf", ".pdf")) <= 84
    assert "\x00" not in safe_filename("cv\x00.pdf", ".pdf")


@pytest.fixture
def no_pipeline():
    # The real background pipeline opens its own DB session; never let tests reach any configured database.
    with patch.object(ResumeService, "_async_pipeline_isolated", new=AsyncMock()) as m:
        yield m


async def _upload(client, name, data, mime="application/pdf"):
    return await client.post("/api/v1/resumes/upload", files={"file": (name, io.BytesIO(data), mime)})


async def test_valid_pdf_and_docx_are_accepted_with_sanitised_names(client, no_pipeline):
    r = await _upload(client, "../../../My CV!.pdf", PDF)
    assert r.status_code == 202 and r.json()["data"]["file_name"] == "My CV.pdf"
    d = await _upload(client, "cv.docx", _docx(), DOCX_MIME)
    assert d.status_code == 202
    async with client.sessionmaker() as s:
        keys = [x.s3_key for x in (await s.execute(select(Resume))).scalars()]
    assert all(".." not in k and "\\" not in k for k in keys)
    assert no_pipeline.await_count == 2
    sent = no_pipeline.await_args_list[0].args  # (user_id, resume_id, content, s3_key, file_name)
    assert sent[2] == PDF  # the validated bytes are what get processed


INVALID_UPLOADS = [
    pytest.param("cv.pdf", lambda: b"MZ\x90\x00 not a pdf", "application/pdf", 400, id="pdf-type-but-not-pdf-bytes"),
    pytest.param("cv.docx", lambda: _docx(with_document=False), DOCX_MIME, 400, id="zip-without-word-document"),
    pytest.param("cv.docx", lambda: b"%PDF-1.4 hello", DOCX_MIME, 400, id="pdf-bytes-declared-as-docx"),
    pytest.param("cv.pdf", lambda: b"", "application/pdf", 400, id="empty"),
    pytest.param("cv.txt", lambda: b"hello", "text/plain", 400, id="wrong-type"),
    pytest.param("big.pdf", lambda: b"%PDF-1.4\n" + b"0" * MAX_RESUME_BYTES, "application/pdf", 413, id="over-5mb"),
]


@pytest.mark.parametrize("name,make,mime,code", INVALID_UPLOADS)
async def test_invalid_uploads_are_rejected_and_nothing_is_stored(client, no_pipeline, name, make, mime, code):
    r = await _upload(client, name, make(), mime)
    assert r.status_code == code
    async with client.sessionmaker() as s:
        assert (await s.execute(select(Resume))).scalars().all() == []
    no_pipeline.assert_not_awaited()


def test_exact_size_limit_is_accepted_and_one_byte_over_is_not():
    ok = b"%PDF-1.4\n" + b"0" * (MAX_RESUME_BYTES - 9)
    assert validate_resume_upload("application/pdf", "a.pdf", ok) == "a.pdf"
    with pytest.raises(HTTPException) as exc:
        validate_resume_upload("application/pdf", "a.pdf", ok + b"0")
    assert exc.value.status_code == 413


# ── fabricated-skills leak ───────────────────────────────────────────────────
async def test_canned_resume_skills_never_reach_matching_or_the_project_interview(client, me):
    async with client.sessionmaker() as s:
        prof = Profile(user_id=me.id, first_name="A")
        s.add(prof)
        skill = Skill(name="Excel")
        s.add(skill)
        await s.flush()
        s.add(ProfileSkill(profile_id=prof.id, skill_id=skill.id))
        r = Resume(user_id=me.id, file_name="cv.pdf", s3_key=f"k-{uuid.uuid4()}")
        s.add(r)
        await s.flush()
        # exactly what the stubbed pipeline stores for EVERY upload
        s.add(ResumeMetadata(resume_id=r.id, extracted_skills={"skills": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy"]}))
        await s.commit()
    async with client.sessionmaker() as s:
        assert await load_student_skills(s, me.id) == ["Excel"]
        data = await TrainingService(s).resolve_resume_data(me.id)
    assert data["skills"] == ["Excel"] and data["source"] == "profile"
