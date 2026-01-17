"""
P8s i18n Middleware - Language detection and activation.

Provides middleware that:
- Detects user's preferred language from Accept-Language header
- Activates the appropriate language for each request
- Optionally uses URL prefix for language selection

Example:
    ```python
    from p8s import P8s
    from p8s.i18n.middleware import LocaleMiddleware

    app = P8s()
    app.add_middleware(LocaleMiddleware, default_language="en")
    ```
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from p8s.i18n import activate, deactivate


class LocaleMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic language detection and activation.

    Detects language from:
    1. URL prefix (if use_url_prefix=True): /it/products/
    2. Accept-Language header: Accept-Language: it-IT,it;q=0.9,en;q=0.8
    3. Cookie (if set): language=it
    4. Default language fallback

    Example:
        ```python
        from p8s.i18n.middleware import LocaleMiddleware

        app.add_middleware(
            LocaleMiddleware,
            default_language="en",
            supported_languages=["en", "it", "fr", "de"],
        )
        ```
    """

    def __init__(
        self,
        app,
        default_language: str = "en",
        supported_languages: list[str] | None = None,
        use_url_prefix: bool = False,
        cookie_name: str = "language",
    ):
        """
        Initialize locale middleware.

        Args:
            app: ASGI application
            default_language: Default language if none detected
            supported_languages: List of supported language codes
            use_url_prefix: Whether to detect language from URL prefix
            cookie_name: Name of cookie storing language preference
        """
        super().__init__(app)
        self.default_language = default_language
        self.supported_languages = supported_languages or ["en"]
        self.use_url_prefix = use_url_prefix
        self.cookie_name = cookie_name

    def parse_accept_language(self, header: str) -> list[str]:
        """
        Parse Accept-Language header into list of language codes.

        Args:
            header: Accept-Language header value

        Returns:
            List of language codes sorted by preference
        """
        languages = []

        if not header:
            return languages

        for part in header.split(","):
            part = part.strip()
            if not part:
                continue

            # Handle quality values: en-US;q=0.9
            if ";" in part:
                lang, quality = part.split(";", 1)
                lang = lang.strip()
                try:
                    q = float(quality.split("=")[1])
                except (IndexError, ValueError):
                    q = 1.0
            else:
                lang = part
                q = 1.0

            # Normalize: en-US -> en
            if "-" in lang:
                lang = lang.split("-")[0]

            languages.append((lang.lower(), q))

        # Sort by quality descending
        languages.sort(key=lambda x: x[1], reverse=True)
        return [lang for lang, _ in languages]

    def detect_language(self, request: Request) -> str:
        """
        Detect the preferred language from the request.

        Args:
            request: Starlette/FastAPI request

        Returns:
            Detected language code
        """
        # 1. Check URL prefix
        if self.use_url_prefix:
            path_parts = request.url.path.strip("/").split("/")
            if path_parts and path_parts[0] in self.supported_languages:
                return path_parts[0]

        # 2. Check cookie
        cookie_lang = request.cookies.get(self.cookie_name)
        if cookie_lang and cookie_lang in self.supported_languages:
            return cookie_lang

        # 3. Parse Accept-Language header
        accept_language = request.headers.get("accept-language", "")
        for lang in self.parse_accept_language(accept_language):
            if lang in self.supported_languages:
                return lang

        # 4. Default
        return self.default_language

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with language activation.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Detect and activate language
        language = self.detect_language(request)
        activate(language)

        # Store language in request state for access in handlers
        request.state.language = language

        try:
            response = await call_next(request)
            return response
        finally:
            # Reset language context
            deactivate()


def get_language_from_request(request: Request) -> str:
    """
    Get the active language from a request.

    Args:
        request: Starlette/FastAPI request

    Returns:
        Language code if set, otherwise 'en'
    """
    return getattr(request.state, "language", "en")
