"""
Traveo — Domain exception hierarchy + global handlers.

Every error leaves the API in the same envelope:
{"success": false, "error": {"code": "...", "message": "...", "details": {...}}, "request_id": "..."}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class TraveoError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"
    message: str = "Bad request"

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None, code: str | None = None):
        self.message = message or self.__class__.message
        self.details = details or {}
        if code:
            self.code = code
        super().__init__(self.message)


class NotFoundError(TraveoError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "Resource not found"


class UnauthorizedError(TraveoError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    message = "Authentication required"


class ForbiddenError(TraveoError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    message = "You are not allowed to perform this action"


class ConflictError(TraveoError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "Conflict"


class ValidationFailed(TraveoError):
    status_code = 422
    code = "validation_failed"
    message = "Validation failed"


class RateLimited(TraveoError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    message = "Too many requests, slow down"


# ── identity ──────────────────────────────────────────────────────
class OtpInvalid(UnauthorizedError):
    code = "otp_invalid"
    message = "Incorrect or expired OTP"


class IdentityMismatch(ValidationFailed):
    code = "identity_mismatch"
    message = "The college name on your ID card does not match the selected college"


class InvalidCollegeId(ValidationFailed):
    code = "invalid_college_id"
    message = "This ID number does not look like a valid ID for the selected college"


class IdentityAlreadyUsed(ConflictError):
    code = "identity_already_used"
    message = "This college ID is already registered with another account"


class StudentNotVerified(ForbiddenError):
    code = "student_not_verified"
    message = "Your student identity is still under verification"


class DriverNotVerified(ForbiddenError):
    code = "driver_not_verified"
    message = "Your driver profile is pending verification"


# ── rides ─────────────────────────────────────────────────────────
class RideStateError(ConflictError):
    code = "invalid_ride_state"
    message = "This action is not valid in the current ride state"


class ActiveRideExists(ConflictError):
    code = "active_ride_exists"
    message = "You already have an active ride. Finish or leave it first"


class GroupFull(ConflictError):
    code = "group_full"
    message = "No seats left in this ride"


class NotSameCollege(ForbiddenError):
    code = "not_same_college"
    message = "Only students of the same college can join this ride"


class RouteNotCompatible(ValidationFailed):
    code = "route_not_compatible"
    message = "Your pickup/drop is too far from this ride's route"


class OfferUnavailable(ConflictError):
    code = "offer_unavailable"
    message = "This ride offer is no longer available"


class CodeInvalid(ValidationFailed):
    code = "code_invalid"
    message = "That code does not match any passenger at this stop"


# ── handlers ───────────────────────────────────────────────────────
def _error_body(code: str, message: str, details: Any, request: Request) -> dict[str, Any]:
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "request_id": getattr(request.state, "request_id", None),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TraveoError)
    async def _traveo(request: Request, exc: TraveoError):
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details, request),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e.get("loc", [])[1:]), "message": e.get("msg")}
            for e in exc.errors()
        ]
        first = errors[0]["message"] if errors else "Invalid request"
        return ORJSONResponse(
            status_code=422,
            content=_error_body("validation_failed", first, {"errors": errors}, request),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}.get(
            exc.status_code, "http_error"
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, str(exc.detail), None, request),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.exception("unhandled_error", path=request.url.path)
        return ORJSONResponse(
            status_code=500,
            content=_error_body("internal_error", "Something went wrong on our side", None, request),
        )
