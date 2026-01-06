"""
P8s Exceptions - Custom exception handling.
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class P8sException(Exception):
    """
    Base P8s exception.
    
    All framework exceptions should inherit from this.
    """
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)


class NotFoundError(P8sException):
    """Resource not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=404, detail=detail)


class ValidationError(P8sException):
    """Validation error."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=422, detail=detail)


class AuthenticationError(P8sException):
    """Authentication required or failed."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=401, detail=detail)


class PermissionError(P8sException):
    """Permission denied."""
    
    def __init__(
        self,
        message: str = "Permission denied",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=403, detail=detail)


class ConfigurationError(P8sException):
    """Configuration error."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=500, detail=detail)


class AIError(P8sException):
    """AI/LLM related error."""
    
    def __init__(
        self,
        message: str = "AI operation failed",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=500, detail=detail)


async def p8s_exception_handler(
    request: Request,
    exc: P8sException,
) -> JSONResponse:
    """
    Global exception handler for P8s exceptions.
    
    Returns structured JSON error responses.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )
