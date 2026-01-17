"""
P8s Auth Router - Authentication endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.auth.dependencies import require_auth
from p8s.auth.models import (
    LoginRequest,
    TokenResponse,
    User,
    UserCreate,
    UserResponse,
)
from p8s.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from p8s.core.settings import get_settings
from p8s.db.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Register a new user.

    Args:
        user_in: User registration data.
        session: Database session.

    Returns:
        Created user.

    Raises:
        400: Email already registered.
    """
    # Check if email exists
    result = await session.execute(select(User).where(User.email == user_in.email))

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username exists (if provided)
    if user_in.username:
        result = await session.execute(
            select(User).where(User.username == user_in.username)
        )

        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    # Create user
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        username=user_in.username,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
    )

    session.add(user)
    await session.flush()
    await session.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Login with email/username and password.

    Args:
        login_data: Login credentials (identifier can be email or username).
        session: Database session.

    Returns:
        Access and refresh tokens.

    Raises:
        401: Invalid credentials.
    """
    from sqlalchemy import or_

    # Find user by email OR username
    identifier = login_data.identifier.strip()
    result = await session.execute(
        select(User).where(
            or_(
                User.email == identifier,
                User.username == identifier,
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    session.add(user)

    # Create tokens
    settings = get_settings()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.auth.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Refresh access token.

    Args:
        refresh_token: Valid refresh token.
        session: Database session.

    Returns:
        New access and refresh tokens.

    Raises:
        401: Invalid refresh token.
    """
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    from uuid import UUID

    result = await session.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    settings = get_settings()

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.auth.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_auth),
) -> User:
    """
    Get current user profile.

    Args:
        user: Authenticated user.

    Returns:
        User profile.
    """
    return user


@router.post("/logout")
async def logout(
    user: User = Depends(require_auth),
) -> dict:
    """
    Logout current user.

    Note: This is a client-side operation. The token should be
    deleted from client storage.

    Returns:
        Success message.
    """
    # In a real implementation, you might want to:
    # - Blacklist the token
    # - Clear server-side sessions
    # - Log the logout event

    return {"message": "Successfully logged out"}


class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""

    current_password: str
    new_password: str = Field(min_length=8)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Change the current user's password.

    Args:
        data: Current and new password.
        user: Authenticated user.
        session: Database session.

    Returns:
        Success message.

    Raises:
        400: Current password is incorrect.
    """
    # Verify current password
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    user.password_hash = get_password_hash(data.new_password)
    session.add(user)
    await session.flush()


    return {"message": "Password changed successfully"}
