import asyncio
import time
from typing import Any, Dict

from ..gateway import AIGateway


class EchoGateway(AIGateway):
    """A simple echo gateway for testing."""

    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()

        # Simulate network latency
        await asyncio.sleep(0.12)

        latency = int((time.time() - start_time) * 1000)
        provider_name = request.get("provider_name", "echo")
        model_name = request.get("model_name", "default")

        return {
            "status": "success",
            "response_text": f"Handshake complete with provider '{provider_name}' model '{model_name}'. Message: Hello Enterprise Admin!",
            "latency_ms": latency,
            "tokens_used": 42,
        }
