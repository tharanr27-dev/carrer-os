import logging

from app.modules.recommendations.schemas import AIRecommendationItem

logger = logging.getLogger("careeros")

# ---------------------------------------------------------------------------
# Configurable weight vector — adjust via environment variables or
# Admin Feature Flags (Phase 16) for A/B testing.
# ---------------------------------------------------------------------------
WEIGHTS = {
    "confidence": 0.30,
    "impact": 0.25,
    "learning_progress_boost": 0.15,
    "recency": 0.10,
    "acceptance_history": 0.05,
    "difficulty_penalty": -0.05,  # Hard items are downranked unless user score is high
    "goal_alignment": 0.10,
}

DIFFICULTY_FACTORS = {"EASY": 1.0, "MEDIUM": 0.85, "HARD": 0.70}


class RankingEngine:
    """
    Pure-Python, AI-free recommendation ranking.

    Deterministic, unit-testable, and decoupled from the LLM pipeline.
    Accepts AI-generated candidates + user context signals and produces
    a final float `rank_score` for each item.
    """

    def rank(
        self,
        candidates: list[AIRecommendationItem],
        context: dict,
        acceptance_rate: float = 0.5,
    ) -> list[tuple[AIRecommendationItem, float]]:
        """
        Returns a list of (candidate, rank_score) tuples, sorted desc.

        Args:
            candidates:      Raw AI recommendation items.
            context:         Aggregated user context from ContextAggregator.
            acceptance_rate: Historical acceptance rate (0–1) for this user.
        """
        ranked = []
        career_goals = {g.lower() for g in context.get("career_goals", [])}

        for item in candidates:
            score = 0.0

            # Core AI quality signals
            score += WEIGHTS["confidence"] * item.confidence_score
            score += WEIGHTS["impact"] * item.estimated_impact

            # Difficulty adjustment — penalise hard items for struggling users
            skill_levels = context.get("skill_progress", [])
            avg_skill = (
                sum(s["level"] for s in skill_levels) / len(skill_levels) if skill_levels else 50.0
            )
            diff_factor = DIFFICULTY_FACTORS.get(item.difficulty, 0.85)
            if item.difficulty == "HARD" and avg_skill < 50:
                diff_factor = 0.50  # Hard items with weak foundation ranked much lower
            score += WEIGHTS["difficulty_penalty"] * (1 - diff_factor)

            # Career goal alignment
            skill_overlap = sum(1 for skill in item.related_skills if skill.lower() in career_goals)
            goal_score = min(skill_overlap / max(len(item.related_skills), 1), 1.0)
            score += WEIGHTS["goal_alignment"] * goal_score

            # Historical acceptance boost
            score += WEIGHTS["acceptance_history"] * acceptance_rate

            ranked.append((item, round(score, 4)))

        ranked.sort(key=lambda x: x[1], reverse=True)
        logger.info(
            f"Ranked {len(ranked)} recommendations. Top score: {ranked[0][1] if ranked else 0}"
        )
        return ranked
