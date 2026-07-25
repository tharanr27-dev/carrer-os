import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Inject request_id into a context variable or attach to logger if using structlog
        # For simplicity with standard logging, we attach it to request state

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
