"""
Tests for P8s Session Backend.
"""

import pytest
from datetime import datetime, timedelta


class TestSessionBackend:
    """Test SessionBackend base class."""

    def test_session_backend_import(self):
        """Test SessionBackend can be imported."""
        from p8s.sessions import SessionBackend

        assert SessionBackend is not None


class TestInMemorySessionBackend:
    """Test InMemorySessionBackend."""

    def test_inmemory_import(self):
        """Test InMemorySessionBackend can be imported."""
        from p8s.sessions import InMemorySessionBackend

        assert InMemorySessionBackend is not None

    def test_inmemory_init(self):
        """Test InMemorySessionBackend initialization."""
        from p8s.sessions import InMemorySessionBackend

        backend = InMemorySessionBackend()
        assert backend._sessions == {}

    @pytest.mark.asyncio
    async def test_inmemory_set_get(self):
        """Test setting and getting session data."""
        from p8s.sessions import InMemorySessionBackend

        backend = InMemorySessionBackend()
        await backend.set("test_id", {"user_id": 123})

        data = await backend.get("test_id")
        assert data == {"user_id": 123}

    @pytest.mark.asyncio
    async def test_inmemory_get_nonexistent(self):
        """Test getting nonexistent session returns None."""
        from p8s.sessions import InMemorySessionBackend

        backend = InMemorySessionBackend()

        data = await backend.get("nonexistent")
        assert data is None

    @pytest.mark.asyncio
    async def test_inmemory_delete(self):
        """Test deleting a session."""
        from p8s.sessions import InMemorySessionBackend

        backend = InMemorySessionBackend()
        await backend.set("test_id", {"data": "value"})
        await backend.delete("test_id")

        data = await backend.get("test_id")
        assert data is None

    def test_generate_session_id(self):
        """Test session ID generation."""
        from p8s.sessions import InMemorySessionBackend

        backend = InMemorySessionBackend()
        session_id = backend.generate_session_id()

        assert len(session_id) > 20
        assert isinstance(session_id, str)


class TestRedisSessionBackend:
    """Test RedisSessionBackend."""

    def test_redis_import(self):
        """Test RedisSessionBackend can be imported."""
        from p8s.sessions import RedisSessionBackend

        assert RedisSessionBackend is not None

    def test_redis_init(self):
        """Test RedisSessionBackend initialization."""
        from p8s.sessions import RedisSessionBackend

        backend = RedisSessionBackend(
            url="redis://localhost:6379",
            prefix="mysession:",
            default_ttl=3600,
        )

        assert backend.url == "redis://localhost:6379"
        assert backend.prefix == "mysession:"
        assert backend.default_ttl == 3600


class TestSession:
    """Test Session class."""

    def test_session_import(self):
        """Test Session can be imported."""
        from p8s.sessions import Session

        assert Session is not None

    def test_session_acts_like_dict(self):
        """Test Session behaves like a dict."""
        from p8s.sessions import Session

        session = Session({"key": "value"})
        assert session["key"] == "value"

    def test_session_modified_on_setitem(self):
        """Test Session tracks modifications."""
        from p8s.sessions import Session

        session = Session()
        assert session.modified is False

        session["user_id"] = 123
        assert session.modified is True

    def test_session_modified_on_delete(self):
        """Test Session tracks deletions."""
        from p8s.sessions import Session

        session = Session({"key": "value"})
        session._modified = False

        del session["key"]
        assert session.modified is True

    def test_session_modified_on_clear(self):
        """Test Session tracks clear."""
        from p8s.sessions import Session

        session = Session({"key": "value"})
        session._modified = False

        session.clear()
        assert session.modified is True


class TestSessionMiddleware:
    """Test SessionMiddleware."""

    def test_middleware_import(self):
        """Test SessionMiddleware can be imported."""
        from p8s.sessions import SessionMiddleware

        assert SessionMiddleware is not None

    def test_middleware_defaults(self):
        """Test SessionMiddleware default settings."""
        from p8s.sessions import SessionMiddleware, InMemorySessionBackend

        middleware = SessionMiddleware(app=None)

        assert middleware.cookie_name == "session_id"
        assert middleware.max_age == 86400
        assert middleware.path == "/"
        assert middleware.httponly is True
        assert isinstance(middleware.backend, InMemorySessionBackend)


class TestGetSession:
    """Test get_session helper."""

    def test_get_session_import(self):
        """Test get_session can be imported."""
        from p8s.sessions import get_session

        assert get_session is not None

    def test_get_session_requires_middleware(self):
        """Test get_session raises error without middleware."""
        from p8s.sessions import get_session
        from unittest.mock import MagicMock

        request = MagicMock()
        request.state = MagicMock(spec=[])

        with pytest.raises(RuntimeError, match="not available"):
            get_session(request)


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports correct symbols."""
        from p8s.sessions import __all__

        assert "SessionBackend" in __all__
        assert "InMemorySessionBackend" in __all__
        assert "RedisSessionBackend" in __all__
        assert "Session" in __all__
        assert "SessionMiddleware" in __all__
        assert "get_session" in __all__
