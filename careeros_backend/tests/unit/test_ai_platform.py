import pytest

from app.modules.ai.dependencies import get_ai_orchestrator
from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.providers.echo_gateway import EchoGateway


@pytest.mark.asyncio
async def test_echo_gateway():
    """Test that the mock Echo Gateway returns correctly structured response."""
    gateway = EchoGateway()
    payload = {"provider_name": "mock", "model_name": "test-gpt"}

    response = await gateway.handle(payload)

    assert response["status"] == "success"
    assert "Handshake complete" in response["response_text"]
    assert response["tokens_used"] == 42
    assert "latency_ms" in response


@pytest.mark.asyncio
async def test_ai_orchestrator_routing():
    """Test that the orchestrator routes to the correct gateway."""
    orchestrator = AIOrchestrator()
    orchestrator.register_gateway("mock", EchoGateway())

    payload = {"provider_name": "mock", "model_name": "test-gpt"}
    response = await orchestrator.process_request("mock", payload)

    assert response["status"] == "success"


@pytest.mark.asyncio
async def test_ai_orchestrator_unknown_provider():
    """Test that the orchestrator raises an error for unregistered providers."""
    orchestrator = AIOrchestrator()

    with pytest.raises(ValueError, match="Unknown AI provider: non_existent"):
        await orchestrator.process_request("non_existent", {})


def test_dependencies_singleton():
    """Test that get_ai_orchestrator returns a singleton instance."""
    instance1 = get_ai_orchestrator()
    instance2 = get_ai_orchestrator()

    assert instance1 is instance2
    assert "mock" in instance1.gateways
