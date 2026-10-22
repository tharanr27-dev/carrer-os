import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.skills import load_student_skills
from app.modules.training.bank.behavioural import RESUME_PROJECT_TEMPLATES
from app.modules.training.bank.catalog import (
    DIFFICULTIES,
    LEVELS,
    ROUNDS,
    TARGET_ROLES,
    TOPIC_INDEX,
    valid_topic,
)
from app.modules.training.generation import generate_follow_up, generate_questions
from app.modules.training.llm import LLMUnavailable, TrainingLLM
from app.modules.training.models import (
    TrainingAttempt,
    TrainingAttemptItem,
    TrainingProfile,
    TrainingQuestion,
)
from app.modules.training.progress import (
    STAGE_ORDER,
    compute_progress,
    topic_label,
)
from app.modules.training.schemas import AnswerRequest, AttemptCreate, NextRequest, ProfileUpdate
from app.modules.training.scoring import evaluate_text, grade_mcq, self_assessed_code
from app.modules.training.seed import ensure_seed
from app.modules.training.textutils import clean_text, fingerprint
from app.modules.users.models import Education, Profile, Project

logger = logging.getLogger("careeros")

EXAM_GRACE_SECONDS = 15
GENERATED_HOURLY_CAP = 40
GENERATED_TOTAL_CAP = 500
DEFAULT_QTYPE = {"aptitude": "mcq", "technical": "mcq"}
GENERATABLE_ROUNDS = {"aptitude", "technical", "communication", "hr", "managerial"}
LEVEL_PREFERRED = {"fresher": {"easy", "medium"}, "junior": {"medium"}, "mid": {"medium", "hard"}}
ROLE_TOPICS = {
    "Python Developer": ["python", "oop", "dsa", "sql", "dbms", "rest-api", "git", "testing"],
    "Frontend Developer": ["javascript", "typescript", "web-basics", "react-next", "rest-api", "git", "testing"],
    "Backend Developer": ["backend", "rest-api", "authentication", "databases", "sql", "dbms", "os", "networks"],
    "Full Stack Developer": ["javascript", "react-next", "backend", "rest-api", "sql", "authentication", "git"],
    "Software Engineer": ["dsa", "oop", "dbms", "os", "networks", "software-engineering", "complexity"],
    "Data Analyst": ["sql", "data-analysis", "ds-statistics", "python", "dbms"],
    "AI/ML Engineer": ["machine-learning", "deep-learning", "python", "nlp-llm", "rag", "ds-statistics", "ai-project"],
    "DevOps Engineer": ["os", "networks", "git", "testing", "backend", "software-engineering"],
}
TEMPLATE_KEYWORDS = [
    [["component", "module", "layer"], ["database", "api", "frontend", "backend"], ["flow", "request", "interact", "connect"]],
    [["i "], ["implemented", "built", "designed", "wrote", "developed", "my part"], ["team", "alone", "responsib"]],
    [["because", "reason", "chose"], ["alternative", "compared", "instead", "trade"], ["requirement", "easy", "performance", "familiar"]],
    [["problem", "challenge", "issue", "bug"], ["solved", "fixed", "approach", "debug"], ["learn", "result"]],
    [["test", "unit", "manual", "validate"], ["bug", "error", "log", "monitor"]],
    [["retry", "fallback", "timeout", "error handling"], ["log", "monitor", "message", "graceful"]],
    [["cache", "queue", "index", "replica", "load balanc", "scale"], ["bottleneck", "database", "traffic", "users"]],
    [["improve", "add", "refactor", "optimi"], ["test", "feature", "performance", "security"]],
    [["used", "built", "project", "example"], ["learn", "concept", "practical", "challenge"]],
    [["concept", "explain", "means"], ["example", "applied", "used"]],
    [["course", "subject", "learn", "theory"], ["project", "practical", "role", "relevant"]],
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _iso(dt: Optional[datetime]) -> Optional[str]:
    dt = _aware(dt)
    return dt.isoformat() if dt else None


def _not_found(what: str = "Attempt") -> HTTPException:
    # Same response for "missing" and "someone else's" so existence never leaks across students.
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


class TrainingService:
    def __init__(self, db: AsyncSession, llm: Optional[TrainingLLM] = None):
        self.db = db
        self.llm = llm

    @property
    def ai_available(self) -> bool:
        return bool(self.llm and self.llm.available)

    # ── Profile ──────────────────────────────────────────────────────────────

    async def get_profile(self, user_id: uuid.UUID) -> TrainingProfile:
        row = (await self.db.execute(select(TrainingProfile).where(TrainingProfile.user_id == user_id))).scalar_one_or_none()
        if row is None:
            row = TrainingProfile(user_id=user_id, level="fresher", language="en")
            self.db.add(row)
            try:
                await self.db.commit()
            except IntegrityError:
                # Two concurrent first requests (e.g. the roadmap and resume tabs) both tried to create
                # the row; user_id is UNIQUE, so keep the winner's row instead of failing with a 500.
                await self.db.rollback()
                row = (await self.db.execute(select(TrainingProfile).where(TrainingProfile.user_id == user_id))).scalar_one()
        return row

    async def update_profile(self, user_id: uuid.UUID, data: ProfileUpdate) -> Dict[str, Any]:
        row = await self.get_profile(user_id)
        if data.target_role is not None:
            row.target_role = data.target_role or None
        if data.level:
            row.level = data.level
        if data.language:
            row.language = data.language
        if data.reset_resume_data:
            row.resume_data = None
        elif data.resume_data is not None:
            row.resume_data = data.resume_data.model_dump()
        await self.db.commit()
        return await self.profile_view(user_id)

    async def resolve_resume_data(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Student-edited data wins; otherwise what Career OS already knows about them. Never invented."""
        prof = await self.get_profile(user_id)
        if prof.resume_data:
            return {**prof.resume_data, "source": "student_edited"}
        profile = (await self.db.execute(select(Profile).where(Profile.user_id == user_id))).scalar_one_or_none()
        projects, degree = [], None
        if profile is not None:
            rows = (await self.db.execute(select(Project).where(Project.profile_id == profile.id))).scalars().all()
            projects = [{"title": p.title, "description": p.description, "tech_stack": None} for p in rows if p.title]
            edu = (await self.db.execute(select(Education).where(Education.profile_id == profile.id))).scalars().first()
            degree = edu.degree if edu and edu.degree else None
        skills = await load_student_skills(self.db, user_id)
        return {"projects": projects[:10], "skills": skills[:40], "degree": degree, "source": "profile"}

    async def profile_view(self, user_id: uuid.UUID) -> Dict[str, Any]:
        prof = await self.get_profile(user_id)
        return {
            "target_role": prof.target_role,
            "level": prof.level,
            "language": prof.language,
            "resume_data": await self.resolve_resume_data(user_id),
        }

    # ── Catalog ──────────────────────────────────────────────────────────────

    async def meta(self, user_id: uuid.UUID) -> Dict[str, Any]:
        await ensure_seed(self.db)
        rows = (
            await self.db.execute(
                select(TrainingQuestion.round, TrainingQuestion.topic, func.count())
                .where(
                    TrainingQuestion.deleted_at.is_(None),
                    (TrainingQuestion.owner_user_id.is_(None)) | (TrainingQuestion.owner_user_id == user_id),
                    TrainingQuestion.source != "resume_template",
                )
                .group_by(TrainingQuestion.round, TrainingQuestion.topic)
            )
        ).all()
        counts = {(r, t): c for r, t, c in rows}
        rounds = []
        for key in STAGE_ORDER:
            meta = ROUNDS[key]
            groups = []
            for group, topics in meta["groups"].items():
                groups.append({
                    "name": group,
                    "topics": [{"slug": s, "label": l, "questions": counts.get((key, s), 0)} for s, l in topics],
                })
            rounds.append({"key": key, "label": meta["label"], "stage": meta["stage"], "groups": groups})
        return {
            "rounds": rounds,
            "target_roles": TARGET_ROLES,
            "levels": LEVELS,
            "difficulties": DIFFICULTIES,
            "ai_available": self.ai_available,
            "ai_note": None if self.ai_available else "AI question generation and AI answer evaluation are off (no AI provider is configured). Reviewed questions and rule-based estimates are used instead.",
            "labels": ["foundational", "commonly tested", "role-specific", "scenario-based", "advanced"],
            "disclaimer": "Practice questions are for preparation. No question is guaranteed to appear in any real interview.",
        }

    # ── Question selection / de-duplication ──────────────────────────────────

    async def _seen_map(self, user_id: uuid.UUID, limit: int = 600) -> Dict[uuid.UUID, datetime]:
        rows = (
            await self.db.execute(
                select(TrainingAttemptItem.question_id, func.max(TrainingAttemptItem.created_at))
                .where(TrainingAttemptItem.user_id == user_id)
                .group_by(TrainingAttemptItem.question_id)
                .order_by(func.max(TrainingAttemptItem.created_at).desc())
                .limit(limit)
            )
        ).all()
        return {qid: ts for qid, ts in rows}

    async def _topic_weights(self, user_id: uuid.UUID, round_: str) -> Dict[str, float]:
        rows = (
            await self.db.execute(
                select(TrainingAttemptItem.topic, func.avg(TrainingAttemptItem.score), func.count())
                .where(TrainingAttemptItem.user_id == user_id, TrainingAttemptItem.round == round_,
                       TrainingAttemptItem.score.is_not(None))
                .group_by(TrainingAttemptItem.topic)
            )
        ).all()
        return {t: 1.0 + 3.0 * (1.0 - float(avg)) for t, avg, n in rows if n >= 2}

    async def pick_questions(
        self,
        user_id: uuid.UUID,
        round_: str,
        topic: Optional[str],
        difficulty: Optional[str],
        count: int,
        exclude: Set[uuid.UUID],
        level: str = "fresher",
        role: Optional[str] = None,
        qtype: Optional[str] = None,
        topics: Optional[List[str]] = None,
        adaptive: bool = True,
    ) -> Dict[str, Any]:
        stmt = select(TrainingQuestion).where(
            TrainingQuestion.round == round_,
            TrainingQuestion.deleted_at.is_(None),
            TrainingQuestion.source != "resume_template",
            (TrainingQuestion.owner_user_id.is_(None)) | (TrainingQuestion.owner_user_id == user_id),
        )
        if topic:
            stmt = stmt.where(TrainingQuestion.topic == topic)
        elif topics:
            stmt = stmt.where(TrainingQuestion.topic.in_(topics))
        if difficulty:
            stmt = stmt.where(TrainingQuestion.difficulty == difficulty)
        if qtype:
            stmt = stmt.where(TrainingQuestion.qtype == qtype)
        pool = [q for q in (await self.db.execute(stmt.limit(1500))).scalars().all()
                if q.id not in exclude and (not q.roles or not role or role in q.roles)]
        seen = await self._seen_map(user_id)
        weights = await self._topic_weights(user_id, round_) if (adaptive and not topic) else {}
        preferred = LEVEL_PREFERRED.get(level, LEVEL_PREFERRED["fresher"])

        def key(q: TrainingQuestion) -> float:
            w = weights.get(q.topic, 1.5 if weights else 1.0)
            d_penalty = 0.0 if (difficulty or q.difficulty in preferred) else 1.0
            return random.random() / w + d_penalty

        unseen = sorted([q for q in pool if q.id not in seen], key=key)
        chosen = unseen[:count]
        repeats = 0
        if len(chosen) < count:
            used = {q.id for q in chosen}
            old = sorted([q for q in pool if q.id in seen and q.id not in used], key=lambda q: seen[q.id])
            take = old[: count - len(chosen)]
            repeats = len(take)
            chosen += take
        return {"questions": chosen, "repeats": repeats, "pool_size": len(pool), "unseen": len(unseen)}

    async def _generate(
        self, user_id: uuid.UUID, round_: str, topic: str, difficulty: str, qtype: str, count: int,
        level: str, role: Optional[str],
    ) -> Dict[str, Any]:
        """Returns {"questions": [TrainingQuestion], "notice": str|None}. Never raises on provider trouble."""
        if round_ not in GENERATABLE_ROUNDS or not valid_topic(round_, topic):
            return {"questions": [], "notice": "AI generation is not available for this selection."}
        if not self.ai_available:
            return {"questions": [], "notice": "AI question generation is not configured, so reviewed questions are used."}
        hour_ago = _now() - timedelta(hours=1)
        base = select(func.count()).select_from(TrainingQuestion).where(
            TrainingQuestion.owner_user_id == user_id, TrainingQuestion.source == "generated")
        total = (await self.db.execute(base)).scalar_one()
        last_hour = (await self.db.execute(base.where(TrainingQuestion.created_at >= hour_ago))).scalar_one()
        if total >= GENERATED_TOTAL_CAP or last_hour >= GENERATED_HOURLY_CAP:
            return {"questions": [], "notice": "You have reached the AI generation limit for now. Reviewed questions are used instead."}
        existing = (await self.db.execute(
            select(TrainingQuestion.prompt).where(
                TrainingQuestion.round == round_, TrainingQuestion.topic == topic,
                (TrainingQuestion.owner_user_id.is_(None)) | (TrainingQuestion.owner_user_id == user_id)).limit(200)
        )).scalars().all()
        try:
            gen = await generate_questions(self.llm, round_, topic, difficulty, qtype, count, level, role, list(existing))
        except LLMUnavailable:
            return {"questions": [], "notice": "AI generation is temporarily unavailable, so reviewed questions are used."}
        if not gen:
            return {"questions": [], "notice": "The AI output did not pass validation, so reviewed questions are used."}
        rows = []
        for g in gen:
            q = TrainingQuestion(**g, owner_user_id=user_id, category=TOPIC_INDEX[f"{round_}:{topic}"]["group"])
            self.db.add(q)
            rows.append(q)
        await self.db.flush()
        return {"questions": rows, "notice": None}

    # ── Resume / project questions ───────────────────────────────────────────

    async def _resume_questions(self, user_id: uuid.UUID, count: int) -> List[TrainingQuestion]:
        data = await self.resolve_resume_data(user_id)
        projects = [p for p in data.get("projects", []) if p.get("title")][:3]
        skills = data.get("skills", [])[:4]
        degree = data.get("degree")
        # Order matters because the list is trimmed: core project questions first (round-robin across
        # projects), then a skill and an education question, then the deeper project questions.
        specs: List[tuple] = []
        for idx in (0, 1, 2, 3):
            specs += [(idx, {"project": p["title"]}) for p in projects]
        specs += [(8, {"skill": s}) for s in skills[:2]]
        if degree:
            specs.append((10, {"degree": degree}))
        for idx in (4, 5, 6, 7):
            specs += [(idx, {"project": p["title"]}) for p in projects]
        specs += [(9, {"skill": s}) for s in skills[2:4]]
        if not specs:
            raise HTTPException(status_code=422, detail="Add at least one project or skill (Resume & Projects tab) to start this interview.")
        # Interleave so the first questions cover different projects/templates, then trim.
        specs = specs[: max(count, 1)]
        rows = []
        for idx, fills in specs:
            kind, difficulty, template = RESUME_PROJECT_TEMPLATES[idx]
            prompt = template.format(**fills)
            q = TrainingQuestion(
                round="resume", topic="resume-project", category="Your Profile", difficulty=difficulty, qtype="text",
                label="based on your profile", prompt=prompt, source="resume_template", review_status="template",
                model_answer="Answer using your REAL project details: what you built, why, what you personally did, a concrete challenge and the result. If you did not do something, say so honestly.",
                rubric={"keywords": TEMPLATE_KEYWORDS[idx], "framework": None},
                fingerprint=fingerprint(prompt + str(uuid.uuid4())), owner_user_id=user_id,
                follow_ups=["Which part of that would you do differently now?"],
            )
            self.db.add(q)
            rows.append(q)
        await self.db.flush()
        return rows

    # ── Attempts ─────────────────────────────────────────────────────────────

    def _new_item(self, attempt_id, user_id, pos, q: TrainingQuestion, parent=None, prompt_override=None) -> TrainingAttemptItem:
        return TrainingAttemptItem(
            attempt_id=attempt_id, question_id=q.id, user_id=user_id, position=pos, round=q.round,
            topic=q.topic, difficulty=q.difficulty, parent_item_id=parent, prompt_override=prompt_override,
        )

    async def create_attempt(self, user_id: uuid.UUID, req: AttemptCreate) -> Dict[str, Any]:
        await ensure_seed(self.db)
        prof = await self.get_profile(user_id)
        notices: List[str] = []
        if req.mode == "mock":
            if not req.mock:
                raise HTTPException(status_code=422, detail="Mock interview settings are required")
            attempt, questions, notices = await self._build_mock(user_id, req, prof)
        else:
            if not req.round:
                raise HTTPException(status_code=422, detail="A round is required")
            if req.topic and not valid_topic(req.round, req.topic):
                raise HTTPException(status_code=422, detail="Unknown topic for this round")
            if req.round == "resume" and req.mode == "exam":
                raise HTTPException(status_code=422, detail="Exam mode is not available for this round")
            attempt = TrainingAttempt(
                user_id=user_id, mode=req.mode, round=req.round, topic=req.topic, difficulty=req.difficulty,
                status="IN_PROGRESS", started_at=_now(),
                config={"adaptive": req.adaptive, "planned_count": req.count, "level": prof.level, "role": prof.target_role},
            )
            if req.round == "resume":
                questions = await self._resume_questions(user_id, req.count)
            else:
                qtype = req.qtype or DEFAULT_QTYPE.get(req.round)
                picked = await self.pick_questions(
                    user_id, req.round, req.topic, req.difficulty, req.count, set(), prof.level, prof.target_role,
                    qtype=qtype if req.round in DEFAULT_QTYPE or req.qtype else None, adaptive=req.adaptive)
                questions = picked["questions"]
                if req.generate and req.topic:
                    g = await self._generate(user_id, req.round, req.topic, req.difficulty or "medium", qtype or "text",
                                             min(req.count, 5), prof.level, prof.target_role)
                    if g["notice"]:
                        notices.append(g["notice"])
                    questions = (g["questions"] + questions)[: req.count]
                elif req.generate:
                    notices.append("Pick a specific topic to generate new questions.")
                if picked["repeats"]:
                    notices.append("You have already seen all reviewed questions for this selection, so some are repeated.")
            if req.mode == "exam":
                per = 75 if all(q.qtype == "mcq" for q in questions) else 180
                attempt.time_limit_sec = req.time_limit_sec or per * max(len(questions), 1)
            if not questions:
                raise HTTPException(status_code=404, detail="No questions are available for this selection yet.")
        attempt.config = {**(attempt.config or {}), "notices": notices}
        self.db.add(attempt)
        await self.db.flush()
        for i, q in enumerate(questions, start=1):
            self.db.add(self._new_item(attempt.id, user_id, i, q))
        await self.db.commit()
        return await self.attempt_view(user_id, attempt.id)

    async def _build_mock(self, user_id, req: AttemptCreate, prof: TrainingProfile):
        m = req.mock
        role = m.role or prof.target_role
        per_round = max(2, min(8, m.duration_min // (3 * len(m.rounds))))
        notices: List[str] = []
        questions: List[TrainingQuestion] = []
        used: Set[uuid.UUID] = set()
        for r in sorted(m.rounds, key=lambda x: ROUNDS[x]["stage"]):
            if r == "resume":
                try:
                    qs = await self._resume_questions(user_id, per_round)
                except HTTPException:
                    notices.append("Resume & project round skipped: add a project or skill first.")
                    continue
            else:
                topics = ROLE_TOPICS.get(role or "") if r == "technical" else None
                diff = m.difficulty
                if r == "coding" and not diff:
                    diff = None
                picked = await self.pick_questions(
                    user_id, r, None, diff, 2 if r == "coding" else per_round, used, m.level, role,
                    topics=topics, adaptive=True)
                qs = picked["questions"]
                if r == "coding":
                    qs = [q for q in qs if q.difficulty != "hard" or m.level != "fresher"][:2]
                if picked["repeats"]:
                    notices.append(f"Some {ROUNDS[r]['label']} questions repeat: you have seen all reviewed ones.")
            used.update(q.id for q in qs)
            questions.extend(qs)
        if not questions:
            raise HTTPException(status_code=404, detail="No questions are available for these rounds yet.")
        attempt = TrainingAttempt(
            user_id=user_id, mode="mock", round="mock", difficulty=m.difficulty, status="IN_PROGRESS",
            started_at=_now(), time_limit_sec=m.duration_min * 60,
            config={"role": role, "level": m.level, "rounds": m.rounds, "language": m.language,
                    "duration_min": m.duration_min, "planned_count": len(questions)},
        )
        return attempt, questions, notices

    async def _get_attempt(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> TrainingAttempt:
        att = (
            await self.db.execute(select(TrainingAttempt).where(
                TrainingAttempt.id == attempt_id, TrainingAttempt.user_id == user_id, TrainingAttempt.deleted_at.is_(None)))
        ).scalar_one_or_none()
        if att is None:
            raise _not_found()
        return att

    def _deadline(self, att: TrainingAttempt) -> Optional[datetime]:
        if att.mode == "practice" or not att.time_limit_sec:
            return None
        return _aware(att.started_at) + timedelta(seconds=att.time_limit_sec)

    def _reveal(self, att: TrainingAttempt, item: TrainingAttemptItem) -> bool:
        if att.status == "COMPLETED":
            return True
        return att.mode in ("practice", "mock") and item.answered_at is not None

    def item_view(self, att: TrainingAttempt, item: TrainingAttemptItem) -> Dict[str, Any]:
        q = item.question
        reveal = self._reveal(att, item)
        extra = dict(q.extra or {})
        view: Dict[str, Any] = {
            "id": str(item.id),
            "position": item.position,
            "round": item.round,
            "topic": item.topic,
            "topic_label": topic_label(item.round, item.topic),
            "difficulty": item.difficulty,
            "qtype": q.qtype,
            "prompt": item.prompt_override or q.prompt,
            "options": q.options if q.qtype == "mcq" else None,
            "label": q.label,
            "source": q.source,
            "review_status": q.review_status,
            "is_follow_up": item.parent_item_id is not None,
            "coding": extra or None,
            "answered": item.answered_at is not None,
            "answer": item.answer if (item.answered_at is not None and (reveal or att.mode == "exam")) else None,
            "time_taken_sec": item.time_taken_sec,
            "result": None,
        }
        if reveal and item.answered_at is not None:
            ev = item.evaluation or {}
            view["result"] = {
                "is_correct": item.is_correct,
                "correct_index": q.correct_index if q.qtype == "mcq" else None,
                "explanation": q.explanation if item.parent_item_id is None else None,
                "model_answer": q.model_answer if item.parent_item_id is None else None,
                "score": item.score,
                "score_kind": item.score_kind,
                "evaluation": ev,
            }
        elif reveal and att.status == "COMPLETED" and item.parent_item_id is None:
            # Unanswered at the end: show the answer so the student can learn from it.
            view["result"] = {"is_correct": None, "correct_index": q.correct_index if q.qtype == "mcq" else None,
                              "explanation": q.explanation, "model_answer": q.model_answer, "score": None,
                              "score_kind": None, "evaluation": None}
        if not reveal and view["coding"]:
            view["coding"].pop("solution", None)
        return view

    async def attempt_view(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> Dict[str, Any]:
        att = await self._get_attempt(user_id, attempt_id)
        await self.db.refresh(att, attribute_names=["items"])
        deadline = self._deadline(att)
        return {
            "id": str(att.id), "mode": att.mode, "round": att.round, "topic": att.topic,
            "difficulty": att.difficulty, "status": att.status, "config": att.config,
            "time_limit_sec": att.time_limit_sec, "started_at": _iso(att.started_at),
            "deadline": _iso(deadline), "ended_at": _iso(att.ended_at), "summary": att.summary,
            "items": [self.item_view(att, i) for i in att.items],
            "ai_available": self.ai_available,
        }

    # ── Answering ────────────────────────────────────────────────────────────

    async def answer(self, user_id: uuid.UUID, attempt_id: uuid.UUID, req: AnswerRequest) -> Dict[str, Any]:
        att = await self._get_attempt(user_id, attempt_id)
        await self.db.refresh(att, attribute_names=["items"])
        if att.status == "COMPLETED":
            raise HTTPException(status_code=409, detail="This attempt is already finished")
        item = next((i for i in att.items if str(i.id) == req.item_id), None)
        if item is None:
            raise _not_found("Question")
        now = _now()
        deadline = self._deadline(att)
        if deadline and now > deadline + timedelta(seconds=EXAM_GRACE_SECONDS):
            raise HTTPException(status_code=409, detail="Time is over for this attempt. Submit to see your results.")
        if att.mode != "exam" and item.answered_at is not None:
            raise HTTPException(status_code=409, detail="This question was already answered")
        if att.mode == "mock":
            earlier = [i for i in att.items if i.position < item.position and i.answered_at is None]
            if earlier:
                raise HTTPException(status_code=409, detail="Answer the questions in order in a mock interview")

        q = item.question
        if q.qtype == "mcq":
            if req.index is None or not q.options or req.index >= len(q.options):
                raise HTTPException(status_code=422, detail="Choose one of the options")
            item.answer = {"index": req.index}
            item.is_correct = grade_mcq(q.correct_index, req.index)
            item.score = 1.0 if item.is_correct else 0.0
            item.score_kind = "objective"
            item.evaluation = None
        elif q.qtype == "code":
            code_text = req.text or ""
            if not code_text.strip() and req.self_passed is None:
                raise HTTPException(status_code=422, detail="Write your solution first")
            total = req.self_total or len((q.extra or {}).get("tests", [])) or 1
            item.answer = {"text": code_text, "self_passed": req.self_passed or 0, "self_total": total}
            item.evaluation = self_assessed_code(req.self_passed or 0, total, q.model_answer, q.explanation)
            item.score, item.score_kind, item.is_correct = item.evaluation["score"], "self_assessed", None
        else:
            text = req.text or ""
            if len(text.split()) < 3:
                raise HTTPException(status_code=422, detail="Write a short answer first")
            item.answer = {"text": text}
            question_text = item.prompt_override or q.prompt
            if item.parent_item_id is not None:
                # Follow-ups have no reference rubric: only an AI estimate can score them.
                ev = await evaluate_text(self.llm, question_text, text, None, None, None)
                if ev["method"] == "ai_estimate":
                    item.evaluation, item.score, item.score_kind = ev, ev["score"], "ai_estimate"
                else:
                    item.evaluation = {"method": "unscored", "disclaimer": "Follow-up questions are for practice and are not scored without an AI provider.",
                                       "strengths": [], "improvements": ["Compare your answer with the main answer's key ideas."]}
                    item.score, item.score_kind = None, None
            else:
                ev = await evaluate_text(self.llm, question_text, text, q.rubric, q.model_answer, (q.rubric or {}).get("framework"))
                item.evaluation, item.score, item.score_kind = ev, ev["score"], ev["method"]
            item.is_correct = None
        item.answered_at = now
        item.time_taken_sec = req.time_taken_sec
        new_follow_up = None
        if att.mode in ("practice", "mock") and q.qtype == "text" and item.parent_item_id is None:
            new_follow_up = await self._maybe_follow_up(att, item, q, req.text or "")
        await self.db.commit()
        await self.db.refresh(att, attribute_names=["items"])
        if att.mode == "exam":
            return {"saved": True, "item_id": str(item.id)}
        return {"saved": True, "item": self.item_view(att, item), "follow_up": self.item_view(att, new_follow_up) if new_follow_up else None}

    async def _maybe_follow_up(self, att, item, q: TrainingQuestion, text: str) -> Optional[TrainingAttemptItem]:
        if len(text.split()) < 8 or any(i.parent_item_id == item.id for i in att.items):
            return None
        fu = await generate_follow_up(self.llm, item.prompt_override or q.prompt, text) if self.ai_available else None
        if not fu and q.follow_ups:
            fu = clean_text(q.follow_ups[0], 300)
        if not fu:
            return None
        for other in att.items:
            if other.position > item.position:
                other.position += 1
        new = self._new_item(att.id, att.user_id, item.position + 1, q, parent=item.id, prompt_override=fu)
        self.db.add(new)
        await self.db.flush()
        att.items.append(new)
        att.items.sort(key=lambda i: i.position)
        return new

    async def next_questions(self, user_id: uuid.UUID, attempt_id: uuid.UUID, req: NextRequest) -> Dict[str, Any]:
        att = await self._get_attempt(user_id, attempt_id)
        await self.db.refresh(att, attribute_names=["items"])
        if att.status == "COMPLETED":
            raise HTTPException(status_code=409, detail="This attempt is already finished")
        if att.mode != "practice":
            raise HTTPException(status_code=409, detail="More questions can only be added in practice mode")
        if att.round == "resume":
            raise HTTPException(status_code=409, detail="Resume questions are generated once per session")
        prof = await self.get_profile(user_id)
        exclude = {i.question_id for i in att.items}
        difficulty = att.difficulty
        cfg = att.config or {}
        if cfg.get("adaptive", True) and not difficulty:
            recent = [i for i in att.items if i.score is not None][-5:]
            if len(recent) >= 3:
                avg = sum(i.score for i in recent) / len(recent)
                cur = DIFFICULTIES.index(recent[-1].difficulty) if recent[-1].difficulty in DIFFICULTIES else 1
                difficulty = DIFFICULTIES[min(cur + 1, 2)] if avg >= 0.8 else DIFFICULTIES[max(cur - 1, 0)] if avg <= 0.4 else recent[-1].difficulty
        notices: List[str] = []
        new_qs: List[TrainingQuestion] = []
        qtype = req.qtype or DEFAULT_QTYPE.get(att.round)
        if req.generate:
            if not att.topic:
                notices.append("Pick a specific topic to generate new questions.")
            else:
                g = await self._generate(user_id, att.round, att.topic, difficulty or "medium", qtype or "text", req.count, prof.level, prof.target_role)
                new_qs = g["questions"]
                if g["notice"]:
                    notices.append(g["notice"])
        if len(new_qs) < req.count:
            picked = await self.pick_questions(
                user_id, att.round, att.topic, difficulty, req.count - len(new_qs), exclude | {q.id for q in new_qs},
                prof.level, prof.target_role, qtype=qtype if att.round in DEFAULT_QTYPE or req.qtype else None, adaptive=cfg.get("adaptive", True))
            new_qs += picked["questions"]
            if picked["repeats"]:
                notices.append("You have seen all reviewed questions for this selection; some are repeated.")
        if not new_qs:
            raise HTTPException(status_code=404, detail="No more questions available for this selection.")
        pos = max((i.position for i in att.items), default=0)
        for q in new_qs:
            pos += 1
            self.db.add(self._new_item(att.id, user_id, pos, q))
        await self.db.commit()
        view = await self.attempt_view(user_id, attempt_id)
        return {"attempt": view, "added": [i for i in view["items"] if i["position"] > pos - len(new_qs)], "notices": notices}

    # ── Finish / reports ─────────────────────────────────────────────────────

    async def finish(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> Dict[str, Any]:
        att = await self._get_attempt(user_id, attempt_id)
        await self.db.refresh(att, attribute_names=["items"])
        if att.status != "COMPLETED":
            att.summary = await self._summarise(att)
            att.status = "COMPLETED"
            att.ended_at = _now()
            await self.db.commit()
        return await self.attempt_view(user_id, attempt_id)

    async def _summarise(self, att: TrainingAttempt) -> Dict[str, Any]:
        main = [i for i in att.items if i.parent_item_id is None]
        answered = [i for i in main if i.answered_at is not None]
        scored = [i for i in answered if i.score is not None]
        counted = [i.score for i in main if (i.score is not None)] if att.mode != "exam" else [
            (i.score if i.score is not None else 0.0) for i in main]
        mcq = [i for i in answered if i.score_kind == "objective"]
        est = [i for i in scored if i.score_kind in ("ai_estimate", "keyword_estimate")]
        selfs = [i for i in scored if i.score_kind == "self_assessed"]

        def pct(xs):
            return round(100 * sum(xs) / len(xs), 1) if xs else None

        topics: Dict[tuple, List[TrainingAttemptItem]] = {}
        for i in scored:
            topics.setdefault((i.round, i.topic), []).append(i)
        by_topic = [{"round": r, "topic": t, "label": topic_label(r, t), "attempted": len(v),
                     "score_pct": pct([x.score for x in v])} for (r, t), v in topics.items()]
        by_topic.sort(key=lambda x: x["score_pct"])
        by_round: Dict[str, Any] = {}
        for r in {i.round for i in scored}:
            rows = [i for i in scored if i.round == r]
            by_round[r] = {"label": ROUNDS[r]["label"], "attempted": len(rows), "score_pct": pct([x.score for x in rows]),
                           "objective_pct": pct([x.score for x in rows if x.score_kind == "objective"]),
                           "estimated_pct": pct([x.score for x in rows if x.score_kind in ("ai_estimate", "keyword_estimate")])}
        overall = pct(counted)
        times = [i.time_taken_sec for i in answered if i.time_taken_sec]
        weak = [t for t in by_topic if t["score_pct"] < 60]
        strong = [t for t in by_topic if t["score_pct"] >= 75]
        suggestions = [{"title": f"Review {t['label']}", "reason": f"You scored {t['score_pct']}% here.",
                        "action": {"type": "practice", "round": t["round"], "topic": t["topic"], "difficulty": "easy" if t["score_pct"] < 45 else "medium", "mode": "practice"}}
                       for t in weak[:3]]
        prev = (await self.db.execute(
            select(TrainingAttempt).where(
                TrainingAttempt.user_id == att.user_id, TrainingAttempt.status == "COMPLETED", TrainingAttempt.id != att.id,
                TrainingAttempt.round == att.round, TrainingAttempt.topic == att.topic)
            .order_by(TrainingAttempt.ended_at.desc()).limit(1))).scalar_one_or_none()
        prev_pct = ((prev.summary or {}).get("overall_pct") if prev else None)
        summary = {
            "total_questions": len(main), "answered": len(answered), "skipped": len(main) - len(answered),
            "correct": sum(1 for i in mcq if i.is_correct), "objective_total": len(mcq),
            "objective_pct": pct([i.score for i in mcq]),
            "estimated_pct": pct([i.score for i in est]), "self_assessed_pct": pct([i.score for i in selfs]),
            "overall_pct": overall,
            "total_time_sec": round(sum(times), 1) if times else None,
            "avg_time_sec": round(sum(times) / len(times), 1) if times else None,
            "by_topic": by_topic, "by_round": by_round,
            "strengths": [t["label"] for t in strong[:5]], "weak_areas": [t["label"] for t in weak[:5]],
            "wrong_item_ids": [str(i.id) for i in mcq if not i.is_correct],
            "suggestions": suggestions,
            "previous_overall_pct": prev_pct,
            "change_vs_previous": round(overall - prev_pct, 1) if (overall is not None and prev_pct is not None) else None,
            "score_notes": "Objective = exact-match MCQ. Estimated = AI/keyword rubric estimate. Self-assessed = your own marking; code is not executed.",
        }
        if att.mode == "mock":
            summary["readiness_note"] = self._readiness(overall)
        return summary

    @staticmethod
    def _readiness(overall: Optional[float]) -> str:
        if overall is None:
            return "Not enough scored answers to comment."
        if overall >= 75:
            return "Strong result on this simulation (75%+). Keep practising weaker topics to stay consistent."
        if overall >= 60:
            return "Developing (60-74%). Focus on the weak topics listed and repeat a mock in a few days."
        return "Needs more practice (<60%). Work through the suggested topics, then retry. This is practice feedback, not a prediction of hiring decisions."

    # ── History / progress ───────────────────────────────────────────────────

    async def history(self, user_id: uuid.UUID, page: int, size: int, status_filter: Optional[str] = None) -> Dict[str, Any]:
        stmt = select(TrainingAttempt).where(TrainingAttempt.user_id == user_id, TrainingAttempt.deleted_at.is_(None))
        if status_filter:
            stmt = stmt.where(TrainingAttempt.status == status_filter)
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
        rows = (await self.db.execute(stmt.order_by(TrainingAttempt.started_at.desc()).offset((page - 1) * size).limit(size))).scalars().all()
        return {"page": page, "size": size, "total": total, "items": [self._attempt_row(a) for a in rows]}

    @staticmethod
    def _attempt_row(a: TrainingAttempt) -> Dict[str, Any]:
        return {"id": str(a.id), "mode": a.mode, "round": a.round, "topic": a.topic, "difficulty": a.difficulty,
                "status": a.status, "started_at": _iso(a.started_at), "ended_at": _iso(a.ended_at),
                "overall_pct": (a.summary or {}).get("overall_pct"), "summary": a.summary,
                "planned": (a.config or {}).get("planned_count")}

    async def progress(self, user_id: uuid.UUID) -> Dict[str, Any]:
        item_rows = (await self.db.execute(
            select(TrainingAttemptItem).where(TrainingAttemptItem.user_id == user_id, TrainingAttemptItem.score.is_not(None))
            .order_by(TrainingAttemptItem.answered_at.desc()).limit(4000))).scalars().all()
        items = [{"round": i.round, "topic": i.topic, "difficulty": i.difficulty, "score": i.score, "score_kind": i.score_kind,
                  "time_taken_sec": i.time_taken_sec, "answered_at": _iso(i.answered_at)} for i in item_rows]
        att_rows = (await self.db.execute(
            select(TrainingAttempt).where(TrainingAttempt.user_id == user_id, TrainingAttempt.deleted_at.is_(None))
            .order_by(TrainingAttempt.started_at.desc()).limit(200))).scalars().all()
        attempts = [{**self._attempt_row(a), "summary": a.summary} for a in att_rows]
        data = await self.resolve_resume_data(user_id)
        result = compute_progress(items, attempts, has_projects=bool(data.get("projects")))
        in_progress = next((a for a in attempts if a["status"] == "IN_PROGRESS"), None)
        result["resume_attempt"] = in_progress
        result["profile"] = await self.profile_view(user_id)
        return result

    async def browse(self, user_id: uuid.UUID, round_: Optional[str], topic: Optional[str], difficulty: Optional[str],
                     page: int, size: int) -> Dict[str, Any]:
        await ensure_seed(self.db)
        stmt = select(TrainingQuestion).where(
            TrainingQuestion.deleted_at.is_(None), TrainingQuestion.source != "resume_template",
            (TrainingQuestion.owner_user_id.is_(None)) | (TrainingQuestion.owner_user_id == user_id))
        if round_:
            stmt = stmt.where(TrainingQuestion.round == round_)
        if topic:
            stmt = stmt.where(TrainingQuestion.topic == topic)
        if difficulty:
            stmt = stmt.where(TrainingQuestion.difficulty == difficulty)
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
        rows = (await self.db.execute(stmt.order_by(TrainingQuestion.round, TrainingQuestion.topic, TrainingQuestion.created_at)
                                      .offset((page - 1) * size).limit(size))).scalars().all()
        return {"page": page, "size": size, "total": total, "items": [
            {"id": str(q.id), "round": q.round, "topic": q.topic, "topic_label": topic_label(q.round, q.topic),
             "difficulty": q.difficulty, "qtype": q.qtype, "label": q.label, "source": q.source,
             "review_status": q.review_status, "prompt": q.prompt, "options": q.options} for q in rows]}
