from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def success_response(
    data: Any = None, message: str = "Success", request_id: Optional[str] = None
) -> APIResponse:
    return APIResponse(success=True, message=message, data=data, request_id=request_id)


def error_response(
    errors: List[str], message: str = "Error", request_id: Optional[str] = None
) -> APIResponse:
    return APIResponse(success=False, message=message, errors=errors, request_id=request_id)
