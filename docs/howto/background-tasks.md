# How to Implement Background Tasks

P8s uses `ARQ` (Async Redis Queue) for high-performance background processing.

## Step 1: Install Redis

Ensure Redis is running:

```bash
docker run -d -p 6379:6379 redis
```

## Step 2: Define Tasks

Create a `tasks.py` file in your app:

```python
# backend/blog/tasks.py
from p8s.tasks import task

@task
async def send_newsletter(ctx, post_id: int):
    print(f"Sending newsletter for post {post_id}...")
    # Simulate work
    await asyncio.sleep(5)
    print("Newsletter sent!")
```

## Step 3: Enqueue Tasks

Call the task from your views or logic:

```python
from p8s.tasks import enqueue_task

async def create_post(post: Post):
    # ... save post ...
    await enqueue_task("send_newsletter", post.id)
```

## Step 4: Run Worker

Start the worker process to execute tasks:

```bash
p8s worker
```

## Periodic Tasks (Cron)

You can also define scheduled tasks:

```python
from p8s.tasks import periodic_task

@periodic_task(cron="0 9 * * *")  # Every day at 9 AM
async def daily_cleanup(ctx):
    print("Performing daily cleanup...")
```

The worker automatically handles scheduling (no separate beat process required).
