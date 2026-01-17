"""
Worker configuration and runner for P8s tasks.

Provides:
- ARQ worker integration
- Task discovery
- Periodic task scheduling
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WorkerSettings:
    """
    Configuration for the task worker.

    Usage:
        # In your project's tasks.py or worker.py
        from p8s.tasks import WorkerSettings

        worker_settings = WorkerSettings(
            redis_url="redis://localhost:6379",
            task_modules=["myapp.tasks", "myapp.users.tasks"],
        )

        # Run with: p8s worker
    """

    # Redis connection
    redis_url: str = "redis://localhost:6379"

    # Modules to import for task discovery
    task_modules: list[str] = field(default_factory=list)

    # Queue names to process
    queues: list[str] = field(default_factory=lambda: ["default"])

    # Concurrency settings
    max_jobs: int = 10  # Max concurrent jobs
    job_timeout: int = 300  # Default job timeout (seconds)

    # Retry settings
    max_retries: int = 3
    retry_delay: int = 60  # Seconds between retries

    # Health check
    health_check_interval: int = 60  # Seconds

    # Logging
    log_level: str = "INFO"

    def get_arq_settings(self) -> dict[str, Any]:
        """Convert to ARQ-compatible settings dict."""
        try:
            from arq.connections import RedisSettings
        except ImportError:
            raise ImportError("ARQ worker requires 'arq' package: pip install arq")

        # Import task modules to register tasks
        functions = self._discover_tasks()

        # Get periodic tasks (cron jobs)
        cron_jobs = self._get_cron_jobs()

        return {
            "redis_settings": RedisSettings.from_dsn(self.redis_url),
            "functions": functions,
            "cron_jobs": cron_jobs,
            "max_jobs": self.max_jobs,
            "job_timeout": self.job_timeout,
            "retry_jobs": True,
            "health_check_interval": self.health_check_interval,
        }

    def _discover_tasks(self) -> list[Callable[..., Any]]:
        """Import task modules and collect registered tasks."""
        from p8s.tasks.decorators import TaskDefinition

        # Import all task modules
        for module_name in self.task_modules:
            try:
                importlib.import_module(module_name)
                logger.info(f"Imported task module: {module_name}")
            except ImportError as e:
                logger.warning(f"Failed to import task module {module_name}: {e}")

        # Collect all registered task functions
        tasks = TaskDefinition.all()
        functions = []

        for name, task_def in tasks.items():
            # Create ARQ-compatible function
            async def wrapper(
                ctx: dict[str, Any],
                *args: Any,
                _task_func: Callable[..., Any] = task_def.func,
                **kwargs: Any,
            ) -> Any:
                return await _task_func(*args, **kwargs)

            wrapper.__name__ = name
            wrapper.__qualname__ = name
            functions.append(wrapper)

        logger.info(f"Discovered {len(functions)} tasks")
        return functions

    def _get_cron_jobs(self) -> list[Any]:
        """Get periodic tasks as ARQ cron jobs."""
        from p8s.tasks.decorators import get_periodic_tasks

        try:
            from arq import cron
        except ImportError:
            return []

        cron_jobs = []
        for task_def, options in get_periodic_tasks():
            # Create ARQ-compatible wrapper that accepts ctx
            original_func = task_def.func

            async def cron_wrapper(
                ctx: dict[str, Any], _fn: Any = original_func
            ) -> Any:
                return await _fn()

            cron_wrapper.__name__ = task_def.name
            cron_wrapper.__qualname__ = task_def.name

            if options.cron:
                # Parse cron expression (minute hour day month day_of_week)
                parts = options.cron.split()
                if len(parts) >= 5:
                    job = cron(
                        cron_wrapper,
                        minute=self._parse_cron_field(parts[0]),
                        hour=self._parse_cron_field(parts[1]),
                        day=self._parse_cron_field(parts[2]),
                        month=self._parse_cron_field(parts[3]),
                        weekday=self._parse_cron_field(parts[4]),
                    )
                    cron_jobs.append(job)
            elif options.interval:
                # Interval-based scheduling (run every N seconds)
                # ARQ doesn't support pure intervals, convert to cron-ish
                # For intervals < 1 hour, run every minute and check internally
                job = cron(
                    cron_wrapper,
                    second=0,  # Every minute
                    timeout=options.timeout,
                )
                cron_jobs.append(job)

        return cron_jobs

    def _parse_cron_field(self, field: str) -> set[int] | None:
        """Parse a cron field to ARQ format."""
        if field == "*":
            return None
        if field.isdigit():
            return {int(field)}
        if "," in field:
            return {int(x) for x in field.split(",")}
        if "-" in field:
            start, end = field.split("-")
            return set(range(int(start), int(end) + 1))
        if "/" in field:
            # Step values like */5
            _, step = field.split("/")
            return set(range(0, 60, int(step)))
        return None


def run_worker(settings: WorkerSettings) -> None:
    """
    Run the ARQ worker.

    This is called by the CLI `p8s worker` command.
    Note: ARQ manages its own event loop, so this is a sync function.
    """
    try:
        from arq import run_worker as arq_run_worker
    except ImportError:
        logger.error("ARQ not installed. Run: pip install arq")
        return

    arq_settings = settings.get_arq_settings()

    # Create a WorkerSettings class for ARQ
    class Settings:
        redis_settings = arq_settings["redis_settings"]
        functions = arq_settings["functions"]
        cron_jobs = arq_settings.get("cron_jobs", [])
        max_jobs = arq_settings["max_jobs"]
        job_timeout = arq_settings["job_timeout"]
        health_check_interval = arq_settings.get("health_check_interval", 60)

    logger.info(f"Starting worker with {len(Settings.functions)} tasks")
    logger.info(f"Processing queues: {settings.queues}")

    # Run worker (ARQ manages its own event loop)
    arq_run_worker(Settings)


def run_beat(settings: WorkerSettings) -> None:
    """
    Run the periodic task scheduler.

    For ARQ, periodic tasks are handled by the worker itself,
    so this is a convenience wrapper.
    """
    logger.info("Periodic tasks are handled by the ARQ worker")
    logger.info("Run 'p8s worker' to start processing periodic tasks")


def discover_worker_settings() -> WorkerSettings | None:
    """
    Auto-discover worker settings from the project.

    Looks for:
    1. WORKER_SETTINGS in settings module
    2. worker.py or tasks.py with worker_settings
    """
    try:
        from p8s.core.settings import get_settings

        settings = get_settings()

        # Check for task settings in app settings
        if hasattr(settings, "tasks"):
            task_config = settings.tasks
            return WorkerSettings(
                redis_url=getattr(task_config, "redis_url", "redis://localhost:6379"),
                task_modules=getattr(task_config, "modules", []),
                max_jobs=getattr(task_config, "max_jobs", 10),
            )
    except Exception as e:
        logger.debug(f"Could not load settings: {e}")

    # Try to find worker.py or tasks.py in current directory
    for filename in ["worker.py", "tasks.py"]:
        path = Path.cwd() / filename
        if path.exists():
            # Add cwd to path for import
            if str(Path.cwd()) not in sys.path:
                sys.path.insert(0, str(Path.cwd()))

            module_name = filename.replace(".py", "")
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "worker_settings"):
                    return module.worker_settings
            except ImportError:
                pass

    return None
