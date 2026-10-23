"""Résumé extraction/analysis/storage and the recommendations engine now run on REAL data (no canned output).

Everything uses the isolated in-memory SQLite database and a temp upload directory; nothing touches a remote DB."""

import io
import uuid
import zipfile
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.modules.recommendations.context_aggregator import ContextAggregator
from app.modules.recommendations.recommendation_engine import RecommendationEngine
from app.modules.resumes.analysis import analyze_text
from app.modules.resumes.models import Resume, ResumeAnalysis, ResumeMetadata
from app.modules.resumes.text_extraction import DOCX, PDF, extract_text
from app.modules.training.models import TrainingAttempt, TrainingAttemptItem, TrainingProfile, TrainingQuestion
from app.modules.jobs.skills import load_student_skills
from app.modules.users.models import Profile

from training_fakes import GOOD_RESUME, make_docx, make_pdf

R = "/api/v1/resumes"
POOR = ["john", "i worked on stuff and was responsible for things at a small shop for some time", "i like computers and i am a hard worker who is good with people", "i can learn quickly and i am good at many things"]


# ── extraction ───────────────────────────────────────────────────────────────
def test_pdf_and_docx_text_are_really_extracted():
    for ct, data in ((PDF, make_pdf(GOOD_RESUME)), (DOCX, make_docx(GOOD_RESUME))):
        r = extract_text(ct, data)
        assert r.ok and "priya.raman@example.com" in r.text and "FastAPI" in r.text


def test_image_only_corrupt_encrypted_and_oversized_inputs_are_handled_honestly():
    empty = extract_text(PDF, make_pdf([]))
    assert not empty.ok and any("scanned" in w for w in empty.warnings)
    bad = extract_text(PDF, b"%PDF-1.4 this is not really a pdf")
    assert not bad.ok and bad.warnings
    assert not extract_text(DOCX, b"PK\x03\x04garbage").ok
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:t>x</w:t>" * 10)
    assert not extract_text(DOCX, buf.getvalue()).ok
    assert extract_text("text/plain", b"hi").warnings == ["Unsupported file type."]


def test_docx_xml_entities_are_not_expanded():
    xml = '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "AAAAAAAAAA">]><w:document xmlns:w="x"><w:body><w:p><w:r><w:t>&a;&a;</w:t></w:r></w:p></w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    out = extract_text(DOCX, buf.getvalue()).text
    assert "AAAA" not in out  # a regex over the XML never expands entities


# ── analysis is computed from the file, not canned ───────────────────────────
def test_analysis_differs_by_content_and_is_labelled_rule_based():
    good = analyze_text("\n".join(GOOD_RESUME), "Backend Developer")
    poor = analyze_text("\n".join(POOR), "Backend Developer")
    assert good.ats_score > 70 > poor.ats_score
    assert good.quality_score > poor.quality_score
    assert "FastAPI" in good.extracted_skills and "FastAPI" not in poor.extracted_skills
    kw = good.keyword_analysis
    assert kw["method"] == "rule_based_v1" and "not an AI" in kw["disclaimer"]
    assert {"education", "skills", "projects"} <= set(kw["sections_found"])
    assert kw["contact"] == {"email": True, "phone": True, "profile_link": True}
    assert kw["quantified_lines"] >= 3
    # the old stub returned identical numbers for every file
    assert (good.ats_score, good.quality_score) != (85.0, 80.0)
    cats = {s.category for s in poor.suggestions}
    assert {"Contact details", "Structure"} <= cats
    assert any("responsible for" in s.suggestion_text for s in good.suggestions)  # weak phrase present in GOOD_RESUME


def test_missing_keywords_depend_on_the_target_role_and_never_invent_skills():
    text = "\n".join(GOOD_RESUME)
    be = analyze_text(text, "Backend Developer").keyword_analysis
    assert "Redis" in be["missing"] and "Python" not in be["missing"] and be["target_role"] == "Backend Developer"
    none = analyze_text(text, None).keyword_analysis
    assert none["missing"] == [] and none["target_role"] is None  # no role -> no role-specific claims
    assert analyze_text(text, "Chef").keyword_analysis["missing"] == []


def test_empty_resume_scores_zero_with_an_explanation():
    a = analyze_text("", None, ["Almost no text could be extracted."])
    assert a.ats_score == a.quality_score == a.grammar_score == 0.0
    assert a.suggestions[0].impact == "HIGH" and a.keyword_analysis["warnings"] == ["Almost no text could be extracted."]


# ── full pipeline through the API ────────────────────────────────────────────
@pytest.fixture
def pipeline(client, tmp_path, monkeypatch):
    """Run the real background pipeline against the isolated DB and a temp upload dir."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    with patch("app.modules.resumes.service.AsyncSessionLocal", client.sessionmaker):
        yield tmp_path / "uploads"


async def _upload(client, name, data, mime):
    return await client.post(f"{R}/upload", files={"file": (name, io.BytesIO(data), mime)})


async def test_uploaded_pdf_is_stored_analysed_persisted_and_downloadable(client, pipeline, me):
    async with client.sessionmaker() as s:
        s.add(TrainingProfile(user_id=me.id, target_role="Backend Developer", level="fresher", language="en"))
        await s.commit()
    pdf = make_pdf(GOOD_RESUME)
    up = await _upload(client, "../../My CV.pdf", pdf, "application/pdf")
    assert up.status_code == 202
    rid = up.json()["data"]["id"]

    listing = (await client.get(R)).json()["data"]
    assert next(r for r in listing if r["id"] == rid)["status"] == "COMPLETED"
    an = (await client.get(f"{R}/{rid}/analysis")).json()["data"]
    assert an["keyword_analysis"]["method"] == "rule_based_v1" and an["keyword_analysis"]["target_role"] == "Backend Developer"
    assert an["ats_score"] > 70 and "FastAPI" in an["keyword_analysis"]["found"] and an["suggestions"]

    async with client.sessionmaker() as s:
        meta = (await s.execute(select(ResumeMetadata))).scalars().one()
        assert meta.extracted_skills["method"] == "text_match_v1" and "FastAPI" in meta.extracted_skills["skills"]
        assert "raw_text" not in meta.parsed_content and meta.parsed_content["text_extracted"] is True  # no résumé text stored in the DB
        stored = (await s.execute(select(Resume))).scalars().one()
    assert (pipeline / stored.s3_key).read_bytes() == pdf  # the original really is on disk

    dl = await client.get(f"{R}/{rid}/download")
    assert dl.status_code == 200 and dl.content == pdf and dl.headers["content-type"] == "application/pdf"
    assert 'filename="My CV.pdf"' in dl.headers["content-disposition"] and dl.headers["x-content-type-options"] == "nosniff"


async def test_other_students_cannot_download_and_missing_files_are_a_clear_404(client, pipeline, me):
    rid = (await _upload(client, "cv.pdf", make_pdf(GOOD_RESUME), "application/pdf")).json()["data"]["id"]
    owner = me.id
    me.id = uuid.uuid4()
    assert (await client.get(f"{R}/{rid}/download")).status_code == 403
    me.id = owner
    (pipeline / (await _first_resume(client)).s3_key).unlink()
    gone = await client.get(f"{R}/{rid}/download")
    assert gone.status_code == 404 and "not available" in gone.json()["detail"]


async def _first_resume(client):
    async with client.sessionmaker() as s:
        return (await s.execute(select(Resume))).scalars().first()


async def test_path_traversal_in_a_stored_key_is_never_served(client, pipeline, me, tmp_path):
    (tmp_path / "secret.txt").write_text("top secret")
    async with client.sessionmaker() as s:
        r = Resume(user_id=me.id, file_name="x.pdf", s3_key="../secret.txt", content_type="application/pdf", status="COMPLETED")
        s.add(r)
        await s.commit()
        rid = r.id
    resp = await client.get(f"{R}/{rid}/download")
    assert resp.status_code == 404 and b"top secret" not in resp.content


async def test_scanned_pdf_is_flagged_not_scored_as_good(client, pipeline):
    rid = (await _upload(client, "scan.pdf", make_pdf([]), "application/pdf")).json()["data"]["id"]
    an = (await client.get(f"{R}/{rid}/analysis")).json()["data"]
    assert an["ats_score"] == 0.0 and any("scanned" in w for w in an["keyword_analysis"]["warnings"])


# ── skills from the résumé are used only when they came from real extraction ──
async def test_real_extraction_skills_are_used_but_legacy_canned_ones_are_not(client, me):
    async with client.sessionmaker() as s:
        s.add(Profile(user_id=me.id, first_name="A"))
        old = Resume(user_id=me.id, file_name="old.pdf", s3_key=f"k-{uuid.uuid4()}", status="COMPLETED")
        s.add(old)
        await s.flush()
        s.add(ResumeMetadata(resume_id=old.id, extracted_skills={"skills": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy"]}))  # legacy stub format
        await s.commit()
    async with client.sessionmaker() as s:
        assert await load_student_skills(s, me.id) == []
    async with client.sessionmaker() as s:
        new = Resume(user_id=me.id, file_name="new.pdf", s3_key=f"k-{uuid.uuid4()}", status="COMPLETED")
        s.add(new)
        await s.flush()
        s.add(ResumeMetadata(resume_id=new.id, extracted_skills={"skills": ["Rust", "Docker"], "method": "text_match_v1"}))
        await s.commit()
    async with client.sessionmaker() as s:
        assert set(await load_student_skills(s, me.id)) == {"Rust", "Docker"}


# ── recommendations ──────────────────────────────────────────────────────────
async def test_context_never_uses_another_students_resume_analysis(client, me):
    other = uuid.uuid4()
    async with client.sessionmaker() as s:
        r = Resume(user_id=other, file_name="b.pdf", s3_key=f"k-{uuid.uuid4()}", status="COMPLETED")
        s.add(r)
        await s.flush()
        s.add(ResumeAnalysis(resume_id=r.id, ats_score=99.0, grammar_score=90, quality_score=90,
                             keyword_analysis={"method": "rule_based_v1", "missing": ["SecretOtherUserKeyword"]}))
        await s.commit()
    async with client.sessionmaker() as s:
        mine = await ContextAggregator(s).build_context(me.id)
        theirs = await ContextAggregator(s).build_context(other)
    assert mine["ats_score"] is None and mine["resume_weaknesses"] == []  # was: the newest analysis of ANY user
    assert theirs["ats_score"] == 99.0


async def test_new_student_gets_first_step_prompts_not_invented_insights():
    ctx = {"user_id": "u", "profile": {}, "career_goals": [], "resume_weaknesses": [], "ats_score": None,
           "interview_scores": {}, "communication_scores": {}, "skill_progress": [], "roadmap_status": None,
           "has_career_report": False, "target_role": None, "training": None, "resume_suggestions": []}
    recs = (await RecommendationEngine().generate_candidates(ctx)).recommendations
    titles = {r.title for r in recs}
    assert {"Complete your profile", "Upload your résumé for analysis", "Generate your learning roadmap", "Take the career discovery assessment"} <= titles
    text = " ".join(r.title + r.description + r.reason for r in recs)
    for invented in ("72/100", "Docker", "Kubernetes", "87%", "Vocabulary score", "FAANG", "System Design"):
        assert invented not in text


async def test_recommendations_are_driven_by_real_saved_data(client, me):
    async with client.sessionmaker() as s:
        s.add(Profile(user_id=me.id, first_name="A", completion_percentage=90))
        s.add(TrainingProfile(user_id=me.id, target_role="Backend Developer", level="fresher", language="en"))
        r = Resume(user_id=me.id, file_name="a.pdf", s3_key=f"k-{uuid.uuid4()}", status="COMPLETED")
        s.add(r)
        await s.flush()
        s.add(ResumeAnalysis(resume_id=r.id, ats_score=55.0, grammar_score=80, quality_score=50,
                             keyword_analysis={"method": "rule_based_v1", "missing": ["Redis", "Docker"]}))
        # three wrong SQL answers -> a weak topic
        q = TrainingQuestion(round="technical", topic="sql", difficulty="easy", qtype="mcq", prompt="q?", options=["a", "b", "c", "d"],
                             correct_index=0, source="curated", fingerprint=str(uuid.uuid4()))
        s.add(q)
        att = TrainingAttempt(user_id=me.id, mode="practice", round="technical", status="COMPLETED", started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
        s.add(att)
        await s.flush()
        for i in range(3):
            s.add(TrainingAttemptItem(attempt_id=att.id, question_id=q.id, user_id=me.id, position=i + 1, round="technical",
                                      topic="sql", difficulty="easy", score=0.0, score_kind="objective", is_correct=False))
        await s.commit()
    async with client.sessionmaker() as s:
        ctx = await ContextAggregator(s).build_context(me.id)
    assert ctx["ats_score"] == 55.0 and ctx["target_role"] == "Backend Developer"
    recs = (await RecommendationEngine().generate_candidates(ctx)).recommendations
    by_title = {r.title: r for r in recs}
    assert "Complete your profile" not in by_title  # 90% complete: not triggered
    assert "Improve your résumé's readiness" in by_title and "55/100" in by_title["Improve your résumé's readiness"].reason
    assert any(r.category == "SKILL" and "Redis" in r.description for r in recs)
    assert any(r.category == "PRACTICE" and "SQL" in r.title for r in recs)  # the weak topic found in real attempts


async def test_old_simulated_resume_analysis_is_flagged_not_trusted():
    ctx = {"profile": {"completion": 100}, "ats_score": 60.0, "resume_method": None, "resume_suggestions": [{"text": "x", "category": "c", "impact": "HIGH"}],
           "resume_weaknesses": [], "roadmap_status": {"title": "t"}, "has_career_report": True, "training": None}
    recs = (await RecommendationEngine().generate_candidates(ctx)).recommendations
    r = next(r for r in recs if r.title.startswith("Improve your résumé"))
    assert "simulated" in r.reason and r.confidence_score < 0.5
