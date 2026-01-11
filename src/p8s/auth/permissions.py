"""
P8s Permissions - Django-style permission system.

Provides:
- Permission model for granular access control
- Group model for organizing users
- User-permission relationships
- Permission checking utilities
"""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from p8s.db.base import Model

if TYPE_CHECKING:
    pass


# ============================================================================
# Link tables for many-to-many relationships
# ============================================================================


class UserPermissionLink(SQLModel, table=True):
    """Link table for User-Permission many-to-many."""

    __tablename__ = "p8s_user_permissions"

    user_id: UUID = Field(foreign_key="p8s_users.id", primary_key=True)
    permission_id: UUID = Field(foreign_key="p8s_permissions.id", primary_key=True)


class UserGroupLink(SQLModel, table=True):
    """Link table for User-Group many-to-many."""

    __tablename__ = "p8s_user_groups"

    user_id: UUID = Field(foreign_key="p8s_users.id", primary_key=True)
    group_id: UUID = Field(foreign_key="p8s_groups.id", primary_key=True)


class GroupPermissionLink(SQLModel, table=True):
    """Link table for Group-Permission many-to-many."""

    __tablename__ = "p8s_group_permissions"

    group_id: UUID = Field(foreign_key="p8s_groups.id", primary_key=True)
    permission_id: UUID = Field(foreign_key="p8s_permissions.id", primary_key=True)


# ============================================================================
# Permission Model
# ============================================================================


class Permission(Model, table=True):
    """
    Permission model for granular access control.

    Similar to Django's auth.Permission model.

    Attributes:
        codename: Unique permission identifier (e.g., "add_product", "view_order")
        name: Human-readable permission name
        content_type: Associated model/app (e.g., "products.product")

    Example:
        ```python
        # Create permission
        perm = Permission(
            codename="add_product",
            name="Can add product",
            content_type="products.product",
        )

        # Check permission on user
        if user.has_perm("products.add_product"):
            ...
        ```
    """

    __tablename__ = "p8s_permissions"

    codename: str = Field(
        max_length=100,
        index=True,
        description="Unique permission identifier",
    )

    name: str = Field(
        max_length=255,
        description="Human-readable permission name",
    )

    content_type: str | None = Field(
        default=None,
        max_length=100,
        index=True,
        description="Associated model (app.model format)",
    )

    # Relationships
    groups: list["Group"] = Relationship(
        back_populates="permissions",
        link_model=GroupPermissionLink,
    )

    # Note: User relationship handled via queries (UserPermissionLink table)
    # to avoid circular imports. Query UserPermissionLink directly.

    class Admin:
        list_display = ["codename", "name", "content_type", "created_at"]
        search_fields = ["codename", "name"]
        list_filter = ["content_type"]

    @property
    def full_codename(self) -> str:
        """Get full permission codename with content type prefix."""
        if self.content_type:
            return f"{self.content_type}.{self.codename}"
        return self.codename

    def __repr__(self) -> str:
        return f"<Permission {self.full_codename}>"


# ============================================================================
# Group Model
# ============================================================================


class Group(Model, table=True):
    """
    Group model for organizing users with shared permissions.

    Similar to Django's auth.Group model.

    Attributes:
        name: Unique group name
        permissions: Permissions granted to all members

    Example:
        ```python
        # Create group with permissions
        editors = Group(name="Editors")
        editors.permissions = [edit_perm, view_perm]

        # Add user to group
        user.groups.append(editors)
        ```
    """

    __tablename__ = "p8s_groups"

    name: str = Field(
        unique=True,
        max_length=150,
        index=True,
        description="Unique group name",
    )

    # Relationships
    permissions: list[Permission] = Relationship(
        back_populates="groups",
        link_model=GroupPermissionLink,
    )

    # Note: User relationship handled via queries (UserGroupLink table)
    # to avoid circular imports. Query UserGroupLink directly.

    class Admin:
        list_display = ["name", "created_at"]
        search_fields = ["name"]

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


# ============================================================================
# Utility functions
# ============================================================================


def get_permission_codename(
    action: str,
    model_name: str,
    app_name: str | None = None,
) -> str:
    """
    Generate permission codename in Django format.

    Args:
        action: Permission action (add, change, delete, view)
        model_name: Model name (lowercase)
        app_name: Optional app name for prefix

    Returns:
        Permission codename string

    Example:
        >>> get_permission_codename("add", "product", "products")
        "products.add_product"
    """
    codename = f"{action}_{model_name}"
    if app_name:
        return f"{app_name}.{codename}"
    return codename


async def create_model_permissions(
    model_class: type,
    session: Any,
    app_name: str | None = None,
) -> list[Permission]:
    """
    Create default CRUD permissions for a model.

    Args:
        model_class: The model class to create permissions for
        session: Database session
        app_name: Optional app name

    Returns:
        List of created Permission instances

    Example:
        ```python
        from products.models import Product

        perms = await create_model_permissions(Product, session, "products")
        # Creates: add_product, change_product, delete_product, view_product
        ```
    """
    model_name = model_class.__name__.lower()
    content_type = f"{app_name}.{model_name}" if app_name else model_name

    actions = [
        ("add", f"Can add {model_name}"),
        ("change", f"Can change {model_name}"),
        ("delete", f"Can delete {model_name}"),
        ("view", f"Can view {model_name}"),
    ]

    permissions = []
    for action, name in actions:
        perm = Permission(
            codename=f"{action}_{model_name}",
            name=name,
            content_type=content_type,
        )
        session.add(perm)
        permissions.append(perm)

    await session.flush()
    return permissions


def permission_required(permission: str):
    """
    Decorator to require a specific permission for a route.

    Args:
        permission: Required permission codename

    Example:
        ```python
        from p8s.auth.permissions import permission_required

        @router.post("/products")
        @permission_required("products.add_product")
        async def create_product(user: User = Depends(require_auth)):
            ...
        ```
    """
    from functools import wraps

    from fastapi import HTTPException, status

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by Depends)
            user = kwargs.get("user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not await user.has_perm_async(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
