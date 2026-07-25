from abc import ABC, abstractmethod
from typing import Any, Dict


class OAuthProvider(ABC):
    @abstractmethod
    def get_login_url(self, state: str) -> str:
        """Returns the authorization URL for the provider."""
        pass

    @abstractmethod
    async def exchange_code_for_user(self, code: str) -> Dict[str, Any]:
        """Exchanges the authorization code for user info from the provider."""
        pass
