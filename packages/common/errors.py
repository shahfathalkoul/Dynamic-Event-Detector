"""Custom exception hierarchy and FastAPI exception handlers.

Usage::

    from packages.common.errors import PlatformError, RetryableError

    raise RetryableError("Qdrant unavailable", retry_after_seconds=5)
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class PlatformError(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, status_code: int = 500, detail: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}


class RetryableError(PlatformError):
    """Transient error that may succeed on retry."""

    def __init__(self, message: str, retry_after_seconds: int = 5, **kwargs):
        super().__init__(message, status_code=503, **kwargs)
        self.retry_after_seconds = retry_after_seconds


class AuthError(PlatformError):
    """Authentication or authorization failure."""

    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class ForbiddenError(PlatformError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(PlatformError):
    """Resource not found."""

    def __init__(self, message: str = "Not found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class RateLimitError(PlatformError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60, **kwargs):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class ValidationError(PlatformError):
    """Input validation failure."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=422, **kwargs)


# ── FastAPI exception handlers ───────────────────────────────────────

async def platform_error_handler(_request: Request, exc: PlatformError) -> JSONResponse:
    """Map PlatformError subclasses to proper HTTP responses."""
    headers = {}
    if isinstance(exc, RetryableError):
        headers["Retry-After"] = str(exc.retry_after_seconds)
    if isinstance(exc, RateLimitError):
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "detail": exc.detail,
        },
        headers=headers,
    )


def register_error_handlers(app) -> None:
    """Register all custom exception handlers on a FastAPI app."""
    app.add_exception_handler(PlatformError, platform_error_handler)
