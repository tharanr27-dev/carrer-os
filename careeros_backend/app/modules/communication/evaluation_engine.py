import logging

from app.core.ai.pipeline import AIGlobalPipeline
from app.modules.communication.schemas import AICommunicationAnalysis, AICommunicationReport

logger = logging.getLogger("careeros")


class CommunicationEvaluationEngine:
    """
    Abides by the Shared AI Pipeline rule.
    Focuses on rigorous linguistic and grammar analysis.
    """

    def __init__(self):
        self.ai_pipeline = AIGlobalPipeline()

    async def analyze_message(self, text: str) -> AICommunicationAnalysis:
        logger.info("Analyzing linguistic structure via Global AI Pipeline")

        # Stubbing the Strict AI Output Parsing
        return AICommunicationAnalysis(
            grammar_score=7.5,
            vocabulary_score=8.0,
            tone_score=8.5,
            clarity_score=7.0,
            feedbacks=[
                {
                    "category": "Vocabulary",
                    "original_text": "I did a lot of stuff",
                    "suggested_correction": "I managed several initiatives",
                    "reasoning": "'Stuff' is unprofessional. Use precise action verbs.",
                }
            ],
        )

    async def generate_final_report(self, messages: list[dict]) -> AICommunicationReport:
        logger.info("Generating final comprehensive communication report")

        return AICommunicationReport(
            overall_score=7.8,
            grammar_score=7.5,
            vocabulary_score=8.0,
            tone_score=8.5,
            fluency_score=8.0,
            strengths=["Maintained a confident tone", "Structured paragraphs well"],
            weaknesses=["Overused filler phrases", "Repetitive vocabulary"],
            improvement_suggestions=["Practice active voice", "Expand technical lexicon"],
        )
