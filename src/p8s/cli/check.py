"""
P8s CLI Check Command - System validation and health checks.

Provides Django-style system check framework:
- Validate configuration
- Check database connectivity
- Verify required settings

Example:
    ```bash
    p8s check
    p8s check --deploy  # Deployment checks
    ```
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CheckLevel(str, Enum):
    """Check severity level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CheckMessage:
    """A check result message."""

    level: CheckLevel
    message: str
    hint: str | None = None
    obj: Any = None
    id: str | None = None

    @property
    def is_error(self) -> bool:
        """Check if this is an error or critical."""
        return self.level in (CheckLevel.ERROR, CheckLevel.CRITICAL)

    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.level == CheckLevel.WARNING


# Global registry of check functions
_checks: list[tuple[Callable, list[str]]] = []


def register_check(
    *tags: str,
) -> Callable[[Callable], Callable]:
    """
    Register a check function.

    Args:
        *tags: Tags for filtering (e.g., "database", "security", "deploy")

    Example:
        ```python
        @register_check("database")
        def check_database_connection():
            try:
                # test connection
                return []
            except Exception as e:
                return [CheckMessage(
                    level=CheckLevel.ERROR,
                    message=f"Database connection failed: {e}",
                    hint="Check DATABASE_URL setting",
                )]
        ```
    """

    def decorator(func: Callable) -> Callable:
        _checks.append((func, list(tags)))
        return func

    return decorator


def get_checks(tags: list[str] | None = None) -> list[tuple[Callable, list[str]]]:
    """Get registered checks, optionally filtered by tags."""
    if not tags:
        return _checks.copy()

    return [
        (func, func_tags)
        for func, func_tags in _checks
        if any(t in func_tags for t in tags)
    ]


async def run_checks(
    tags: list[str] | None = None,
    include_deploy: bool = False,
) -> list[CheckMessage]:
    """
    Run all registered checks.

    Args:
        tags: Filter by tags
        include_deploy: Include deployment checks

    Returns:
        List of check messages
    """
    import asyncio

    check_tags = list(tags) if tags else None
    if include_deploy and check_tags:
        check_tags.append("deploy")
    elif include_deploy:
        check_tags = None  # Run all including deploy

    checks = get_checks(check_tags)
    messages = []

    for func, _ in checks:
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()

            if isinstance(result, list):
                messages.extend(result)
            elif result:
                messages.append(result)
        except Exception as e:
            messages.append(
                CheckMessage(
                    level=CheckLevel.ERROR,
                    message=f"Check '{func.__name__}' raised exception: {e}",
                )
            )

    return messages


def format_check_results(messages: list[CheckMessage]) -> str:
    """Format check results for display."""
    if not messages:
        return "System check identified no issues."

    errors = [m for m in messages if m.is_error]
    warnings = [m for m in messages if m.is_warning]
    infos = [m for m in messages if not m.is_error and not m.is_warning]

    lines = []

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for msg in errors:
            lines.append(f"  ✗ {msg.message}")
            if msg.hint:
                lines.append(f"    HINT: {msg.hint}")

    if warnings:
        lines.append(f"\nWARNINGS ({len(warnings)}):")
        for msg in warnings:
            lines.append(f"  ⚠ {msg.message}")
            if msg.hint:
                lines.append(f"    HINT: {msg.hint}")

    if infos:
        lines.append(f"\nINFO ({len(infos)}):")
        for msg in infos:
            lines.append(f"  ℹ {msg.message}")

    total = len(messages)
    lines.append(f"\nSystem check identified {total} issue(s).")

    return "\n".join(lines)


# ============================================================================
# Built-in Checks
# ============================================================================


@register_check("settings")
def check_secret_key() -> list[CheckMessage]:
    """Check SECRET_KEY is set and secure."""
    messages = []

    try:
        from p8s.core.settings import get_settings

        settings = get_settings()

        secret = getattr(settings, "secret_key", None)
        if not secret:
            messages.append(
                CheckMessage(
                    level=CheckLevel.ERROR,
                    message="SECRET_KEY is not set",
                    hint="Set SECRET_KEY in your settings or environment",
                    id="settings.E001",
                )
            )
        elif secret == "changeme" or len(secret) < 32:
            messages.append(
                CheckMessage(
                    level=CheckLevel.WARNING,
                    message="SECRET_KEY appears insecure",
                    hint="Use a long, random string for SECRET_KEY",
                    id="settings.W001",
                )
            )
    except Exception:
        pass  # Settings not configured

    return messages


@register_check("settings", "deploy")
def check_debug_mode() -> list[CheckMessage]:
    """Check DEBUG is False in production."""
    messages = []

    try:
        from p8s.core.settings import get_settings

        settings = get_settings()

        if getattr(settings, "debug", False):
            messages.append(
                CheckMessage(
                    level=CheckLevel.WARNING,
                    message="DEBUG mode is enabled",
                    hint="Set DEBUG=False in production",
                    id="settings.W002",
                )
            )
    except Exception:
        pass

    return messages


__all__ = [
    "CheckLevel",
    "CheckMessage",
    "register_check",
    "get_checks",
    "run_checks",
    "format_check_results",
]
