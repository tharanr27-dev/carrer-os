import pytest

from app.modules.training.generation import generate_follow_up, generate_questions, validate_generated
from app.modules.training.llm import LLMUnavailable, extract_json
from app.modules.training.progress import compute_progress, recommend, round_status
from app.modules.training.scoring import evaluate_text, grade_mcq, keyword_eval, self_assessed_code
from app.modules.training.textutils import clean_text, fingerprint, is_near_duplicate

from training_fakes import FakeLLM

GOOD_MCQ = {
    "prompt": "Which keyword defines a function in Python?",
    "options": ["def", "func", "lambda only", "function"],
    "correct_index": 0,
    "explanation": "Python uses the def keyword to define functions.",
}
GOOD_TEXT = {
    "prompt": "Explain what a database index is and one drawback.",
    "model_answer": "An index is a data structure that speeds up lookups at the cost of slower writes and extra storage.",
    "explanation": "Common mistake: forgetting the write cost.",
    "rubric_keywords": [["lookup", "search", "faster"], ["write", "storage", "cost"]],
    "follow_ups": ["When would you not add an index?"],
}


# ── scoring ──────────────────────────────────────────────────────────────────
def test_grade_mcq_exact_match_only():
    assert grade_mcq(2, 2) is True
    assert grade_mcq(2, 1) is False
    assert grade_mcq(2, "2") is False
    assert grade_mcq(1, True) is False


def test_keyword_eval_rewards_coverage_and_is_labelled_estimate():
    rubric = {"keywords": [["mutable"], ["immutable"], ["hash", "dictionary key"]], "framework": None}
    good = keyword_eval(rubric, "Lists are mutable so you can change them. Tuples are immutable and hashable, so they work as a dictionary key.", "ref")
    bad = keyword_eval(rubric, "I think they are different.", "ref")
    empty = keyword_eval(rubric, "", "ref")
    assert good["score"] > bad["score"] > empty["score"] == 0.0
    assert good["method"] == "keyword_estimate" and "not a recruiter" in good["disclaimer"]
    assert bad["improvements"]


def test_star_structure_detected():
    rubric = {"keywords": [], "framework": "STAR"}
    star = "The situation was a tight deadline. My task was to deliver the API. I decided to split the work and I built tests first. As a result we shipped on time and I learned planning."
    plain = "I am hardworking."
    assert keyword_eval(rubric, star, None)["criteria"]["structure"] > keyword_eval(rubric, plain, None)["criteria"]["structure"]


def test_self_assessed_code_never_claims_execution():
    ev = self_assessed_code(2, 3, "sol", "why")
    assert ev["method"] == "self_assessed" and "NOT executed" in ev["disclaimer"]
    assert ev["score"] == pytest.approx(0.667, abs=0.001)
    assert self_assessed_code(99, 3, None, None)["score"] == 1.0
    assert self_assessed_code("x", None, None, None)["self_total"] == 1


async def test_ai_evaluation_valid_malformed_and_unavailable():
    ok = {"correctness": 4, "relevance": 5, "completeness": 3, "structure": 4, "clarity": 4,
          "strengths": ["clear"], "improvements": ["add example"], "stronger_answer": "better"}
    r = await evaluate_text(FakeLLM([ok]), "Q?", "a reasonably long answer for the model to score", None, "ref")
    assert r["method"] == "ai_estimate" and r["score"] == pytest.approx(0.8)
    bad = await evaluate_text(FakeLLM([{"correctness": 99}]), "Q?", "a reasonably long answer for the model to score", None, "ref")
    assert bad["method"] == "keyword_estimate" and "fallback_reason" in bad
    down = await evaluate_text(FakeLLM([LLMUnavailable("timeout")]), "Q?", "a reasonably long answer for the model to score", None, "ref")
    assert down["method"] == "keyword_estimate"
    off = await evaluate_text(FakeLLM(available=False), "Q?", "a reasonably long answer for the model to score", None, "ref")
    assert off["method"] == "keyword_estimate" and "fallback_reason" not in off


# ── generation validation ────────────────────────────────────────────────────
def test_valid_generated_questions_pass():
    assert validate_generated(GOOD_MCQ, "mcq").correct_index == 0
    assert validate_generated(GOOD_TEXT, "text").follow_ups == ["When would you not add an index?"]


@pytest.mark.parametrize("mutation", [
    {"options": ["a", "b", "c"]},                       # too few options
    {"options": ["same", "same", "x", "y"]},            # duplicates
    {"correct_index": 7},                               # out of range
    {"correct_index": None},                            # missing
    {"prompt": "short"},                                # too short
    {"explanation": ""},                                # no explanation
    {"prompt": "This was asked at Google in a real interview: what is a stack?"},   # company claim
])
def test_malformed_generated_mcq_rejected(mutation):
    with pytest.raises(ValueError):  # pydantic ValidationError is a ValueError
        validate_generated({**GOOD_MCQ, **mutation}, "mcq")


def test_text_question_requires_model_answer():
    with pytest.raises(ValueError):  # pydantic ValidationError is a ValueError
        validate_generated({**GOOD_TEXT, "model_answer": "too short"}, "text")


def test_generated_text_is_sanitised():
    q = validate_generated({**GOOD_MCQ, "prompt": "Which <script>alert(1)</script>keyword defines a function in Python?"}, "mcq")
    assert "<" not in q.prompt and "script" not in q.prompt.replace("alert(1)", "")


async def test_generate_questions_filters_invalid_and_duplicates():
    existing = ["Which keyword defines a function in Python?"]
    llm = FakeLLM([{"questions": [GOOD_MCQ, {"prompt": "bad"}, {**GOOD_MCQ, "prompt": "Which keyword defines a function in the Python language?"},
                                  {**GOOD_MCQ, "prompt": "Which statement ends a loop early in Python?",
                                   "options": ["break", "stop", "exit", "halt"], "explanation": "break leaves the loop immediately."}]}])
    out = await generate_questions(llm, "technical", "python", "easy", "mcq", 3, existing_prompts=existing)
    prompts = [q["prompt"] for q in out]
    assert prompts == ["Which statement ends a loop early in Python?"]  # exact + near duplicate + malformed dropped
    assert out[0]["source"] == "generated" and out[0]["review_status"] == "unreviewed"
    assert "Google" not in llm.calls[0]["user"]


async def test_generate_questions_bad_structure_and_outage():
    with pytest.raises(LLMUnavailable):
        await generate_questions(FakeLLM([{"unexpected": 1}]), "technical", "python", "easy", "mcq", 2)
    with pytest.raises(LLMUnavailable):
        await generate_questions(FakeLLM([LLMUnavailable("down")]), "technical", "python", "easy", "mcq", 2)
    assert await generate_questions(FakeLLM([{"questions": [{"prompt": "x"}]}]), "technical", "python", "easy", "mcq", 2) == []


async def test_follow_up_validation():
    assert await generate_follow_up(FakeLLM([{"follow_up": "Why did you pick that index type?"}]), "Q", "A") == "Why did you pick that index type?"
    assert await generate_follow_up(FakeLLM([{"follow_up": "ok"}]), "Q", "A") is None
    assert await generate_follow_up(FakeLLM([LLMUnavailable("x")]), "Q", "A") is None


def test_text_helpers():
    assert fingerprint("What is a Stack?") == fingerprint("what is a stack")
    assert is_near_duplicate("Explain the difference between a list and a tuple in Python", ["What is the difference between a list and tuple in python?"])
    assert not is_near_duplicate("Explain closures", ["What is a deadlock?"])
    assert clean_text("<b>hi</b>\x00 there") == "hi there"
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": [1, 2]} done') == {"a": [1, 2]}


# ── progress engine ──────────────────────────────────────────────────────────
def _item(round_, topic, score, kind="objective", diff="medium"):
    return {"round": round_, "topic": topic, "difficulty": diff, "score": score, "score_kind": kind,
            "time_taken_sec": 20, "answered_at": "2026-01-01T00:00:00+00:00"}


def test_no_data_reports_no_fake_progress():
    p = compute_progress([], [])
    assert p["overall_pct"] is None
    assert all(r["status"] == "not_started" and r["combined_pct"] is None for r in p["rounds"].values())
    assert p["weakest_topics"] == [] and p["trend"] == [] and p["completion_rate"] is None
    assert p["recommendations"][0]["rule"] == "no_activity"


def test_weak_topic_needs_minimum_samples_and_drives_recommendation():
    few = [_item("technical", "sql", 0.0), _item("technical", "sql", 0.0)]
    assert compute_progress(few, [])["weakest_topics"] == []
    rows = [_item("technical", "sql", 0.0)] * 3 + [_item("technical", "python", 1.0)] * 4
    p = compute_progress(rows, [])
    assert [t["topic"] for t in p["weakest_topics"]] == ["sql"]
    rec = p["recommendations"][0]
    assert rec["rule"] == "weak_topic" and rec["action"]["topic"] == "sql" and rec["action"]["difficulty"] == "easy"


def test_round_status_thresholds():
    assert round_status(0, None) == "not_started"
    assert round_status(5, 90.0) == "in_progress"
    assert round_status(10, 55.0) == "needs_work"
    assert round_status(10, 65.0) == "on_track"
    assert round_status(10, 80.0) == "strong"


def test_strong_aptitude_weak_communication_rule():
    rows = [_item("aptitude", "percentages", 1.0)] * 12 + [_item("communication", "self-introduction", 0.2, "keyword_estimate")] * 3
    rules = [r["rule"] for r in compute_progress(rows, [])["recommendations"]]
    assert "strong_aptitude_weak_communication" in rules


def test_project_interview_recommended_only_with_projects():
    rows = [_item("aptitude", "percentages", 0.7)] * 12
    assert "project_interview" in [r["rule"] for r in compute_progress(rows, [], has_projects=True)["recommendations"]]
    assert "project_interview" not in [r["rule"] for r in recommend(compute_progress(rows, [])["rounds"], [], False, 12)]


def test_trend_and_improvement_come_from_completed_attempts():
    attempts = [{"id": str(i), "status": "COMPLETED", "round": "aptitude", "topic": None, "ended_at": f"2026-01-{i + 1:02d}",
                 "summary": {"overall_pct": 40 + i * 5}} for i in reversed(range(6))]
    p = compute_progress([_item("aptitude", "x", 1.0)], attempts)
    assert [t["overall_pct"] for t in p["trend"]] == [40, 45, 50, 55, 60, 65]
    assert p["improvement_pct_points"] == pytest.approx(15.0)
    assert p["completion_rate"] == 100.0
