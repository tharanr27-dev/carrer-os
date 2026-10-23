import logging
from collections import Counter
from typing import Any, Dict, List

from app.modules.learning.schemas import AILearningModule, AILearningRoadmap, AILearningTask
from app.modules.training.bank.catalog import TOPIC_INDEX
from app.modules.training.seed import all_seed

logger = logging.getLogger("careeros")

MINUTES_PER_QUESTION = 4  # rough planning figure, not a measurement
MAX_TOPIC_MODULES = 5


def _topics_for_role(role: str) -> List[str]:
    from app.modules.training.service import ROLE_TOPICS  # imported lazily: training.service is heavy

    if role in ROLE_TOPICS:
        return ROLE_TOPICS[role]
    r = (role or "").lower()
    for key, topics in ROLE_TOPICS.items():
        if key.lower().split()[0].split("/")[0] in r:
            return topics
    return ["dsa", "oop", "dbms", "sql", "git", "complexity"]


class LearningRoadmapEngine:
    """Builds a study plan from the reviewed Interview Prep topics for the target role and the student's REAL saved
    results. It is deterministic and rule-based: no AI, no invented resources (tasks point to this platform's own
    practice pages). Context contract: target_role, training (progress dict), resume_suggestions, resume_weaknesses.
    """

    async def generate_roadmap(self, context: Dict[str, Any]) -> AILearningRoadmap:
        role = context.get("target_role") or "your target role"
        training = context.get("training") or {}
        per_topic = Counter((q["round"], q["topic"]) for q in all_seed() if q["round"] == "technical")
        role_topics = [t for t in _topics_for_role(context.get("target_role") or "") if ("technical", t) in per_topic]

        weak = {(t["round"], t["topic"]): t for t in training.get("weakest_topics", [])}
        practised = {(t["round"], t["topic"]) for t in (training.get("weakest_topics", []) + training.get("strongest_topics", []))}
        ordered: List[tuple] = [k for k in weak if k[0] == "technical"]
        ordered += [("technical", t) for t in role_topics if ("technical", t) not in ordered and ("technical", t) not in practised]
        ordered += [("technical", t) for t in role_topics if ("technical", t) not in ordered]
        modules: List[AILearningModule] = []

        for key in ordered[:MAX_TOPIC_MODULES]:
            label = TOPIC_INDEX[f"{key[0]}:{key[1]}"]["label"]
            n = per_topic[key]
            minutes = max(15, min(60, n * MINUTES_PER_QUESTION))
            if key in weak:
                why = f"You scored {weak[key]['score_pct']}% over {weak[key]['attempted']} answers here, below the 60% target."
                diff = "EASY" if weak[key]["score_pct"] < 45 else "MEDIUM"
            else:
                why = f"A core topic for {role}. You have no weak result recorded for it yet."
                diff = "MEDIUM"
            modules.append(AILearningModule(
                title=label, description=why, estimated_hours=round(minutes * 2 / 60, 1),
                tasks=[
                    AILearningTask(
                        title=f"Practise {label} questions", description=f"Answer the {n} reviewed {label} questions in practice mode; read each explanation.",
                        resource_type="PRACTICE", resource_url="/interview-prep?tab=technical", estimated_minutes=minutes, difficulty=diff),
                    AILearningTask(
                        title=f"Retry the {label} questions you missed", description="Use the results page to review mistakes, then repeat the topic until you score 70%+.",
                        resource_type="PRACTICE", resource_url="/interview-prep?tab=progress", estimated_minutes=minutes // 2, difficulty=diff),
                ],
            ))

        suggestions = context.get("resume_suggestions") or []
        missing = [m for m in (context.get("resume_weaknesses") or []) if isinstance(m, str)][:5]
        if suggestions or missing:
            tasks = [
                AILearningTask(title=f"Résumé: {s['category']}", description=s["text"], resource_type="EXERCISE", resource_url="/resume",
                               estimated_minutes=20, difficulty="EASY")
                for s in suggestions[:3]
            ]
            if missing:
                tasks.append(AILearningTask(
                    title="Check role keywords", resource_type="EXERCISE", resource_url="/resume", estimated_minutes=20, difficulty="EASY",
                    description=f"Skills typical for {role} that your résumé does not mention: {', '.join(missing)}. Add only those you really have; learn the rest."))
            modules.append(AILearningModule(
                title="Résumé readiness", description="From your latest résumé analysis.",
                estimated_hours=round(sum(t.estimated_minutes for t in tasks) / 60, 1), tasks=tasks))

        modules.append(AILearningModule(
            title="Mock interview checkpoint", description="Test the topics together under time pressure.", estimated_hours=0.5,
            tasks=[AILearningTask(
                title="Take a timed mock interview", description="Choose the rounds relevant to your target role.", resource_type="PRACTICE",
                resource_url="/interview-prep?tab=mock", estimated_minutes=30, difficulty="MEDIUM")],
        ))
        have_data = bool(training.get("total_scored_answers"))
        return AILearningRoadmap(
            title=f"Road to {role}" if context.get("target_role") else "Your study roadmap",
            description=(
                "Built from the reviewed Interview Prep topics for this role"
                + (" and your saved practice results" if have_data else " (no practice results saved yet, so topics follow the role)")
                + ". Rule-based, not AI. Time estimates are rough planning figures."
                + ("" if context.get("target_role") else " Set a target role in Interview Prep for a role-specific plan.")
            ),
            modules=modules,
        )

