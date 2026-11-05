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
    """Raised for missing configuration, provider errors, timeouts and unparseable output.

    `reason` is a stable machine-readable code (never provider text): not_configured, timeout, network, auth,
    rate_limited, quota, model_unavailable, overloaded, bad_output or error.
    """

    def __init__(self, message: str = "AI provider error", reason: str = "error"):
        super().__init__(message)
        self.reason = reason


def _reason_for_status(status: int, body: str) -> str:
    if status in (401, 403) or (status == 400 and "api key" in body):  # xAI answers 400 for a bad key
        return "auth"
    if status == 404:
        return "model_unavailable"
    if status == 429:
        return "quota" if any(w in body for w in ("credit", "billing", "quota")) else "rate_limited"
    if status in (500, 502, 503, 504, 529):
        return "overloaded"
    return "error"


class TrainingLLM:
    """Provider-neutral chat client. `provider` is "groq" or "xai" (both OpenAI-compatible chat completions) or "anthropic"."""

    ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
    XAI_URL = "https://api.x.ai/v1/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    OPENAI_STYLE = ("xai", "groq")

    def __init__(self, api_key: Optional[str], model: str, timeout: float, provider: str = "anthropic",
                 url: Optional[str] = None):
        # A blank/whitespace key (e.g. `XAI_API_KEY= ` in .env) means "not configured".
        self.api_key = (api_key or "").strip() or None
        self.model = model
        self.timeout = timeout
        self.provider = provider
        self.url = url or {"xai": self.XAI_URL, "groq": self.GROQ_URL}.get(provider, self.ANTHROPIC_URL)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _request(self, system: str, messages: list, max_tokens: int) -> tuple[dict, dict]:
        if self.provider in self.OPENAI_STYLE:
            payload = {"model": self.model, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": system}, *messages]}
            if self.provider == "groq" and "gpt-oss" in self.model:
                payload["reasoning_effort"] = "low"  # reasoning tokens count against max_tokens; keep replies fast
            return payload, {"Authorization": f"Bearer {self.api_key}", "content-type": "application/json"}
        payload = {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages}
        return payload, {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    def _text(self, body: dict) -> str:
        if self.provider in self.OPENAI_STYLE:
            return body["choices"][0]["message"].get("content") or ""
        blocks = body.get("content") or []
        return "".join(b.get("text", "") for b in blocks if isinstance(b, dict))

    async def _complete(self, system: str, messages: list, max_tokens: int) -> str:
        if not self.available:
            raise LLMUnavailable("AI provider is not configured", "not_configured")
        payload, headers = self._request(system, messages, max_tokens)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=5.0)) as client:
                resp = await client.post(self.url, json=payload, headers=headers)
        except httpx.TimeoutException:
            logger.warning("Training LLM request timed out")
            raise LLMUnavailable("AI provider timed out", "timeout")
        except httpx.HTTPError:
            logger.warning("Training LLM request failed")
            raise LLMUnavailable("AI provider unreachable", "network")
        if resp.status_code != 200:
            logger.warning("Training LLM returned HTTP %s", resp.status_code)
            raise LLMUnavailable("AI provider error", _reason_for_status(resp.status_code, resp.text[:500].lower()))
        try:
            return self._text(resp.json())
        except (ValueError, AttributeError, TypeError, KeyError, IndexError):
            raise LLMUnavailable("AI provider returned unreadable output", "bad_output")

    async def complete_json(self, system: str, user: str, max_tokens: int = 1800) -> Any:
        raw = await self._complete(system, [{"role": "user", "content": user}], max_tokens)
        try:
            return extract_json(raw)
        except (ValueError, TypeError):
            raise LLMUnavailable("AI provider returned unreadable output", "bad_output")

    async def complete_text(self, system: str, messages: list, max_tokens: int = 600) -> str:
        """Plain-text chat completion. `messages`: [{"role": "user"|"assistant", "content": str}, ...]."""
        text = (await self._complete(system, messages, max_tokens)).strip()
        if not text:
            raise LLMUnavailable("AI provider returned an empty reply", "bad_output")
        return text


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


def _build_llm() -> TrainingLLM:
    """Groq or Grok (xAI) when a key is set, otherwise Anthropic when ANTHROPIC_API_KEY is set.

    The provider is detected from the key itself: Groq keys start with "gsk_". The key may be supplied as
    GROQ_API_KEY or XAI_API_KEY."""
    key = (settings.GROQ_API_KEY or settings.XAI_API_KEY or "").strip()
    if key.startswith("gsk_"):
        return TrainingLLM(key, settings.GROQ_MODEL, settings.TRAINING_LLM_TIMEOUT_SECONDS,
                           provider="groq", url=settings.GROQ_API_URL)
    if key:
        return TrainingLLM(key, settings.XAI_MODEL, settings.TRAINING_LLM_TIMEOUT_SECONDS,
                           provider="xai", url=settings.XAI_API_URL)
    return TrainingLLM(settings.ANTHROPIC_API_KEY, settings.TRAINING_LLM_MODEL, settings.TRAINING_LLM_TIMEOUT_SECONDS)


_llm = _build_llm()


def get_llm() -> TrainingLLM:
    return _llm
