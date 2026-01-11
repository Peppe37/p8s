"""
P8s Auth Decorators - Django-style authentication decorators.

These decorators provide a familiar Django-like API for protecting routes,
while internally using FastAPI's dependency injection system.
"""

from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException, status

T = TypeVar("T")


def login_required(func: T) -> T:
    """
    Decorator to require authentication for a route.

    Similar to Django's @login_required decorator.

    Example:
        ```python
        from p8s.auth.decorators import login_required

        @app.get("/profile")
        @login_required
        async def profile(user: User = Depends(require_auth)):
            return {"email": user.email}
        ```

    Note: The 'user' must still be injected via Depends(require_auth).
    This decorator is primarily for readability and documentation.
    """
    func._login_required = True
    return func


def staff_member_required(func: T) -> T:
    """
    Decorator to require staff status for a route.

    Similar to Django's @staff_member_required decorator.

    Example:
        ```python
        @app.get("/admin/stats")
        @staff_member_required
        async def admin_stats(user: User = Depends(require_auth)):
            if not user.is_staff:
                raise HTTPException(403, "Staff access required")
            return {"stats": ...}
        ```
    """
    func._staff_required = True
    return func


def superuser_required(func: T) -> T:
    """
    Decorator to require superuser status for a route.

    Example:
        ```python
        @app.delete("/system/reset")
        @superuser_required
        async def reset_system(user: User = Depends(require_auth)):
            ...
        ```
    """
    func._superuser_required = True
    return func


def permission_required(*permissions: str) -> Callable[[T], T]:
    """
    Decorator factory to require specific permissions.

    Similar to Django's @permission_required decorator.

    Example:
        ```python
        from p8s.auth.decorators import permission_required

        @app.post("/articles")
        @permission_required("articles.add_article")
        async def create_article(user: User = Depends(require_auth)):
            ...

        @app.post("/publish")
        @permission_required("articles.add_article", "articles.publish_article")
        async def publish(user: User = Depends(require_auth)):
            ...
        ```
    """

    def decorator(func: T) -> T:
        func._permissions_required = permissions
        return func

    return decorator


def user_passes_test(
    test_func: Callable[[Any], bool], message: str = "Access denied"
) -> Callable[[T], T]:
    """
    Decorator factory that checks if user passes a custom test.

    Similar to Django's @user_passes_test decorator.

    Example:
        ```python
        from p8s.auth.decorators import user_passes_test

        def has_premium(user):
            return user.subscription_type == "premium"

        @app.get("/premium-content")
        @user_passes_test(has_premium, "Premium subscription required")
        async def premium_content(user: User = Depends(require_auth)):
            ...
        ```
    """

    def decorator(func: T) -> T:
        func._user_test = test_func
        func._user_test_message = message
        return func

    return decorator


# Dependency wrappers for easier use


def require_login():
    """
    Create a dependency that requires login.

    Example:
        ```python
        @app.get("/dashboard")
        async def dashboard(user: User = require_login()):
            return {"user": user.email}
        ```
    """
    from fastapi import Depends

    from p8s.auth.dependencies import require_auth

    return Depends(require_auth)


def require_staff():
    """
    Create a dependency that requires staff status.

    Example:
        ```python
        @app.get("/admin")
        async def admin_page(user: User = require_staff()):
            return {"admin": True}
        ```
    """
    from fastapi import Depends

    from p8s.auth.dependencies import require_auth
    from p8s.auth.models import User

    async def check_staff(user: User = Depends(require_auth)) -> User:
        if not user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff access required",
            )
        return user

    return Depends(check_staff)


def require_superuser():
    """
    Create a dependency that requires superuser status.
    """
    from fastapi import Depends

    from p8s.auth.dependencies import require_auth
    from p8s.auth.models import User

    async def check_superuser(user: User = Depends(require_auth)) -> User:
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser access required",
            )
        return user

    return Depends(check_superuser)


def require_perm(permission: str):
    """
    Create a dependency that requires a specific permission.

    Example:
        ```python
        @app.post("/articles")
        async def create_article(user: User = require_perm("articles.add_article")):
            ...
        ```
    """
    from fastapi import Depends

    from p8s.auth.dependencies import require_permission

    return Depends(require_permission(permission))


def require_perms(*permissions: str):
    """
    Create a dependency that requires all specified permissions.

    Example:
        ```python
        @app.post("/publish")
        async def publish(user: User = require_perms("articles.add", "articles.publish")):
            ...
        ```
    """
    from fastapi import Depends

    from p8s.auth.dependencies import require_auth
    from p8s.auth.models import User

    async def check_all_perms(user: User = Depends(require_auth)) -> User:
        for perm in permissions:
            if not user.has_perm(perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {perm}",
                )
        return user

    return Depends(check_all_perms)
