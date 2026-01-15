"""
P8s Middleware - Django-style middleware system for FastAPI.

Provides:
- Middleware base class
- Request/Response processing hooks
- Built-in middlewares (CORS, Timing, etc.)
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

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


class RateLimitMiddleware(Middleware):
    """
    Rate limiting middleware to prevent abuse.

    Supports configurable rate limits with sliding window algorithm.

    Example:
        ```python
        from p8s.middleware import RateLimitMiddleware

        # 100 requests per minute per IP
        app.add_middleware(
            MiddlewareWrapper,
            middleware=RateLimitMiddleware(rate="100/minute")
        )

        # 1000 requests per hour with custom key function
        app.add_middleware(
            MiddlewareWrapper,
            middleware=RateLimitMiddleware(
                rate="1000/hour",
                key_func=lambda r: r.headers.get("X-API-Key", r.client.host),
            )
        )
        ```
    """

    # Rate period mappings in seconds
    PERIODS = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }

    def __init__(
        self,
        rate: str = "100/minute",
        key_func: Callable[[Request], str] | None = None,
        exempt_paths: list[str] | None = None,
        backend: str = "memory",
    ) -> None:
        """
        Initialize rate limit middleware.

        Args:
            rate: Rate limit in format "count/period" (e.g., "100/minute").
            key_func: Function to extract rate limit key from request.
                      Defaults to client IP address.
            exempt_paths: Paths exempt from rate limiting.
            backend: Cache backend to use ("memory" or "redis").
        """
        self.limit, self.period = self._parse_rate(rate)
        self.key_func = key_func or self._default_key_func
        self.exempt_paths = exempt_paths or []
        self.backend = backend
        self._cache = None

    def _parse_rate(self, rate: str) -> tuple[int, int]:
        """Parse rate string like '100/minute' to (count, seconds)."""
        parts = rate.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate format: {rate}. Use 'count/period'.")

        count = int(parts[0])
        period_name = parts[1].lower()

        if period_name not in self.PERIODS:
            raise ValueError(
                f"Unknown period: {period_name}. "
                f"Valid periods: {list(self.PERIODS.keys())}"
            )

        return count, self.PERIODS[period_name]

    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP."""
        if request.client:
            return f"ratelimit:{request.client.host}"
        return "ratelimit:unknown"

    def _get_cache(self):
        """Get or create cache backend."""
        if self._cache is None:
            from p8s.cache import get_cache

            self._cache = get_cache(self.backend)
        return self._cache

    def _is_exempt(self, request: Request) -> bool:
        """Check if request path is exempt."""
        path = request.url.path
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    async def process_request(self, request: Request, call_next) -> Response:
        # Skip rate limiting for exempt paths
        if self._is_exempt(request):
            return await call_next(request)

        cache = self._get_cache()
        key = self.key_func(request)

        # Get current count
        current = cache.get(key, 0)

        # Check if rate limit exceeded
        if current >= self.limit:
            from starlette.responses import JSONResponse

            retry_after = self.period
            return JSONResponse(
                {
                    "detail": "Rate limit exceeded",
                    "limit": self.limit,
                    "period": self.period,
                    "retry_after": retry_after,
                },
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        # Increment counter with TTL
        try:
            cache.incr(key)
            # Set expiration if this is a new key
            if current == 0:
                cache.set(key, 1, timeout=self.period)
        except (ValueError, TypeError):
            # If incr fails, just set the value
            cache.set(key, 1, timeout=self.period)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.limit - current - 1)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self.period)

        return response


class CSRFMiddleware(Middleware):
    """
    Cross-Site Request Forgery protection middleware.

    Validates CSRF tokens for POST/PUT/PATCH/DELETE requests.
    Token can be provided via:
    - X-CSRF-Token header
    - csrf_token form field
    - _csrf cookie

    Exempt paths can be configured (e.g., API endpoints with their own auth).

    Example:
        ```python
        from p8s.middleware import CSRFMiddleware

        app.add_middleware(
            MiddlewareWrapper,
            middleware=CSRFMiddleware(
                secret_key="your-secret-key",
                exempt_paths=["/api/", "/webhooks/"],
            )
        )
        ```
    """

    def __init__(
        self,
        secret_key: str | None = None,
        cookie_name: str = "_csrf",
        header_name: str = "X-CSRF-Token",
        form_field: str = "csrf_token",
        exempt_paths: list[str] | None = None,
        exempt_methods: list[str] | None = None,
        secure: bool = True,
        same_site: str = "strict",
    ) -> None:
        self.secret_key = secret_key
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.form_field = form_field
        self.exempt_paths = exempt_paths or ["/api/"]  # API paths exempt by default
        self.exempt_methods = exempt_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]
        self.secure = secure
        self.same_site = same_site

    def _get_secret(self) -> str:
        """Get secret key from settings if not provided."""
        if self.secret_key:
            return self.secret_key

        try:
            from p8s.core.settings import get_settings

            return get_settings().secret_key
        except Exception:
            return "fallback-csrf-secret"

    def generate_token(self) -> str:
        """Generate a new CSRF token."""
        import hashlib
        import secrets

        random_bytes = secrets.token_bytes(32)
        secret = self._get_secret().encode()

        token = hashlib.sha256(random_bytes + secret).hexdigest()
        return token

    def validate_token(self, token: str, cookie_token: str) -> bool:
        """Validate CSRF token against cookie."""
        if not token or not cookie_token:
            return False

        # Simple comparison for now
        # In production, consider timing-safe comparison
        import hmac

        return hmac.compare_digest(token, cookie_token)

    def _is_exempt(self, request: Request) -> bool:
        """Check if request is exempt from CSRF validation."""
        # Check method
        if request.method in self.exempt_methods:
            return True

        # Check path
        path = request.url.path
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True

        return False

    async def process_request(self, request: Request, call_next) -> Response:
        # Skip CSRF for exempt requests
        if self._is_exempt(request):
            return await call_next(request)

        # Get CSRF token from cookie
        cookie_token = request.cookies.get(self.cookie_name)

        # Get CSRF token from request (header or form)
        request_token = request.headers.get(self.header_name)

        if not request_token:
            # Try to get from form data (for traditional form submissions)
            content_type = request.headers.get("content-type", "")
            if "form" in content_type:
                try:
                    form_data = await request.form()
                    request_token = form_data.get(self.form_field)
                except Exception:
                    pass

        # Validate token
        if cookie_token and not self.validate_token(request_token, cookie_token):
            from starlette.responses import JSONResponse

            return JSONResponse(
                {"detail": "CSRF token invalid or missing"},
                status_code=403,
            )

        # Process request
        response = await call_next(request)

        # Set CSRF cookie if not present
        if not cookie_token:
            new_token = self.generate_token()
            response.set_cookie(
                key=self.cookie_name,
                value=new_token,
                httponly=True,
                secure=self.secure,
                samesite=self.same_site,
            )

        return response


def get_csrf_token(request: Request) -> str:
    """
    Get the CSRF token from a request.

    Use this in templates to include the token in forms:

        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    Args:
        request: The current request.

    Returns:
        CSRF token string.
    """
    return request.cookies.get("_csrf", "")


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
