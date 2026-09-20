"""
Traveo Backend — Centralized Exception Hierarchy

Every domain has its own exception class. The global exception handler
translates these into consistent API error responses. Stack traces are
never exposed to clients.
"""

from __future__ import annotations

from typing import Any


class TraveoError(Exception):
    """Base exception for all Traveo domain errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        self.status_code = status_code or self.__class__.status_code
        self.details = details or {}
        super().__init__(self.message)


# ── Authentication ───────────────────────────────────────────
class AuthenticationError(TraveoError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication failed."


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid credentials provided."


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"
    message = "Token has expired."


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    message = "Invalid or malformed token."


class OTPError(AuthenticationError):
    error_code = "OTP_ERROR"
    message = "OTP verification failed."


class OTPExpiredError(OTPError):
    error_code = "OTP_EXPIRED"
    message = "OTP has expired."


class OTPInvalidError(OTPError):
    error_code = "OTP_INVALID"
    message = "Invalid OTP."


class OTPRateLimitError(OTPError):
    status_code = 429
    error_code = "OTP_RATE_LIMIT"
    message = "Too many OTP attempts. Please try again later."


# ── Authorization ────────────────────────────────────────────
class AuthorizationError(TraveoError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class InsufficientPermissionsError(AuthorizationError):
    error_code = "INSUFFICIENT_PERMISSIONS"
    message = "Insufficient permissions."


# ── Validation ───────────────────────────────────────────────
class ValidationError(TraveoError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed."


# ── Not Found ────────────────────────────────────────────────
class NotFoundError(TraveoError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found."


class UserNotFoundError(NotFoundError):
    error_code = "USER_NOT_FOUND"
    message = "User not found."


class RideNotFoundError(NotFoundError):
    error_code = "RIDE_NOT_FOUND"
    message = "Ride not found."


class DriverNotFoundError(NotFoundError):
    error_code = "DRIVER_NOT_FOUND"
    message = "Driver not found."


class GroupNotFoundError(NotFoundError):
    error_code = "GROUP_NOT_FOUND"
    message = "Ride group not found."


# ── Conflict ─────────────────────────────────────────────────
class ConflictError(TraveoError):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict."


class DuplicateError(ConflictError):
    error_code = "DUPLICATE"
    message = "Resource already exists."


class UserAlreadyExistsError(DuplicateError):
    error_code = "USER_ALREADY_EXISTS"
    message = "A user with this phone or email already exists."


# ── Ride ─────────────────────────────────────────────────────
class RideError(TraveoError):
    status_code = 400
    error_code = "RIDE_ERROR"
    message = "Ride operation failed."


class InvalidRideStateError(RideError):
    error_code = "INVALID_RIDE_STATE"
    message = "Ride is not in a valid state for this operation."


class DuplicateBookingError(RideError):
    status_code = 409
    error_code = "DUPLICATE_BOOKING"
    message = "You already have an active ride request."


class GroupFullError(RideError):
    error_code = "GROUP_FULL"
    message = "Ride group is at maximum capacity."


class GroupLockedError(RideError):
    error_code = "GROUP_LOCKED"
    message = "Ride group is locked. No modifications allowed."


class NoDriverFoundError(RideError):
    error_code = "NO_DRIVER_FOUND"
    message = "No available drivers found."


class DriverAlreadyAssignedError(RideError):
    status_code = 409
    error_code = "DRIVER_ALREADY_ASSIGNED"
    message = "A driver has already been assigned to this ride."


# ── Payment ──────────────────────────────────────────────────
class PaymentError(TraveoError):
    status_code = 400
    error_code = "PAYMENT_ERROR"
    message = "Payment operation failed."


class PaymentFailedError(PaymentError):
    error_code = "PAYMENT_FAILED"
    message = "Payment processing failed."


class RefundError(PaymentError):
    error_code = "REFUND_ERROR"
    message = "Refund processing failed."


class InsufficientBalanceError(PaymentError):
    error_code = "INSUFFICIENT_BALANCE"
    message = "Insufficient wallet balance."


# ── Wallet ───────────────────────────────────────────────────
class WalletError(TraveoError):
    status_code = 400
    error_code = "WALLET_ERROR"
    message = "Wallet operation failed."


# ── Maps ─────────────────────────────────────────────────────
class MapsError(TraveoError):
    status_code = 502
    error_code = "MAPS_SERVICE_ERROR"
    message = "Maps service unavailable."


# ── Notification ─────────────────────────────────────────────
class NotificationError(TraveoError):
    status_code = 502
    error_code = "NOTIFICATION_ERROR"
    message = "Notification delivery failed."


# ── Chat ─────────────────────────────────────────────────────
class ChatError(TraveoError):
    status_code = 400
    error_code = "CHAT_ERROR"
    message = "Chat operation failed."


# ── Rate Limiting ────────────────────────────────────────────
class RateLimitError(TraveoError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."


# ── Database ─────────────────────────────────────────────────
class DatabaseError(TraveoError):
    status_code = 500
    error_code = "DATABASE_ERROR"
    message = "A database error occurred."
