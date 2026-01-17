"""
Task decorators for defining background tasks.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Module-level task registry
_task_registry: dict[str, "TaskDefinition"] = {}


@dataclass
class TaskOptions:
    """Configuration options for a task."""

    name: str | None = None
    queue: str = "default"
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: int = 300  # seconds
    unique: bool = False  # Prevent duplicate tasks


@dataclass
class PeriodicTaskOptions(TaskOptions):
    """Configuration for periodic/scheduled tasks."""

    cron: str | None = None  # Cron expression
    interval: int | None = None  # Seconds between runs


@dataclass
class TaskDefinition:
    """A registered task definition."""

    func: Callable[..., Any]
    options: TaskOptions

    def __post_init__(self) -> None:
        # Register task globally
        _task_registry[self.name] = self

    @property
    def name(self) -> str:
        return self.options.name or f"{self.func.__module__}.{self.func.__name__}"

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Direct execution (for testing or sync use)."""
        return await self.func(*args, **kwargs)

    async def enqueue(
        self,
        *args: Any,
        delay: int | None = None,
        at: datetime | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Enqueue task for background execution.

        Args:
            *args: Positional arguments for the task
            delay: Delay execution by N seconds
            at: Execute at specific datetime
            **kwargs: Keyword arguments for the task

        Returns:
            Task ID
        """
        from p8s.tasks.queue import get_queue

        queue = get_queue()

        # Calculate defer time
        defer_until = None
        if delay:
            defer_until = datetime.now(timezone.utc) + timedelta(seconds=delay)
        elif at:
            defer_until = at

        task_id = await queue.enqueue(
            self.name,
            args=args,
            kwargs=kwargs,
            defer_until=defer_until,
            options=self.options,
        )

        logger.info(f"Enqueued task {self.name} with ID {task_id}")
        return task_id

    @classmethod
    def get(cls, name: str) -> "TaskDefinition | None":
        """Get a registered task by name."""
        return _task_registry.get(name)

    @classmethod
    def all(cls) -> dict[str, "TaskDefinition"]:
        """Get all registered tasks."""
        return _task_registry.copy()


def task(
    func: F | None = None,
    *,
    name: str | None = None,
    queue: str = "default",
    max_retries: int = 3,
    retry_delay: int = 60,
    timeout: int = 300,
    unique: bool = False,
) -> F | Callable[[F], F]:
    """
    Decorator to define a background task.

    Usage:
        @task
        async def my_task(arg1: str):
            ...

        @task(max_retries=5, timeout=600)
        async def long_task():
            ...

        # Enqueue for background execution
        await my_task.enqueue(arg1="value")

        # Direct execution (testing)
        await my_task("value")
    """

    def decorator(fn: F) -> F:
        if not asyncio.iscoroutinefunction(fn):
            raise TypeError(f"Task {fn.__name__} must be an async function")

        options = TaskOptions(
            name=name,
            queue=queue,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            unique=unique,
        )

        task_def = TaskDefinition(func=fn, options=options)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await task_def(*args, **kwargs)

        # Attach task definition to wrapper
        wrapper.task_def = task_def  # type: ignore
        wrapper.enqueue = task_def.enqueue  # type: ignore
        wrapper.name = task_def.name  # type: ignore

        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    return decorator


# Registry for periodic tasks
_periodic_tasks: list[tuple[TaskDefinition, PeriodicTaskOptions]] = []


def periodic_task(
    func: F | None = None,
    *,
    cron: str | None = None,
    interval: int | None = None,
    name: str | None = None,
    queue: str = "default",
    max_retries: int = 3,
    timeout: int = 300,
) -> F | Callable[[F], F]:
    """
    Decorator to define a periodic/scheduled task.

    Usage:
        @periodic_task(cron="0 9 * * *")  # Daily at 9am
        async def daily_report():
            ...

        @periodic_task(interval=300)  # Every 5 minutes
        async def health_check():
            ...
    """
    if cron is None and interval is None:
        raise ValueError("Either 'cron' or 'interval' must be specified")

    def decorator(fn: F) -> F:
        if not asyncio.iscoroutinefunction(fn):
            raise TypeError(f"Task {fn.__name__} must be an async function")

        options = PeriodicTaskOptions(
            name=name,
            queue=queue,
            max_retries=max_retries,
            timeout=timeout,
            cron=cron,
            interval=interval,
        )

        task_def = TaskDefinition(func=fn, options=options)
        _periodic_tasks.append((task_def, options))

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await task_def(*args, **kwargs)

        wrapper.task_def = task_def  # type: ignore
        wrapper.enqueue = task_def.enqueue  # type: ignore
        wrapper.name = task_def.name  # type: ignore

        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    return decorator


def get_periodic_tasks() -> list[tuple[TaskDefinition, PeriodicTaskOptions]]:
    """Get all registered periodic tasks."""
    return _periodic_tasks.copy()
