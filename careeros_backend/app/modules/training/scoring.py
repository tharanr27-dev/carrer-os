"""Answer scoring.

Score kinds (always shown to the student, never mixed up):
  objective         - exact-match MCQ grading
  keyword_estimate  - rule-based rubric coverage; a rough estimate, not a recruiter's judgement
  ai_estimate       - LLM rubric evaluation (only when a provider is configured); also an estimate
  self_assessed     - the student's own judgement (coding practice; code is NOT executed)
"""

import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from app.modules.training.llm import LLMUnavailable, TrainingLLM
from app.modules.training.textutils import clean_text

logger = logging.getLogger("careeros")

CRITERIA = ["correctness", "relevance", "completeness", "structure", "clarity"]
STAR_MARKERS = {
    "Situation": r"\b(situation|context|when|at that time|was working|during)\b",
    "Task": r"\b(task|goal|responsib|needed to|had to|objective)\b",
    "Action": r"\b(i (decided|built|created|implemented|organi[sz]ed|led|wrote|started|asked|worked|tried|fixed|planned|learn)|action|steps? i)\b",
    "Result": r"\b(result|outcome|as a result|improv|achiev|learned|finally|ended up|reduced|increased)\b",
}


def grade_mcq(correct_index: Optional[int], answer_index: Any) -> bool:
    return isinstance(answer_index, int) and not isinstance(answer_index, bool) and answer_index == correct_index


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"[.!?\n]+", text) if s.strip()]


def keyword_eval(rubric: Optional[Dict[str, Any]], answer: str, model_answer: Optional[str]) -> Dict[str, Any]:
    """Rule-based rubric: concept coverage + length + structure. Honest about its limits."""
    answer = clean_text(answer, 5000)
    words = answer.split()
    low = answer.lower()
    groups: List[List[str]] = (rubric or {}).get("keywords") or []
    framework = (rubric or {}).get("framework")

    covered, missing = [], []
    for g in groups:
        (covered if any(k.lower() in low for k in g) else missing).append(g)
    coverage = len(covered) / len(groups) if groups else 0.5

    length_factor = min(1.0, len(words) / 40)  # a 40-word answer is the minimum for full credit
    sents = _sentences(answer)
    avg_len = (len(words) / len(sents)) if sents else 0
    clarity = 1.0 if 6 <= avg_len <= 28 else 0.6 if words else 0.0

    if framework == "STAR":
        hits = [k for k, pat in STAR_MARKERS.items() if re.search(pat, low)]
        structure = len(hits) / 4
        struct_note = "STAR parts detected: " + (", ".join(hits) if hits else "none")
    else:
        structure = min(1.0, (len(sents) / 3)) if words else 0.0
        struct_note = f"{len(sents)} sentence(s)"

    crit = {
        "correctness": round(5 * coverage, 1),
        "relevance": round(5 * min(1.0, coverage + 0.15), 1) if words else 0.0,
        "completeness": round(5 * (0.6 * coverage + 0.4 * length_factor), 1),
        "structure": round(5 * structure, 1),
        "clarity": round(5 * clarity, 1),
    }
    score = (0.4 * coverage + 0.2 * length_factor + 0.2 * structure + 0.2 * clarity) if words else 0.0
    score = round(max(0.0, min(1.0, score)), 3)

    feedback, strengths = [], []
    if len(words) < 15:
        feedback.append("Your answer is very short. Add reasoning and an example.")
    if missing:
        hints = ", ".join(f'"{g[0]}"' for g in missing[:4])
        feedback.append(f"Ideas worth covering that were not detected: {hints}.")
    if framework == "STAR" and structure < 1:
        feedback.append("Structure your answer as Situation, Task, Action, Result.")
    if covered:
        strengths.append(f"Covered {len(covered)} of {len(groups)} expected key ideas.")
    if structure >= 0.75:
        strengths.append("Clear structure.")
    return {
        "method": "keyword_estimate",
        "disclaimer": "Automatic keyword-based estimate. It checks coverage of expected ideas, not the quality of your reasoning, and is not a recruiter's judgement.",
        "criteria": crit,
        "structure_note": struct_note,
        "strengths": strengths,
        "improvements": feedback,
        "model_answer": model_answer,
        "score": score,
    }


class AIEvaluation(BaseModel):
    correctness: float = Field(ge=0, le=5)
    relevance: float = Field(ge=0, le=5)
    completeness: float = Field(ge=0, le=5)
    structure: float = Field(ge=0, le=5)
    clarity: float = Field(ge=0, le=5)
    strengths: List[str] = Field(default_factory=list, max_length=5)
    improvements: List[str] = Field(default_factory=list, max_length=5)
    stronger_answer: Optional[str] = Field(default=None, max_length=1500)


EVAL_SYSTEM = (
    "You are a fair interview coach. Evaluate the student's answer against the rubric. Judge correctness, "
    "relevance, completeness, structure and clarity only. Do NOT penalise accent, dialect, regional English or "
    "minor grammar slips that do not affect understanding. Return ONLY JSON: "
    '{"correctness":0-5,"relevance":0-5,"completeness":0-5,"structure":0-5,"clarity":0-5,'
    '"strengths":[...],"improvements":[...],"stronger_answer":"..."}'
)


async def evaluate_text(
    llm: Optional[TrainingLLM],
    question: str,
    answer: str,
    rubric: Optional[Dict[str, Any]],
    model_answer: Optional[str],
    framework: Optional[str] = None,
) -> Dict[str, Any]:
    """AI rubric evaluation when available (validated), otherwise the keyword estimate."""
    answer = clean_text(answer, 5000)
    base = keyword_eval(rubric, answer, model_answer)
    if llm is None or not llm.available or len(answer.split()) < 5:
        return base
    try:
        data = await llm.complete_json(
            EVAL_SYSTEM,
            f"Question: {clean_text(question, 700)}\nExpected ideas / reference: {clean_text(model_answer or '', 1200)}\n"
            f"Framework: {framework or 'none'}\nStudent answer: {answer}",
            max_tokens=700,
        )
        ev = AIEvaluation.model_validate(data)
    except (LLMUnavailable, ValidationError, ValueError, TypeError):
        base["fallback_reason"] = "AI evaluation was unavailable; showing the rule-based estimate instead."
        return base
    crit = {c: round(getattr(ev, c), 1) for c in CRITERIA}
    return {
        "method": "ai_estimate",
        "disclaimer": "AI-generated estimate against a rubric. It can be wrong and is not equivalent to a recruiter's decision.",
        "criteria": crit,
        "strengths": [clean_text(s, 300) for s in ev.strengths],
        "improvements": [clean_text(s, 300) for s in ev.improvements],
        "model_answer": model_answer,
        "stronger_answer": clean_text(ev.stronger_answer, 1500) if ev.stronger_answer else None,
        "score": round(sum(crit.values()) / (5 * len(CRITERIA)), 3),
    }


def self_assessed_code(passed: Any, total: Any, solution: Optional[str], explanation: Optional[str]) -> Dict[str, Any]:
    try:
        total_i = max(1, min(int(total), 50))
        passed_i = max(0, min(int(passed), total_i))
    except (TypeError, ValueError):
        total_i, passed_i = 1, 0
    return {
        "method": "self_assessed",
        "disclaimer": "Code is NOT executed on this platform. This score is your own self-assessment against the listed test cases.",
        "self_passed": passed_i,
        "self_total": total_i,
        "model_answer": solution,
        "explanation": explanation,
        "score": round(passed_i / total_i, 3),
    }
