"""Universal role-based training: any job title, fresh questions, instant evaluation, trustworthy review.

Reuses the existing question bank, attempt/item tables, de-duplication ("seen" map), scoring helpers and optional LLM
client; no schema changes are required. A role session is a TrainingAttempt with mode="role" whose `config` stores the
role, the plan and the notices. All marks are computed here from persisted evaluations, never from client input.

Scoring rules (also returned to the client):
  * MCQ = 1 mark, written answer = 2 marks. Partial credit is awarded in quarter marks.
  * Written answers: status Correct at score >= 0.75, Partially Correct at >= 0.34, otherwise Incorrect.
  * An unanswered question earns 0 and stays in the total. A question that cannot be evaluated reliably is marked
    "Needs Manual Review", earns nothing and is excluded from the total (it is shown, not silently scored).
"""

import logging
import random
import re
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException
from sqlalchemy import func, select

from app.modules.training.bank.catalog import DIFFICULTIES, TOPIC_INDEX
from app.modules.training.llm import LLMUnavailable
from app.modules.training.models import TrainingAttempt, TrainingAttemptItem, TrainingProfile, TrainingQuestion
from app.modules.training.progress import STRONG_AT, WEAK_BELOW
from app.modules.training.role_generation import MAX_GENERATED_PER_CALL, generate_role_questions
from app.modules.training.roles import (
    InvalidRole,
    RoleProfile,
    resolve_role,
    search_roles,
    topic_label_for,
)
from app.modules.training.schemas import RoleAgain, RoleAnswer, RoleSessionCreate
from app.modules.training.scoring import evaluate_text, grade_mcq
from app.modules.training.seed import ensure_seed
from app.modules.training.service import (
    GENERATED_HOURLY_CAP,
    GENERATED_TOTAL_CAP,
    TrainingService,
    _iso,
    _not_found,
    _now,
)
from app.modules.training.textutils import clean_text

logger = logging.getLogger("careeros")

MAX_MARKS = {"mcq": 1.0, "text": 2.0}
CORRECT_AT = 0.75
PARTIAL_AT = 0.34
WORKPLACE_ROUNDS = ("hr", "communication", "managerial")
TECH_FAMILIES = {"Software", "Data & AI", "Cloud & Security"}
# Workplace questions that assume a software job are not offered to other professions.
_SOFTWARE_WORDS = re.compile(
    r"(api|database|spreadsheet|bug|production|code|coding|postgresql|mongodb|technical|system|software|feature)", re.IGNORECASE)
LEVEL_BASE_DIFFICULTY = {"fresher": 0, "junior": 1, "mid": 1}
STATUS_LABEL = {
    "correct": "Correct",
    "partial": "Partially Correct",
    "incorrect": "Incorrect",
    "manual_review": "Needs Manual Review",
    "unanswered": "Unanswered",
}
SCORING_RULES = [
    "Multiple-choice questions are worth 1 mark and are graded on the server by exact comparison with the answer key.",
    "Written answers are worth 2 marks. They are scored against the expected concepts: Correct at 75% or more of the available credit, "
    "Partially Correct from 34%, otherwise Incorrect. Partial credit is awarded in quarter marks.",
    "Unanswered questions earn 0 marks and are included in the total, so skipping lowers your percentage.",
    "A question that cannot be evaluated reliably is marked 'Needs Manual Review'. It earns no marks and is left out of the total; compare your answer with the model answer yourself.",
    f"Strong topics score {int(STRONG_AT * 100)}% or more; weak topics score below {int(WEAK_BELOW * 100)}%. "
    "Scores are practice feedback, not a prediction of any real interview result.",
]


def _round_quarter(x: float) -> float:
    return round(x * 4) / 4


def _first_sentence(text: Optional[str], limit: int = 170) -> str:
    s = clean_text(text or "", 600)
    for sep in (". ", "\n"):
        if sep in s:
            s = s.split(sep)[0]
            break
    return s[:limit].rstrip(". ") + "." if s else ""


def _concept_label(group: List[str]) -> str:
    return (group[0] if group else "").strip().capitalize()


class RoleTrainingService(TrainingService):
    def __init__(self, db, llm=None, rng: Optional[random.Random] = None):
        super().__init__(db, llm)
        self.rng = rng or random.Random()

    # ── role discovery ───────────────────────────────────────────────────────

    async def _topic_counts(self, user_id: uuid.UUID) -> Dict[str, int]:
        rows = (await self.db.execute(
            select(TrainingQuestion.topic, func.count()).where(
                TrainingQuestion.round == "technical", TrainingQuestion.deleted_at.is_(None),
                TrainingQuestion.source == "curated", TrainingQuestion.qtype.in_(("mcq", "text")),
            ).group_by(TrainingQuestion.topic)
        )).all()
        return {t: c for t, c in rows}

    async def list_roles(self, user_id: uuid.UUID, q: str, limit: int) -> Dict[str, Any]:
        await ensure_seed(self.db)
        counts = await self._topic_counts(user_id)
        found = search_roles(q, limit)
        roles = [{
            "title": e["title"], "family": e["family"], "aliases": e.get("aliases", []),
            "topics": [{"slug": d, "label": topic_label_for(d)} for d in e["domains"]],
            "available_questions": sum(counts.get(d, 0) for d in e["domains"]),
        } for e in found]
        qn = (q or "").strip().lower()
        exact = any(r["title"].lower() == qn or qn in (a.lower() for a in r["aliases"]) for r in roles)
        return {"roles": roles, "query": q or "", "exact_match": exact,
                "custom_allowed": True, "recent": await self._recent_roles(user_id), "ai_available": self.ai_available}

    async def _recent_roles(self, user_id: uuid.UUID, limit: int = 5) -> List[Dict[str, Any]]:
        rows = (await self.db.execute(
            select(TrainingAttempt).where(TrainingAttempt.user_id == user_id, TrainingAttempt.mode == "role",
                                          TrainingAttempt.deleted_at.is_(None)).order_by(TrainingAttempt.started_at.desc()).limit(40)
        )).scalars().all()
        seen, out = set(), []
        for a in rows:
            cfg = a.config or {}
            key = cfg.get("role_key")
            if key and key not in seen:
                seen.add(key)
                out.append({"title": cfg.get("role_title"), "key": key})
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _profile_or_422(title: str) -> RoleProfile:
        try:
            return resolve_role(title)
        except InvalidRole as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    async def resolve(self, user_id: uuid.UUID, title: str) -> Dict[str, Any]:
        await ensure_seed(self.db)
        prof = self._profile_or_422(title)
        counts = await self._topic_counts(user_id)
        seen = await self._seen_map(user_id)
        pool = await self._candidates(user_id, prof, None)
        domain_pool = [q for q in pool if q.round == "technical"]
        unseen = [q for q in domain_pool if q.id not in seen]
        available = len(domain_pool)
        if available == 0 and not self.ai_available:
            msg = ("There are no reviewed questions for this job title yet and AI question generation is not configured, "
                   "so a role-specific session cannot be built. Pick a related role from the list instead.")
        elif available < 8 and not self.ai_available:
            msg = f"Only {available} reviewed questions match this role and AI generation is off, so sessions will be short and may repeat."
        elif available < 8:
            msg = "Few reviewed questions match this role; the rest of each session will be generated by AI and marked as unreviewed."
        else:
            msg = None
        return {
            "title": prof.title, "key": prof.key, "match": prof.match, "matched_title": prof.matched_title,
            "family": prof.family, "mapped": prof.mapped, "level_hint": prof.level_hint, "notes": prof.notes,
            "topics": [{"slug": d, "label": topic_label_for(d), "available": counts.get(d, 0)} for d in prof.domains],
            "available_questions": available, "unseen_questions": len(unseen),
            "ai_available": self.ai_available,
            "can_start": available > 0 or self.ai_available,
            "message": msg,
        }

    # ── candidate pools ──────────────────────────────────────────────────────

    @staticmethod
    def _compatible(q: TrainingQuestion, prof: RoleProfile) -> bool:
        if not q.roles:
            return True
        allowed = {prof.key, prof.title, prof.matched_title}
        return bool(allowed & set(q.roles))

    async def _candidates(self, user_id: uuid.UUID, prof: RoleProfile, topics: Optional[List[str]]) -> List[TrainingQuestion]:
        stmt = select(TrainingQuestion).where(
            TrainingQuestion.deleted_at.is_(None), TrainingQuestion.source != "resume_template",
            TrainingQuestion.qtype.in_(("mcq", "text")),
            (TrainingQuestion.owner_user_id.is_(None)) | (TrainingQuestion.owner_user_id == user_id),
            TrainingQuestion.round == "technical",
        )
        rows = (await self.db.execute(stmt.limit(2500))).scalars().all()
        allowed = set(topics) if topics else set(prof.domains)
        out = []
        for q in rows:
            if q.roles and prof.key in q.roles:  # generated earlier for exactly this role
                if not topics or q.topic in allowed:
                    out.append(q)
            elif q.topic in allowed and self._compatible(q, prof):
                out.append(q)
        return out

    async def _workplace_pool(self, user_id: uuid.UUID, prof: RoleProfile, level: str) -> List[TrainingQuestion]:
        rows = (await self.db.execute(select(TrainingQuestion).where(
            TrainingQuestion.deleted_at.is_(None), TrainingQuestion.round.in_(WORKPLACE_ROUNDS), TrainingQuestion.qtype == "text",
            TrainingQuestion.source != "resume_template",
            (TrainingQuestion.owner_user_id.is_(None)) | (TrainingQuestion.owner_user_id == user_id)).limit(800))).scalars().all()
        tech_role = prof.family in TECH_FAMILIES or (prof.match == "keywords" and prof.mapped)
        return [q for q in rows if self._compatible(q, prof) and (level == "fresher" or q.topic != "fresher")
                and (tech_role or not _SOFTWARE_WORDS.search(q.prompt))]

    # ── history ──────────────────────────────────────────────────────────────

    async def _role_attempts(self, user_id: uuid.UUID, key: str, limit: int = 60) -> List[TrainingAttempt]:
        rows = (await self.db.execute(
            select(TrainingAttempt).where(TrainingAttempt.user_id == user_id, TrainingAttempt.mode == "role",
                                          TrainingAttempt.deleted_at.is_(None)).order_by(TrainingAttempt.started_at.desc()).limit(limit)
        )).scalars().all()
        return [a for a in rows if (a.config or {}).get("role_key") == key]

    @staticmethod
    def _topic_stats(attempts: List[TrainingAttempt]) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for a in attempts:
            for it in a.items:
                if it.parent_item_id is None and it.score is not None:
                    s = stats.setdefault(it.topic, {"sum": 0.0, "n": 0})
                    s["sum"] += it.score
                    s["n"] += 1
        for s in stats.values():
            s["avg"] = s["sum"] / s["n"]
        return stats

    def _target_difficulty(self, requested: Optional[str], level: str, attempts: List[TrainingAttempt], notes: List[str]) -> str:
        if requested:
            return requested
        base = LEVEL_BASE_DIFFICULTY.get(level, 0)
        recent = sorted((i for a in attempts for i in a.items if i.parent_item_id is None and i.score is not None and i.answered_at),
                        key=lambda i: i.answered_at)[-8:]
        idx = base
        if len(recent) >= 5:
            avg = sum(i.score for i in recent) / len(recent)
            if avg >= 0.8:
                idx = min(base + 1, 2)
                notes.append(f"Difficulty raised to {DIFFICULTIES[idx]} because you scored {round(avg * 100)}% on your last {len(recent)} answers for this role.")
            elif avg <= 0.4:
                idx = max(base - 1, 0)
                notes.append(f"Difficulty lowered to {DIFFICULTIES[idx]} because you scored {round(avg * 100)}% on your last {len(recent)} answers for this role.")
        return DIFFICULTIES[idx]

    async def _generation_allowed(self, user_id: uuid.UUID) -> Optional[str]:
        base = select(func.count()).select_from(TrainingQuestion).where(
            TrainingQuestion.owner_user_id == user_id, TrainingQuestion.source == "generated")
        total = (await self.db.execute(base)).scalar_one()
        recent = (await self.db.execute(base.where(TrainingQuestion.created_at >= _now() - timedelta(hours=1)))).scalar_one()
        if total >= GENERATED_TOTAL_CAP or recent >= GENERATED_HOURLY_CAP:
            return "You have reached the AI generation limit for now, so stored questions are used."
        return None

    # ── selection ────────────────────────────────────────────────────────────

    def _pick(self, pool: List[TrainingQuestion], n: int, seen: Dict[uuid.UUID, Any], weights: Dict[str, float],
              target: int, used: Set[uuid.UUID]) -> List[TrainingQuestion]:
        """Weighted round-robin over topics. Within a topic: unseen first, then the longest-ago seen; closest difficulty;
        and a preference for question kinds not yet used in this session."""
        by_topic: Dict[str, List[TrainingQuestion]] = {}
        for q in pool:
            if q.id not in used:
                by_topic.setdefault(q.topic, []).append(q)

        def key(q: TrainingQuestion):
            diff = abs((DIFFICULTIES.index(q.difficulty) if q.difficulty in DIFFICULTIES else 1) - target)
            return (0 if q.id not in seen else 1, seen.get(q.id) or 0, diff, self.rng.random())

        for lst in by_topic.values():
            lst.sort(key=key)
        kinds: Dict[str, int] = {}
        chosen: List[TrainingQuestion] = []
        while len(chosen) < n and by_topic:
            topics = list(by_topic)
            # Never repeat a seen question while some other topic still has an unseen one (lists are sorted unseen-first).
            topics = [x for x in topics if by_topic[x][0].id not in seen] or topics
            t = self.rng.choices(topics, weights=[max(weights.get(x, 1.0), 0.05) for x in topics])[0]
            head = by_topic[t][:4]
            q = min(head, key=lambda c: (0 if c.id not in seen else 1, kinds.get(c.label or "", 0)))
            by_topic[t].remove(q)
            if not by_topic[t]:
                del by_topic[t]
            kinds[q.label or ""] = kinds.get(q.label or "", 0) + 1
            chosen.append(q)
            used.add(q.id)
        return chosen

    async def start_session(self, user_id: uuid.UUID, req: RoleSessionCreate, *, previous: Optional[TrainingAttempt] = None) -> Dict[str, Any]:
        await ensure_seed(self.db)
        prof = self._profile_or_422(req.role_title)
        tprof = (await self.db.execute(select(TrainingProfile).where(TrainingProfile.user_id == user_id))).scalar_one_or_none()
        level = req.level or prof.level_hint or (tprof.level if tprof else None) or "fresher"
        notes: List[str] = list(prof.notes)
        notices: List[str] = []

        slugs = [t for t in req.topics if f"technical:{t}" in TOPIC_INDEX]
        hints = [clean_text(t, 40) for t in req.topics if f"technical:{t}" not in TOPIC_INDEX and clean_text(t, 40)][:4]

        attempts = await self._role_attempts(user_id, prof.key)
        stats = self._topic_stats(attempts)
        seen = await self._seen_map(user_id)
        target_name = self._target_difficulty(req.difficulty, level, attempts, notes)
        target = DIFFICULTIES.index(target_name)

        pool = await self._candidates(user_id, prof, slugs or None)
        focus = req.focus
        weak_topics = sorted([t for t, s in stats.items() if s["avg"] < CORRECT_AT], key=lambda t: stats[t]["avg"])
        if focus == "weak":
            if weak_topics:
                focused = [q for q in pool if q.topic in weak_topics]
                if focused:
                    pool = focused
                notes.append("Improve Weak Areas: questions focus on " + ", ".join(self._label(t) for t in weak_topics[:4]) + ".")
            else:
                focus = "mixed"
                notices.append("No weak topics are recorded for this role yet, so this is a mixed session.")

        n_work = 0 if (focus == "weak" or req.count < 5) else min(4, round(req.count * 0.2))
        work_pool = await self._workplace_pool(user_id, prof, level) if n_work else []
        n_domain = req.count - (n_work if work_pool else 0)

        # Fill a shortfall of UNSEEN questions with validated AI generation (one call, only for the gap).
        unseen_domain = sum(1 for q in pool if q.id not in seen)
        generated: List[TrainingQuestion] = []
        gen_info = {"requested": 0, "accepted": 0, "rejected": 0, "used": False}
        if unseen_domain < n_domain:
            if not req.generate:
                notices.append("AI generation was turned off for this session, so only stored questions are used.")
            elif not self.ai_available:
                notices.append("AI question generation is not configured, so this session uses stored reviewed questions only.")
            else:
                blocked = await self._generation_allowed(user_id)
                if blocked:
                    notices.append(blocked)
                else:
                    want = min(n_domain - unseen_domain, MAX_GENERATED_PER_CALL)
                    existing = [q.prompt for q in pool][:200]
                    gen_hints = hints + [self._label(t) for t in weak_topics[:2]]
                    try:
                        res = await generate_role_questions(self.llm, prof, level, target_name, want, existing, gen_hints)
                        gen_info = {"requested": want, "accepted": len(res["questions"]), "rejected": res["rejected"], "used": True}
                        for g in res["questions"]:
                            row = TrainingQuestion(**g, owner_user_id=user_id)
                            self.db.add(row)
                            generated.append(row)
                        await self.db.flush()
                        if res["rejected"]:
                            notices.append(f"{res['rejected']} AI-generated question(s) failed validation and were discarded.")
                        if not res["questions"]:
                            notices.append("The AI output did not pass validation, so stored questions are used.")
                    except LLMUnavailable:
                        notices.append("AI generation is temporarily unavailable, so stored questions are used.")
        pool = pool + generated

        weights: Dict[str, float] = {}
        for t in {q.topic for q in pool}:
            s = stats.get(t)
            if not s:
                weights[t] = 1.5  # never practised for this role: raise priority
            elif s["n"] >= 2 and s["avg"] < WEAK_BELOW:
                weights[t] = 1.0 + 3.0 * (1.0 - s["avg"])
            elif s["n"] >= 4 and s["avg"] >= 0.85:
                weights[t] = 0.5
            else:
                weights[t] = 1.0
        if slugs and not weak_topics:
            weights = {t: 1.0 for t in weights}

        used: Set[uuid.UUID] = set()
        chosen = self._pick(pool, n_domain, seen, weights, target, used)
        chosen.sort(key=lambda q: DIFFICULTIES.index(q.difficulty) if q.difficulty in DIFFICULTIES else 1)
        work = self._pick(work_pool, n_work, seen, {}, target, used) if (n_work and work_pool) else []
        questions = chosen + work

        if not chosen:
            raise HTTPException(status_code=422, detail=(
                f"No role-specific questions are available for '{prof.title}' right now. "
                + ("AI generation could not provide valid questions. Try again or choose a related role." if self.ai_available
                   else "There are no reviewed questions for this job title and AI question generation is not configured. "
                        "Pick a related role from the list, or ask an administrator to enable an AI provider.")))
        repeats = [q for q in questions if q.id in seen]
        fresh = len(questions) - len(repeats)
        if len(questions) < req.count:
            notices.append(f"Only {len(questions)} of the {req.count} requested questions are available for this role right now.")
        if repeats:
            notices.append(f"{len(repeats)} question(s) repeat earlier practice on purpose: the stored bank for this role has no more unseen questions"
                           + ("" if self.ai_available else " and AI generation is not configured") + ". They are marked 'Seen before'.")
        if generated:
            notices.append(f"{sum(1 for q in questions if q.source == 'generated')} question(s) were generated by AI and are marked 'Unreviewed': answer keys are validated but not guaranteed correct.")

        allocation: Dict[str, int] = {}
        for q in chosen:
            allocation[q.topic] = allocation.get(q.topic, 0) + 1
        alloc_view = []
        for t, c in sorted(allocation.items(), key=lambda kv: -kv[1]):
            s = stats.get(t)
            reason = ("not practised for this role yet" if not s or not s.get("n")
                      else f"weak so far ({round(s['avg'] * 100)}%)" if s["avg"] < WEAK_BELOW
                      else f"strong so far ({round(s['avg'] * 100)}%), kept light" if weights.get(t, 1) < 1 else "balanced practice")
            alloc_view.append({"topic": t, "label": self._label(t), "count": c, "reason": reason})
        if work:
            notes.append(f"{len(work)} workplace/communication question(s) were added because they matter for any role.")
        notes.append(f"{fresh} of {len(questions)} questions are new to you" + (f"; {len(repeats)} are repeats." if repeats else "."))

        att = TrainingAttempt(
            user_id=user_id, mode="role", round="role", topic=None, difficulty=target_name, status="IN_PROGRESS", started_at=_now(),
            config={
                "role_title": prof.title, "role_key": prof.key, "role_match": prof.match, "matched_title": prof.matched_title,
                "mapped": prof.mapped, "domains": prof.domains, "level": level,
                "requested": {"difficulty": req.difficulty, "topics": req.topics, "count": req.count, "focus": req.focus, "generate": req.generate},
                "focus": focus, "planned_count": len(questions), "notices": notices,
                "plan": {"notes": notes, "allocation": alloc_view, "fresh": fresh, "repeats": len(repeats),
                         "workplace": len(work), "generation": gen_info},
                "repeat_question_ids": [str(q.id) for q in repeats],
                "previous_session_id": str(previous.id) if previous else None,
            },
        )
        self.db.add(att)
        await self.db.flush()
        for i, q in enumerate(questions, start=1):
            self.db.add(self._new_item(att.id, user_id, i, q))
        await self.db.commit()
        return await self.session_view(user_id, att.id)

    @staticmethod
    def _label(topic: str) -> str:
        return TOPIC_INDEX.get(f"technical:{topic}", {}).get("label") or topic_label_for(topic)

    # ── views ────────────────────────────────────────────────────────────────

    async def _get_role_attempt(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> TrainingAttempt:
        att = await self._get_attempt(user_id, attempt_id)
        if att.mode != "role":
            raise _not_found("Role session")
        await self.db.refresh(att, attribute_names=["items"])
        return att

    def _topic_name(self, item: TrainingAttemptItem) -> str:
        q = item.question
        return TOPIC_INDEX.get(f"{item.round}:{item.topic}", {}).get("label") or (q.category if q and q.category else None) or topic_label_for(item.topic)

    def _result_view(self, q: TrainingQuestion, item: TrainingAttemptItem, answered: bool) -> Dict[str, Any]:
        ev = item.evaluation or {}
        status_ = ev.get("status") if answered else "unanswered"
        res: Dict[str, Any] = {
            "status": status_, "status_label": STATUS_LABEL.get(status_ or "", status_),
            "marks": (ev.get("marks") if answered else (0.0 if q.qtype in MAX_MARKS else None)),
            "max_marks": ev.get("max_marks", MAX_MARKS.get(q.qtype)),
            "score": item.score if answered else None, "method": ev.get("method"), "disclaimer": ev.get("disclaimer"),
            "explanation": q.explanation or q.model_answer, "got_right": ev.get("got_right", []), "missing": ev.get("missing", []),
            "suggestion": ev.get("suggestion"), "your_answer": item.answer if answered else None,
        }
        if q.qtype == "mcq":
            ok = q.correct_index is not None and q.options and 0 <= q.correct_index < len(q.options)
            res["correct_index"] = q.correct_index if ok else None
            res["correct_answer"] = q.options[q.correct_index] if ok else None
        else:
            groups = (q.rubric or {}).get("keywords") or []
            res["expected_concepts"] = [_concept_label(g) for g in groups if g]
            res["model_answer"] = q.model_answer
        return res

    def _item_view(self, att: TrainingAttempt, item: TrainingAttemptItem) -> Dict[str, Any]:
        q = item.question
        cfg = att.config or {}
        answered = item.answered_at is not None
        view = {
            "id": str(item.id), "position": item.position, "topic": item.topic, "topic_label": self._topic_name(item),
            "difficulty": item.difficulty, "qtype": q.qtype, "kind": q.label, "source": q.source, "review_status": q.review_status,
            "prompt": q.prompt, "options": q.options if q.qtype == "mcq" else None,
            "max_marks": MAX_MARKS.get(q.qtype), "answered": answered,
            "is_repeat": str(q.id) in set(cfg.get("repeat_question_ids", [])),
            "is_workplace": item.round in WORKPLACE_ROUNDS, "result": None,
        }
        if answered:
            view["result"] = self._result_view(q, item, True)
        elif att.status == "COMPLETED":
            view["result"] = self._result_view(q, item, False)
        return view

    async def session_view(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> Dict[str, Any]:
        att = await self._get_role_attempt(user_id, attempt_id)
        cfg = att.config or {}
        items = [i for i in att.items if i.parent_item_id is None]
        answered = [i for i in items if i.answered_at is not None]
        nxt = next((i for i in items if i.answered_at is None), None)
        return {
            "id": str(att.id), "status": att.status, "mode": att.mode,
            "role": {"title": cfg.get("role_title"), "key": cfg.get("role_key"), "matched_title": cfg.get("matched_title"),
                     "mapped": cfg.get("mapped"), "topics": [{"slug": d, "label": self._label(d)} for d in cfg.get("domains", [])]},
            "level": cfg.get("level"), "difficulty": att.difficulty, "requested": cfg.get("requested"), "focus": cfg.get("focus"),
            "plan": cfg.get("plan"), "notices": cfg.get("notices", []), "started_at": _iso(att.started_at), "ended_at": _iso(att.ended_at),
            "total_questions": len(items), "answered": len(answered), "next_position": nxt.position if nxt else None,
            "items": [self._item_view(att, i) for i in items], "summary": att.summary, "ai_available": self.ai_available,
            "scoring_rules": SCORING_RULES,
        }

    # ── answering ────────────────────────────────────────────────────────────

    def _evaluate_mcq(self, q: TrainingQuestion, index: Optional[int]) -> Dict[str, Any]:
        if index is None or not q.options or not 0 <= index < len(q.options):
            raise HTTPException(status_code=422, detail="Choose one of the options")
        if q.correct_index is None or not 0 <= q.correct_index < len(q.options):
            return self._manual("This question's answer key is missing, so it cannot be graded automatically.", q)
        ok = grade_mcq(q.correct_index, index)
        correct_text = q.options[q.correct_index]
        return {
            "status": "correct" if ok else "incorrect", "score": 1.0 if ok else 0.0, "max_marks": MAX_MARKS["mcq"],
            "marks": 1.0 if ok else 0.0, "method": "objective", "disclaimer": None,
            "got_right": [f"You chose the correct option: {correct_text}"] if ok else [],
            "missing": [] if ok else [f"You chose \"{q.options[index]}\". The correct answer is \"{correct_text}\"."],
            "suggestion": "Good. Try a harder question on this topic." if ok else f"Revise this concept: {_first_sentence(q.explanation)}",
        }

    @staticmethod
    def _manual(reason: str, q: TrainingQuestion) -> Dict[str, Any]:
        return {"status": "manual_review", "score": None, "max_marks": MAX_MARKS.get(q.qtype), "marks": None, "method": "manual",
                "disclaimer": "This answer could not be evaluated reliably. Compare it with the model answer yourself; it earns no marks and is left out of the total.",
                "got_right": [], "missing": [], "suggestion": reason}

    async def _evaluate_text(self, q: TrainingQuestion, text: str) -> Dict[str, Any]:
        groups = [g for g in ((q.rubric or {}).get("keywords") or []) if g]
        if len(groups) < 2 and not (self.ai_available and q.model_answer):
            return self._manual("This question has no reliable marking guide, so use the model answer to check yourself.", q)
        ev = await evaluate_text(self.llm, q.prompt, text, q.rubric, q.model_answer, None)
        low = text.lower()
        covered = [g for g in groups if any(k.lower() in low for k in g)]
        missing = [g for g in groups if g not in covered]
        if ev["method"] == "ai_estimate":
            c = ev["criteria"]
            score = (c["correctness"] + c["relevance"] + c["completeness"]) / 15.0
            got, miss = list(ev.get("strengths", [])), list(ev.get("improvements", []))
            method, disclaimer = "ai_estimate", ev["disclaimer"]
        else:
            words = len(text.split())
            coverage = len(covered) / len(groups) if groups else 0.0
            score = coverage * min(1.0, 0.7 + 0.3 * min(1.0, words / 20))
            got = [f"Covered: {_concept_label(g)}" for g in covered]
            miss = [f"Missing: {_concept_label(g)}" for g in missing]
            method = "keyword_estimate"
            disclaimer = ("Rule-based estimate: it checks which expected ideas appear in your answer (accepting common synonyms), "
                          "not the quality of your reasoning. Different wording of a correct idea may be missed.")
        score = round(max(0.0, min(1.0, score)), 3)
        st = "correct" if score >= CORRECT_AT else "partial" if score >= PARTIAL_AT else "incorrect"
        marks = _round_quarter(score * MAX_MARKS["text"])
        return {
            "status": st, "score": score, "max_marks": MAX_MARKS["text"], "marks": marks, "method": method, "disclaimer": disclaimer,
            "got_right": got, "missing": miss,
            "suggestion": "Good answer. Add a concrete example to make it stronger." if st == "correct"
            else f"Revise {self._label(q.topic)}: {_first_sentence(q.model_answer or q.explanation)}",
        }

    async def answer_role(self, user_id: uuid.UUID, attempt_id: uuid.UUID, req: RoleAnswer) -> Dict[str, Any]:
        att = await self._get_role_attempt(user_id, attempt_id)
        item = next((i for i in att.items if str(i.id) == req.item_id and i.parent_item_id is None), None)
        if item is None:
            raise _not_found("Question")
        if att.status == "COMPLETED" and item.answered_at is None:
            raise HTTPException(status_code=409, detail="This session is already finished")
        if item.answered_at is not None:
            # Idempotent: the saved evaluation is returned and nothing is scored twice.
            return {"saved": True, "already_answered": True, "item": self._item_view(att, item)}
        q = item.question
        if q.qtype == "mcq":
            ev = self._evaluate_mcq(q, req.index)
            answer_payload = {"index": req.index}
        else:
            text = clean_text(req.text or "", 6000)
            if not text.strip():
                raise HTTPException(status_code=422, detail="Write an answer first")
            ev = await self._evaluate_text(q, text)
            answer_payload = {"text": text}
        await self.db.refresh(item)
        if item.answered_at is not None:  # another request answered it while we were evaluating: keep the first result
            await self.db.refresh(att, attribute_names=["items"])
            return {"saved": True, "already_answered": True, "item": self._item_view(att, item)}
        item.answer = answer_payload
        item.evaluation = ev
        item.score = ev["score"]
        item.score_kind = {"objective": "objective", "keyword_estimate": "keyword_estimate", "ai_estimate": "ai_estimate"}.get(ev["method"])
        item.is_correct = (ev["status"] == "correct") if q.qtype == "mcq" and ev["status"] != "manual_review" else None
        item.answered_at = _now()
        item.time_taken_sec = req.time_taken_sec
        await self.db.commit()
        await self.db.refresh(att, attribute_names=["items"])
        return {"saved": True, "already_answered": False, "item": self._item_view(att, item)}

    # ── finishing / review ───────────────────────────────────────────────────

    @staticmethod
    def item_status(item: TrainingAttemptItem) -> str:
        return "unanswered" if item.answered_at is None else (item.evaluation or {}).get("status") or "manual_review"

    def _summarise_role(self, att: TrainingAttempt) -> Dict[str, Any]:
        cfg = att.config or {}
        items = [i for i in att.items if i.parent_item_id is None]
        counts = {k: 0 for k in STATUS_LABEL}
        earned = available = 0.0
        topics: Dict[str, Dict[str, Any]] = {}
        for it in items:
            st = self.item_status(it)
            counts[st] += 1
            mx = (it.evaluation or {}).get("max_marks") or MAX_MARKS.get(it.question.qtype, 1.0)
            t = topics.setdefault(it.topic, {"topic": it.topic, "label": self._topic_name(it), "questions": 0, "answered": 0,
                                             "earned": 0.0, "available": 0.0})
            t["questions"] += 1
            if st != "unanswered":
                t["answered"] += 1
            if st == "manual_review":
                continue
            got = float((it.evaluation or {}).get("marks") or 0.0) if st != "unanswered" else 0.0
            earned += got
            available += mx
            t["earned"] += got
            t["available"] += mx
        by_topic = []
        for t in topics.values():
            pct = round(100 * t["earned"] / t["available"], 1) if t["available"] else None
            by_topic.append({**t, "earned": round(t["earned"], 2), "available": round(t["available"], 2), "pct": pct})
        by_topic.sort(key=lambda t: (t["pct"] is None, t["pct"] if t["pct"] is not None else 0))
        scored = [t for t in by_topic if t["pct"] is not None]
        strong = [t["label"] for t in scored if t["pct"] >= STRONG_AT * 100]
        weak = [t for t in scored if t["pct"] < WEAK_BELOW * 100]
        revision = [{"topic": t["topic"], "label": t["label"],
                     "reason": f"You scored {t['pct']}% here ({t['earned']} of {t['available']} marks)."} for t in weak]
        revision += [{"topic": t["topic"], "label": t["label"], "reason": f"{t['questions'] - t['answered']} question(s) were left unanswered."}
                     for t in by_topic if t["questions"] > t["answered"] and t["pct"] is not None and t["pct"] >= WEAK_BELOW * 100]
        pct = round(100 * earned / available, 1) if available else None
        return {
            "role_title": cfg.get("role_title"), "difficulty": att.difficulty, "level": cfg.get("level"),
            "topics": sorted({t["label"] for t in by_topic}),
            "total_questions": len(items), "answered": len(items) - counts["unanswered"], "unanswered": counts["unanswered"],
            "correct": counts["correct"], "partial": counts["partial"], "incorrect": counts["incorrect"], "manual_review": counts["manual_review"],
            "marks_earned": round(earned, 2), "marks_available": round(available, 2), "percentage": pct,
            "by_topic": by_topic, "strong_topics": strong, "weak_topics": [t["label"] for t in weak], "revision": revision,
            "next": {"improve_weak_available": bool(weak or any(t["questions"] > t["answered"] for t in by_topic)),
                     "weak_labels": [t["label"] for t in weak]},
            "scoring_rules": SCORING_RULES,
        }

    async def finish_role(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> Dict[str, Any]:
        att = await self._get_role_attempt(user_id, attempt_id)
        if att.status != "COMPLETED":
            att.summary = self._summarise_role(att)
            att.status = "COMPLETED"
            att.ended_at = _now()
            await self.db.commit()
        return await self.session_view(user_id, attempt_id)

    async def review(self, user_id: uuid.UUID, attempt_id: uuid.UUID, status_filter: str = "all") -> Dict[str, Any]:
        att = await self._get_role_attempt(user_id, attempt_id)
        if att.status != "COMPLETED":
            raise HTTPException(status_code=409, detail="Finish the assessment to see the full review.")
        items = [i for i in att.items if i.parent_item_id is None]
        counts = {"all": len(items), **{k: 0 for k in STATUS_LABEL}}
        for it in items:
            counts[self.item_status(it)] += 1
        keep = items if status_filter == "all" else [i for i in items if self.item_status(i) == status_filter]
        return {"id": str(att.id), "filter": status_filter, "counts": counts, "summary": att.summary,
                "items": [self._item_view(att, i) for i in keep]}

    async def again(self, user_id: uuid.UUID, attempt_id: uuid.UUID, req: RoleAgain) -> Dict[str, Any]:
        att = await self._get_role_attempt(user_id, attempt_id)
        cfg, rq = att.config or {}, (att.config or {}).get("requested") or {}
        create = RoleSessionCreate(
            role_title=cfg.get("role_title"), level=cfg.get("level"), difficulty=rq.get("difficulty"),
            topics=rq.get("topics") or [], count=req.count or rq.get("count") or 10, focus=req.focus, generate=rq.get("generate", True))
        return await self.start_session(user_id, create, previous=att)

    # ── history / progress per role ──────────────────────────────────────────

    async def sessions(self, user_id: uuid.UUID, title: Optional[str], page: int, size: int) -> Dict[str, Any]:
        stmt = select(TrainingAttempt).where(TrainingAttempt.user_id == user_id, TrainingAttempt.mode == "role",
                                             TrainingAttempt.deleted_at.is_(None)).order_by(TrainingAttempt.started_at.desc())
        rows = (await self.db.execute(stmt.limit(200))).scalars().all()
        if title:
            key = self._profile_or_422(title).key
            rows = [a for a in rows if (a.config or {}).get("role_key") == key]
        total = len(rows)
        page_rows = rows[(page - 1) * size: page * size]
        return {"page": page, "size": size, "total": total, "items": [{
            "id": str(a.id), "role_title": (a.config or {}).get("role_title"), "status": a.status, "difficulty": a.difficulty,
            "started_at": _iso(a.started_at), "ended_at": _iso(a.ended_at), "total_questions": len([i for i in a.items if i.parent_item_id is None]),
            "answered": len([i for i in a.items if i.parent_item_id is None and i.answered_at]),
            "percentage": (a.summary or {}).get("percentage")} for a in page_rows]}

    async def role_progress(self, user_id: uuid.UUID, title: str) -> Dict[str, Any]:
        prof = self._profile_or_422(title)
        attempts = await self._role_attempts(user_id, prof.key)
        stats = self._topic_stats(attempts)
        seen = await self._seen_map(user_id)
        pool = await self._candidates(user_id, prof, None)
        done = [a for a in attempts if a.status == "COMPLETED"]
        pcts = [(a.summary or {}).get("percentage") for a in done if (a.summary or {}).get("percentage") is not None]
        topics = [{"topic": t, "label": self._label(t), "answered": int(s["n"]), "avg_pct": round(100 * s["avg"], 1)} for t, s in stats.items()]
        topics.sort(key=lambda x: x["avg_pct"])
        return {
            "role": {"title": prof.title, "key": prof.key}, "sessions_completed": len(done), "sessions_in_progress": len(attempts) - len(done),
            "questions_answered": sum(int(s["n"]) for s in stats.values()),
            "average_percentage": round(sum(pcts) / len(pcts), 1) if pcts else None,
            "latest_percentage": pcts[0] if pcts else None,
            "topics": topics, "weak_topics": [t for t in topics if t["avg_pct"] < WEAK_BELOW * 100],
            "strong_topics": [t for t in topics if t["avg_pct"] >= STRONG_AT * 100],
            "stored_questions": len(pool), "unseen_stored_questions": sum(1 for q in pool if q.id not in seen),
            "ai_available": self.ai_available,
            "note": "Progress is tracked separately for each job role and comes only from your saved answers.",
        }
