from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import logger
from app.core.responses import error_response


class APIException(HTTPException):
    """Standard API exception for service-layer HTTP errors."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
    req_id = getattr(request.state, "request_id", None)
    logger.warning(f"Validation error: {errors}", extra={"request_id": req_id})

    return JSONResponse(
        status_code=422,
        content=error_response(
            errors=errors, message="Validation Failed", request_id=req_id
        ).model_dump(),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    req_id = getattr(request.state, "request_id", None)
    logger.error(f"Database error: {str(exc)}", exc_info=True, extra={"request_id": req_id})

    return JSONResponse(
        status_code=500,
        content=error_response(
            errors=["Internal database error occurred."],
            message="Database Error",
            request_id=req_id,
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={"request_id": req_id})

    return JSONResponse(
        status_code=500,
        content=error_response(
            errors=["An unexpected error occurred."],
            message="Internal Server Error",
            request_id=req_id,
        ).model_dump(),
    )
