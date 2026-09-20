"""
Traveo Backend — Standard API Response Schemas

Every endpoint uses these schemas for consistent response formatting.
Matches the contract defined in Part 11 of the specification.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata returned with list endpoints."""

    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total matching items")
    total_pages: int = Field(ge=0, description="Total pages")


class ErrorDetail(BaseModel):
    """Error payload in failure responses."""

    code: str = Field(description="Machine-readable error code")
    details: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, str] | None = Field(
        default=None, description="Field-level validation errors"
    )


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope.

    Success:
        {"success": true, "message": "...", "data": {...}, "meta": {...}}

    Failure:
        {"success": false, "message": "...", "error": {"code": "...", ...}}
    """

    success: bool
    message: str
    data: T | None = None
    meta: PaginationMeta | None = None
    error: ErrorDetail | None = None


# ── Convenience Constructors ─────────────────────────────────

def success_response(
    data: Any = None,
    message: str = "Success",
    meta: PaginationMeta | None = None,
) -> dict[str, Any]:
    """Build a successful response dict."""
    response: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        response["meta"] = meta.model_dump()
    return response


def error_response(
    message: str = "An error occurred.",
    code: str = "ERROR",
    details: dict[str, Any] | None = None,
    fields: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build an error response dict."""
    error: dict[str, Any] = {"code": code}
    if details:
        error["details"] = details
    if fields:
        error["fields"] = fields
    return {
        "success": False,
        "message": message,
        "error": error,
    }


def paginated_response(
    data: list[Any],
    total_items: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> dict[str, Any]:
    """Build a paginated list response."""
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    return success_response(
        data=data,
        message=message,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )
