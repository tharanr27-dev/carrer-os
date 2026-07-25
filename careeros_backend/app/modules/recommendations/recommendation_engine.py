import logging

from app.core.ai.pipeline import AIGlobalPipeline
from app.modules.recommendations.schemas import AIRecommendationItem, AIRecommendationList

logger = logging.getLogger("careeros")


class RecommendationEngine:
    """
    Routes the aggregated user context through the Global AI Pipeline
    to generate a raw candidate recommendation list.

    Does NOT perform ranking — that is the Ranking Engine's sole responsibility.
    """

    def __init__(self):
        self.ai_pipeline = AIGlobalPipeline()

    async def generate_candidates(self, context: dict) -> AIRecommendationList:
        logger.info(
            "Generating recommendation candidates via Global AI Pipeline",
            extra={"user_id": context.get("user_id")},
        )

        # Production flow:
        # 1. PromptManager fetches versioned "recommendation_v1" prompt template.
        # 2. ContextBuilder serialises the context dict into prompt variables.
        # 3. LLMRouter selects provider by cost / latency configuration.
        # 4. ResponseValidator enforces AIRecommendationList Pydantic schema.

        # --- Stubbed structured AI output ---
        return AIRecommendationList(
            recommendations=[
                AIRecommendationItem(
                    category="SKILL",
                    title="Master Docker & Kubernetes",
                    description="Docker was identified as a critical missing skill across your Resume ATS analysis and Career Report. Complete a hands-on Docker/K8s course and deploy a personal project.",
                    reason="Your ATS score is reduced by ~12 points because 'Docker' and 'Kubernetes' are absent. These keywords appear in 87% of Senior Backend Engineer JDs.",
                    confidence_score=0.93,
                    estimated_impact=0.85,
                    difficulty="MEDIUM",
                    related_skills=["Docker", "Kubernetes", "CI/CD", "DevOps"],
                    source_modules=["Phase 6 Resume", "Phase 5 Career Discovery"],
                ),
                AIRecommendationItem(
                    category="INTERVIEW",
                    title="Practice System Design Interviews",
                    description="Your technical interview score was 72/100 with System Design flagged as the primary weakness. Attempt 3 system design mock interviews this week.",
                    reason="Interview reports indicate System Design gaps in scalability questions. This directly impacts your target role eligibility.",
                    confidence_score=0.91,
                    estimated_impact=0.80,
                    difficulty="HARD",
                    related_skills=["System Design", "Distributed Systems", "Scalability"],
                    source_modules=["Phase 8 Interview"],
                ),
                AIRecommendationItem(
                    category="RESUME",
                    title="Add Quantified Achievements to Experience Section",
                    description="Your resume lacks quantifiable impact statements. Replace descriptive bullets with metrics (e.g., 'Reduced API latency by 40%').",
                    reason="Grammar and ATS analysis show strong prose but zero quantified metrics — a major differentiator for FAANG-tier applications.",
                    confidence_score=0.88,
                    estimated_impact=0.75,
                    difficulty="EASY",
                    related_skills=["Professional Writing"],
                    source_modules=["Phase 6 Resume", "Phase 9 Communication"],
                ),
                AIRecommendationItem(
                    category="COMMUNICATION",
                    title="Eliminate Filler Phrases in Professional Communication",
                    description="Communication analysis detected frequent use of 'like', 'um', and 'basically'. Complete a 2-week active voice and filler-word elimination programme.",
                    reason="Vocabulary score of 80/100 is good, but filler phrases reduce perceived confidence — critical for leadership roles.",
                    confidence_score=0.82,
                    estimated_impact=0.65,
                    difficulty="EASY",
                    related_skills=["Communication", "Professional Tone"],
                    source_modules=["Phase 9 Communication"],
                ),
            ]
        )
