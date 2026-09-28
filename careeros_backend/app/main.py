from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

# Exceptions & Responses
from app.core.exceptions import (
    global_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from app.core.middleware.rate_limit import RateLimitMiddleware

# Middlewares
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.middleware.security import SecurityHeadersMiddleware
from app.modules.admin.router import router as admin_router
from app.modules.analytics.router import router as analytics_router

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.career_discovery.router import router as discovery_router
from app.modules.communication.router import router as communication_router
from app.modules.community.router import router as community_router
from app.modules.interviews.router import router as interviews_router
from app.modules.learning.router import router as learning_router
from app.modules.mentor.router import router as mentor_router
from app.modules.placements.router import router as placements_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.recruiters.router import router as recruiters_router
from app.modules.resumes.router import router as resumes_router
from app.modules.users.router import router as users_router

from contextlib import asynccontextmanager
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# 1. Custom Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# 2. Middlewares (Order matters: in Starlette, add_middleware is LIFO.
#    The LAST middleware added becomes the OUTERMOST (first to run).
#    We want CORS to be the outermost so preflight requests are handled
#    before the rate-limiter can block them with a 429.

# 1. Innermost middleware added first
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# 2. Rate limiter – inside CORS so CORS headers always make it to the response
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
# 3. CORS outermost – wildcard "*" + allow_credentials=True is rejected by
#    browsers; use explicit origins instead.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Routes
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(
    discovery_router, prefix=f"{settings.API_V1_STR}/discovery", tags=["career_discovery"]
)
app.include_router(resumes_router, prefix=f"{settings.API_V1_STR}/resumes", tags=["resumes"])
app.include_router(mentor_router, prefix=f"{settings.API_V1_STR}/mentor", tags=["mentor"])
app.include_router(
    interviews_router, prefix=f"{settings.API_V1_STR}/interviews", tags=["interviews"]
)
app.include_router(
    communication_router, prefix=f"{settings.API_V1_STR}/communication", tags=["communication"]
)
app.include_router(learning_router, prefix=f"{settings.API_V1_STR}/learning", tags=["learning"])
app.include_router(
    recommendations_router,
    prefix=f"{settings.API_V1_STR}/recommendations",
    tags=["recommendations"],
)
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(community_router, prefix=f"{settings.API_V1_STR}/community", tags=["community"])
app.include_router(
    recruiters_router, prefix=f"{settings.API_V1_STR}/recruiters", tags=["recruiters"]
)
app.include_router(
    placements_router, prefix=f"{settings.API_V1_STR}/placements", tags=["placements"]
)
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])


@app.get("/health")
async def health_check():
    from app.core.responses import success_response

    return success_response(data={"status": "ok"}, message="System is healthy")


@app.get("/health/live", include_in_schema=False)
async def liveness_check():
    from app.core.responses import success_response

    return success_response(data={"status": "alive"}, message="Service is alive")


@app.get("/health/ready", include_in_schema=False)
async def readiness_check():
    from app.core.responses import success_response

    return success_response(data={"status": "ready"}, message="Service is ready")


@app.get("/metrics", include_in_schema=False)
async def metrics():
    payload = """# HELP app_up Service availability\n# TYPE app_up gauge\napp_up 1\n# HELP http_requests_total Total requests\n# TYPE http_requests_total counter\nhttp_requests_total 1\n"""
    return PlainTextResponse(payload, media_type="text/plain; version=0.0.4")
