"""
Tests for P8s OAuth2 Social Login.
"""

import pytest


class TestOAuth2Token:
    """Test OAuth2Token dataclass."""

    def test_token_import(self):
        """Test OAuth2Token can be imported."""
        from p8s.auth.social.providers import OAuth2Token

        token = OAuth2Token(access_token="test-token")
        assert token.access_token == "test-token"
        assert token.token_type == "Bearer"


class TestOAuth2UserInfo:
    """Test OAuth2UserInfo dataclass."""

    def test_user_info_import(self):
        """Test OAuth2UserInfo can be imported."""
        from p8s.auth.social.providers import OAuth2UserInfo

        info = OAuth2UserInfo(
            id="123",
            email="test@example.com",
            name="Test User",
        )
        assert info.id == "123"
        assert info.email == "test@example.com"


class TestGoogleProvider:
    """Test GoogleProvider."""

    def test_provider_import(self):
        """Test GoogleProvider can be imported."""
        from p8s.auth.social import GoogleProvider

        assert GoogleProvider.name == "google"

    def test_provider_init(self):
        """Test provider initialization."""
        from p8s.auth.social import GoogleProvider

        provider = GoogleProvider(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost/callback",
        )
        assert provider.client_id == "test-id"

    def test_authorization_url(self):
        """Test authorization URL generation."""
        from p8s.auth.social import GoogleProvider

        provider = GoogleProvider(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost/callback",
        )

        url = provider.get_authorization_url(state="test-state")

        assert "accounts.google.com" in url
        assert "client_id=test-id" in url
        assert "state=test-state" in url


class TestGitHubProvider:
    """Test GitHubProvider."""

    def test_provider_import(self):
        """Test GitHubProvider can be imported."""
        from p8s.auth.social import GitHubProvider

        assert GitHubProvider.name == "github"

    def test_authorization_url(self):
        """Test authorization URL generation."""
        from p8s.auth.social import GitHubProvider

        provider = GitHubProvider(
            client_id="gh-client",
            client_secret="gh-secret",
        )

        url = provider.get_authorization_url(redirect_uri="http://localhost/callback")

        assert "github.com" in url
        assert "client_id=gh-client" in url


class TestMicrosoftProvider:
    """Test MicrosoftProvider."""

    def test_provider_import(self):
        """Test MicrosoftProvider can be imported."""
        from p8s.auth.social import MicrosoftProvider

        assert MicrosoftProvider.name == "microsoft"


class TestProviderRegistry:
    """Test provider registration."""

    def test_register_and_get(self):
        """Test registering and getting providers."""
        from p8s.auth.social import (
            GoogleProvider,
            get_provider,
            register_provider,
        )

        provider = GoogleProvider(
            client_id="test",
            client_secret="test",
        )
        register_provider(provider)

        retrieved = get_provider("google")
        assert retrieved is provider


class TestSocialAccount:
    """Test SocialAccount model."""

    def test_model_import(self):
        """Test SocialAccount can be imported."""
        from p8s.auth.social import SocialAccount

        assert SocialAccount is not None

    def test_model_fields(self):
        """Test model has expected fields."""
        from p8s.auth.social.models import SocialAccount

        fields = SocialAccount.model_fields
        assert "provider" in fields
        assert "provider_user_id" in fields
        assert "user_id" in fields


class TestOAuthRouter:
    """Test OAuth router endpoints."""

    def test_router_import(self):
        """Test router can be imported."""
        from p8s.auth.social import oauth_router

        assert oauth_router is not None

    def test_router_has_endpoints(self):
        """Test router has expected routes."""
        from p8s.auth.social import oauth_router

        routes = [r.path for r in oauth_router.routes]
        assert any("/login/" in r for r in routes)
        assert any("/callback/" in r for r in routes)


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.auth.social import __all__

        assert "OAuth2Provider" in __all__
        assert "GoogleProvider" in __all__
        assert "GitHubProvider" in __all__
        assert "SocialAccount" in __all__
