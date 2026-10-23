from typing import Any, Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession


class AIContentModerationEngine:  # historical name; rule-based, see moderate_content
    def __init__(self, db: AsyncSession):
        self.db = db

    async def moderate_content(self, text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Simple keyword filter. It is NOT an AI model: it only flags a few listed words and misses almost
        everything else (toxicity, spam, harassment in other words). Human moderation is still required.
        Returns a tuple: (is_safe: bool, scores: Dict) where the scores are fixed markers, not probabilities.
        """
        bad_words = ["spam", "toxic", "hate"]
        is_safe = True
        scores = {"toxicity": 0.0, "spam": 0.0}

        lower_text = text.lower()
        if any(word in lower_text for word in bad_words):
            is_safe = False
            scores = {"toxicity": 0.9, "spam": 0.8}

        return is_safe, scores
