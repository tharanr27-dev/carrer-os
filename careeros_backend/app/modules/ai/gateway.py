"""Gateway for AI platform"""

import abc
from typing import Any, Dict


class AIGateway(abc.ABC):
    @abc.abstractmethod
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process an AI request and return response data."""
        pass
