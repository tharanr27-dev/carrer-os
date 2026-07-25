import logging
from typing import Dict, List

from app.modules.ai.dependencies import get_ai_orchestrator
from app.modules.career_discovery.schemas import AICareerAnalysis

logger = logging.getLogger("careeros")


class CareerDiscoveryAIEngine:
    """
    Abstraction layer for AI interaction.
    Now utilizes the Enterprise AI Platform's Gateway and Orchestrator.
    """

    def __init__(self):
        self.orchestrator = get_ai_orchestrator()

    async def generate_career_report(self, raw_answers: List[Dict]) -> AICareerAnalysis:
        logger.info("Initiating AI Career Discovery Analysis via AI Orchestrator...")

        request_payload = {
            "provider_name": "mock",  # Using mock for now
            "model_name": "gpt-4",
            "task": "career_discovery",
            "context": raw_answers,
        }

        # Route through the Enterprise AI platform
        result = await self.orchestrator.process_request("mock", request_payload)

        # Convert result back into expected schema
        # In production, we'd use a Pydantic parser on the LLM output.
        simulated_response = AICareerAnalysis(
            personality_analysis={
                "traits": ["Analytical", "Introverted"],
                "raw_ai_message": result.get("response_text"),
            },
            interest_analysis={"fields": ["Software Engineering", "Data Science"]},
            skill_gaps={"missing": ["System Design", "Cloud Infrastructure"]},
            career_timeline={"1_year": "Junior Developer", "3_year": "Mid-level Engineer"},
            recommended_matches=[],
        )

        logger.info("AI Analysis completed successfully via Orchestrator.")
        return simulated_response
