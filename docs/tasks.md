# Background Tasks

P8s provides an async-first background task system built on [ARQ](https://arq-docs.helpmanual.io/).

## Quick Start

### Define a Task

```python
from p8s.tasks import task, periodic_task

@task
async def send_welcome_email(user_id: int):
    """Send welcome email to new user."""
    user = await User.get(user_id)
    await email.send(user.email, "Welcome!")
    return {"sent": True}

@task(max_retries=5, timeout=600)
async def process_large_file(file_path: str):
    """Process a large file with retry logic."""
    ...
```

### Enqueue Tasks

```python
# Enqueue for immediate execution
task_id = await send_welcome_email.enqueue(user_id=1)

# Delay execution by 60 seconds
await send_welcome_email.enqueue(user_id=1, delay=60)

# Schedule for specific time
from datetime import datetime, timedelta
run_at = datetime.utcnow() + timedelta(hours=1)
await send_welcome_email.enqueue(user_id=1, at=run_at)
```

### Run the Worker

```bash
p8s worker
```

---

## Installation

The tasks module requires Redis and ARQ for production:

```bash
pip install p8s[tasks]
# or
pip install arq redis
```

For development/testing, the in-memory backend works without Redis.

---

## Task Options

| Option        | Type | Default   | Description                             |
| ------------- | ---- | --------- | --------------------------------------- |
| `name`        | str  | auto      | Task name (defaults to module.function) |
| `queue`       | str  | "default" | Queue name                              |
| `max_retries` | int  | 3         | Max retry attempts on failure           |
| `retry_delay` | int  | 60        | Seconds between retries                 |
| `timeout`     | int  | 300       | Task timeout in seconds                 |
| `unique`      | bool | False     | Prevent duplicate tasks                 |

Example:

```python
@task(
    name="emails.send_newsletter",
    queue="high",
    max_retries=5,
    timeout=600,
)
async def send_newsletter(campaign_id: int):
    ...
```

---

## Periodic Tasks

Schedule recurring tasks with cron expressions or intervals:

```python
from p8s.tasks import periodic_task

@periodic_task(cron="0 9 * * *")  # Daily at 9am
async def daily_report():
    """Generate and email daily report."""
    ...

@periodic_task(interval=300)  # Every 5 minutes
async def health_check():
    """Check system health."""
    ...

@periodic_task(cron="0 0 * * 0")  # Weekly on Sunday
async def weekly_cleanup():
    """Clean up old data."""
    ...
```

### Cron Format

```text
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

Examples:

- `0 9 * * *` - Daily at 9:00 AM
- `*/15 * * * *` - Every 15 minutes
- `0 0 1 * *` - First day of each month at midnight
- `0 12 * * 1-5` - Weekdays at noon

---

## Queue Backends

### In-Memory (Development)

Default backend, no configuration required:

```python
from p8s.tasks import TaskQueue

# Auto-uses in-memory if Redis not configured
TaskQueue.setup(backend="memory")
```

### Redis (Production)

```python
from p8s.tasks import TaskQueue

TaskQueue.setup(
    backend="redis",
    redis_url="redis://localhost:6379"
)
```

In `settings.py`:

```python
class AppSettings(Settings):
    tasks = {
        "redis_url": "redis://localhost:6379",
        "modules": ["myapp.tasks", "orders.tasks"],
    }
```

---

## CLI Commands

### `p8s worker`

Start the background task worker:

```bash
# Basic usage
p8s worker

# Custom Redis
p8s worker --redis redis://localhost:6379

# Multiple queues
p8s worker --queue high --queue default --queue low

# Concurrency
p8s worker --max-jobs 20

# Burst mode (exit when empty)
p8s worker --burst
```

### `p8s beat`

Show registered periodic tasks:

```bash
p8s beat
```

Note: ARQ processes periodic tasks within the worker. Run `p8s worker` to execute both regular and periodic tasks.

---

## Task Results

Check task status and results:

```python
from p8s.tasks import get_queue, TaskStatus

queue = get_queue()

# Get result
result = await queue.get_result(task_id)

if result.status == TaskStatus.COMPLETED:
    print(f"Result: {result.result}")
elif result.status == TaskStatus.FAILED:
    print(f"Error: {result.error}")
elif result.status == TaskStatus.RUNNING:
    print("Still running...")
```

---

## Integration with FastAPI

In your `main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from p8s.tasks import TaskQueue

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup task queue on startup
    TaskQueue.setup(backend="redis", redis_url="redis://localhost:6379")
    yield
    # Cleanup on shutdown

app = FastAPI(lifespan=lifespan)
```

---

## Testing

Use the in-memory backend for tests:

```python
import pytest
from p8s.tasks import TaskQueue, task

@task
async def my_task(value: int):
    return value * 2

@pytest.fixture
def task_queue():
    return TaskQueue.setup(backend="memory")

async def test_task_execution(task_queue):
    # Direct execution
    result = await my_task(5)
    assert result == 10

async def test_task_enqueue(task_queue):
    task_id = await my_task.enqueue(value=5)

    # Wait for completion (in-memory executes immediately)
    import asyncio
    await asyncio.sleep(0.1)

    result = await task_queue.get_result(task_id)
    assert result.result == 10
```

---

## Best Practices

1. **Keep tasks focused**: One task, one responsibility
2. **Make tasks idempotent**: Safe to retry
3. **Use appropriate timeouts**: Prevent stuck workers
4. **Handle failures gracefully**: Log errors, alert on critical failures
5. **Monitor queue depth**: Set up alerts for growing queues

```python
@task(max_retries=3)
async def idempotent_task(order_id: int):
    """Idempotent task - safe to retry."""
    order = await Order.get(order_id)

    # Check if already processed
    if order.status == "processed":
        return {"skipped": True}

    # Process and mark as done
    await process_order(order)
    order.status = "processed"
    await order.save()

    return {"processed": True}
```
