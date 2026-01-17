"""
Tests for P8s CSRF Protection.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestGenerateToken:
    """Test token generation."""

    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        from p8s.csrf import generate_csrf_token

        token = generate_csrf_token()
        assert len(token) > 20
        assert isinstance(token, str)

    def test_tokens_are_unique(self):
        """Test tokens are unique."""
        from p8s.csrf import generate_csrf_token

        tokens = [generate_csrf_token() for _ in range(10)]
        assert len(set(tokens)) == 10


class TestMaskToken:
    """Test token masking."""

    def test_mask_token(self):
        """Test token masking."""
        from p8s.csrf import mask_token

        token = "test_token_12345"
        masked = mask_token(token)

        assert ":" in masked
        assert masked != token

    def test_unmask_token(self):
        """Test token unmasking."""
        from p8s.csrf import mask_token, unmask_token

        original = "test_token_12345"
        masked = mask_token(original)
        unmasked = unmask_token(masked)

        assert unmasked == original

    def test_unmask_invalid_returns_none(self):
        """Test invalid token returns None."""
        from p8s.csrf import unmask_token

        result = unmask_token("invalid")
        assert result is None


class TestCompareTokens:
    """Test token comparison."""

    def test_compare_same_tokens(self):
        """Test comparing identical tokens."""
        from p8s.csrf import compare_tokens

        token = "test_token"
        assert compare_tokens(token, token) is True

    def test_compare_different_tokens(self):
        """Test comparing different tokens."""
        from p8s.csrf import compare_tokens

        assert compare_tokens("token1", "token2") is False


class TestCSRFMiddleware:
    """Test CSRF middleware."""

    def test_middleware_import(self):
        """Test middleware can be imported."""
        from p8s.csrf import CSRFMiddleware

        assert CSRFMiddleware is not None

    def test_middleware_init(self):
        """Test middleware initialization."""
        from p8s.csrf import CSRFMiddleware

        middleware = CSRFMiddleware(app=None)

        assert middleware.cookie_name == "csrf_token"
        assert middleware.header_name == "X-CSRF-Token"

    def test_exempt_paths(self):
        """Test exempt paths."""
        from p8s.csrf import CSRFMiddleware

        middleware = CSRFMiddleware(
            app=None,
            exempt_paths=["/api/webhooks/", "/health"],
        )

        assert middleware._is_exempt("/api/webhooks/stripe") is True
        assert middleware._is_exempt("/health") is True
        assert middleware._is_exempt("/api/users/") is False


class TestGetCSRFToken:
    """Test get_csrf_token helper."""

    def test_get_csrf_token_import(self):
        """Test function can be imported."""
        from p8s.csrf import get_csrf_token

        assert get_csrf_token is not None

    def test_get_csrf_token_raises_without_middleware(self):
        """Test raises error without middleware."""
        from p8s.csrf import get_csrf_token

        request = MagicMock()
        request.state = MagicMock(spec=[])

        with pytest.raises(RuntimeError, match="not available"):
            get_csrf_token(request)

    def test_get_csrf_token_success(self):
        """Test getting token from request."""
        from p8s.csrf import get_csrf_token

        request = MagicMock()
        request.state.csrf_token = "test_token"

        token = get_csrf_token(request)
        assert token == "test_token"


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.csrf import __all__

        assert "CSRFMiddleware" in __all__
        assert "generate_csrf_token" in __all__
        assert "get_csrf_token" in __all__
