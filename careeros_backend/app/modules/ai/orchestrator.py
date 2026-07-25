from typing import Any, Dict

from .gateway import AIGateway


class AIOrchestrator:
    """Orchestrates AI requests to various provider gateways."""

    def __init__(self):
        self.gateways: Dict[str, AIGateway] = {}

    def register_gateway(self, provider_name: str, gateway: AIGateway):
        """Register a new AI gateway provider."""
        self.gateways[provider_name] = gateway

    async def process_request(self, provider_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the specified provider."""
        if provider_name not in self.gateways:
            raise ValueError(f"Unknown AI provider: {provider_name}")

        gateway = self.gateways[provider_name]
        return await gateway.handle(request)
