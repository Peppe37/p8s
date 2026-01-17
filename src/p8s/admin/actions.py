"""
P8s Admin Actions - Django-style admin actions for bulk operations.

Provides:
- @admin_action decorator for defining actions
- Action registry
- Execution utilities
"""

from collections.abc import Callable
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


# Registry for admin actions
# Format: {ModelName: {action_name: {"func": callable, "description": str}}}
_admin_actions: dict[str, dict[str, dict[str, Any]]] = {}


def admin_action(
    description: str | None = None,
    *,
    model: type | None = None,
    confirm: bool = False,
    confirm_message: str | None = None,
) -> Callable[[T], T]:
    """
    Decorator to define an admin action.

    The decorated function receives:
    - session: AsyncSession
    - queryset: List of selected model instances

    Example (Django-style with model parameter):
        ```python
        from p8s.admin import admin_action
        from backend.models import Product

        @admin_action("Mark as Featured", model=Product)
        async def mark_featured(session, queryset):
            for item in queryset:
                item.is_featured = True
                session.add(item)
            return f"{len(queryset)} products marked as featured"
        ```

    Example (Classic style - referenced in Admin class):
        ```python
        @admin_action(description="Mark selected products as active")
        async def mark_active(session, queryset):
            for item in queryset:
                item.is_active = True
                session.add(item)
            return f"{len(queryset)} products activated"

        class Product(Model, table=True):
            name: str
            is_active: bool = True

            class Admin:
                actions = ["mark_active"]
        ```

    Args:
        description: Human-readable description for the action.
        model: Optional model class to auto-register the action for.
        confirm: If True, require user confirmation before execution.
        confirm_message: Custom confirmation message.

    Returns:
        Decorator function.
    """

    def decorator(func: T) -> T:
        # Store action metadata on the function
        func._admin_action = True
        func._action_description = (
            description or func.__name__.replace("_", " ").title()
        )
        func._action_confirm = confirm
        func._action_confirm_message = (
            confirm_message
            or f"Are you sure you want to {func.__name__.replace('_', ' ')}?"
        )

        # If model is provided, auto-register the action
        if model is not None:
            model_name = model.__name__
            register_action(
                model_name=model_name,
                action_name=func.__name__,
                func=func,
                description=func._action_description,
            )

        return func

    return decorator


def register_action(
    model_name: str,
    action_name: str,
    func: Callable,
    description: str | None = None,
) -> None:
    """
    Register an action for a model.

    Args:
        model_name: Name of the model class.
        action_name: Name of the action.
        func: Async function to execute.
        description: Human-readable description.
    """
    if model_name not in _admin_actions:
        _admin_actions[model_name] = {}

    _admin_actions[model_name][action_name] = {
        "func": func,
        "description": description
        or getattr(func, "_action_description", action_name.replace("_", " ").title()),
        "confirm": getattr(func, "_action_confirm", False),
        "confirm_message": getattr(func, "_action_confirm_message", None),
    }


def get_model_actions(model_name: str) -> dict[str, dict[str, Any]]:
    """
    Get all registered actions for a model.

    Args:
        model_name: Name of the model class.

    Returns:
        Dictionary of action_name -> action metadata.
    """
    return _admin_actions.get(model_name, {}).copy()


def get_action(model_name: str, action_name: str) -> dict[str, Any] | None:
    """
    Get a specific action for a model.

    Args:
        model_name: Name of the model class.
        action_name: Name of the action.

    Returns:
        Action metadata or None.
    """
    return _admin_actions.get(model_name, {}).get(action_name)


async def execute_action(
    model_name: str,
    action_name: str,
    session: AsyncSession,
    item_ids: list[UUID],
) -> dict[str, Any]:
    """
    Execute an admin action.

    Args:
        model_name: Name of the model class.
        action_name: Name of the action.
        session: Database session.
        item_ids: List of item IDs to act on.

    Returns:
        Result dictionary with message or error.

    Raises:
        ValueError: If action not found.
    """
    from sqlalchemy import select

    from p8s.admin.registry import get_model

    action = get_action(model_name, action_name)
    if not action:
        raise ValueError(f"Action '{action_name}' not found for model '{model_name}'")

    model = get_model(model_name)
    if not model:
        raise ValueError(f"Model '{model_name}' not found")

    # Load items
    result = await session.execute(select(model).where(model.id.in_(item_ids)))
    queryset = list(result.scalars().all())

    if not queryset:
        return {"message": "No items selected", "affected": 0}

    # Execute action
    func = action["func"]
    response = await func(session, queryset)

    # Process response
    if isinstance(response, str):
        return {"message": response, "affected": len(queryset)}
    elif isinstance(response, dict):
        return {"affected": len(queryset), **response}
    else:
        return {
            "message": f"Action completed on {len(queryset)} items",
            "affected": len(queryset),
        }


# ============================================================================
# Built-in Actions
# ============================================================================


@admin_action(description="Delete selected items")
async def delete_selected(session: AsyncSession, queryset: list) -> str:
    """Soft delete all selected items."""
    for item in queryset:
        if hasattr(item, "soft_delete"):
            item.soft_delete()
        else:
            await session.delete(item)
        session.add(item)
    return f"{len(queryset)} items deleted"


@admin_action(description="Restore deleted items")
async def restore_selected(session: AsyncSession, queryset: list) -> str:
    """Restore soft-deleted items."""
    restored = 0
    for item in queryset:
        if hasattr(item, "restore") and hasattr(item, "deleted_at") and item.deleted_at:
            item.restore()
            session.add(item)
            restored += 1
    return f"{restored} items restored"


# Register built-in actions as default available to all models
DEFAULT_ACTIONS = {
    "delete_selected": delete_selected,
    "restore_selected": restore_selected,
}
