"""Universal role training: any job title, fresh questions, instant evaluation, backend scoring, review, ownership.

Isolated in-memory SQLite. The LLM is a scripted FakeLLM (or unavailable); nothing here calls a real provider.
"""

import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.main import app
from app.modules.training.llm import LLMUnavailable, get_llm
from app.modules.training.models import TrainingAttempt, TrainingAttemptItem, TrainingQuestion
from app.modules.training.role_generation import validate_role_question
from app.modules.training.roles import clean_role_title, InvalidRole, resolve_role, vocabulary_for

from training_fakes import FakeLLM

R = "/api/v1/training"


# -- helpers -------------------------------------------------------------------------------------------------------

async def start(client, title="Prompt Engineer", **kw):
    return await client.post(f"{R}/role-sessions", json={"role_title": title, "generate": False, **kw})


async def ok_start(client, title="Prompt Engineer", **kw):
    r = await start(client, title, **kw)
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def question_of(client, item_id):
    async with client.sessionmaker() as s:
        item = (await s.execute(select(TrainingAttemptItem).where(TrainingAttemptItem.id == uuid.UUID(item_id)))).scalar_one()
        return item.question


async def answer(client, sid, item, mode="correct"):
    """mode: correct | wrong | half (text only)."""
    q = await question_of(client, item["id"])
    if q.qtype == "mcq":
        idx = q.correct_index if mode == "correct" else (q.correct_index + 1) % len(q.options)
        body = {"item_id": item["id"], "index": idx}
    else:
        groups = [g for g in q.rubric["keywords"] if g]
        if mode == "correct":
            picked = groups
        elif mode == "half":
            picked = groups[: max(1, len(groups) // 2)]
        else:
            picked = []
        # The filler is nonsense so that it can never match a rubric keyword by accident.
        filler = " ".join(["qzx"] * 18)
        text = (", ".join(g[0] for g in picked) + " " + filler) if picked else filler
        body = {"item_id": item["id"], "text": text}
    r = await client.post(f"{R}/role-sessions/{sid}/answer", json=body)
    assert r.status_code == 200, r.text
    return r.json()["data"]


async def finish(client, sid):
    r = await client.post(f"{R}/role-sessions/{sid}/finish")
    assert r.status_code == 200, r.text
    return r.json()["data"]


def with_ai(responses):
    ai = FakeLLM(responses)
    app.dependency_overrides[get_llm] = lambda: ai
    return ai


def gen_mcq(prompt, topic="Prompt Design", correct=0, **over):
    opts = ["Option alpha is right", "Option beta is wrong", "Option gamma is wrong", "Option delta is wrong"]
    d = {"kind": "core", "topic": topic, "qtype": "mcq", "difficulty": "easy", "prompt": prompt, "options": opts, "correct_index": correct,
         "correct_answer_text": opts[correct], "explanation": "Option alpha is right because it reflects how prompt design works in practice.",
         "skill_tags": ["prompt design"]}
    d.update(over)
    return d


# -- roles: search, normalisation, custom titles ---------------------------------------------------------------------

async def test_role_search_lists_catalog_and_accepts_custom_titles(client):
    r = (await client.get(f"{R}/roles", params={"q": "prompt"})).json()["data"]
    assert [x["title"] for x in r["roles"]][0] == "Prompt Engineer" and r["custom_allowed"] is True
    assert r["roles"][0]["available_questions"] >= 12 and r["exact_match"] is False
    exact = (await client.get(f"{R}/roles", params={"q": "Cloud Engineer"})).json()["data"]
    assert exact["exact_match"] is True
    nothing = (await client.get(f"{R}/roles", params={"q": "Underwater Basket Weaver"})).json()["data"]
    assert nothing["roles"] == [] and nothing["custom_allowed"] is True


def test_role_normalisation_preserves_the_students_title_but_matches_variants():
    assert clean_role_title("  Cloud   Security   Engineer ") == "Cloud Security Engineer"
    assert resolve_role("FRONT-END developer").key == resolve_role("Frontend Developer").key
    assert resolve_role("Senior Frontend Developer").title == "Senior Frontend Developer"  # wording preserved
    assert resolve_role("Senior Frontend Developer").matched_title == "Frontend Developer"
    assert resolve_role("Sound Engineer").mapped is False  # accepted, but no reviewed topics are claimed
    for bad in ["", "x", "a" * 61, "http://evil.example", "!!!!", "12345"]:
        with pytest.raises(InvalidRole):
            clean_role_title(bad)


async def test_resolve_endpoint_reports_coverage_honestly_and_rejects_junk(client):
    mapped = (await client.post(f"{R}/roles/resolve", json={"title": "Cybersecurity Analyst"})).json()["data"]
    assert mapped["mapped"] and mapped["available_questions"] >= 10 and mapped["can_start"]
    unmapped = (await client.post(f"{R}/roles/resolve", json={"title": "Sound Engineer"})).json()["data"]
    assert unmapped["mapped"] is False and unmapped["available_questions"] == 0
    assert unmapped["can_start"] is False and "AI question generation is not configured" in unmapped["message"]
    assert (await client.post(f"{R}/roles/resolve", json={"title": "http://x.y"})).status_code == 422


# -- relevant, different questions per role ---------------------------------------------------------------------------

async def test_common_role_gets_role_relevant_questions(client):
    s = await ok_start(client, "Frontend Developer", count=10)
    domain = [i for i in s["items"] if not i["is_workplace"]]
    allowed = {t["slug"] for t in s["role"]["topics"]}
    assert domain and all(i["topic"] in allowed for i in domain)
    assert s["role"]["title"] == "Frontend Developer" and s["status"] == "IN_PROGRESS"
    assert len({i["id"] for i in s["items"]}) == len(s["items"])


async def test_custom_title_maps_to_topics_and_preserves_the_wording(client):
    s = await ok_start(client, "Cloud Security Specialist", count=8)
    assert s["role"]["title"] == "Cloud Security Specialist" and s["role"]["matched_title"] == "Cloud Engineer"
    topics = {i["topic"] for i in s["items"] if not i["is_workplace"]}
    assert topics & {"cybersecurity", "cloud-computing"}


async def test_two_roles_get_different_questions(client):
    a = await ok_start(client, "Prompt Engineer", count=8)
    b = await ok_start(client, "Data Analyst", count=8)
    ta = {i["topic"] for i in a["items"] if not i["is_workplace"]}
    tb = {i["topic"] for i in b["items"] if not i["is_workplace"]}
    assert ta & {"prompt-engineering", "llm-safety"} and not (ta & tb - {"python"})
    assert tb and tb <= {"sql", "data-analysis", "ds-statistics", "python", "dbms"}  # only Data Analyst topics
    prompts_a = {i["prompt"] for i in a["items"] if not i["is_workplace"]}
    prompts_b = {i["prompt"] for i in b["items"] if not i["is_workplace"]}
    assert not (prompts_a & prompts_b)


async def test_session_mixes_kinds_and_adds_workplace_questions(client):
    s = await ok_start(client, "Cloud Engineer", count=10)
    assert any(i["is_workplace"] for i in s["items"])
    assert len({i["qtype"] for i in s["items"]}) >= 2 or len({i["kind"] for i in s["items"]}) >= 2
    assert s["plan"]["allocation"] and all(a["reason"] for a in s["plan"]["allocation"])


# -- unreachable roles: honest failure, no unrelated filler ------------------------------------------------------------

async def test_unmapped_role_without_ai_is_refused_with_a_clear_message_not_filled_with_unrelated_questions(client):
    r = await start(client, "Sound Engineer", count=10)
    assert r.status_code == 422
    assert "AI question generation is not configured" in r.text and "Sound Engineer" in r.text
    async with client.sessionmaker() as s:
        assert (await s.execute(select(TrainingAttempt))).scalars().first() is None  # nothing was created


# -- fresh questions across sessions ------------------------------------------------------------------------------------

async def test_next_session_prefers_questions_the_student_has_not_seen(client):
    first = await ok_start(client, "Software Engineer", count=6)   # pool of 16 domain questions
    second = await ok_start(client, "Software Engineer", count=6)
    d1 = {i["prompt"] for i in first["items"] if not i["is_workplace"]}
    d2 = {i["prompt"] for i in second["items"] if not i["is_workplace"]}
    assert not (d1 & d2)
    assert second["plan"]["repeats"] == 0 and not any(i["is_repeat"] for i in second["items"])


async def test_exhausted_bank_repeats_are_intentional_labelled_and_explained(client):
    first = await ok_start(client, "UI/UX Designer", count=8)       # only 8 reviewed domain questions exist
    assert not any(i["is_repeat"] for i in first["items"])
    second = await ok_start(client, "UI/UX Designer", count=8)
    repeats = [i for i in second["items"] if i["is_repeat"]]
    assert repeats and second["plan"]["repeats"] == len(repeats)
    assert any("repeat earlier practice on purpose" in n for n in second["notices"])
    assert len({i["id"] for i in second["items"]}) == len(second["items"])
    assert len({i["prompt"] for i in second["items"]}) == len(second["items"])  # never twice inside one session


async def test_not_enough_questions_returns_a_smaller_set_with_a_notice(client):
    s = await ok_start(client, "Product Manager", count=30)
    assert len(s["items"]) < 30 and any("available for this role right now" in n for n in s["notices"])


# -- instant evaluation -----------------------------------------------------------------------------------------------

async def test_mcq_is_graded_on_the_server_and_the_answer_is_hidden_until_submitted(client):
    s = await ok_start(client, "Cybersecurity Analyst", count=6)
    mcq = next(i for i in s["items"] if i["qtype"] == "mcq")
    assert mcq["result"] is None and "correct_index" not in str(mcq)  # nothing leaks before submission
    q = await question_of(client, mcq["id"])
    wrong = await answer(client, s["id"], mcq, "wrong")
    res = wrong["item"]["result"]
    assert res["status"] == "incorrect" and res["marks"] == 0 and res["max_marks"] == 1
    assert res["correct_index"] == q.correct_index and res["correct_answer"] == q.options[q.correct_index]
    assert res["explanation"] and res["missing"] and res["suggestion"]
    right = await answer(client, s["id"], next(i for i in s["items"] if i["qtype"] == "mcq" and i["id"] != mcq["id"]), "correct")
    assert right["item"]["result"]["status"] == "correct" and right["item"]["result"]["marks"] == 1
    assert right["item"]["result"]["got_right"]


async def test_text_answers_can_earn_partial_credit(client):
    s = await ok_start(client, "Prompt Engineer", count=16)
    texts = [i for i in s["items"] if i["qtype"] == "text" and not i["is_workplace"]]
    assert len(texts) >= 3
    full = (await answer(client, s["id"], texts[0], "correct"))["item"]["result"]
    half = (await answer(client, s["id"], texts[1], "half"))["item"]["result"]
    none = (await answer(client, s["id"], texts[2], "wrong"))["item"]["result"]
    assert full["status"] == "correct" and full["marks"] >= 1.5 and full["max_marks"] == 2
    assert half["status"] == "partial" and 0 < half["marks"] < 1.5
    assert none["status"] == "incorrect" and none["marks"] == 0
    assert none["expected_concepts"] and none["model_answer"] and none["missing"] and "Rule-based estimate" in none["disclaimer"]
    assert half["got_right"] and half["missing"] and full["method"] == "keyword_estimate"


async def test_resubmitting_an_answer_does_not_score_twice(client):
    s = await ok_start(client, "Cloud Engineer", count=5)
    item = next(i for i in s["items"] if i["qtype"] == "mcq")
    q = await question_of(client, item["id"])
    first = await answer(client, s["id"], item, "wrong")
    r = await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": item["id"], "index": q.correct_index})
    again = r.json()["data"]
    assert again["already_answered"] is True and again["item"]["result"]["status"] == "incorrect"  # first result stands
    assert again["item"]["result"]["marks"] == first["item"]["result"]["marks"] == 0


async def test_invalid_item_and_empty_answers_are_rejected(client):
    s = await ok_start(client, "Cloud Engineer", count=5)
    assert (await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": str(uuid.uuid4()), "index": 0})).status_code == 404
    mcq = next(i for i in s["items"] if i["qtype"] == "mcq")
    assert (await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": mcq["id"]})).status_code == 422
    assert (await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": mcq["id"], "index": 9})).status_code == 422
    txt = next(i for i in s["items"] if i["qtype"] == "text")
    assert (await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": txt["id"], "text": "   "})).status_code == 422


async def test_question_without_a_marking_guide_needs_manual_review_and_is_not_scored(client):
    s = await ok_start(client, "Cloud Engineer", count=5)
    txt = next(i for i in s["items"] if i["qtype"] == "text")
    async with client.sessionmaker() as db:
        q = (await db.execute(select(TrainingQuestion).where(TrainingQuestion.id == (await question_of(client, txt["id"])).id))).scalar_one()
        q.rubric = {"keywords": [], "framework": None}
        await db.commit()
    res = (await answer(client, s["id"], txt, "correct"))["item"]["result"]
    assert res["status"] == "manual_review" and res["marks"] is None and "model_answer" in res
    done = await finish(client, s["id"])
    assert done["summary"]["manual_review"] == 1


# -- final scoring and review ------------------------------------------------------------------------------------------

async def test_final_score_is_computed_from_persisted_answers_and_unanswered_count_as_zero(client):
    s = await ok_start(client, "Cloud Engineer", count=8)
    items = s["items"]
    await answer(client, s["id"], items[0], "correct")
    await answer(client, s["id"], items[1], "wrong")
    await answer(client, s["id"], items[2], "correct")
    done = await finish(client, s["id"])
    summary = done["summary"]
    # recompute independently from the database rows
    async with client.sessionmaker() as db:
        rows = (await db.execute(select(TrainingAttemptItem).where(TrainingAttemptItem.attempt_id == uuid.UUID(s["id"])))).scalars().all()
        earned = sum((r.evaluation or {}).get("marks") or 0 for r in rows if r.answered_at)
        available = sum(MAX for MAX in ((2.0 if r.question.qtype == "text" else 1.0) for r in rows))
    assert summary["marks_earned"] == pytest.approx(earned)
    assert summary["marks_available"] == pytest.approx(available)
    assert summary["percentage"] == pytest.approx(round(100 * earned / available, 1))
    assert summary["total_questions"] == 8 and summary["answered"] == 3 and summary["unanswered"] == 5
    assert summary["correct"] + summary["partial"] + summary["incorrect"] + summary["manual_review"] == 3
    assert any("Unanswered questions earn 0" in r for r in summary["scoring_rules"])
    assert (await finish(client, s["id"]))["summary"] == summary  # finishing twice does not change anything


async def test_review_lists_every_question_with_filters_and_reveals_unanswered_answers(client):
    s = await ok_start(client, "Cybersecurity Analyst", count=6)
    await answer(client, s["id"], s["items"][0], "correct")
    await answer(client, s["id"], s["items"][1], "wrong")
    assert (await client.get(f"{R}/role-sessions/{s['id']}/review")).status_code == 409  # not finished yet
    await finish(client, s["id"])
    rev = (await client.get(f"{R}/role-sessions/{s['id']}/review")).json()["data"]
    assert rev["counts"]["all"] == 6 and rev["counts"]["unanswered"] == 4 and len(rev["items"]) == 6
    un = (await client.get(f"{R}/role-sessions/{s['id']}/review", params={"status": "unanswered"})).json()["data"]
    assert len(un["items"]) == 4 and all(i["result"]["status"] == "unanswered" and i["result"]["marks"] == 0 for i in un["items"])
    assert all(i["result"].get("correct_answer") or i["result"].get("model_answer") for i in un["items"])
    done = [i for i in rev["items"] if i["answered"]]
    assert all(i["result"]["explanation"] is not None and i["result"]["your_answer"] for i in done)
    inc = (await client.get(f"{R}/role-sessions/{s['id']}/review", params={"status": "incorrect"})).json()["data"]
    assert len(inc["items"]) == rev["counts"]["incorrect"]
    assert (await client.get(f"{R}/role-sessions/{s['id']}/review", params={"status": "bogus"})).status_code == 422


async def test_topic_breakdown_strengths_weaknesses_and_revision(client):
    s = await ok_start(client, "Cybersecurity Analyst", count=10)
    for it in s["items"]:
        await answer(client, s["id"], it, "correct" if it["topic"] == "cybersecurity" else "wrong")
    summary = (await finish(client, s["id"]))["summary"]
    by = {t["topic"]: t for t in summary["by_topic"]}
    assert by["cybersecurity"]["pct"] == 100.0
    assert any(t["label"] == "Cybersecurity Fundamentals" for t in [{"label": x} for x in summary["strong_topics"]])
    own = {t["slug"] for t in s["role"]["topics"]}  # workplace questions are mixed in at random and scored separately
    others = [t for k, t in by.items() if k != "cybersecurity" and k in own and t["pct"] is not None]
    assert others and all(t["pct"] == 0 for t in others)
    assert summary["weak_topics"] and summary["revision"]


# -- adaptation ------------------------------------------------------------------------------------------------------

async def test_improve_weak_areas_focuses_on_topics_where_marks_were_lost(client):
    s = await ok_start(client, "Cybersecurity Analyst", count=12)
    for it in s["items"]:
        await answer(client, s["id"], it, "correct" if it["topic"] == "cybersecurity" else "wrong")
    await finish(client, s["id"])
    r = await client.post(f"{R}/role-sessions/{s['id']}/again", json={"focus": "weak", "count": 6})
    assert r.status_code == 201
    nxt = r.json()["data"]
    topics = {i["topic"] for i in nxt["items"]}
    weak_before = {i["topic"] for i in s["items"] if i["topic"] != "cybersecurity" and not i["is_workplace"]}
    assert topics <= weak_before and "cybersecurity" not in topics and nxt["focus"] == "weak"
    assert any("Improve Weak Areas" in n for n in nxt["plan"]["notes"])
    assert nxt["id"] != s["id"] and nxt["plan"]["workplace"] == 0


async def test_weak_focus_without_history_falls_back_to_a_mixed_session_with_a_notice(client):
    s = await ok_start(client, "Cloud Engineer", count=6, focus="weak")
    assert s["focus"] == "mixed" and any("No weak topics" in n for n in s["notices"])


async def test_practice_again_uses_history_to_avoid_seen_questions_and_weights_weak_topics(client):
    s = await ok_start(client, "Python Developer", count=10)
    weak = next(i["topic"] for i in s["items"] if not i["is_workplace"])  # a topic this session really contained
    for it in s["items"]:
        await answer(client, s["id"], it, "wrong" if it["topic"] == weak else "correct")
    await finish(client, s["id"])
    nxt = (await client.post(f"{R}/role-sessions/{s['id']}/again", json={"focus": "mixed"})).json()["data"]
    prev = {i["prompt"] for i in s["items"]}
    fresh = [i for i in nxt["items"] if i["prompt"] not in prev]
    assert len(fresh) >= len(nxt["items"]) // 2  # prefers unseen questions
    reasons = {a["topic"]: a["reason"] for a in nxt["plan"]["allocation"]}
    if weak in reasons:  # the topic where marks were lost is labelled as weak in the explanation of the plan
        assert "weak so far" in reasons[weak]


async def test_difficulty_adapts_to_recent_results_and_says_why(client):
    s = await ok_start(client, "Software Engineer", count=8, level="fresher")
    assert s["difficulty"] == "easy"
    for it in s["items"]:
        await answer(client, s["id"], it, "correct")
    await finish(client, s["id"])
    nxt = (await client.post(f"{R}/role-sessions/{s['id']}/again", json={"focus": "mixed"})).json()["data"]
    assert nxt["difficulty"] == "medium" and any("Difficulty raised to medium" in n for n in nxt["plan"]["notes"])


async def test_progress_is_tracked_separately_per_role(client):
    a = await ok_start(client, "Cloud Engineer", count=6)
    for it in a["items"]:
        await answer(client, a["id"], it, "correct")
    await finish(client, a["id"])
    pa = (await client.get(f"{R}/roles/progress", params={"title": "Cloud Engineer"})).json()["data"]
    pb = (await client.get(f"{R}/roles/progress", params={"title": "Data Analyst"})).json()["data"]
    assert pa["sessions_completed"] == 1 and pa["questions_answered"] == 6 and pa["average_percentage"] is not None
    assert pb["sessions_completed"] == 0 and pb["questions_answered"] == 0 and pb["average_percentage"] is None
    assert pa["unseen_stored_questions"] < pa["stored_questions"]


# -- ownership and legacy isolation ------------------------------------------------------------------------------------

async def test_a_student_cannot_touch_another_students_session(client):
    s = await ok_start(client, "Cloud Engineer", count=5)
    item = s["items"][0]

    class Other:
        id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: Other()
    sid = s["id"]
    assert (await client.get(f"{R}/role-sessions/{sid}")).status_code == 404
    assert (await client.post(f"{R}/role-sessions/{sid}/answer", json={"item_id": item["id"], "index": 0})).status_code == 404
    assert (await client.post(f"{R}/role-sessions/{sid}/finish")).status_code == 404
    assert (await client.get(f"{R}/role-sessions/{sid}/review")).status_code == 404
    assert (await client.post(f"{R}/role-sessions/{sid}/again", json={"focus": "mixed"})).status_code == 404
    assert (await client.get(f"{R}/role-sessions")).json()["data"]["total"] == 0
    assert (await client.get(f"{R}/roles/progress", params={"title": "Cloud Engineer"})).json()["data"]["sessions_completed"] == 0


async def test_legacy_endpoints_do_not_score_or_list_role_sessions(client):
    s = await ok_start(client, "Cloud Engineer", count=5)
    assert (await client.post(f"/api/v1/training/attempts/{s['id']}/answer", json={"item_id": s["items"][0]["id"], "index": 0})).status_code == 409
    assert (await client.post(f"/api/v1/training/attempts/{s['id']}/finish")).status_code == 409
    listing = (await client.get("/api/v1/training/attempts")).json()["data"]
    assert all(a["id"] != s["id"] for a in listing["items"])
    mine = (await client.get(f"{R}/role-sessions")).json()["data"]
    assert [x["id"] for x in mine["items"]] == [s["id"]] and mine["items"][0]["role_title"] == "Cloud Engineer"


async def test_unauthenticated_requests_are_rejected():
    from httpx import ASGITransport, AsyncClient

    app.dependency_overrides.pop(get_current_user, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for method, path in (("get", f"{R}/roles"), ("post", f"{R}/roles/resolve"), ("post", f"{R}/role-sessions"),
                             ("get", f"{R}/role-sessions/{uuid.uuid4()}"), ("post", f"{R}/role-sessions/{uuid.uuid4()}/answer")):
            r = await getattr(c, method)(path, **({"json": {}} if method == "post" else {}))
            assert r.status_code in (401, 403), path


# -- AI generation (scripted provider) and validation ----------------------------------------------------------------------

async def test_custom_role_uses_validated_generation_and_labels_it_unreviewed(client):
    ai = with_ai([{"questions": [
        gen_mcq("Which instrument measures sound pressure level in a studio?", "Acoustics", 0,
                options=["A sound level meter", "A multimeter", "A thermometer", "A hygrometer"],
                correct_answer_text="A sound level meter", explanation="A sound level meter measures sound pressure level in decibels.",
                skill_tags=["acoustics"]),
        gen_mcq("What does a limiter do to an audio signal during mixing?", "Mixing", 2,
                options=["Boosts all frequencies", "Adds reverb", "Prevents the level exceeding a set ceiling", "Removes the noise floor"],
                correct_answer_text="Prevents the level exceeding a set ceiling",
                explanation="A limiter prevents the level exceeding a set ceiling.", skill_tags=["mixing"]),
        gen_mcq("This is not valid because the answer text mismatches.", "Mixing", 1, correct_answer_text="Something else entirely"),
    ]}])
    r = await client.post(f"{R}/role-sessions", json={"role_title": "Sound Engineer", "count": 3, "generate": True})
    assert r.status_code == 201, r.text
    s = r.json()["data"]
    assert len(ai.calls) == 1 and s["role"]["mapped"] is False and s["role"]["title"] == "Sound Engineer"
    assert len(s["items"]) == 2 and all(i["source"] == "generated" and i["review_status"] == "unreviewed" for i in s["items"])
    assert any("1 AI-generated question(s) failed validation" in n for n in s["notices"])
    assert any("marked 'Unreviewed'" in n for n in s["notices"])
    # and they are stored for this student only, tagged with the role, so the same role reuses them next time
    async with client.sessionmaker() as db:
        rows = (await db.execute(select(TrainingQuestion).where(TrainingQuestion.source == "generated"))).scalars().all()
    assert len(rows) == 2 and all(r.owner_user_id is not None and r.roles == [s["role"]["key"]] for r in rows)
    again = await ok_start(client, "Sound Engineer", count=3)
    assert {i["prompt"] for i in again["items"]} == {i["prompt"] for i in s["items"]}  # reused: no new generation call
    assert len(ai.calls) == 1


async def test_generation_only_fills_the_gap_and_unavailable_provider_falls_back_honestly(client):
    with_ai([LLMUnavailable("down", "timeout")])
    r = await client.post(f"{R}/role-sessions", json={"role_title": "UI/UX Designer", "count": 14, "generate": True})
    assert r.status_code == 201
    s = r.json()["data"]
    assert not any(i["source"] == "generated" for i in s["items"])
    assert any("temporarily unavailable" in n for n in s["notices"])
    ai = with_ai([{"questions": []}])
    full = await client.post(f"{R}/role-sessions", json={"role_title": "Python Developer", "count": 5, "generate": True})
    assert full.status_code == 201 and not ai.calls  # enough unseen stored questions: no paid call at all


async def test_unmapped_role_with_unusable_ai_output_fails_clearly(client):
    with_ai([{"questions": [{"nonsense": True}]}])
    r = await client.post(f"{R}/role-sessions", json={"role_title": "Sound Engineer", "count": 5, "generate": True})
    assert r.status_code == 422 and "could not provide valid questions" in r.text


def _profile():
    return resolve_role("Prompt Engineer")


def test_generated_question_validation_rejects_malformed_questions():
    prof = _profile()
    vocab = vocabulary_for(prof)
    base = gen_mcq("How should a prompt specify the desired output format for a parser?", "Prompt Design")
    assert validate_role_question(base, prof, vocab, []).options[0] == "Option alpha is right"
    bad_cases = {
        "answer text disagrees with index": {**base, "correct_answer_text": "Option beta is wrong"},
        "index out of range": {**base, "correct_index": 7},
        "duplicate options": {**base, "options": ["Same", "Same", "Other", "Another"], "correct_answer_text": "Same"},
        "all of the above": {**base, "options": ["One", "Two", "Three", "All of the above"], "correct_index": 3, "correct_answer_text": "All of the above"},
        "company claim": {**base, "prompt": "This was asked at Google in a real interview about prompt design?"},
        "no skill tags": {**base, "skill_tags": []},
        "unknown kind": {**base, "kind": "trivia"},
        "bad difficulty": {**base, "difficulty": "impossible"},
        "irrelevant to role": gen_mcq("What is the boiling point of water at sea level in kelvin?", "Physics", 0, skill_tags=["physics"]),
        "text with one concept group": {"kind": "core", "topic": "Prompt Design", "qtype": "text", "difficulty": "easy",
                                        "prompt": "Explain how few-shot examples help a prompt.", "model_answer": "Examples show the model the pattern to follow in its answer.",
                                        "explanation": "Examples reduce ambiguity in the prompt.", "rubric_keywords": [["examples"]], "skill_tags": ["prompt"]},
        "explanation endorses another option": {**base, "explanation": "The correct choice is Option beta is wrong because it is the better one."},
    }
    for name, raw in bad_cases.items():
        with pytest.raises((ValueError, ValidationError)):
            validate_role_question(raw, prof, vocab, [])
            pytest.fail(f"accepted malformed question: {name}")
    with pytest.raises(ValueError):
        validate_role_question(base, prof, vocab, [base["prompt"]])  # exact duplicate of an existing question
    with pytest.raises(ValueError):
        validate_role_question({**base, "prompt": "How should a prompt specify the desired output format for a parser please?"}, prof, vocab, [base["prompt"]])  # near-duplicate


async def test_text_answers_with_a_provider_use_the_validated_ai_estimate(client):
    s = await ok_start(client, "Prompt Engineer", count=16)
    txt = next(i for i in s["items"] if i["qtype"] == "text" and not i["is_workplace"])
    good = {"correctness": 4, "relevance": 5, "completeness": 4, "structure": 3, "clarity": 3, "strengths": ["Accurate"], "improvements": ["Add an example"]}
    with_ai([good])
    r = await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": txt["id"], "text": "A reasonably detailed answer about the topic with several relevant words."})
    res = r.json()["data"]["item"]["result"]
    assert res["method"] == "ai_estimate" and res["status"] == "correct" and "can be wrong" in res["disclaimer"]
    assert res["got_right"] == ["Accurate"] and res["marks"] == pytest.approx(1.75)
    # invalid AI output is never trusted: it falls back to the rule-based estimate
    txt2 = next(i for i in s["items"] if i["qtype"] == "text" and not i["is_workplace"] and i["id"] != txt["id"])
    with_ai([{"correctness": 99}])
    r2 = await client.post(f"{R}/role-sessions/{s['id']}/answer", json={"item_id": txt2["id"], "text": "Another reasonably detailed answer about the topic with several words."})
    assert r2.json()["data"]["item"]["result"]["method"] == "keyword_estimate"


async def test_session_view_contract_has_the_fields_the_frontend_expects(client):
    s = await ok_start(client, "Prompt Engineer", count=6)
    for key in ("id", "status", "role", "level", "difficulty", "plan", "notices", "total_questions", "answered", "next_position", "items", "scoring_rules", "ai_available"):
        assert key in s, key
    assert {"title", "key", "mapped", "topics"} <= set(s["role"])
    it = s["items"][0]
    assert {"id", "position", "topic", "topic_label", "difficulty", "qtype", "kind", "prompt", "options", "max_marks", "answered", "is_repeat", "source", "review_status", "result"} <= set(it)
    res = (await answer(client, s["id"], it, "correct"))["item"]["result"]
    assert {"status", "status_label", "marks", "max_marks", "explanation", "got_right", "missing", "suggestion", "your_answer"} <= set(res)
    done = await finish(client, s["id"])
    assert {"marks_earned", "marks_available", "percentage", "by_topic", "strong_topics", "weak_topics", "revision", "correct", "partial", "incorrect", "unanswered"} <= set(done["summary"])


async def test_software_flavoured_workplace_questions_are_not_offered_to_other_professions(client):
    import re

    from app.modules.training.role_training import _SOFTWARE_WORDS

    with_ai([{"questions": [
        gen_mcq(f"Which microphone technique number {n} reduces unwanted background noise when recording a single vocalist?", "Recording", 0,
                options=[f"Use a cardioid pattern close to the source {n}", "Record from across the room", "Turn every fader to maximum", "Remove the pop filter"],
                correct_answer_text=f"Use a cardioid pattern close to the source {n}",
                explanation=f"A cardioid pattern close to the source {n} rejects sound from the sides and rear.", skill_tags=["recording"])
        for n in range(1, 9)]}])
    r = await client.post(f"{R}/role-sessions", json={"role_title": "Sound Engineer", "count": 10, "generate": True})
    assert r.status_code == 201, r.text
    work = [i for i in r.json()["data"]["items"] if i["is_workplace"]]
    assert work and not any(_SOFTWARE_WORDS.search(i["prompt"]) for i in work)
    # a software role may still receive them
    sw = await ok_start(client, "Backend Developer", count=30)
    assert any(i["is_workplace"] for i in sw["items"])
    assert re.search(r"api|database", " ".join(i["prompt"] for i in sw["items"]).lower())
