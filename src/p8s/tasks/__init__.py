"""
P8s Tasks - Async background task queue.

Provides:
- ARQ-based async task queue
- Decorator-based task definition
- Periodic/scheduled tasks
- Task retry with backoff
- In-memory backend for development/testing

Example:
    from p8s.tasks import task, periodic_task

    @task
    async def send_email(user_id: int):
        user = await User.get(user_id)
        await email.send(user.email, "Welcome!")

    @periodic_task(cron="0 9 * * *")
    async def daily_report():
        ...

    # Enqueue task
    await send_email.enqueue(user_id=1)
"""

from p8s.tasks.decorators import periodic_task, task
from p8s.tasks.queue import TaskQueue, get_queue
from p8s.tasks.worker import WorkerSettings

__all__ = [
    # Decorators
    "task",
    "periodic_task",
    # Queue
    "TaskQueue",
    "get_queue",
    # Worker
    "WorkerSettings",
]
