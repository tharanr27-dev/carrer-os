"""Validated AI question generation + follow-up generation.

Everything the model returns is untrusted: it is parsed against a strict schema, sanitised, checked for
claims of being real company questions, and de-duplicated before it is ever stored or shown.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.modules.training.bank.catalog import TOPIC_INDEX
from app.modules.training.llm import LLMUnavailable, TrainingLLM
from app.modules.training.textutils import clean_text, fingerprint, is_near_duplicate

logger = logging.getLogger("careeros")

MAX_PER_REQUEST = 5
_COMPANY_CLAIM = re.compile(
    r"\b(asked (at|by|in)|actual interview|real interview|previous year|was asked|frequently asked at|"
    r"google|amazon|microsoft|infosys|tcs|wipro|cognizant|accenture|zoho|meta|apple|netflix)\b",
    re.IGNORECASE,
)


class GeneratedQuestion(BaseModel):
    prompt: str = Field(min_length=12, max_length=900)
    options: Optional[List[str]] = None
    correct_index: Optional[int] = None
    explanation: str = Field(min_length=15, max_length=1200)
    model_answer: Optional[str] = Field(default=None, max_length=2000)
    rubric_keywords: List[List[str]] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)

    @field_validator("prompt", "explanation", "model_answer", mode="before")
    @classmethod
    def _clean(cls, v):
        return clean_text(v, 2000) if v is not None else v


def validate_generated(raw: Dict[str, Any], qtype: str) -> GeneratedQuestion:
    q = GeneratedQuestion.model_validate(raw)
    if _COMPANY_CLAIM.search(q.prompt) or _COMPANY_CLAIM.search(q.explanation):
        raise ValueError("claims to be a company/historical question")
    if qtype == "mcq":
        opts = [clean_text(o, 300) for o in (q.options or [])]
        if len(opts) != 4 or any(not o for o in opts) or len({o.lower() for o in opts}) != 4:
            raise ValueError("MCQ needs exactly four distinct non-empty options")
        if q.correct_index is None or not 0 <= q.correct_index < 4:
            raise ValueError("MCQ needs correct_index 0-3")
        q.options = opts
    else:
        if not q.model_answer or len(q.model_answer) < 30:
            raise ValueError("text question needs a model answer")
        q.options, q.correct_index = None, None
    q.follow_ups = [clean_text(f, 300) for f in q.follow_ups[:3] if clean_text(f, 300)]
    groups = [[clean_text(k, 40).lower() for k in grp if clean_text(k, 40)] for grp in q.rubric_keywords[:8] if isinstance(grp, list)]
    q.rubric_keywords = [g for g in groups if g]
    return q


SYSTEM = (
    "You write practice questions for students preparing for IT job interviews and placement tests. "
    "Return ONLY valid JSON. Never claim a question was asked by any real company or in any real interview. "
    "Questions must be unambiguous, factually correct, and match the requested topic and difficulty."
)


def _prompt(round_: str, topic: str, difficulty: str, qtype: str, count: int, level: str, role: Optional[str], avoid: List[str]) -> str:
    label = TOPIC_INDEX.get(f"{round_}:{topic}", {}).get("label", topic)
    shape = (
        '{"prompt": str, "options": [4 distinct strings], "correct_index": 0-3, "explanation": str}'
        if qtype == "mcq"
        else '{"prompt": str, "model_answer": str, "explanation": "common mistakes", '
        '"rubric_keywords": [[synonyms for concept 1], [synonyms for concept 2]], "follow_ups": [up to 2 strings]}'
    )
    avoid_txt = "\n".join(f"- {a[:120]}" for a in avoid[:12]) or "- (none)"
    return (
        f"Create {count} NEW {qtype} practice questions.\nRound: {round_}\nTopic: {label}\nDifficulty: {difficulty}\n"
        f"Student level: {level}\nTarget role: {role or 'general IT'}\n"
        f'Return JSON: {{"questions": [{shape}, ...]}}\n'
        f"Do NOT repeat or paraphrase these existing questions:\n{avoid_txt}"
    )


async def generate_questions(
    llm: TrainingLLM,
    round_: str,
    topic: str,
    difficulty: str,
    qtype: str,
    count: int,
    level: str = "fresher",
    role: Optional[str] = None,
    existing_prompts: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Returns validated, de-duplicated question dicts (may be fewer than requested, or empty).

    Raises LLMUnavailable if the provider cannot be used at all.
    """
    count = max(1, min(count, MAX_PER_REQUEST))
    existing = list(existing_prompts or [])
    data = await llm.complete_json(SYSTEM, _prompt(round_, topic, difficulty, qtype, count, level, role, existing))
    items = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise LLMUnavailable("unexpected structure")
    accepted: List[Dict[str, Any]] = []
    for raw in items[: count + 2]:
        if len(accepted) >= count:
            break
        try:
            q = validate_generated(raw, qtype)
        except (ValidationError, ValueError, TypeError, AttributeError) as exc:
            logger.info("Rejected generated question: %s", str(exc)[:120])
            continue
        if is_near_duplicate(q.prompt, existing + [a["prompt"] for a in accepted]):
            logger.info("Rejected near-duplicate generated question")
            continue
        accepted.append(
            dict(
                round=round_, topic=topic, difficulty=difficulty, qtype=qtype, prompt=q.prompt,
                options=q.options, correct_index=q.correct_index, explanation=q.explanation,
                model_answer=q.model_answer,
                rubric={"keywords": q.rubric_keywords, "framework": None} if qtype != "mcq" else None,
                follow_ups=q.follow_ups, label="AI-generated practice question",
                source="generated", review_status="unreviewed", fingerprint=fingerprint(q.prompt),
            )
        )
    return accepted


async def generate_follow_up(llm: TrainingLLM, question: str, answer: str) -> Optional[str]:
    """One short follow-up question based on the student's actual answer; None if unusable."""
    try:
        data = await llm.complete_json(
            SYSTEM,
            "Given this interview practice question and the student's answer, write ONE short, specific "
            'follow-up question that probes their answer. Return JSON {"follow_up": str}.\n'
            f"Question: {clean_text(question, 600)}\nAnswer: {clean_text(answer, 1500)}",
            max_tokens=200,
        )
    except LLMUnavailable:
        return None
    fu = clean_text(data.get("follow_up") if isinstance(data, dict) else "", 300)
    if 10 <= len(fu) <= 300 and not _COMPANY_CLAIM.search(fu):
        return fu
    return None
