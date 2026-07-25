from typing import Any, Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession


class AIContentModerationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def moderate_content(self, text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Uses existing AI Global Pipeline to check for toxicity/spam.
        Returns a tuple: (is_safe: bool, scores: Dict)
        """
        # Mock logic representing an integration with the AI pipeline.
        # In a real implementation, it sends the text to the LLM router and parses the JSON response.

        # We assume safe for now unless text contains specific bad words (mock)
        bad_words = ["spam", "toxic", "hate"]
        is_safe = True
        scores = {"toxicity": 0.0, "spam": 0.0}

        lower_text = text.lower()
        if any(word in lower_text for word in bad_words):
            is_safe = False
            scores = {"toxicity": 0.9, "spam": 0.8}

        return is_safe, scores
