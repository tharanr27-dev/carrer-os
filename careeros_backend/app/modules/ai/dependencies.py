from .orchestrator import AIOrchestrator
from .providers.echo_gateway import EchoGateway

# Singleton instance of the orchestrator
_orchestrator = AIOrchestrator()

# Register providers
_orchestrator.register_gateway("mock", EchoGateway())
_orchestrator.register_gateway("test", EchoGateway())


def get_ai_orchestrator() -> AIOrchestrator:
    """Dependency injection for the AI Orchestrator."""
    return _orchestrator
