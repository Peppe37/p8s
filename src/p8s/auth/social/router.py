"""
P8s OAuth2 Router - API endpoints for social login.
"""

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.auth.security import create_access_token, create_refresh_token
from p8s.core.settings import get_settings
from p8s.db.session import get_session

from .models import SocialAccount
from .providers import get_provider, OAuth2UserInfo

router = APIRouter(prefix="/auth/social", tags=["social-auth"])


# State storage (in production, use Redis/database)
_oauth_states: dict[str, dict[str, Any]] = {}


class TokenResponse(BaseModel):
    """OAuth login response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    is_new_user: bool = False


@router.get("/login/{provider}")
async def oauth_login(
    provider: str,
    redirect_uri: str | None = Query(None),
    next: str | None = Query(None),
) -> RedirectResponse:
    """
    Initiate OAuth2 login flow.

    Redirects user to provider's authorization page.

    Args:
        provider: Provider name (google, github, microsoft)
        redirect_uri: Override callback URI
        next: URL to redirect after successful login
    """
    oauth_provider = get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "provider": provider,
        "redirect_uri": redirect_uri,
        "next": next,
    }

    # Build callback URI
    settings = get_settings()
    callback_uri = redirect_uri or f"{settings.base_url}/auth/social/callback/{provider}"

    auth_url = oauth_provider.get_authorization_url(
        redirect_uri=callback_uri,
        state=state,
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Handle OAuth2 callback.

    Exchanges code for tokens and creates/updates user.

    Args:
        provider: Provider name
        code: Authorization code from provider
        state: CSRF state token
    """
    # Validate state
    state_data = _oauth_states.pop(state, None)
    if not state_data or state_data.get("provider") != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state",
        )

    oauth_provider = get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    # Get callback URI
    settings = get_settings()
    redirect_uri = (
        state_data.get("redirect_uri")
        or f"{settings.base_url}/auth/social/callback/{provider}"
    )

    try:
        # Exchange code for token
        token = await oauth_provider.exchange_code(code, redirect_uri)

        # Get user info from provider
        user_info = await oauth_provider.get_user_info(token)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {str(e)}",
        )

    # Find or create user
    user, is_new = await _get_or_create_user(session, provider, user_info)

    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.auth.access_token_expire_minutes * 60,
        user_id=str(user.id),
        is_new_user=is_new,
    )


async def _get_or_create_user(
    session: AsyncSession,
    provider: str,
    user_info: OAuth2UserInfo,
) -> tuple[Any, bool]:
    """
    Find existing user or create new one from OAuth info.

    Returns:
        Tuple of (user, is_new)
    """
    from p8s.auth.models import User

    # Check for existing social account
    result = await session.execute(
        select(SocialAccount).where(
            SocialAccount.provider == provider,
            SocialAccount.provider_user_id == user_info.id,
        )
    )
    social_account = result.scalar_one_or_none()

    if social_account:
        # Existing social account - get user
        result = await session.execute(
            select(User).where(User.id == social_account.user_id)
        )
        user = result.scalar_one()

        # Update social account data
        social_account.extra_data = user_info.raw_data
        from datetime import datetime, timezone
        social_account.last_login = datetime.now(timezone.utc)
        session.add(social_account)

        return user, False

    # Check if user exists with same email
    if user_info.email:
        result = await session.execute(
            select(User).where(User.email == user_info.email)
        )
        user = result.scalar_one_or_none()

        if user:
            # Link existing user to social account
            await SocialAccount.get_or_create(
                session,
                provider=provider,
                provider_user_id=user_info.id,
                user_id=user.id,
                extra_data=user_info.raw_data,
            )
            return user, False

    # Create new user
    import secrets

    user = User(
        email=user_info.email,
        username=user_info.email.split("@")[0] if user_info.email else None,
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        password_hash=secrets.token_hex(32),  # Random password (can't login with password)
        is_active=True,
    )
    session.add(user)
    await session.flush()

    # Create social account
    await SocialAccount.get_or_create(
        session,
        provider=provider,
        provider_user_id=user_info.id,
        user_id=user.id,
        extra_data=user_info.raw_data,
    )

    return user, True


@router.get("/providers")
async def list_providers() -> list[str]:
    """
    List available OAuth providers.

    Returns:
        List of configured provider names
    """
    from .providers import get_all_providers
    return list(get_all_providers().keys())
