"""
Task queue backends for P8s.

Supports:
- InMemory (development/testing)
- Redis via ARQ (production)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0


@dataclass
class QueuedTask:
    """A task waiting in the queue."""

    id: str
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    defer_until: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    options: Any = None


class TaskQueueBackend(ABC):
    """Abstract base class for task queue backends."""

    @abstractmethod
    async def enqueue(
        self,
        task_name: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        defer_until: datetime | None = None,
        options: Any = None,
    ) -> str:
        """Add a task to the queue. Returns task ID."""
        ...

    @abstractmethod
    async def get_result(self, task_id: str) -> TaskResult | None:
        """Get the result of a completed task."""
        ...

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        ...

    @abstractmethod
    async def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        ...


class InMemoryQueue(TaskQueueBackend):
    """
    In-memory task queue for development and testing.

    Tasks are executed immediately in the background.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, QueuedTask] = {}
        self._results: dict[str, TaskResult] = {}
        self._running_tasks: set[str] = set()

    async def enqueue(
        self,
        task_name: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        defer_until: datetime | None = None,
        options: Any = None,
    ) -> str:
        from p8s.tasks.decorators import TaskDefinition

        task_id = str(uuid.uuid4())

        queued = QueuedTask(
            id=task_id,
            name=task_name,
            args=args,
            kwargs=kwargs,
            defer_until=defer_until,
            options=options,
        )
        self._tasks[task_id] = queued

        # Set initial result as pending
        self._results[task_id] = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
        )

        # Get task definition
        task_def = TaskDefinition.get(task_name)
        if task_def is None:
            self._results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=f"Task '{task_name}' not found",
            )
            return task_id

        # Schedule execution
        async def execute() -> None:
            # Wait if deferred
            if defer_until:
                delay = (defer_until - datetime.now(timezone.utc)).total_seconds()
                if delay > 0:
                    await asyncio.sleep(delay)

            self._running_tasks.add(task_id)
            self._results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
            )

            try:
                result = await task_def.func(*args, **kwargs)
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    started_at=self._results[task_id].started_at,
                    completed_at=datetime.now(timezone.utc),
                )
                logger.info(f"Task {task_name} ({task_id}) completed successfully")
            except Exception as e:
                logger.exception(f"Task {task_name} ({task_id}) failed")
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                    started_at=self._results[task_id].started_at,
                    completed_at=datetime.now(timezone.utc),
                )
            finally:
                self._running_tasks.discard(task_id)

        # Run in background
        asyncio.create_task(execute())

        return task_id

    async def get_result(self, task_id: str) -> TaskResult | None:
        return self._results.get(task_id)

    async def cancel(self, task_id: str) -> bool:
        if task_id in self._running_tasks:
            return False  # Cannot cancel running task

        if task_id in self._tasks:
            del self._tasks[task_id]
            self._results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.CANCELLED,
            )
            return True
        return False

    async def get_pending_count(self) -> int:
        return sum(
            1
            for r in self._results.values()
            if r.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        )


class RedisQueue(TaskQueueBackend):
    """
    Redis-backed task queue using ARQ.

    Requires: pip install arq redis
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_queue: str = "arq:queue",
    ) -> None:
        self._redis_url = redis_url
        self._default_queue = default_queue
        self._pool: Any = None

    async def _get_pool(self) -> Any:
        if self._pool is None:
            try:
                from arq import create_pool
                from arq.connections import RedisSettings

                # Parse redis URL
                settings = RedisSettings.from_dsn(self._redis_url)
                self._pool = await create_pool(settings)
            except ImportError:
                raise ImportError(
                    "Redis queue requires 'arq' package: pip install arq"
                )
        return self._pool

    async def enqueue(
        self,
        task_name: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        defer_until: datetime | None = None,
        options: Any = None,
    ) -> str:
        pool = await self._get_pool()

        # ARQ job options
        job_kwargs: dict[str, Any] = {}
        if defer_until:
            job_kwargs["_defer_until"] = defer_until

        if options:
            if hasattr(options, "timeout"):
                job_kwargs["_timeout"] = options.timeout
            if hasattr(options, "queue"):
                job_kwargs["_queue_name"] = options.queue

        job = await pool.enqueue_job(
            task_name,
            *args,
            **kwargs,
            **job_kwargs,
        )

        return job.job_id if job else str(uuid.uuid4())

    async def get_result(self, task_id: str) -> TaskResult | None:
        pool = await self._get_pool()

        try:
            from arq.jobs import Job

            job = Job(task_id, pool)
            info = await job.info()

            if info is None:
                return None

            status_map = {
                "pending": TaskStatus.PENDING,
                "running": TaskStatus.RUNNING,
                "complete": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED,
            }

            return TaskResult(
                task_id=task_id,
                status=status_map.get(info.status, TaskStatus.PENDING),
                result=info.result if info.status == "complete" else None,
                error=str(info.result) if info.status == "failed" else None,
                started_at=info.start_time,
                completed_at=info.finish_time,
            )
        except Exception as e:
            logger.warning(f"Failed to get job info: {e}")
            return None

    async def cancel(self, task_id: str) -> bool:
        pool = await self._get_pool()
        try:
            from arq.jobs import Job

            job = Job(task_id, pool)
            await job.abort()
            return True
        except Exception:
            return False

    async def get_pending_count(self) -> int:
        pool = await self._get_pool()
        try:
            # Count jobs in queue
            count = await pool.zcard(self._default_queue)
            return count
        except Exception:
            return 0


# Global queue instance
_queue: TaskQueueBackend | None = None


class TaskQueue:
    """
    High-level task queue interface.

    Usage:
        from p8s.tasks import TaskQueue

        # Initialize (usually in app startup)
        TaskQueue.setup(backend="redis", redis_url="redis://localhost:6379")

        # Or use in-memory for development
        TaskQueue.setup(backend="memory")

        # Enqueue tasks
        from myapp.tasks import send_email
        await send_email.enqueue(user_id=1)
    """

    @classmethod
    def setup(
        cls,
        backend: str = "memory",
        redis_url: str = "redis://localhost:6379",
        **kwargs: Any,
    ) -> TaskQueueBackend:
        """
        Initialize the task queue.

        Args:
            backend: "memory" or "redis"
            redis_url: Redis connection URL (for redis backend)
        """
        global _queue

        if backend == "memory":
            _queue = InMemoryQueue()
        elif backend == "redis":
            _queue = RedisQueue(redis_url=redis_url, **kwargs)
        else:
            raise ValueError(f"Unknown backend: {backend}")

        logger.info(f"Task queue initialized with {backend} backend")
        return _queue

    @classmethod
    def get(cls) -> TaskQueueBackend:
        """Get the current queue backend."""
        global _queue
        if _queue is None:
            # Auto-setup with memory backend
            _queue = InMemoryQueue()
        return _queue


def get_queue() -> TaskQueueBackend:
    """Get the current task queue backend."""
    return TaskQueue.get()
