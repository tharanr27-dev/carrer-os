"""Progress, roadmap and next-step recommendations computed ONLY from the student's saved attempts.

No row, no number: a round with no scored answers reports `not_started` and `None` scores.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.modules.training.bank.catalog import ROUNDS, TOPIC_INDEX

STAGE_ORDER = sorted(ROUNDS.keys(), key=lambda r: ROUNDS[r]["stage"])
MIN_FOR_ON_TRACK = 10  # scored answers needed in a round before it can count as "on track"
MIN_FOR_WEAK_TOPIC = 3  # scored answers needed before a topic can be called weak
WEAK_BELOW = 0.60
STRONG_AT = 0.75

SCORING_RULES = [
    "Aptitude and MCQ scores are objective: the percentage of questions answered correctly.",
    "Written answers (technical, HR, communication, resume, managerial) get an ESTIMATE: an AI rubric score when an AI provider is configured, otherwise a rule-based keyword and structure check. Estimates are guidance, not a recruiter's decision.",
    "Coding scores are SELF-ASSESSED against listed test cases. Code is not executed on this platform.",
    f"A round is 'on track' at {int(WEAK_BELOW * 100)}% and 'strong' at {int(STRONG_AT * 100)}% once you have at least {MIN_FOR_ON_TRACK} scored answers in it.",
    f"A topic is flagged weak only after {MIN_FOR_WEAK_TOPIC} scored answers with an average below {int(WEAK_BELOW * 100)}%.",
    "Recommendations are rule-based on your saved attempts. They are not predictions of interview results.",
]


def _pct(values: List[float]) -> Optional[float]:
    return round(100 * sum(values) / len(values), 1) if values else None


def round_status(attempted: int, combined: Optional[float]) -> str:
    if attempted == 0 or combined is None:
        return "not_started"
    if attempted < MIN_FOR_ON_TRACK:
        return "in_progress"
    if combined < WEAK_BELOW * 100:
        return "needs_work"
    return "strong" if combined >= STRONG_AT * 100 else "on_track"


def topic_label(round_: str, topic: str) -> str:
    return TOPIC_INDEX.get(f"{round_}:{topic}", {}).get("label", topic)


def compute_progress(items: List[Dict[str, Any]], attempts: List[Dict[str, Any]], has_projects: bool = False) -> Dict[str, Any]:
    """items: scored answered items; attempts: all attempts (newest first)."""
    by_round: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_topic: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for it in items:
        by_round[it["round"]].append(it)
        by_topic[(it["round"], it["topic"])].append(it)

    rounds: Dict[str, Any] = {}
    for r in STAGE_ORDER:
        rows = by_round.get(r, [])
        obj = [x["score"] for x in rows if x["score_kind"] == "objective"]
        est = [x["score"] for x in rows if x["score_kind"] in ("ai_estimate", "keyword_estimate")]
        self_ = [x["score"] for x in rows if x["score_kind"] == "self_assessed"]
        combined = _pct([x["score"] for x in rows])
        times = [x["time_taken_sec"] for x in rows if x.get("time_taken_sec")]
        rounds[r] = {
            "label": ROUNDS[r]["label"],
            "stage": ROUNDS[r]["stage"],
            "attempted": len(rows),
            "objective_pct": _pct(obj),
            "estimated_pct": _pct(est),
            "self_assessed_pct": _pct(self_),
            "combined_pct": combined,
            "avg_time_sec": round(sum(times) / len(times), 1) if times else None,
            "status": round_status(len(rows), combined),
            "last_practised": max((x["answered_at"] for x in rows if x.get("answered_at")), default=None),
        }

    topic_stats = []
    for (r, t), rows in by_topic.items():
        topic_stats.append(
            {"round": r, "topic": t, "label": topic_label(r, t), "attempted": len(rows),
             "score_pct": _pct([x["score"] for x in rows]),
             "difficulty_mix": dict(_count([x["difficulty"] for x in rows]))}
        )
    weak = sorted(
        [t for t in topic_stats if t["attempted"] >= MIN_FOR_WEAK_TOPIC and t["score_pct"] < WEAK_BELOW * 100],
        key=lambda t: t["score_pct"],
    )[:5]
    strong = sorted(
        [t for t in topic_stats if t["attempted"] >= MIN_FOR_WEAK_TOPIC and t["score_pct"] >= STRONG_AT * 100],
        key=lambda t: -t["score_pct"],
    )[:5]

    done = [a for a in attempts if a["status"] == "COMPLETED"]
    completion_rate = round(100 * len(done) / len(attempts), 1) if attempts else None
    trend = [
        {"attempt_id": a["id"], "date": a["ended_at"], "round": a["round"], "topic": a.get("topic"),
         "overall_pct": (a.get("summary") or {}).get("overall_pct")}
        for a in reversed(done)
        if (a.get("summary") or {}).get("overall_pct") is not None
    ][-12:]
    improvement = None
    if len(trend) >= 6:
        first = sum(t["overall_pct"] for t in trend[:3]) / 3
        last = sum(t["overall_pct"] for t in trend[-3:]) / 3
        improvement = round(last - first, 1)

    started = [r for r in STAGE_ORDER if rounds[r]["status"] != "not_started"]
    overall = _pct([rounds[r]["combined_pct"] / 100 for r in started]) if started else None
    stage = next((r for r in STAGE_ORDER if rounds[r]["status"] in ("not_started", "in_progress", "needs_work")), None)
    current_stage = (
        {"round": stage, "label": ROUNDS[stage]["label"], "status": rounds[stage]["status"]}
        if stage
        else {"round": "mock", "label": "Final readiness review (full mock interview)", "status": "ready_for_review"}
    )

    return {
        "overall_pct": overall,
        "total_scored_answers": len(items),
        "rounds": rounds,
        "current_stage": current_stage,
        "weakest_topics": weak,
        "strongest_topics": strong,
        "completion_rate": completion_rate,
        "attempts_total": len(attempts),
        "attempts_completed": len(done),
        "trend": trend,
        "improvement_pct_points": improvement,
        "recent_attempts": attempts[:5],
        "recommendations": recommend(rounds, weak, has_projects, len(items)),
        "scoring_rules": SCORING_RULES,
    }


def _count(values):
    out: Dict[str, int] = defaultdict(int)
    for v in values:
        out[v] += 1
    return out


def _difficulty_for(score_pct: Optional[float]) -> str:
    if score_pct is None or score_pct < 45:
        return "easy"
    return "medium" if score_pct < 75 else "hard"


def recommend(rounds: Dict[str, Any], weak: List[Dict[str, Any]], has_projects: bool, total: int) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if total == 0:
        return [{
            "rule": "no_activity",
            "title": "Start with an aptitude warm-up",
            "reason": "You have no saved practice yet. A mixed aptitude set shows where to focus.",
            "action": {"type": "practice", "round": "aptitude", "topic": None, "difficulty": "easy", "mode": "practice"},
        }]
    for t in weak[:2]:
        recs.append({
            "rule": "weak_topic",
            "title": f"Strengthen {t['label']}",
            "reason": f"Your average on {t['label']} is {t['score_pct']}% over {t['attempted']} answers (below {int(WEAK_BELOW * 100)}%).",
            "action": {"type": "practice", "round": t["round"], "topic": t["topic"],
                       "difficulty": _difficulty_for(t["score_pct"]), "mode": "practice"},
        })
    apt, com, hr, cod = rounds["aptitude"], rounds["communication"], rounds["hr"], rounds["coding"]
    soft_est = [x for x in (com["combined_pct"], hr["combined_pct"]) if x is not None]
    if apt["combined_pct"] is not None and apt["combined_pct"] >= STRONG_AT * 100 and (
        not soft_est or min(soft_est) < WEAK_BELOW * 100
    ):
        recs.append({
            "rule": "strong_aptitude_weak_communication",
            "title": "Practise structured spoken-style answers",
            "reason": "Your aptitude is strong, but communication or HR answers are weak or untried. STAR-structured answers are the quickest improvement.",
            "action": {"type": "practice", "round": "hr", "topic": "behavioural", "difficulty": "medium", "mode": "practice"},
        })
    if cod["status"] in ("not_started", "in_progress") or (cod["combined_pct"] is not None and cod["combined_pct"] < WEAK_BELOW * 100):
        recs.append({
            "rule": "coding_practice",
            "title": "Build problem-solving patterns",
            "reason": "Coding practice is limited or below target. Work through one pattern at a time (arrays, hashing, then recursion).",
            "action": {"type": "practice", "round": "coding", "topic": "arrays-strings", "difficulty": "easy", "mode": "practice"},
        })
    if has_projects and rounds["resume"]["status"] == "not_started":
        recs.append({
            "rule": "project_interview",
            "title": "Rehearse explaining your projects",
            "reason": "You have projects on your profile but no project-interview practice yet.",
            "action": {"type": "practice", "round": "resume", "topic": "resume-project", "difficulty": None, "mode": "practice"},
        })
    ready = all(rounds[r]["status"] in ("on_track", "strong") for r in ("aptitude", "technical", "hr"))
    if ready:
        recs.append({
            "rule": "ready_for_mock",
            "title": "Take a full mock interview",
            "reason": "Your core rounds are on track. A timed multi-round simulation tests them together.",
            "action": {"type": "mock"},
        })
    if not recs:
        nxt = next((r for r in STAGE_ORDER if rounds[r]["status"] in ("not_started", "in_progress")), "technical")
        recs.append({
            "rule": "next_stage",
            "title": f"Continue with {ROUNDS[nxt]['label']}",
            "reason": "This is the next round in your roadmap with the least practice so far.",
            "action": {"type": "practice", "round": nxt, "topic": None, "difficulty": "medium", "mode": "practice"},
        })
    return recs[:3]
