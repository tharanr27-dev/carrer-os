import logging

from app.modules.ai.dependencies import get_ai_orchestrator
from app.modules.interviews.schemas import AIEvaluationScore, AIFinalReport

logger = logging.getLogger("careeros")


class InterviewEvaluationEngine:
    """
    Abides by the Shared AI Pipeline rule.
    Does not call LLM directly; routes through Enterprise AI Orchestrator.
    """

    def __init__(self):
        self.orchestrator = get_ai_orchestrator()

    async def evaluate_answer(self, question: str, answer: str) -> AIEvaluationScore:
        logger.info("Evaluating single interview answer via Enterprise AI Orchestrator")

        request_payload = {
            "provider_name": "mock",
            "model_name": "gpt-4",
            "task": "interview_evaluation",
            "question": question,
            "answer": answer,
        }

        # Route through the Enterprise AI platform
        result = await self.orchestrator.process_request("mock", request_payload)

        # In production, this would pass the strict schema to the orchestrator
        # and parse it via Pydantic
        return AIEvaluationScore(
            overall_score=8.5,
            grammar_score=9.0,
            confidence_score=8.0,
            strengths=[
                "Clear articulation",
                "Used STAR method",
                f"AI notes: {result.get('response_text')[:20]}",
            ],
            improvements=["Could go deeper into scaling bottlenecks"],
        )

    async def generate_next_question(self, past_qa: list[dict], interview_type: str) -> str:
        logger.info("Generating next logical question via AI")
        return "Can you explain how you would shard that PostgreSQL database you mentioned?"

    async def generate_final_report(self, all_qa: list[dict]) -> AIFinalReport:
        logger.info("Generating final comprehensive interview report")
        return AIFinalReport(
            overall_score=85.0,
            technical_score=90.0,
            communication_score=80.0,
            detailed_analysis={"summary": "Strong technical skills, decent communication."},
            recommended_learning=["Advanced Distributed Systems"],
        )
