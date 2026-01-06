"""
P8s Auth Models - User model and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field as PydanticField
from sqlmodel import Field, Relationship

from p8s.db.base import Model


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
    - Active/verified status

    Example:
        ```python
        user = User(
            email="user@example.com",
            password_hash=get_password_hash("password123"),
        )
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

    # Permissions
    role: UserRole = Field(default=UserRole.USER)

    # Timestamps
    last_login: datetime | None = Field(default=None)

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
        Check if user has a specific permission.

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

    email: EmailStr
    password: str
