"""
P8s Auth Models - User model and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, EmailStr
from pydantic import Field as PydanticField
from sqlmodel import Field

from p8s.db.base import Model

if TYPE_CHECKING:
    pass


class UserRole(str, Enum):
    """User roles."""

    USER = "user"
    STAFF = "staff"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class User(Model, table=True):
    """
    Built-in User model.

    Provides:
    - Email-based authentication
    - Password hashing
    - Role-based permissions
    - Granular permission system (Django-style)
    - Group membership
    - Active/verified status

    Example:
        ```python
        user = User(
            email="user@example.com",
            password_hash=get_password_hash("password123"),
        )

        # Check permissions
        if user.has_perm("products.add_product"):
            ...
        ```
    """

    __tablename__ = "p8s_users"

    # Authentication
    email: str = Field(
        unique=True,
        index=True,
        max_length=255,
    )
    password_hash: str = Field(max_length=255)

    # Profile
    username: str | None = Field(default=None, max_length=100, unique=True)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)

    # Status
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    # Role-based permissions (legacy, kept for backward compatibility)
    role: UserRole = Field(default=UserRole.USER)

    # Timestamps
    last_login: datetime | None = Field(default=None)

    # Note: Permission relationships are handled via explicit queries
    # to avoid circular import issues. Use get_all_permissions() method
    # or query UserPermissionLink/UserGroupLink tables directly.

    # Admin configuration
    class Admin:
        list_display = ["email", "username", "role", "is_active", "created_at"]
        search_fields = ["email", "username", "first_name", "last_name"]
        list_filter = ["role", "is_active", "is_verified"]
        readonly_fields = ["password_hash", "last_login"]

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    @property
    def is_admin(self) -> bool:
        """Check if user is admin or superuser."""
        return self.role in (UserRole.ADMIN, UserRole.SUPERUSER)

    @property
    def is_staff(self) -> bool:
        """Check if user has staff permissions."""
        return self.role in (UserRole.STAFF, UserRole.ADMIN, UserRole.SUPERUSER)

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission (legacy method).

        Args:
            permission: Permission string (e.g., "admin.read").

        Returns:
            True if user has permission.
        """
        if self.role == UserRole.SUPERUSER:
            return True

        # Basic role-based permissions
        if permission.startswith("admin.") and self.is_admin:
            return True
        if permission.startswith("staff.") and self.is_staff:
            return True

        return False

    def has_perm(self, perm: str) -> bool:
        """
        Check if user has a specific permission (Django-style).

        For role-based permissions, this checks:
        1. Superuser status (superusers have all permissions)
        2. Admin/Staff role-based permissions

        For granular permissions, use has_perm_async() with a database session.

        Args:
            perm: Permission codename (e.g., "products.add_product")

        Returns:
            True if user has the permission (role-based check only).

        Example:
            ```python
            if user.has_perm("products.add_product"):
                # Quick role-based check
                ...

            # For granular permissions, use async method:
            if await user.has_perm_async("products.add_product", session):
                ...
            ```
        """
        # Inactive users have no permissions
        if not self.is_active:
            return False

        # Superusers have all permissions
        if self.role == UserRole.SUPERUSER:
            return True

        # Fall back to role-based check
        return self.has_permission(perm)

    async def has_perm_async(self, perm: str, session: Any) -> bool:
        """
        Check if user has a specific permission (async, with DB query).

        This method checks:
        1. Superuser status (superusers have all permissions)
        2. User's direct permissions (via database query)
        3. Permissions from user's groups (via database query)
        4. Role-based fallback

        Args:
            perm: Permission codename (e.g., "products.add_product")
            session: AsyncSession for database queries

        Returns:
            True if user has the permission.

        Example:
            ```python
            async with get_session() as session:
                if await user.has_perm_async("products.add_product", session):
                    ...
            ```
        """
        from sqlalchemy import select

        # Inactive users have no permissions
        if not self.is_active:
            return False

        # Superusers have all permissions
        if self.role == UserRole.SUPERUSER:
            return True

        # Check direct user permissions
        from p8s.auth.permissions import Permission, UserPermissionLink

        result = await session.execute(
            select(Permission)
            .join(UserPermissionLink, Permission.id == UserPermissionLink.permission_id)
            .where(UserPermissionLink.user_id == self.id)
            .where(
                (Permission.codename == perm)
                | (Permission.codename + "." + Permission.content_type == perm)
            )
        )
        if result.scalar_one_or_none():
            return True

        # Check group permissions
        from p8s.auth.permissions import Group, GroupPermissionLink, UserGroupLink

        result = await session.execute(
            select(Permission)
            .join(
                GroupPermissionLink, Permission.id == GroupPermissionLink.permission_id
            )
            .join(Group, Group.id == GroupPermissionLink.group_id)
            .join(UserGroupLink, Group.id == UserGroupLink.group_id)
            .where(UserGroupLink.user_id == self.id)
            .where(
                (Permission.codename == perm)
                | (Permission.codename + "." + Permission.content_type == perm)
            )
        )
        if result.scalar_one_or_none():
            return True

        # Fall back to role-based check
        return self.has_permission(perm)

    def has_perms(self, perm_list: list[str]) -> bool:
        """
        Check if user has all specified permissions (role-based).

        Args:
            perm_list: List of permission codenames.

        Returns:
            True if user has ALL permissions.

        Example:
            ```python
            if user.has_perms(["products.add_product", "products.change_product"]):
                ...
            ```
        """
        return all(self.has_perm(perm) for perm in perm_list)


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    password: str = PydanticField(min_length=8)
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    password: str | None = PydanticField(default=None, min_length=8)
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class UserResponse(BaseModel):
    """Schema for user responses (excludes sensitive data)."""

    id: Any
    email: str
    username: str | None
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Schema for login request."""

    identifier: str  # Can be email or username
    password: str
