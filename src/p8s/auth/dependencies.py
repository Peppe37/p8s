"""
P8s Auth Dependencies - FastAPI dependencies for authentication.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.auth.models import User, UserRole
from p8s.auth.security import decode_token
from p8s.db.session import get_session

# Bearer token security
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """
    Get the current authenticated user.

    Returns None if no valid token is provided.
    Use this for optional authentication.

    Example:
        ```python
        @app.get("/profile")
        async def get_profile(
            user: User | None = Depends(get_current_user)
        ):
            if user:
                return {"user": user.email}
            return {"user": None}
        ```
    """
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)

    if not payload:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")

    if not user_id:
        return None

    try:
        result = await session.execute(select(User).where(User.id == UUID(user_id)))
        return result.scalar_one_or_none()
    except Exception:
        return None


async def require_auth(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Require authentication.

    Raises 401 if no valid token is provided.

    Example:
        ```python
        @app.get("/protected")
        async def protected_route(
            user: User = Depends(require_auth)
        ):
            return {"user": user.email}
        ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    payload = decode_token(credentials.credentials)

    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    try:
        result = await session.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise credentials_exception

        return user
    except Exception:
        raise credentials_exception


def require_role(*roles: UserRole):
    """
    Dependency factory to require specific roles.

    Example:
        ```python
        @app.get("/admin")
        async def admin_only(
            user: User = Depends(require_role(UserRole.ADMIN))
        ):
            return {"admin": True}
        ```
    """

    async def role_checker(
        user: User = Depends(require_auth),
    ) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_checker


def require_admin(user: User = Depends(require_auth)) -> User:
    """
    Require admin or superuser role.

    Example:
        ```python
        @app.delete("/users/{id}")
        async def delete_user(
            id: UUID,
            user: User = Depends(require_admin)
        ):
            # Only admins can delete users
            pass
        ```
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_permission(permission: str):
    """
    Dependency factory to require specific permission.

    Example:
        ```python
        @app.post("/publish")
        async def publish(
            user: User = Depends(require_permission("content.publish"))
        ):
            pass
        ```
    """

    async def permission_checker(
        user: User = Depends(require_auth),
    ) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return user

    return permission_checker


# Convenient type aliases
CurrentUser = Annotated[User | None, Depends(get_current_user)]
AuthenticatedUser = Annotated[User, Depends(require_auth)]
AdminUser = Annotated[User, Depends(require_admin)]
