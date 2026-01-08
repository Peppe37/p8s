"""
P8s Middleware - Django-style middleware system for FastAPI.

Provides:
- Middleware base class
- Request/Response processing hooks
- Built-in middlewares (CORS, Timing, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class Middleware(ABC):
    """
    Abstract base class for P8s middleware.
    
    Similar to Django's middleware, provides hooks for request/response processing.
    
    Example:
        ```python
        from p8s.middleware import Middleware
        
        class TimingMiddleware(Middleware):
            async def process_request(self, request, call_next):
                start = time.time()
                response = await call_next(request)
                duration = time.time() - start
                response.headers["X-Request-Time"] = str(duration)
                return response
        ```
    """
    
    @abstractmethod
    async def process_request(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Process the request.
        
        Args:
            request: The incoming request.
            call_next: Function to call the next middleware/handler.
        
        Returns:
            The response.
        """
        pass


class MiddlewareWrapper(BaseHTTPMiddleware):
    """Wrapper to adapt P8s Middleware to Starlette."""
    
    def __init__(self, app: Any, middleware: Middleware) -> None:
        super().__init__(app)
        self.middleware = middleware
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        return await self.middleware.process_request(request, call_next)


# ============================================================================
# Built-in Middlewares
# ============================================================================

class RequestTimingMiddleware(Middleware):
    """
    Add request timing header to responses.
    
    Adds X-Request-Time header showing processing duration in seconds.
    """
    
    async def process_request(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Request-Time"] = f"{process_time:.4f}"
        return response


class RequestLoggingMiddleware(Middleware):
    """
    Log all requests.
    
    Logs method, path, status code, and duration.
    """
    
    def __init__(self, logger: Any = None) -> None:
        import logging
        self.logger = logger or logging.getLogger("p8s.requests")
    
    async def process_request(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        
        self.logger.info(
            f"{request.method} {request.url.path} {response.status_code} ({duration:.3f}s)"
        )
        
        return response


class SecurityHeadersMiddleware(Middleware):
    """
    Add security headers to responses.
    
    Includes X-Content-Type-Options, X-Frame-Options, etc.
    """
    
    def __init__(
        self,
        content_type_options: str = "nosniff",
        frame_options: str = "DENY",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
    ) -> None:
        self.headers = {
            "X-Content-Type-Options": content_type_options,
            "X-Frame-Options": frame_options,
            "X-XSS-Protection": xss_protection,
            "Referrer-Policy": referrer_policy,
        }
    
    async def process_request(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for key, value in self.headers.items():
            response.headers[key] = value
        return response


class MaintenanceModeMiddleware(Middleware):
    """
    Return 503 when in maintenance mode.
    
    Example:
        ```python
        middleware = MaintenanceModeMiddleware(
            enabled=os.getenv("MAINTENANCE_MODE") == "true",
            allowed_ips=["127.0.0.1"],
        )
        ```
    """
    
    def __init__(
        self,
        enabled: bool = False,
        allowed_ips: list[str] | None = None,
        message: str = "Service temporarily unavailable for maintenance",
    ) -> None:
        self.enabled = enabled
        self.allowed_ips = set(allowed_ips or [])
        self.message = message
    
    async def process_request(self, request: Request, call_next) -> Response:
        if self.enabled:
            client_ip = request.client.host if request.client else ""
            if client_ip not in self.allowed_ips:
                from starlette.responses import JSONResponse
                return JSONResponse(
                    {"detail": self.message},
                    status_code=503,
                )
        return await call_next(request)


def add_middleware(app: Any, middleware: Middleware) -> None:
    """
    Add a P8s middleware to a FastAPI app.
    
    Args:
        app: FastAPI application.
        middleware: Middleware instance.
    """
    app.add_middleware(MiddlewareWrapper, middleware=middleware)


def configure_middlewares(app: Any, middlewares: list[Middleware]) -> None:
    """
    Configure multiple middlewares on a FastAPI app.
    
    Args:
        app: FastAPI application.
        middlewares: List of middleware instances (processed in order).
    """
    # Add in reverse order so first in list is executed first
    for middleware in reversed(middlewares):
        add_middleware(app, middleware)
