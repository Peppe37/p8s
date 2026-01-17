"""
P8s Admin Audit Log - Track admin actions.

Provides Django-style audit logging:
- Track all admin changes
- Store old/new values
- Query action history

Example:
    ```python
    from p8s.admin.logs import LogEntry, log_action, ActionFlag

    # Log an action
    await log_action(
        user_id=user.id,
        model_name="Product",
        object_id=product.id,
        action=ActionFlag.CHANGE,
        changes={"price": {"old": 10, "new": 15}},
    )

    # Query logs
    logs = await LogEntry.get_for_object("Product", product.id)
    ```
"""

from datetime import datetime, timezone
from enum import IntEnum
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ActionFlag(IntEnum):
    """Action type flags."""

    ADDITION = 1
    CHANGE = 2
    DELETION = 3


class LogEntry(SQLModel, table=True):
    """
    Admin action log entry.

    Records all create, update, delete actions in admin panel.
    """

    __tablename__ = "admin_logentry"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID | None = Field(default=None, index=True)
    content_type: str = Field(index=True)  # Model name
    object_id: str = Field(index=True)  # Object primary key
    object_repr: str = Field(default="")  # String representation
    action_flag: int = Field(default=ActionFlag.CHANGE)
    change_message: str = Field(default="")  # JSON of changes

    @property
    def is_addition(self) -> bool:
        """Check if this was a create action."""
        return self.action_flag == ActionFlag.ADDITION

    @property
    def is_change(self) -> bool:
        """Check if this was an update action."""
        return self.action_flag == ActionFlag.CHANGE

    @property
    def is_deletion(self) -> bool:
        """Check if this was a delete action."""
        return self.action_flag == ActionFlag.DELETION

    @property
    def action_name(self) -> str:
        """Get human-readable action name."""
        names = {
            ActionFlag.ADDITION: "Added",
            ActionFlag.CHANGE: "Changed",
            ActionFlag.DELETION: "Deleted",
        }
        return names.get(self.action_flag, "Unknown")


def create_change_message(changes: dict[str, dict[str, Any]]) -> str:
    """
    Create a change message from field changes.

    Args:
        changes: Dict of {field: {"old": old_val, "new": new_val}}

    Returns:
        JSON string of changes
    """
    import json

    return json.dumps(changes, default=str)


def parse_change_message(message: str) -> dict[str, dict[str, Any]]:
    """
    Parse a change message.

    Args:
        message: JSON string

    Returns:
        Dict of changes
    """
    import json

    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return {}


async def log_action(
    session,
    user_id: UUID | str | None,
    model_name: str,
    object_id: str | UUID,
    action: ActionFlag,
    object_repr: str = "",
    changes: dict[str, dict[str, Any]] | None = None,
) -> LogEntry:
    """
    Log an admin action.

    Args:
        session: Database session
        user_id: ID of user performing action
        model_name: Name of the model
        object_id: Primary key of the object
        action: Type of action
        object_repr: String representation of object
        changes: Dict of field changes

    Returns:
        Created LogEntry
    """
    entry = LogEntry(
        user_id=UUID(str(user_id)) if user_id else None,
        content_type=model_name,
        object_id=str(object_id),
        object_repr=object_repr,
        action_flag=action,
        change_message=create_change_message(changes or {}),
    )

    session.add(entry)
    await session.flush()
    return entry


def calculate_changes(
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    fields: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Calculate changes between old and new data.

    Args:
        old_data: Original values
        new_data: New values
        fields: Fields to compare (all if None)

    Returns:
        Dict of {field: {"old": old_val, "new": new_val}}
    """
    changes = {}

    if fields is None:
        fields = list(set(old_data.keys()) | set(new_data.keys()))

    for field in fields:
        old_val = old_data.get(field)
        new_val = new_data.get(field)

        if old_val != new_val:
            changes[field] = {"old": old_val, "new": new_val}

    return changes


__all__ = [
    "LogEntry",
    "ActionFlag",
    "log_action",
    "create_change_message",
    "parse_change_message",
    "calculate_changes",
]
