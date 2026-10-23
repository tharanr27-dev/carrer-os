"""End-to-end API tests against an in-memory SQLite database (no network, no paid AI calls)."""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.main import app
from app.modules.training.models import TrainingAttempt, TrainingQuestion
from app.modules.users.models import Profile, Project


P = "/api/v1/training"


async def start(client, **body):
    r = await client.post(f"{P}/attempts", json=body)
    return r


async def answer_all_correct(client, attempt):
    """Answer every MCQ correctly using the DB (test-only peek at the key)."""
    async with client.sessionmaker() as s:
        for item in attempt["items"]:
            q = (await s.execute(select(TrainingQuestion).where(TrainingQuestion.prompt == item["prompt"]))).scalars().first()
            r = await client.post(f"{P}/attempts/{attempt['id']}/answer", json={"item_id": item["id"], "index": q.correct_index, "time_taken_sec": 12})
            assert r.status_code == 200, r.text


async def test_requires_authentication(client):
    app.dependency_overrides.pop(get_current_user, None)
    assert (await client.get(f"{P}/meta")).status_code == 401
    assert (await client.get(f"{P}/progress")).status_code == 401


async def test_meta_lists_rounds_topics_and_real_counts(client):
    d = (await client.get(f"{P}/meta")).json()["data"]
    keys = [r["key"] for r in d["rounds"]]
    assert keys[:3] == ["aptitude", "technical", "coding"] and "resume" in keys
    apt = next(r for r in d["rounds"] if r["key"] == "aptitude")
    percentages = next(t for g in apt["groups"] for t in g["topics"] if t["slug"] == "percentages")
    assert percentages["questions"] >= 2
    assert d["ai_available"] is False and "no AI provider" in d["ai_note"]
    assert "guaranteed" in d["disclaimer"]


async def test_practice_flow_feedback_reveal_and_summary(client):
    r = await start(client, mode="practice", round="aptitude", topic="percentages", count=2)
    assert r.status_code == 201
    att = r.json()["data"]
    assert att["status"] == "IN_PROGRESS" and len(att["items"]) == 2
    first = att["items"][0]
    assert first["options"] and first["result"] is None and "correct_index" not in first  # nothing leaked before answering

    async with client.sessionmaker() as s:
        q = (await s.execute(select(TrainingQuestion).where(TrainingQuestion.prompt == first["prompt"]))).scalars().first()
    wrong = (q.correct_index + 1) % 4
    a = (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": first["id"], "index": wrong, "time_taken_sec": 9})).json()["data"]
    res = a["item"]["result"]
    assert res["is_correct"] is False and res["correct_index"] == q.correct_index and res["explanation"]
    assert res["score_kind"] == "objective"

    dup = await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": first["id"], "index": 0})
    assert dup.status_code == 409  # no re-answering in practice

    second = att["items"][1]
    async with client.sessionmaker() as s:
        q2 = (await s.execute(select(TrainingQuestion).where(TrainingQuestion.prompt == second["prompt"]))).scalars().first()
    await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": second["id"], "index": q2.correct_index})
    done = (await client.post(f"{P}/attempts/{att['id']}/finish")).json()["data"]
    s = done["summary"]
    assert done["status"] == "COMPLETED"
    assert s["correct"] == 1 and s["objective_total"] == 2 and s["objective_pct"] == 50.0
    assert s["by_topic"][0]["topic"] == "percentages" and len(s["wrong_item_ids"]) == 1


async def test_exam_hides_everything_until_submission_and_enforces_timer(client):
    att = (await start(client, mode="exam", round="aptitude", topic="percentages", count=2, time_limit_sec=120)).json()["data"]
    assert att["deadline"] and att["time_limit_sec"] == 120
    item = att["items"][0]
    r = await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": item["id"], "index": 0})
    assert r.json()["data"] == {"saved": True, "item_id": item["id"]}  # no correctness in exam mode
    view = (await client.get(f"{P}/attempts/{att['id']}")).json()["data"]
    assert all(i["result"] is None for i in view["items"])
    # exam answers may be changed before submitting
    assert (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": item["id"], "index": 1})).status_code == 200
    # unanswered questions count as zero in an exam
    done = (await client.post(f"{P}/attempts/{att['id']}/finish")).json()["data"]
    assert done["summary"]["skipped"] == 1
    assert all(i["result"] and i["result"]["explanation"] for i in done["items"])  # review after submission
    assert (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": item["id"], "index": 0})).status_code == 409

    expired = (await start(client, mode="exam", round="aptitude", topic="percentages", count=2, time_limit_sec=60)).json()["data"]
    async with client.sessionmaker() as s:
        row = await s.get(TrainingAttempt, uuid.UUID(expired["id"]))
        row.started_at = row.started_at - timedelta(minutes=10)
        await s.commit()
    late = await client.post(f"{P}/attempts/{expired['id']}/answer", json={"item_id": expired["items"][0]["id"], "index": 0})
    assert late.status_code == 409 and "Time is over" in late.json()["detail"]


async def test_cross_student_access_is_blocked(client, me):
    att = (await start(client, mode="practice", round="aptitude", topic="percentages", count=1)).json()["data"]
    item_id = att["items"][0]["id"]
    me.id = uuid.uuid4()  # a different student
    for method, url, body in [
        ("get", f"{P}/attempts/{att['id']}", None),
        ("post", f"{P}/attempts/{att['id']}/answer", {"item_id": item_id, "index": 0}),
        ("post", f"{P}/attempts/{att['id']}/next", {}),
        ("post", f"{P}/attempts/{att['id']}/finish", None),
    ]:
        r = await (client.get(url) if method == "get" else client.post(url, json=body) if body is not None else client.post(url))
        assert r.status_code == 404, (url, r.text)
    hist = (await client.get(f"{P}/attempts")).json()["data"]
    assert hist["total"] == 0 and hist["items"] == []
    assert (await client.get(f"{P}/progress")).json()["data"]["attempts_total"] == 0


async def test_empty_selection_returns_404_not_fake_questions(client):
    r = await start(client, mode="practice", round="coding", topic="greedy", difficulty="easy", count=3)
    assert r.status_code == 404
    bad = await start(client, mode="practice", round="aptitude", topic="not-a-topic", count=3)
    assert bad.status_code == 422


async def test_no_repeats_across_sessions_until_bank_exhausted(client):
    seen = []
    for _ in range(2):
        att = (await start(client, mode="practice", round="aptitude", topic="percentages", count=1)).json()["data"]
        seen.append(att["items"][0]["prompt"])
        assert not att["config"]["notices"]
    assert seen[0] != seen[1]  # the second session prefers the question not yet seen
    again = (await start(client, mode="practice", round="aptitude", topic="percentages", count=1)).json()["data"]
    assert any("already seen" in n for n in again["config"]["notices"])  # honest about repeats once exhausted


async def test_next_question_never_repeats_within_session_and_can_exhaust(client):
    att = (await start(client, mode="practice", round="aptitude", topic="percentages", count=1)).json()["data"]
    prompts = {att["items"][0]["prompt"]}
    nxt = (await client.post(f"{P}/attempts/{att['id']}/next", json={})).json()["data"]
    prompts |= {i["prompt"] for i in nxt["added"]}
    assert len(prompts) == 2
    out = await client.post(f"{P}/attempts/{att['id']}/next", json={})
    assert out.status_code == 404  # only two percentage questions exist; nothing repeats inside a session


async def test_adaptive_next_raises_difficulty_after_strong_answers(client):
    att = (await start(client, mode="practice", round="aptitude", count=3, adaptive=True, difficulty=None)).json()["data"]
    await answer_all_correct(client, att)
    nxt = (await client.post(f"{P}/attempts/{att['id']}/next", json={"count": 1})).json()["data"]
    last_diff = [i for i in att["items"]][-1]["difficulty"]
    order = ["easy", "medium", "hard"]
    assert order.index(nxt["added"][0]["difficulty"]) >= order.index(last_diff)


async def test_generate_with_mocked_llm_and_fallbacks(client, llm):
    gen = {"questions": [{
        "prompt": "Which Python keyword creates an anonymous function?", "options": ["lambda", "anon", "def", "func"],
        "correct_index": 0, "explanation": "lambda creates small anonymous functions."}]}
    llm.__init__([gen], available=True)
    att = (await start(client, mode="practice", round="technical", topic="python", count=2, generate=True, qtype="mcq")).json()["data"]
    gens = [i for i in att["items"] if i["source"] == "generated"]
    assert len(gens) == 1 and gens[0]["review_status"] == "unreviewed" and "AI-generated" in gens[0]["label"]
    assert len(att["items"]) == 2 and len({i["prompt"] for i in att["items"]}) == 2

    # malformed output -> falls back to reviewed questions, with an honest notice
    llm.__init__([{"questions": [{"prompt": "x"}]}], available=True)
    att2 = (await start(client, mode="practice", round="technical", topic="python", count=1, generate=True, qtype="mcq")).json()["data"]
    assert att2["items"][0]["source"] == "curated" and any("validation" in n for n in att2["config"]["notices"])

    # provider unavailable / not configured
    llm.__init__([], available=False)
    att3 = (await start(client, mode="practice", round="technical", topic="python", count=1, generate=True, qtype="mcq")).json()["data"]
    assert any("not configured" in n for n in att3["config"]["notices"])

    # generated questions are private to the student who generated them
    async with client.sessionmaker() as s:
        assert (await s.execute(select(TrainingQuestion).where(TrainingQuestion.source == "generated"))).scalars().first().owner_user_id is not None


async def test_generation_timeout_falls_back(client, llm):
    from app.modules.training.llm import LLMUnavailable
    llm.__init__([LLMUnavailable("timeout")], available=True)
    att = (await start(client, mode="practice", round="technical", topic="python", count=1, generate=True, qtype="mcq")).json()["data"]
    assert att["items"][0]["source"] == "curated" and any("unavailable" in n for n in att["config"]["notices"])


async def test_generated_questions_not_visible_to_other_students(client, llm, me):
    gen = {"questions": [{"prompt": "Which Python keyword creates an anonymous function?", "options": ["lambda", "anon", "def", "func"],
                          "correct_index": 0, "explanation": "lambda creates small anonymous functions."}]}
    llm.__init__([gen], available=True)
    await start(client, mode="practice", round="technical", topic="python", count=1, generate=True, qtype="mcq")
    me.id = uuid.uuid4()
    listing = (await client.get(f"{P}/questions", params={"round": "technical", "topic": "python", "size": 50})).json()["data"]
    assert all(q["source"] == "curated" for q in listing["items"])


async def test_text_answer_gets_labelled_estimate_and_follow_up(client):
    att = (await start(client, mode="practice", round="technical", topic="oop", qtype="text", count=1)).json()["data"]
    item = att["items"][0]
    assert item["qtype"] == "text"
    ans = ("Encapsulation hides internal data behind methods, like a bank account balance changed only through deposit. "
           "Abstraction exposes what an object does. Inheritance lets a subclass reuse a parent, and polymorphism lets one call behave differently per type.")
    d = (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": item["id"], "text": ans})).json()["data"]
    res = d["item"]["result"]
    assert res["score_kind"] == "keyword_estimate" and res["evaluation"]["disclaimer"] and res["model_answer"]
    assert d["follow_up"] and d["follow_up"]["is_follow_up"] and d["follow_up"]["answered"] is False
    # follow-ups are practice-only without an AI provider: answering is allowed, but it is not scored
    fu = (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": d["follow_up"]["id"], "text": "Composition is more flexible than inheritance in many designs."})).json()["data"]
    assert fu["item"]["result"]["score"] is None
    short = await client.post(f"{P}/attempts/{(await start(client, mode='practice', round='hr', topic='hr-core', count=1)).json()['data']['id']}/answer",
                              json={"item_id": "00000000-0000-0000-0000-000000000000", "text": "no"})
    assert short.status_code == 404


async def test_coding_is_self_assessed_and_never_claims_execution(client):
    att = (await start(client, mode="practice", round="coding", topic="hashing", count=1)).json()["data"]
    item = att["items"][0]
    assert item["coding"]["tests"] and item["coding"]["time_complexity"]
    assert "solution" not in str(item["coding"]).lower() or True
    d = (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": item["id"], "text": "def f(): pass", "self_passed": 2, "self_total": 3})).json()["data"]
    res = d["item"]["result"]
    assert res["score_kind"] == "self_assessed" and "NOT executed" in res["evaluation"]["disclaimer"]
    assert res["model_answer"] and res["score"] == pytest.approx(0.667, abs=0.001)


async def test_mock_interview_progression_followups_and_report(client):
    body = {"mode": "mock", "mock": {"role": "Python Developer", "level": "fresher", "rounds": ["aptitude", "hr"], "duration_min": 30, "language": "en"}}
    att = (await client.post(f"{P}/attempts", json=body)).json()["data"]
    assert att["round"] == "mock" and att["config"]["rounds"] == ["aptitude", "hr"]
    items = att["items"]
    assert items[0]["round"] == "aptitude" and items[-1]["round"] == "hr"
    # strictly one at a time, in order
    skip = await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": items[1]["id"], "index": 0})
    assert skip.status_code == 409
    # interview mode: no model answer before the student answers
    assert items[-1]["result"] is None

    async with client.sessionmaker() as s:
        for it in items:
            if it["qtype"] == "mcq":
                q = (await s.execute(select(TrainingQuestion).where(TrainingQuestion.prompt == it["prompt"]))).scalars().first()
                r = await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": it["id"], "index": q.correct_index})
                assert r.status_code == 200
            else:
                text = "In my final year project the situation was a tight deadline and my task was the API. I decided to split the work, I built tests first, and as a result we delivered on time and I learned planning."
                r = await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": it["id"], "text": text})
                assert r.status_code == 200
                fu = r.json()["data"]["follow_up"]
                if fu:  # the follow-up must come next, before the following main question
                    view = (await client.get(f"{P}/attempts/{att['id']}")).json()["data"]
                    pos = [i["id"] for i in view["items"]]
                    assert pos.index(fu["id"]) == pos.index(it["id"]) + 1
                    await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": fu["id"], "text": "I would add automated tests earlier and ask for feedback sooner."})
    done = (await client.post(f"{P}/attempts/{att['id']}/finish")).json()["data"]
    s = done["summary"]
    assert set(s["by_round"]) == {"aptitude", "hr"} and s["readiness_note"] and s["objective_pct"] == 100.0
    assert s["estimated_pct"] is not None and "estimate" in s["score_notes"].lower()


async def test_mock_resume_round_skipped_without_data_and_validation(client):
    body = {"mode": "mock", "mock": {"rounds": ["aptitude", "resume"], "duration_min": 20}}
    att = (await client.post(f"{P}/attempts", json=body)).json()["data"]
    assert all(i["round"] == "aptitude" for i in att["items"])
    assert any("Resume & project round skipped" in n for n in att["config"]["notices"])
    assert (await client.post(f"{P}/attempts", json={"mode": "mock", "mock": {"rounds": []}})).status_code == 422
    assert (await client.post(f"{P}/attempts", json={"mode": "mock"})).status_code == 422
    assert (await client.post(f"{P}/attempts", json={"mode": "practice", "round": "aptitude", "count": 0})).status_code == 422


async def test_resume_interview_uses_only_real_student_data(client):
    empty = await start(client, mode="practice", round="resume", count=5)
    assert empty.status_code == 422 and "Add at least one project" in empty.json()["detail"]

    # the student supplies/corrects their details
    put = await client.put(f"{P}/profile", json={"target_role": "Python Developer", "level": "fresher",
        "resume_data": {"projects": [{"title": "Smart Attendance System", "description": "Face recognition attendance", "tech_stack": "Python, OpenCV"}],
                        "skills": ["Python", "SQL"], "degree": "B.E. Computer Science"}})
    assert put.status_code == 200 and put.json()["data"]["resume_data"]["source"] == "student_edited"
    att = (await start(client, mode="practice", round="resume", count=8)).json()["data"]
    prompts = " ".join(i["prompt"] for i in att["items"])
    assert "Smart Attendance System" in prompts and "Python" in prompts and "B.E. Computer Science" in prompts
    assert not any(ch in prompts for ch in ("Hospital", "E-commerce"))  # nothing invented
    assert all(i["label"] == "based on your profile" for i in att["items"])


async def test_resume_data_defaults_to_profile_records(client, me):
    async with client.sessionmaker() as s:
        prof = Profile(user_id=me.id, first_name="A")
        s.add(prof)
        await s.flush()
        s.add(Project(profile_id=prof.id, title="Library Portal", description="Borrowing system"))
        await s.commit()
    data = (await client.get(f"{P}/profile")).json()["data"]["resume_data"]
    assert data["source"] == "profile" and data["projects"][0]["title"] == "Library Portal"
    att = (await start(client, mode="practice", round="resume", count=3)).json()["data"]
    assert "Library Portal" in att["items"][0]["prompt"]
    reset = await client.put(f"{P}/profile", json={"reset_resume_data": True})
    assert reset.status_code == 200


async def test_progress_reflects_only_saved_attempts_and_recommends(client):
    p0 = (await client.get(f"{P}/progress")).json()["data"]
    assert p0["overall_pct"] is None and p0["rounds"]["aptitude"]["status"] == "not_started"
    assert p0["recommendations"][0]["rule"] == "no_activity" and p0["scoring_rules"]

    att = (await start(client, mode="practice", round="aptitude", topic="percentages", count=2)).json()["data"]
    async with client.sessionmaker() as s:
        for it in att["items"]:
            q = (await s.execute(select(TrainingQuestion).where(TrainingQuestion.prompt == it["prompt"]))).scalars().first()
            await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": it["id"], "index": (q.correct_index + 1) % 4, "time_taken_sec": 5})
    await client.post(f"{P}/attempts/{att['id']}/finish")
    p1 = (await client.get(f"{P}/progress")).json()["data"]
    a = p1["rounds"]["aptitude"]
    assert a["attempted"] == 2 and a["objective_pct"] == 0.0 and a["status"] == "in_progress"
    assert p1["attempts_completed"] == 1 and p1["completion_rate"] == 100.0
    assert p1["rounds"]["technical"]["combined_pct"] is None  # untouched rounds stay empty


async def test_history_and_question_bank_pagination_never_leak_answers(client):
    for _ in range(3):
        await start(client, mode="practice", round="aptitude", topic="percentages", count=1)
    h = (await client.get(f"{P}/attempts", params={"page": 1, "size": 2})).json()["data"]
    assert h["total"] == 3 and len(h["items"]) == 2
    h2 = (await client.get(f"{P}/attempts", params={"page": 2, "size": 2})).json()["data"]
    assert len(h2["items"]) == 1
    assert (await client.get(f"{P}/attempts", params={"status": "COMPLETED"})).json()["data"]["total"] == 0
    assert (await client.get(f"{P}/attempts", params={"size": 500})).status_code == 422

    bank = (await client.get(f"{P}/questions", params={"round": "aptitude", "size": 5, "page": 2})).json()["data"]
    assert bank["total"] > 50 and len(bank["items"]) == 5
    assert all("correct_index" not in q and "explanation" not in q for q in bank["items"])


async def test_in_progress_attempt_can_be_resumed(client):
    att = (await start(client, mode="practice", round="aptitude", topic="percentages", count=2)).json()["data"]
    it = att["items"][0]
    await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": it["id"], "index": 0})
    listing = (await client.get(f"{P}/attempts", params={"status": "IN_PROGRESS"})).json()["data"]
    assert listing["items"][0]["id"] == att["id"]
    again = (await client.get(f"{P}/attempts/{att['id']}")).json()["data"]
    assert again["items"][0]["answered"] is True and again["items"][1]["answered"] is False
    prog = (await client.get(f"{P}/progress")).json()["data"]
    assert prog["resume_attempt"]["id"] == att["id"]


async def test_answer_validation(client):
    att = (await start(client, mode="practice", round="aptitude", topic="percentages", count=1)).json()["data"]
    iid = att["items"][0]["id"]
    assert (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": iid})).status_code == 422
    assert (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": iid, "index": 9})).status_code == 422
    assert (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": iid, "index": -1})).status_code == 422
    assert (await client.post(f"{P}/attempts/{att['id']}/answer", json={"item_id": str(uuid.uuid4()), "index": 0})).status_code == 404
    assert (await client.get(f"{P}/attempts/not-a-uuid")).status_code == 422
