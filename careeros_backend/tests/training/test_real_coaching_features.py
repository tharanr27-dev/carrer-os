"""Interview studio, communication coach, mentor, roadmap and career discovery compute from real inputs.

Isolated in-memory SQLite only; no network and no AI provider."""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.modules.career_discovery.ai_engine import CareerDiscoveryAIEngine
from app.modules.communication.evaluation_engine import CommunicationEvaluationEngine, _scores
from app.modules.communication.models import CommunicationMessage, CommunicationReport, CommunicationSession
from app.modules.communication.service import CommunicationService
from app.modules.interviews.evaluation_engine import InterviewEvaluationEngine
from app.modules.interviews.models import InterviewAnswer, InterviewQuestion, InterviewSession
from app.modules.learning.roadmap_engine import LearningRoadmapEngine
from app.modules.training.models import TrainingProfile
from app.modules.training.seed import ensure_seed

from training_fakes import FakeLLM

STRONG_OOP = (
    "Encapsulation hides internal data behind methods, like a bank account balance changed only through deposit and withdraw. "
    "Abstraction exposes what an object does and hides how. Inheritance lets a subclass reuse and extend a parent, "
    "and polymorphism lets the same call behave differently by object type, for example calculating interest."
)
WEAK = "I do not know much about it."


@pytest.fixture
async def db(sessionmaker_):
    async with sessionmaker_() as s:
        await ensure_seed(s)
        yield s


# ── interview studio ─────────────────────────────────────────────────────────
async def test_hr_interview_opens_with_the_classic_question_and_never_repeats(db):
    e, uid, asked = InterviewEvaluationEngine(db), uuid.uuid4(), []
    first, skills = await e.next_question(uid, "HR", "MEDIUM", asked)
    assert first == "Tell me about yourself." and skills
    asked.append(first)
    for _ in range(8):
        q, _ = await e.next_question(uid, "HR", "MEDIUM", asked)  # no last_answer -> no follow-up
        assert q not in asked
        asked.append(q)


async def test_followup_comes_from_the_bank_only_after_a_substantive_answer(db):
    e, uid = InterviewEvaluationEngine(db), uuid.uuid4()
    q = "Tell me about yourself."
    short, _ = await e.next_question(uid, "HR", "MEDIUM", [q], last_answer="Student.")
    assert short != "Which of those projects are you most proud of?"
    fu, _ = await e.next_question(uid, "HR", "MEDIUM", [q], last_answer="I am a final year student interested in backend development and I built two projects.")
    assert fu == "Which of those projects are you most proud of?"
    again, _ = await e.next_question(uid, "HR", "MEDIUM", [q, fu], last_answer="I built a student attendance system with a team of three people.")
    assert again not in (q, fu)  # a follow-up is asked once, then the interview moves on


async def test_followup_uses_the_llm_only_when_one_is_configured(db):
    e, uid = InterviewEvaluationEngine(db), uuid.uuid4()
    fake = FakeLLM([{"follow_up": "What trade-off did you accept in that attendance design?"}])
    with patch("app.modules.interviews.evaluation_engine.get_llm", return_value=fake):
        q, _ = await e.next_question(uid, "HR", "MEDIUM", ["Tell me about yourself."], last_answer="I built an attendance system with FastAPI and PostgreSQL for my college.")
    assert q == "What trade-off did you accept in that attendance design?"
    broken = FakeLLM([{"unexpected": 1}])
    with patch("app.modules.interviews.evaluation_engine.get_llm", return_value=broken):
        q2, _ = await e.next_question(uid, "HR", "MEDIUM", ["Tell me about yourself."], last_answer="I built an attendance system with FastAPI and PostgreSQL for my college.")
    assert q2 == "Which of those projects are you most proud of?"  # invalid AI output -> reviewed follow-up


async def test_technical_questions_follow_the_target_role(db):
    uid = uuid.uuid4()
    db.add(TrainingProfile(user_id=uid, target_role="Data Analyst", level="fresher", language="en"))
    await db.commit()
    e = InterviewEvaluationEngine(db)
    from app.modules.training.service import ROLE_TOPICS

    seen = set()
    for _ in range(6):
        q, _ = await e.next_question(uid, "TECHNICAL", "MEDIUM", list(seen))
        seen.add(q)
        row = await e._lookup(q)
        assert row is not None and row.topic in ROLE_TOPICS["Data Analyst"]


async def test_answers_are_scored_by_their_content_not_a_constant(db):
    e = InterviewEvaluationEngine(db)
    q = "Explain the four pillars of OOP with a real-world example."
    strong, weak = await e.evaluate_answer(q, STRONG_OOP), await e.evaluate_answer(q, WEAK)
    assert strong.overall_score > 6 > weak.overall_score
    assert (strong.overall_score, weak.overall_score) != (8.5, 8.5)  # the old stub returned 8.5 for everything
    hedgy = await e.evaluate_answer(q, "Maybe I think basically it is just kind of about classes and objects, um, I guess.")
    assert hedgy.confidence_score < strong.confidence_score and any("Hedging" in i or "Filler" in i for i in hedgy.improvements)
    fu = await e.evaluate_answer("Which of those projects are you most proud of?", "My attendance system because it has real users.")
    assert fu.overall_score == 0.0 and "not scored" in fu.improvements[0]


async def _make_interview(db, answers):
    uid = uuid.uuid4()
    s = InterviewSession(user_id=uid, interview_type="TECHNICAL", difficulty="MEDIUM")
    db.add(s)
    await db.flush()
    for q, a in answers:
        row = InterviewQuestion(session_id=s.id, question_text=q)
        db.add(row)
        await db.flush()
        if a is not None:
            db.add(InterviewAnswer(question_id=row.id, answer_text=a))
    await db.commit()
    return s.id


async def test_report_is_computed_from_the_answers_actually_given(db):
    e = InterviewEvaluationEngine(db)
    oop = "Explain the four pillars of OOP with a real-world example."
    good = await e.generate_final_report(await _make_interview(db, [(oop, STRONG_OOP)]))
    poor = await e.generate_final_report(await _make_interview(db, [(oop, WEAK)]))
    assert good.overall_score > poor.overall_score and good.technical_score > poor.technical_score
    assert (good.overall_score, good.technical_score, good.communication_score) != (85.0, 90.0, 80.0)  # the old canned report
    assert good.detailed_analysis["method"] == "rule_based_v1" and "not an AI" in good.detailed_analysis["disclaimer"]
    assert good.detailed_analysis["scored_answers"] == 1 and good.detailed_analysis["per_answer"][0]["model_answer"]
    assert any("OOP" in r for r in poor.recommended_learning) and "No weak topic" in good.recommended_learning[0]


async def test_report_with_no_answers_is_zero_and_says_so_and_followups_are_not_scored(db):
    e = InterviewEvaluationEngine(db)
    empty = await e.generate_final_report(await _make_interview(db, [("Explain closures in JavaScript with an example.", None)]))
    assert empty.overall_score == 0.0 and "No answers were submitted" in empty.recommended_learning[0]
    mixed = await e.generate_final_report(await _make_interview(db, [
        ("Explain the four pillars of OOP with a real-world example.", STRONG_OOP),
        ("When would you prefer composition?", "When I want flexible reuse without deep hierarchies."),
    ]))
    assert mixed.detailed_analysis["questions_answered"] == 2 and mixed.detailed_analysis["scored_answers"] == 1
    assert mixed.overall_score > 60


# ── communication coach ──────────────────────────────────────────────────────
GOOD_MSG = ("I would like to explain how our team designed the attendance service. We separated the API from the "
            "database layer, which made testing simpler. Thank you for reviewing the proposal.")
BAD_MSG = "so basically i think we gonna do stuff, um, like the thing is awesome awesome!!! maybe it is just kinda working and stuff"


async def test_communication_scores_measure_the_text_and_flag_specifics():
    g, b = _scores(GOOD_MSG), _scores(BAD_MSG)
    assert g["tone"] > 8 > b["tone"] and g["grammar"] > b["grammar"] and g["fluency"] > b["fluency"]
    a = await CommunicationEvaluationEngine().analyze_message(BAD_MSG)
    flagged = {(f.category, f.original_text) for f in a.feedbacks}
    assert {("Tone", "gonna"), ("Tone", "stuff"), ("Filler word", "um"), ("Filler word", "basically")} <= flagged
    assert (await CommunicationEvaluationEngine().analyze_message(GOOD_MSG)).feedbacks == []
    assert any(f.category == "Note" for f in (await CommunicationEvaluationEngine().analyze_message("ok thanks")).feedbacks)


async def test_communication_report_uses_only_substantial_messages_and_is_honest_when_empty():
    e = CommunicationEvaluationEngine()
    none = await e.generate_final_report([])
    assert none.overall_score == 0.0 and "No messages were submitted" in none.weaknesses[0]
    short = await e.generate_final_report([{"text": "hi"}])
    assert "15+ words" in short.weaknesses[0]
    r = await e.generate_final_report([{"text": GOOD_MSG}, {"text": BAD_MSG}, {"text": "ok"}])
    assert 0 < r.overall_score < 10 and r.weaknesses and any("filler" in s.lower() for s in r.improvement_suggestions)
    assert "not an AI" in r.improvement_suggestions[-1] and "accent" in r.improvement_suggestions[-1]
    assert r.overall_score != 7.8  # the old canned value


async def test_communication_service_builds_the_report_from_the_session_messages(sessionmaker_):
    async with sessionmaker_() as s:
        cs = CommunicationSession(user_id=uuid.uuid4(), mode="WORKPLACE")
        s.add(cs)
        await s.flush()
        s.add_all([CommunicationMessage(session_id=cs.id, speaker="USER", content_text=GOOD_MSG),
                   CommunicationMessage(session_id=cs.id, speaker="AI", content_text="Please continue.")])
        await s.commit()
        sid = cs.id
        svc = CommunicationService(s)
    with patch("app.db.session.AsyncSessionLocal", sessionmaker_):
        await svc._async_generate_report(sid)
    async with sessionmaker_() as s:
        rep = (await s.execute(select(CommunicationReport).where(CommunicationReport.session_id == sid))).scalars().one()
    assert rep.tone_score == _scores(GOOD_MSG)["tone"] and rep.overall_score > 6  # the AI turn was not scored


# ── mentor ───────────────────────────────────────────────────────────────────
M = "/api/v1/mentor"


async def _mentor_session(client):
    return (await client.post(f"{M}/sessions")).json()["data"]["id"]


async def test_mentor_without_an_ai_provider_gives_a_setup_message_and_real_suggestions(client):
    """No fake chat: the send fails honestly (see test_mentor_ai.py); next steps come from a separate endpoint."""
    sid = await _mentor_session(client)
    r = await client.post(f"{M}/sessions/{sid}/message", json={"content": "How do I get a job?"})
    assert r.status_code == 503 and "GROQ_API_KEY" in r.text
    assert "Handshake" not in r.text and "Enterprise Admin" not in r.text  # the old echo-gateway reply
    titles = [i["title"] for i in (await client.get(f"{M}/suggestions")).json()["data"]]
    assert any("résumé" in t or "profile" in t for t in titles)  # derived from this student's (empty) data


async def test_mentor_with_a_provider_uses_it(client):
    sid = await _mentor_session(client)
    with patch("app.modules.training.llm.get_llm", return_value=FakeLLM(["Start with one project and write its README."])) as g:
        r = (await client.post(f"{M}/sessions/{sid}/message", json={"content": "What should I build?"})).json()["data"]
    assert r["content"] == "Start with one project and write its README."
    llm = g.return_value
    assert llm.calls[0]["messages"][-1] == {"role": "user", "content": "What should I build?"}
    assert "Never invent" in llm.calls[0]["system"]


@pytest.mark.parametrize("content", ["", "x" * 4001])
async def test_mentor_rejects_empty_and_oversized_messages(client, content):
    sid = await _mentor_session(client)
    assert (await client.post(f"{M}/sessions/{sid}/message", json={"content": content})).status_code == 422


# ── learning roadmap ─────────────────────────────────────────────────────────
async def test_roadmap_is_built_from_role_topics_and_real_results_with_no_invented_content():
    r = await LearningRoadmapEngine().generate_roadmap({"target_role": "Python Developer", "training": {"total_scored_answers": 0}})
    titles = [m.title for m in r.modules]
    assert titles[0] == "Python" and "Mock interview checkpoint" in titles and r.title == "Road to Python Developer"
    blob = " ".join(m.title + m.description + " ".join(t.title + t.description + (t.resource_url or "") for t in m.tasks) for m in r.modules)
    for invented in ("asyncio", "Kubernetes", "Designing Data-Intensive", "docs.python.org", "token-bucket"):
        assert invented not in blob
    assert all((t.resource_url or "/").startswith("/") for m in r.modules for t in m.tasks)  # internal practice pages only
    assert "Rule-based, not AI" in r.description and "no practice results saved yet" in r.description


async def test_weak_topics_and_resume_findings_are_prioritised_when_they_exist():
    ctx = {"target_role": "Backend Engineer", "resume_weaknesses": ["Redis", "Docker"],
           "resume_suggestions": [{"category": "Measurable results", "text": "Add numbers.", "impact": "HIGH"}],
           "training": {"total_scored_answers": 9, "weakest_topics": [{"round": "technical", "topic": "sql", "label": "SQL", "attempted": 5, "score_pct": 30.0}],
                        "strongest_topics": []}}
    r = await LearningRoadmapEngine().generate_roadmap(ctx)
    assert r.modules[0].title == "SQL" and "30.0%" in r.modules[0].description and r.modules[0].tasks[0].difficulty == "EASY"
    cv = next(m for m in r.modules if m.title == "Résumé readiness")
    assert "Add numbers." in [t.description for t in cv.tasks] and any("Redis" in t.description for t in cv.tasks)
    assert "your saved practice results" in r.description


# ── career discovery ─────────────────────────────────────────────────────────
async def test_career_report_reflects_each_students_own_answers():
    e = CareerDiscoveryAIEngine()
    data = await e.generate_career_report([{"text": "Python, Pandas and SQL"}, {"text": "Analysing data"}, {"text": "I built a Power BI dashboard to analyse sales data"}])
    web = await e.generate_career_report([{"text": "React, TypeScript and CSS"}, {"text": "Designing experiences"}, {"text": "I designed the user interface in Figma"}])
    assert data.recommended_matches[0].job_title == "Data Analyst" and web.recommended_matches[0].job_title == "Frontend Developer"
    assert data.interest_analysis["fields"] != web.interest_analysis["fields"]
    assert "Analytical" not in str(data.personality_analysis) and "Introverted" not in str(web.personality_analysis)  # old canned traits
    assert "not a personality test" in data.personality_analysis["note"]
    assert round(sum(m.suitability_score for m in data.recommended_matches)) == 100


async def test_career_report_with_no_usable_answers_makes_no_claims():
    r = await CareerDiscoveryAIEngine().generate_career_report([{"text": "idk"}, {"text": ""}])
    assert r.recommended_matches == [] and r.interest_analysis["fields"] == [] and r.skill_gaps["missing"] == []
    assert "cannot be predicted" in r.career_timeline["note"]


async def test_multiple_choice_picks_reach_the_career_analysis_through_the_api(client):
    from app.modules.career_discovery.models import AssessmentQuestion, AssessmentTemplate

    async with client.sessionmaker() as s:
        t = AssessmentTemplate(title="Test assessment")
        s.add(t)
        await s.flush()
        mc = AssessmentQuestion(template_id=t.id, question_text="Which kind of work energises you most?", question_type="MULTIPLE_CHOICE",
                                options=["Building products", "Analysing data", "Designing experiences", "Leading teams"], order_index=1)
        tx = AssessmentQuestion(template_id=t.id, question_text="Which tools do you enjoy?", question_type="TEXT", order_index=2)
        s.add_all([mc, tx])
        await s.commit()
        ids = (t.id, mc.id, tx.id)
    with patch("app.modules.career_discovery.service.AsyncSessionLocal", client.sessionmaker):
        r = await client.post(f"/api/v1/discovery/assessments/{ids[0]}/submit", json={"answers": [
            {"question_id": str(ids[1]), "selected_options": ["Analysing data"]},
            {"question_id": str(ids[2]), "answer_text": "Python and SQL"},
        ]})
    assert r.status_code == 200
    rep = (await client.get(f"/api/v1/discovery/reports/{r.json()['data']['assessment_id']}")).json()["data"]
    assert rep["matches"][0]["job_title"] == "Data Analyst"
    assert "Analysing data" in rep["personality_analysis"]["stated_preferences"]  # the multiple-choice pick was used
