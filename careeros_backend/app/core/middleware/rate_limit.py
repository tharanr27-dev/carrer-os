import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.responses import error_response

# A simple token-bucket rate limiter interface for the middleware
# In production, this should map to Redis. For now, an abstract setup.


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # In memory fallback (do not use in prod)
        self._cache = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host if request.client else "unknown"

        # Rate limit logic (simplified for demonstration)
        current_time = time.time()
        if ip not in self._cache:
            self._cache[ip] = []

        self._cache[ip] = [t for t in self._cache[ip] if current_time - t < self.window_seconds]

        if len(self._cache[ip]) >= self.max_requests:
            req_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                content=error_response(
                    errors=["Too Many Requests"], message="Rate limit exceeded", request_id=req_id
                ).model_dump(),
            )

        self._cache[ip].append(current_time)
        return await call_next(request)
