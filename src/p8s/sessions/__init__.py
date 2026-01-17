"""
P8s Session Backend - Server-side session storage.

Provides Django-style session management with multiple backends:
- InMemorySessionBackend: For development/testing
- RedisSessionBackend: For production with Redis
- DatabaseSessionBackend: For database-backed sessions

Example:
    ```python
    from p8s.sessions import SessionMiddleware, RedisSessionBackend

    app.add_middleware(
        SessionMiddleware,
        backend=RedisSessionBackend(url="redis://localhost:6379"),
    )

    # In a route
    @app.get("/login/")
    async def login(request: Request):
        request.session["user_id"] = user.id
        return {"status": "logged_in"}
    ```
"""

import json
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SessionBackend(ABC):
    """
    Abstract base class for session backends.

    Implement this to create custom session storage.
    """

    @abstractmethod
    async def get(self, session_id: str) -> dict[str, Any] | None:
        """
        Get session data by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict or None if not found
        """
        pass

    @abstractmethod
    async def set(
        self,
        session_id: str,
        data: dict[str, Any],
        expires: datetime | None = None,
    ) -> None:
        """
        Save session data.

        Args:
            session_id: Session identifier
            data: Session data to store
            expires: Expiration datetime
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        pass

    def generate_session_id(self) -> str:
        """Generate a new secure session ID."""
        return secrets.token_urlsafe(32)


class InMemorySessionBackend(SessionBackend):
    """
    In-memory session storage for development/testing.

    Warning: Sessions are lost on server restart.
    """

    def __init__(self):
        self._sessions: dict[str, tuple[dict[str, Any], datetime | None]] = {}

    async def get(self, session_id: str) -> dict[str, Any] | None:
        if session_id not in self._sessions:
            return None

        data, expires = self._sessions[session_id]

        if expires and datetime.now() > expires:
            del self._sessions[session_id]
            return None

        return data

    async def set(
        self,
        session_id: str,
        data: dict[str, Any],
        expires: datetime | None = None,
    ) -> None:
        self._sessions[session_id] = (data, expires)

    async def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class RedisSessionBackend(SessionBackend):
    """
    Redis-backed session storage for production.

    Example:
        ```python
        backend = RedisSessionBackend(url="redis://localhost:6379")
        ```
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "session:",
        default_ttl: int = 86400,  # 24 hours
    ):
        """
        Initialize Redis session backend.

        Args:
            url: Redis connection URL
            prefix: Key prefix for sessions
            default_ttl: Default TTL in seconds
        """
        self.url = url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._redis = None

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
            except ImportError:
                raise ImportError(
                    "redis is required. Install with: pip install redis"
                )
            self._redis = redis.from_url(self.url)
        return self._redis

    async def get(self, session_id: str) -> dict[str, Any] | None:
        redis = await self._get_redis()
        key = f"{self.prefix}{session_id}"
        data = await redis.get(key)

        if data is None:
            return None

        return json.loads(data)

    async def set(
        self,
        session_id: str,
        data: dict[str, Any],
        expires: datetime | None = None,
    ) -> None:
        redis = await self._get_redis()
        key = f"{self.prefix}{session_id}"

        ttl = self.default_ttl
        if expires:
            ttl = int((expires - datetime.now()).total_seconds())

        await redis.set(key, json.dumps(data), ex=ttl)

    async def delete(self, session_id: str) -> None:
        redis = await self._get_redis()
        key = f"{self.prefix}{session_id}"
        await redis.delete(key)


class Session(dict):
    """
    Session object that tracks modifications.

    Acts like a dict but tracks if data has changed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._modified = False
        self._new = False

    @property
    def modified(self) -> bool:
        """Check if session was modified."""
        return self._modified

    @property
    def is_new(self) -> bool:
        """Check if this is a new session."""
        return self._new

    def __setitem__(self, key, value):
        self._modified = True
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self._modified = True
        super().__delitem__(key)

    def clear(self):
        self._modified = True
        super().clear()

    def pop(self, *args):
        self._modified = True
        return super().pop(*args)

    def update(self, *args, **kwargs):
        self._modified = True
        super().update(*args, **kwargs)


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for session management.

    Automatically loads and saves session data for each request.

    Example:
        ```python
        from p8s.sessions import SessionMiddleware, InMemorySessionBackend

        app.add_middleware(
            SessionMiddleware,
            backend=InMemorySessionBackend(),
            cookie_name="session_id",
            max_age=86400,  # 24 hours
        )
        ```
    """

    def __init__(
        self,
        app,
        backend: SessionBackend | None = None,
        cookie_name: str = "session_id",
        max_age: int = 86400,  # 24 hours
        path: str = "/",
        secure: bool = False,
        httponly: bool = True,
        samesite: str = "lax",
    ):
        """
        Initialize session middleware.

        Args:
            app: ASGI application
            backend: Session storage backend
            cookie_name: Cookie name for session ID
            max_age: Cookie max age in seconds
            path: Cookie path
            secure: Set Secure flag on cookie
            httponly: Set HttpOnly flag on cookie
            samesite: SameSite cookie attribute
        """
        super().__init__(app)
        self.backend = backend or InMemorySessionBackend()
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.path = path
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with session handling."""
        # Get or create session ID
        session_id = request.cookies.get(self.cookie_name)
        is_new = session_id is None

        if is_new:
            session_id = self.backend.generate_session_id()

        # Load session data
        session_data = await self.backend.get(session_id)
        session = Session(session_data or {})
        session._new = is_new

        # Attach to request
        request.state.session = session

        # Process request
        response = await call_next(request)

        # Save session if modified
        if session.modified or is_new:
            expires = datetime.now() + timedelta(seconds=self.max_age)
            await self.backend.set(session_id, dict(session), expires)

            # Set cookie
            response.set_cookie(
                key=self.cookie_name,
                value=session_id,
                max_age=self.max_age,
                path=self.path,
                secure=self.secure,
                httponly=self.httponly,
                samesite=self.samesite,
            )

        return response


def get_session(request: Request) -> Session:
    """
    Get the session from a request.

    Args:
        request: FastAPI/Starlette request

    Returns:
        Session object

    Raises:
        RuntimeError: If SessionMiddleware not installed
    """
    if not hasattr(request.state, "session"):
        raise RuntimeError(
            "Session not available. Add SessionMiddleware to the app."
        )
    return request.state.session


__all__ = [
    "SessionBackend",
    "InMemorySessionBackend",
    "RedisSessionBackend",
    "Session",
    "SessionMiddleware",
    "get_session",
]
