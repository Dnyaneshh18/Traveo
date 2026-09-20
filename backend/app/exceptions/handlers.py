"""
Traveo Backend — Exception Handlers

Registers global exception handlers with FastAPI.
Transforms domain exceptions into consistent JSON error responses.
Stack traces are logged but never sent to clients.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import TraveoError

logger = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(TraveoError)
    async def traveo_error_handler(
        request: Request, exc: TraveoError
    ) -> ORJSONResponse:
        logger.warning(
            "domain_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=str(request.url.path),
            details=exc.details,
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "error": {
                    "code": exc.error_code,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        fields: dict[str, str] = {}
        for error in exc.errors():
            loc = ".".join(str(l) for l in error["loc"] if l != "body")
            fields[loc] = error["msg"]
        logger.warning(
            "validation_error",
            path=str(request.url.path),
            fields=fields,
        )
        return ORJSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation failed.",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "fields": fields,
                },
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail or "An error occurred.",
                "error": {
                    "code": "HTTP_ERROR",
                    "details": {},
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> ORJSONResponse:
        logger.exception(
            "unhandled_error",
            path=str(request.url.path),
            error=str(exc),
        )
        return ORJSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred.",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "details": {},
                },
            },
        )
