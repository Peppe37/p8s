"""
P8s Messages Framework - Django-style flash messages.

Provides:
- Message storage using session or cookies
- Message levels (DEBUG, INFO, SUCCESS, WARNING, ERROR)
- Session-based message passing between requests
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class MessageLevel(IntEnum):
    """Message importance levels."""

    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40


# Level tag mapping for CSS classes
LEVEL_TAGS = {
    MessageLevel.DEBUG: "debug",
    MessageLevel.INFO: "info",
    MessageLevel.SUCCESS: "success",
    MessageLevel.WARNING: "warning",
    MessageLevel.ERROR: "error",
}


@dataclass
class Message:
    """
    A single message.

    Attributes:
        level: Message level (IntEnum).
        message: The message text.
        extra_tags: Additional CSS class tags.
    """

    level: int
    message: str
    extra_tags: str = ""

    @property
    def tags(self) -> str:
        """Get all tags as space-separated string."""
        level_tag = LEVEL_TAGS.get(self.level, "")
        if self.extra_tags:
            return f"{level_tag} {self.extra_tags}".strip()
        return level_tag

    @property
    def level_tag(self) -> str:
        """Get level tag only."""
        return LEVEL_TAGS.get(self.level, "")

    def __str__(self) -> str:
        return self.message


@dataclass
class MessageStorage:
    """
    In-memory message storage.

    For production, use session-backed storage.
    """

    messages: list[Message] = field(default_factory=list)
    level: int = MessageLevel.DEBUG

    def add(self, level: int, message: str, extra_tags: str = "") -> None:
        """Add a message if it meets the minimum level."""
        if level >= self.level:
            self.messages.append(Message(level, message, extra_tags))

    def get_messages(self, clear: bool = True) -> list[Message]:
        """Get all messages, optionally clearing them."""
        msgs = self.messages.copy()
        if clear:
            self.messages.clear()
        return msgs

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.get_messages())


# Global request-scoped message storage
# In production, this would be stored in session
_message_storages: dict[str, MessageStorage] = {}


def get_messages_storage(request_id: str = "default") -> MessageStorage:
    """Get message storage for a request."""
    if request_id not in _message_storages:
        _message_storages[request_id] = MessageStorage()
    return _message_storages[request_id]


def add_message(
    level: int,
    message: str,
    extra_tags: str = "",
    request_id: str = "default",
) -> None:
    """
    Add a message to the storage.

    Example:
        ```python
        from p8s.messages import add_message, MessageLevel

        add_message(MessageLevel.SUCCESS, "Profile updated!")
        add_message(MessageLevel.ERROR, "Invalid form data")
        ```
    """
    storage = get_messages_storage(request_id)
    storage.add(level, message, extra_tags)


def get_messages(request_id: str = "default", clear: bool = True) -> list[Message]:
    """
    Get all messages for a request.

    Example:
        ```python
        from p8s.messages import get_messages

        for message in get_messages():
            print(f"[{message.level_tag}] {message}")
        ```
    """
    storage = get_messages_storage(request_id)
    return storage.get_messages(clear)


# Convenience functions
def debug(message: str, extra_tags: str = "", request_id: str = "default") -> None:
    """Add a debug message."""
    add_message(MessageLevel.DEBUG, message, extra_tags, request_id)


def info(message: str, extra_tags: str = "", request_id: str = "default") -> None:
    """Add an info message."""
    add_message(MessageLevel.INFO, message, extra_tags, request_id)


def success(message: str, extra_tags: str = "", request_id: str = "default") -> None:
    """Add a success message."""
    add_message(MessageLevel.SUCCESS, message, extra_tags, request_id)


def warning(message: str, extra_tags: str = "", request_id: str = "default") -> None:
    """Add a warning message."""
    add_message(MessageLevel.WARNING, message, extra_tags, request_id)


def error(message: str, extra_tags: str = "", request_id: str = "default") -> None:
    """Add an error message."""
    add_message(MessageLevel.ERROR, message, extra_tags, request_id)


# FastAPI integration


def get_messages_for_response(request_id: str = "default") -> list[dict[str, Any]]:
    """
    Get messages as JSON-serializable dicts for API responses.

    Example:
        ```python
        from p8s.messages import success, get_messages_for_response

        @app.post("/profile")
        async def update_profile(data: ProfileUpdate):
            await save_profile(data)
            success("Profile saved!")
            return {"messages": get_messages_for_response()}
        ```
    """
    return [
        {
            "level": msg.level_tag,
            "message": msg.message,
            "tags": msg.tags,
        }
        for msg in get_messages(request_id)
    ]
