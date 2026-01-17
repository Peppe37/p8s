"""
P8s CSRF Protection - Cross-Site Request Forgery middleware.

Provides Django-style CSRF protection:
- Automatic token generation
- Token validation on unsafe methods
- Cookie and header support

Example:
    ```python
    from p8s.csrf import CSRFMiddleware

    app.add_middleware(CSRFMiddleware)

    # In templates
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    </form>
    ```
"""

import hashlib
import hmac
import secrets
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


# Safe HTTP methods that don't require CSRF protection
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

# Token settings
CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FIELD_NAME = "csrf_token"


def generate_csrf_token() -> str:
    """
    Generate a secure random CSRF token.

    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def mask_token(token: str, salt: str | None = None) -> str:
    """
    Mask a token to prevent BREACH attacks.

    Args:
        token: The original token
        salt: Optional salt (generated if not provided)

    Returns:
        Masked token in format "salt:masked_value"
    """
    if salt is None:
        salt = secrets.token_hex(8)

    # XOR the token with a hash of the salt
    key = hashlib.sha256(salt.encode()).digest()
    token_bytes = token.encode()

    masked = bytes(b ^ key[i % len(key)] for i, b in enumerate(token_bytes))
    masked_hex = masked.hex()

    return f"{salt}:{masked_hex}"


def unmask_token(masked_token: str) -> str | None:
    """
    Unmask a masked token.

    Args:
        masked_token: Token in format "salt:masked_value"

    Returns:
        Original token or None if invalid
    """
    try:
        salt, masked_hex = masked_token.split(":", 1)
        masked = bytes.fromhex(masked_hex)

        key = hashlib.sha256(salt.encode()).digest()
        token_bytes = bytes(b ^ key[i % len(key)] for i, b in enumerate(masked))

        return token_bytes.decode()
    except (ValueError, UnicodeDecodeError):
        return None


def compare_tokens(token1: str, token2: str) -> bool:
    """
    Compare two tokens in constant time.

    Args:
        token1: First token
        token2: Second token

    Returns:
        True if tokens match
    """
    return hmac.compare_digest(token1, token2)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.

    Generates CSRF tokens and validates them on unsafe requests.

    Example:
        ```python
        from p8s.csrf import CSRFMiddleware

        app.add_middleware(
            CSRFMiddleware,
            cookie_name="csrf_token",
            exempt_paths=["/api/webhooks/"],
        )
        ```
    """

    def __init__(
        self,
        app,
        cookie_name: str = CSRF_COOKIE_NAME,
        header_name: str = CSRF_HEADER_NAME,
        field_name: str = CSRF_FIELD_NAME,
        cookie_secure: bool = False,
        cookie_httponly: bool = False,
        cookie_samesite: str = "lax",
        exempt_paths: list[str] | None = None,
    ):
        """
        Initialize CSRF middleware.

        Args:
            app: ASGI application
            cookie_name: Name of the CSRF cookie
            header_name: Name of the CSRF header
            field_name: Name of the form field
            cookie_secure: Set Secure flag on cookie
            cookie_httponly: Set HttpOnly flag (should be False for JS access)
            cookie_samesite: SameSite cookie attribute
            exempt_paths: Paths exempt from CSRF validation
        """
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.field_name = field_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.exempt_paths = exempt_paths or []

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF validation."""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    async def _get_submitted_token(self, request: Request) -> str | None:
        """Get CSRF token from request header or body."""
        # Try header first
        token = request.headers.get(self.header_name)
        if token:
            return token

        # Try form data
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            try:
                form = await request.form()
                token = form.get(self.field_name)
                if token:
                    return str(token)
            except Exception:
                pass

        # Try JSON body
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.json()
                if isinstance(body, dict):
                    token = body.get(self.field_name)
                    if token:
                        return str(token)
            except Exception:
                pass

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with CSRF validation."""
        # Get or generate token
        cookie_token = request.cookies.get(self.cookie_name)

        if not cookie_token:
            cookie_token = generate_csrf_token()

        # Store token in request state for templates
        request.state.csrf_token = cookie_token

        # Check if validation needed
        if request.method not in SAFE_METHODS and not self._is_exempt(request.url.path):
            submitted_token = await self._get_submitted_token(request)

            if not submitted_token:
                return JSONResponse(
                    {"detail": "CSRF token missing"},
                    status_code=403,
                )

            # Unmask if masked
            if ":" in submitted_token:
                submitted_token = unmask_token(submitted_token)

            if not submitted_token or not compare_tokens(cookie_token, submitted_token):
                return JSONResponse(
                    {"detail": "CSRF token invalid"},
                    status_code=403,
                )

        # Process request
        response = await call_next(request)

        # Set cookie if new token
        if not request.cookies.get(self.cookie_name):
            response.set_cookie(
                key=self.cookie_name,
                value=cookie_token,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
            )

        return response


def get_csrf_token(request: Request) -> str:
    """
    Get CSRF token from request.

    Args:
        request: Starlette/FastAPI request

    Returns:
        CSRF token string

    Raises:
        RuntimeError: If CSRFMiddleware not installed
    """
    if not hasattr(request.state, "csrf_token"):
        raise RuntimeError("CSRF token not available. Add CSRFMiddleware to the app.")
    return request.state.csrf_token


__all__ = [
    "CSRFMiddleware",
    "generate_csrf_token",
    "get_csrf_token",
    "mask_token",
    "unmask_token",
    "compare_tokens",
]
