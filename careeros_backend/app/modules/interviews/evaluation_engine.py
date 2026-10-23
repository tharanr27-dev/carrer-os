"""Interview Studio engine: reviewed questions, rubric scoring and a report computed from the actual answers.

Nothing here is an AI judgement unless an AI provider is configured for follow-up questions. Answers are scored
by the same transparent rubric used in Interview Prep (coverage of expected ideas, length, structure, clarity),
which is a rough estimate and not a recruiter's decision. The report says so.
"""

import logging
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.text_analysis import filler_counts, hedge_counts, mechanical_issues, words
from app.modules.interviews.models import InterviewAnswer, InterviewQuestion
from app.modules.interviews.schemas import AIEvaluationScore, AIFinalReport
from app.modules.training.bank.catalog import TOPIC_INDEX
from app.modules.training.generation import generate_follow_up
from app.modules.training.llm import get_llm
from app.modules.training.models import TrainingProfile, TrainingQuestion
from app.modules.training.scoring import keyword_eval

logger = logging.getLogger("careeros")

METHOD = "rule_based_v1"
DISCLAIMER = (
    "Scores are rule-based estimates: they measure how many expected ideas an answer covers, plus length, "
    "structure and clarity. They are not an AI judgement and not a recruiter's decision."
)
# interview_type -> [(round, topics or None for all)]
POOLS = {
    "HR": [("hr", ["hr-core", "behavioural", "situational", "teamwork-conflict", "fresher"])],
    "BEHAVIORAL": [("hr", ["behavioural", "situational", "ethics", "teamwork-conflict"]), ("managerial", ["ownership"])],
    "MANAGERIAL": [("managerial", None)],
    "TECHNICAL": [("technical", None)],
}
LOW_SCORE = 0.6


def _pool_for(interview_type: str):
    return POOLS.get((interview_type or "").upper(), POOLS["TECHNICAL"])


class InterviewEvaluationEngine:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    # ── Questions ────────────────────────────────────────────────────────────
    async def _candidates(self, user_id: uuid.UUID, interview_type: str, difficulty: str) -> List[TrainingQuestion]:
        rows: List[TrainingQuestion] = []
        for round_, topics in _pool_for(interview_type):
            stmt = select(TrainingQuestion).where(
                TrainingQuestion.round == round_, TrainingQuestion.qtype == "text",
                TrainingQuestion.source == "curated", TrainingQuestion.deleted_at.is_(None),
            )
            if topics:
                stmt = stmt.where(TrainingQuestion.topic.in_(topics))
            rows += list((await self.db.execute(stmt)).scalars().all())
        if (interview_type or "").upper() == "TECHNICAL":
            role = (await self.db.execute(select(TrainingProfile.target_role).where(TrainingProfile.user_id == user_id))).scalar_one_or_none()
            if role:
                from app.modules.training.service import ROLE_TOPICS

                wanted = set(ROLE_TOPICS.get(role, []))
                narrowed = [q for q in rows if q.topic in wanted]
                rows = narrowed or rows
        wanted_diff = (difficulty or "MEDIUM").lower()
        exact = [q for q in rows if q.difficulty == wanted_diff]
        return exact or rows

    async def _lookup(self, prompt: str) -> Optional[TrainingQuestion]:
        return (
            await self.db.execute(select(TrainingQuestion).where(TrainingQuestion.prompt == prompt, TrainingQuestion.source == "curated").limit(1))
        ).scalars().first()

    async def next_question(
        self, user_id: uuid.UUID, interview_type: str, difficulty: str, asked: List[str], last_answer: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """Returns (question text, expected topics). Never repeats a question already asked in this session."""
        asked_set = set(asked)
        if asked and last_answer and len(words(last_answer)) >= 8:
            last = await self._lookup(asked[-1])
            if last is not None:  # the last question was a main question: probe it once
                fu = None
                llm = get_llm()
                if llm.available:
                    fu = await generate_follow_up(llm, last.prompt, last_answer)
                if not fu:
                    fu = next((f for f in (last.follow_ups or []) if f not in asked_set), None)
                if fu and fu not in asked_set:
                    return fu, [TOPIC_INDEX.get(f"{last.round}:{last.topic}", {}).get("label", last.topic)]
        if not asked and (interview_type or "").upper() in ("HR", "BEHAVIORAL"):
            # The classic opener, whatever the chosen difficulty (it is tagged "easy" in the bank).
            opener = await self._lookup("Tell me about yourself.")
            if opener is not None:
                return opener.prompt, [TOPIC_INDEX["hr:hr-core"]["label"]]
        pool = [q for q in await self._candidates(user_id, interview_type, difficulty) if q.prompt not in asked_set]
        if not pool:
            return ("That was the last prepared question. Press Finish to see your report.", [])
        q = random.choice(pool)
        return q.prompt, [TOPIC_INDEX.get(f"{q.round}:{q.topic}", {}).get("label", q.topic)]

    # ── Scoring ──────────────────────────────────────────────────────────────
    async def score_answer(self, question_text: str, answer: str) -> Dict[str, Any]:
        q = await self._lookup(question_text)
        if q is None:  # follow-ups have no reference rubric, so they are not scored
            return {"scored": False, "topic": None}
        ev = keyword_eval(q.rubric, answer, q.model_answer)
        ev.update({"scored": True, "topic": q.topic, "round": q.round, "model_answer": q.model_answer})
        return ev

    async def evaluate_answer(self, question: str, answer: str) -> AIEvaluationScore:
        ev = await self.score_answer(question, answer)
        hedges, fillers = hedge_counts(answer), filler_counts(answer)
        slips = [i for i in mechanical_issues(answer) if i["category"] in ("Repeated word", "Capitalisation")]
        if not ev["scored"]:
            return AIEvaluationScore(
                overall_score=0.0, grammar_score=max(0.0, 10 - 2 * len(slips)),
                confidence_score=max(0.0, 10 - 1.5 * (sum(hedges.values()) + sum(fillers.values()))),
                strengths=[], improvements=["Follow-up question: shown for practice and not scored."],
            )
        improvements = list(ev["improvements"])
        if hedges:
            improvements.append(f"Hedging words ({', '.join(list(hedges)[:3])}) can make answers sound unsure. State your point directly.")
        if fillers:
            improvements.append(f"Filler words detected: {', '.join(list(fillers)[:3])}.")
        return AIEvaluationScore(
            overall_score=round(ev["score"] * 10, 1),
            # Measured from the text only: writing mechanics (repeats, capitalisation) and hedging/filler density.
            grammar_score=float(max(0.0, 10 - 2 * len(slips))),
            confidence_score=float(max(0.0, round(10 - 1.5 * (sum(hedges.values()) + sum(fillers.values())), 1))),
            strengths=list(ev["strengths"]), improvements=improvements,
        )

    # ── Report ───────────────────────────────────────────────────────────────
    async def generate_final_report(self, session_id: uuid.UUID) -> AIFinalReport:
        rows = (
            await self.db.execute(
                select(InterviewQuestion.question_text, InterviewAnswer.answer_text)
                .join(InterviewAnswer, InterviewAnswer.question_id == InterviewQuestion.id)
                .where(InterviewQuestion.session_id == session_id)
                .order_by(InterviewQuestion.created_at.asc())
            )
        ).all()
        scored, per_answer, weak_topics = [], [], []
        all_fillers: Dict[str, int] = {}
        all_hedges: Dict[str, int] = {}
        for q_text, a_text in rows:
            for k, v in filler_counts(a_text).items():
                all_fillers[k] = all_fillers.get(k, 0) + v
            for k, v in hedge_counts(a_text).items():
                all_hedges[k] = all_hedges.get(k, 0) + v
            ev = await self.score_answer(q_text, a_text)
            if not ev["scored"]:
                per_answer.append({"question": q_text[:160], "scored": False, "note": "Follow-up question (not scored)."})
                continue
            scored.append(ev)
            if ev["score"] < LOW_SCORE and ev["topic"]:
                weak_topics.append((ev["round"], ev["topic"]))
            per_answer.append({
                "question": q_text[:160], "scored": True, "score_out_of_10": round(ev["score"] * 10, 1),
                "criteria_out_of_5": ev["criteria"], "improvements": ev["improvements"], "model_answer": ev["model_answer"],
            })
        n = len(scored)
        mean = lambda xs: (sum(xs) / len(xs)) if xs else 0.0  # noqa: E731
        overall = round(mean([e["score"] for e in scored]) * 100, 1)
        technical = round(mean([e["criteria"]["correctness"] for e in scored]) * 20, 1)
        communication = round(mean([(e["criteria"]["structure"] + e["criteria"]["clarity"]) / 2 for e in scored]) * 20, 1)
        learning = [
            f"Practise {TOPIC_INDEX.get(f'{r}:{t}', {}).get('label', t)} in Interview Prep ({r} round)."
            for r, t in dict.fromkeys(weak_topics)
        ]
        if not rows:
            learning = ["No answers were submitted, so there is nothing to score. Try the interview again."]
        elif not learning:
            learning = ["No weak topic detected in this session. Try a harder difficulty or another interview type."]
        return AIFinalReport(
            overall_score=overall, technical_score=technical, communication_score=communication,
            detailed_analysis={
                "method": METHOD, "disclaimer": DISCLAIMER,
                "questions_answered": len(rows), "scored_answers": n,
                "how_scores_work": "Overall = average rubric score of scored answers (0-100). Technical = coverage of expected ideas. "
                                   "Communication = average of structure and clarity.",
                "language": {"filler_words": all_fillers, "hedging_words": all_hedges},
                "per_answer": per_answer,
            },
            recommended_learning=learning,
        )
