"""Optional LLM access for the training module.

No provider is configured in this repository by default. When ANTHROPIC_API_KEY is set (backend
environment only), question generation and rubric evaluation use it; otherwise callers fall back to
the reviewed question bank and rule-based scoring. The key is never sent to the frontend or logged.
"""

import json
import logging
import re
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("careeros")


class LLMUnavailable(Exception):
    """Raised for missing configuration, provider errors, timeouts and unparseable output."""


class TrainingLLM:
    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: Optional[str], model: str, timeout: float):
        # A blank/whitespace key (e.g. `ANTHROPIC_API_KEY= ` in .env) means "not configured".
        self.api_key = (api_key or "").strip() or None
        self.model = model
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def complete_json(self, system: str, user: str, max_tokens: int = 1800) -> Any:
        if not self.available:
            raise LLMUnavailable("AI provider is not configured")
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=5.0)) as client:
                resp = await client.post(self.API_URL, json=payload, headers=headers)
        except httpx.TimeoutException:
            logger.warning("Training LLM request timed out")
            raise LLMUnavailable("AI provider timed out")
        except httpx.HTTPError:
            logger.warning("Training LLM request failed")
            raise LLMUnavailable("AI provider unreachable")
        if resp.status_code != 200:
            logger.warning("Training LLM returned HTTP %s", resp.status_code)
            raise LLMUnavailable("AI provider error")
        try:
            blocks = resp.json().get("content") or []
            raw = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
            return extract_json(raw)
        except (ValueError, AttributeError, TypeError):
            raise LLMUnavailable("AI provider returned unreadable output")


def extract_json(raw: str) -> Any:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except ValueError:
        pass
    start = min([i for i in (raw.find("{"), raw.find("[")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("no JSON found")
    end = max(raw.rfind("}"), raw.rfind("]"))
    return json.loads(raw[start : end + 1])


_llm = TrainingLLM(settings.ANTHROPIC_API_KEY, settings.TRAINING_LLM_MODEL, settings.TRAINING_LLM_TIMEOUT_SECONDS)


def get_llm() -> TrainingLLM:
    return _llm
