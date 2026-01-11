"""
P8s Exceptions - Custom exception handling.
"""

from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse


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


def _wants_json(request: Request) -> bool:
    """
    Check if the request wants a JSON response.

    Returns True for:
    - Explicit application/json Accept header
    - API paths (/api/*, /admin/api/*, etc.)
    - XHR requests
    - When Accept doesn't include text/html

    Returns False (wants HTML) for:
    - Browser navigation (Accept includes text/html)
    """
    accept = request.headers.get("accept", "")

    # API paths always get JSON
    path = request.url.path
    if path.startswith("/api/") or "/api/" in path:
        return True

    # XHR requests get JSON
    if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
        return True

    # Explicit JSON request
    if "application/json" in accept:
        return True

    # Browser navigation - Accept includes text/html
    if "text/html" in accept:
        return False

    # Default: if Accept is empty or */*, check content-type header
    # Browser navigation usually has text/html in Accept
    # API clients usually have application/json or empty

    # Fetch/AJAX with no specific Accept header - treat as API
    if accept == "" or accept == "*/*":
        # Check if it looks like a browser request
        user_agent = request.headers.get("user-agent", "").lower()
        if "mozilla" in user_agent or "chrome" in user_agent or "safari" in user_agent:
            # Browser but not requesting HTML explicitly - likely direct URL access
            # Return HTML for better UX
            return False
        return True

    return True


def create_exception_handlers(
    debug: bool = False,
    templates_dir: Path | None = None,
):
    """
    Create exception handlers for P8s application.

    Args:
        debug: Whether to show detailed error pages.
        templates_dir: Directory to look for custom error templates.

    Returns:
        Dict of exception handlers to register.
    """
    from p8s.core.error_pages import (
        render_debug_404,
        render_debug_error,
        render_production_error,
    )

    async def p8s_exception_handler(
        request: Request,
        exc: P8sException,
    ) -> JSONResponse | HTMLResponse:
        """Handle P8s framework exceptions."""
        # Always return JSON for API requests
        if _wants_json(request):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "message": exc.message,
                    "detail": exc.detail,
                    "status_code": exc.status_code,
                },
            )

        # HTML response
        if debug:
            return render_debug_error(request, exc, exc.status_code)
        else:
            return render_production_error(
                request,
                exc.status_code,
                title=exc.message,
                templates_dir=templates_dir,
            )

    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse | HTMLResponse:
        """Handle FastAPI HTTP exceptions (404, etc.)."""
        # Always return JSON for API requests
        if _wants_json(request):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "message": exc.detail if isinstance(exc.detail, str) else "Error",
                    "status_code": exc.status_code,
                },
            )

        # HTML response
        if debug and exc.status_code == 404:
            return render_debug_404(request)
        elif debug:
            # For other HTTP exceptions in debug, create a synthetic exception
            class HTTPError(Exception):
                pass

            http_error = HTTPError(exc.detail)
            return render_debug_error(request, http_error, exc.status_code)
        else:
            return render_production_error(
                request,
                exc.status_code,
                templates_dir=templates_dir,
            )

    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse | HTMLResponse:
        """Handle uncaught Python exceptions."""
        # Always return JSON for API requests
        if _wants_json(request):
            if debug:
                import traceback

                return JSONResponse(
                    status_code=500,
                    content={
                        "error": True,
                        "message": str(exc),
                        "type": type(exc).__name__,
                        "traceback": traceback.format_exc(),
                        "status_code": 500,
                    },
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": True,
                        "message": "Internal server error",
                        "status_code": 500,
                    },
                )

        # HTML response
        if debug:
            return render_debug_error(request, exc, 500)
        else:
            return render_production_error(
                request,
                500,
                templates_dir=templates_dir,
            )

    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse | HTMLResponse:
        """Handle request validation errors."""
        errors = exc.errors()

        # Always return JSON for API requests
        if _wants_json(request):
            return JSONResponse(
                status_code=422,
                content={
                    "error": True,
                    "message": "Validation error",
                    "detail": errors,
                    "status_code": 422,
                },
            )

        # HTML response
        if debug:
            # Create a descriptive message
            error_messages = []
            for err in errors:
                loc = " -> ".join(str(l) for l in err["loc"])
                error_messages.append(f"{loc}: {err['msg']}")

            class ValidationException(Exception):
                pass

            validation_exc = ValidationException("\n".join(error_messages))
            return render_debug_error(request, validation_exc, 422)
        else:
            return render_production_error(
                request,
                422,
                title="Validation Error",
                message="The submitted data was invalid.",
                templates_dir=templates_dir,
            )

    return {
        P8sException: p8s_exception_handler,
        HTTPException: http_exception_handler,
        Exception: generic_exception_handler,
        RequestValidationError: validation_exception_handler,
    }


# Keep legacy handler for backward compatibility
async def p8s_exception_handler(
    request: Request,
    exc: P8sException,
) -> JSONResponse:
    """
    Global exception handler for P8s exceptions.

    Returns structured JSON error responses.

    DEPRECATED: Use create_exception_handlers() instead.
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
