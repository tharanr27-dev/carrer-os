"""Communication Coach engine: measurements of the student's actual text. No AI, no canned scores.

What is measured (all on a 0-10 scale, text only):
  vocabulary  diversity of words used (root type-token ratio), reliable only for messages of 15+ words
  grammar     MECHANICAL slips only (repeated words, lowercase "I", lowercase sentence starts, spacing,
              missing end punctuation). This is NOT a grammar checker and will miss many real errors.
  tone        professional register: informal words, excess exclamation marks, ALL-CAPS, hedging
  clarity     sentence length (8-22 words reads clearly) and repeated-word density
  fluency     filler-word density (a text proxy: spoken fluency cannot be measured from typed text)
Accent, dialect and regional English are not assessed.
"""

import logging
import math
import re
from typing import Any, Dict, List

from app.core.text_analysis import (
    avg_sentence_length,
    clamp,
    filler_counts,
    hedge_counts,
    informal_hits,
    mechanical_issues,
    sentences,
    top_repeated_words,
    words,
)
from app.modules.communication.schemas import (
    AICommunicationAnalysis,
    AICommunicationReport,
    AILinguisticFeedback,
)

logger = logging.getLogger("careeros")

MIN_WORDS = 15
METHOD = "text_metrics_v1"
POLITE = ("please", "thank you", "thanks", "would you", "could you", "i appreciate", "kind regards", "best regards")


def _scores(text: str) -> Dict[str, float]:
    ws = words(text)
    n = len(ws)
    if n == 0:
        return {"vocabulary": 0.0, "grammar": 0.0, "tone": 0.0, "clarity": 0.0, "fluency": 0.0}
    rttr = len({w.lower() for w in ws}) / math.sqrt(n)
    vocab = clamp((rttr - 2.0) * 2.5)
    slips = len(mechanical_issues(text))
    grammar = clamp(10 - 2.5 * slips)
    informal = len(informal_hits(text))
    shouting = len([w for w in re.findall(r"\b[A-Z]{4,}\b", text)])
    excess_bang = max(0, text.count("!") - 1)
    hedges = sum(hedge_counts(text).values())
    polite = any(p in text.lower() for p in POLITE)
    tone = clamp(10 - 1.5 * informal - 1.0 * excess_bang - 2.0 * min(shouting, 2) - 0.5 * min(hedges, 4) + (0.5 if polite else 0))
    asl = avg_sentence_length(text)
    if asl <= 22:
        clarity = clamp(10 - max(0, 8 - asl) * 0.8)
    else:
        clarity = clamp(10 - (asl - 22) * 0.4)
    clarity = clamp(clarity - 1.5 * len(top_repeated_words(text)))
    fillers = sum(filler_counts(text).values())
    fluency = clamp(10 - 1.2 * (fillers / n * 100))
    return {k: round(v, 1) for k, v in dict(vocabulary=vocab, grammar=grammar, tone=tone, clarity=clarity, fluency=fluency).items()}


class CommunicationEvaluationEngine:
    async def analyze_message(self, text: str) -> AICommunicationAnalysis:
        text = text or ""
        s = _scores(text)
        fb: List[AILinguisticFeedback] = []

        def add(cat, orig, sug, why):
            if len(fb) < 8:
                fb.append(AILinguisticFeedback(category=cat, original_text=orig[:80], suggested_correction=sug[:120], reasoning=why))

        n = len(words(text))
        if n < MIN_WORDS:
            add("Note", text[:60], "Write 15+ words", f"This message has only {n} words, so vocabulary and clarity scores are not reliable.")
        for term, alt in informal_hits(text).items():
            add("Tone", term, alt, f"'{term}' is informal for professional communication.")
        for f, k in filler_counts(text).items():
            add("Filler word", f, "(remove it)", f"'{f}' appears {k} time(s). Fillers weaken a message.")
        for h in list(hedge_counts(text))[:2]:
            add("Confidence", h, "state the point directly", f"Hedging ('{h}') can make you sound unsure.")
        for issue in mechanical_issues(text):
            add(issue["category"], issue["original"], issue["suggestion"], issue["reasoning"])
        long_one = next((x for x in sentences(text) if len(words(x)) > 30), None)
        if long_one:
            add("Clarity", long_one[:60] + "…", "split into two sentences", f"This sentence has {len(words(long_one))} words; aim for under 25.")
        for w, k in top_repeated_words(text)[:1]:
            add("Vocabulary", w, "use a synonym or rephrase", f"'{w}' is repeated {k} times.")
        return AICommunicationAnalysis(
            grammar_score=s["grammar"], vocabulary_score=s["vocabulary"], tone_score=s["tone"], clarity_score=s["clarity"], feedbacks=fb
        )

    async def generate_final_report(self, messages: List[Dict[str, Any]]) -> AICommunicationReport:
        """`messages`: [{"text": str}] — the student's messages for the session."""
        usable = [m["text"] for m in messages if len(words(m.get("text") or "")) >= MIN_WORDS]
        if not usable:
            return AICommunicationReport(
                overall_score=0.0, grammar_score=0.0, vocabulary_score=0.0, tone_score=0.0, fluency_score=0.0,
                strengths=[],
                weaknesses=["No message long enough to measure was submitted (15+ words are needed)."] if messages
                else ["No messages were submitted in this session."],
                improvement_suggestions=["Write a few full sentences (15+ words) per message so the coach has something to measure."],
            )
        per = [_scores(t) for t in usable]
        avg = {k: round(sum(p[k] for p in per) / len(per), 1) for k in per[0]}
        overall = round((avg["grammar"] + avg["vocabulary"] + avg["tone"] + avg["clarity"] + avg["fluency"]) / 5, 1)
        all_text = "\n".join(usable)
        fillers, informal = filler_counts(all_text), informal_hits(all_text)
        label = {"grammar": "Writing mechanics", "vocabulary": "Vocabulary variety", "tone": "Professional tone", "clarity": "Sentence clarity", "fluency": "Filler-word control"}
        strengths = [f"{label[k]} is strong ({v}/10)." for k, v in avg.items() if v >= 8]
        weaknesses = [f"{label[k]} needs work ({v}/10)." for k, v in avg.items() if v < 6]
        suggestions: List[str] = []
        if fillers:
            suggestions.append(f"Cut filler words: {', '.join(f'{w} ×{k}' for w, k in list(fillers.items())[:4])}.")
        if informal:
            suggestions.append("Replace informal words: " + "; ".join(f"{w} → {a}" for w, a in list(informal.items())[:4]) + ".")
        if avg["clarity"] < 7:
            suggestions.append("Aim for sentences of 10-22 words; split long ones.")
        if avg["vocabulary"] < 6:
            suggestions.append("Vary your wording: avoid repeating the same words.")
        if avg["grammar"] < 8:
            suggestions.append("Proofread for repeated words, capital letters and end punctuation before sending.")
        if not suggestions:
            suggestions.append("No specific issue detected by the text checks. Keep practising with longer, more complex messages.")
        return AICommunicationReport(
            overall_score=overall, grammar_score=avg["grammar"], vocabulary_score=avg["vocabulary"], tone_score=avg["tone"],
            fluency_score=avg["fluency"], strengths=strengths or ["No score reached 8/10 yet."], weaknesses=weaknesses,
            improvement_suggestions=suggestions + [
                f"Scores are text-based measurements ({METHOD}), not an AI or human judgement. Grammar is a mechanical check only; accent and dialect are not assessed."
            ],
        )
