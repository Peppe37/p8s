"""
P8s OAuth2 Providers - Base classes and implementations.

Supports OAuth2 authorization code flow for social login.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import httpx


@dataclass
class OAuth2Token:
    """OAuth2 token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    id_token: str | None = None  # For OIDC


@dataclass
class OAuth2UserInfo:
    """Standardized user info from OAuth2 provider."""
    id: str
    email: str
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    picture: str | None = None
    email_verified: bool = False
    raw_data: dict = field(default_factory=dict)


class OAuth2Provider(ABC):
    """
    Abstract base class for OAuth2 providers.

    Subclass this to add new OAuth2/OIDC providers.
    """

    name: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    default_scopes: list[str] = []

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
        scopes: list[str] | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or self.default_scopes

    def get_authorization_url(
        self,
        redirect_uri: str | None = None,
        state: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate OAuth2 authorization URL.

        Args:
            redirect_uri: Override default redirect URI
            state: CSRF state token
            **kwargs: Additional query parameters

        Returns:
            Authorization URL for redirect
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
        }

        if state:
            params["state"] = state

        params.update(kwargs)

        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str | None = None,
    ) -> OAuth2Token:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used in authorization

        Returns:
            OAuth2Token with access token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri or self.redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        return OAuth2Token(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            id_token=data.get("id_token"),
        )

    async def get_user_info(self, token: OAuth2Token) -> OAuth2UserInfo:
        """
        Fetch user info from provider.

        Args:
            token: OAuth2 token

        Returns:
            Standardized user info
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={
                    "Authorization": f"{token.token_type} {token.access_token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_user_info(data)

    @abstractmethod
    def _parse_user_info(self, data: dict) -> OAuth2UserInfo:
        """Parse provider-specific user info response."""
        ...


# ============================================================================
# Provider Implementations
# ============================================================================


class GoogleProvider(OAuth2Provider):
    """Google OAuth2 / OpenID Connect provider."""

    name = "google"
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    default_scopes = ["openid", "email", "profile"]

    def get_authorization_url(self, **kwargs) -> str:
        # Google requires access_type for refresh tokens
        kwargs.setdefault("access_type", "offline")
        kwargs.setdefault("prompt", "consent")
        return super().get_authorization_url(**kwargs)

    def _parse_user_info(self, data: dict) -> OAuth2UserInfo:
        return OAuth2UserInfo(
            id=data["sub"],
            email=data["email"],
            name=data.get("name"),
            first_name=data.get("given_name"),
            last_name=data.get("family_name"),
            picture=data.get("picture"),
            email_verified=data.get("email_verified", False),
            raw_data=data,
        )


class GitHubProvider(OAuth2Provider):
    """GitHub OAuth2 provider."""

    name = "github"
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    userinfo_url = "https://api.github.com/user"
    default_scopes = ["user:email", "read:user"]

    async def get_user_info(self, token: OAuth2Token) -> OAuth2UserInfo:
        """GitHub requires separate call for email."""
        async with httpx.AsyncClient() as client:
            # Get user info
            user_response = await client.get(
                self.userinfo_url,
                headers={
                    "Authorization": f"token {token.access_token}",
                    "Accept": "application/json",
                },
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            # Get emails (primary email may not be in user data)
            email = user_data.get("email")
            if not email:
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"token {token.access_token}",
                        "Accept": "application/json",
                    },
                )
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary = next(
                        (e for e in emails if e.get("primary")),
                        emails[0] if emails else None,
                    )
                    if primary:
                        email = primary["email"]
                        user_data["email_verified"] = primary.get("verified", False)

            user_data["email"] = email
            return self._parse_user_info(user_data)

    def _parse_user_info(self, data: dict) -> OAuth2UserInfo:
        # Split name if available
        name = data.get("name") or data.get("login")
        first_name, last_name = None, None
        if name and " " in name:
            parts = name.split(" ", 1)
            first_name, last_name = parts[0], parts[1]

        return OAuth2UserInfo(
            id=str(data["id"]),
            email=data.get("email", ""),
            name=name,
            first_name=first_name,
            last_name=last_name,
            picture=data.get("avatar_url"),
            email_verified=data.get("email_verified", False),
            raw_data=data,
        )


class MicrosoftProvider(OAuth2Provider):
    """Microsoft Azure AD / Entra ID OAuth2 provider."""

    name = "microsoft"
    authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    userinfo_url = "https://graph.microsoft.com/v1.0/me"
    default_scopes = ["openid", "email", "profile", "User.Read"]

    def _parse_user_info(self, data: dict) -> OAuth2UserInfo:
        return OAuth2UserInfo(
            id=data["id"],
            email=data.get("mail") or data.get("userPrincipalName", ""),
            name=data.get("displayName"),
            first_name=data.get("givenName"),
            last_name=data.get("surname"),
            picture=None,  # Microsoft Graph requires separate photo endpoint
            email_verified=True,  # Microsoft accounts are verified
            raw_data=data,
        )


# ============================================================================
# Provider Registry
# ============================================================================

_providers: dict[str, OAuth2Provider] = {}


def register_provider(provider: OAuth2Provider) -> None:
    """Register an OAuth2 provider."""
    _providers[provider.name] = provider


def get_provider(name: str) -> OAuth2Provider | None:
    """Get a registered provider by name."""
    return _providers.get(name)


def get_all_providers() -> dict[str, OAuth2Provider]:
    """Get all registered providers."""
    return _providers.copy()
