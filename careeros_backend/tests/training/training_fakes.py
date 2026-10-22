from typing import Any, List

from app.modules.training.llm import LLMUnavailable, TrainingLLM


class FakeLLM(TrainingLLM):
    """Scripted LLM: no network. Each complete_json call pops the next scripted response."""

    def __init__(self, responses: List[Any] = None, available: bool = True):
        super().__init__("test-key" if available else None, "test-model", 1.0)
        self.responses = list(responses or [])
        self.calls: List[dict] = []

    async def complete_json(self, system: str, user: str, max_tokens: int = 1800):
        self.calls.append({"system": system, "user": user})
        if not self.available:
            raise LLMUnavailable("not configured")
        if not self.responses:
            raise LLMUnavailable("no scripted response")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r
