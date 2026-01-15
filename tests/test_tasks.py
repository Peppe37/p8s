"""
Tests for the P8s tasks module.
"""

import asyncio

import pytest

from p8s.tasks import TaskQueue, get_queue, periodic_task, task
from p8s.tasks.decorators import TaskDefinition, get_periodic_tasks
from p8s.tasks.queue import InMemoryQueue, TaskStatus

# Enable pytest-asyncio for this module
pytestmark = pytest.mark.asyncio(loop_scope="function")


# ============================================================================
# Test Decorators
# ============================================================================


class TestTaskDecorator:
    """Tests for the @task decorator."""

    def test_task_decorator_registers_function(self):
        """Task decorator should register the function."""

        @task
        async def my_test_task(value: int):
            return value * 2

        assert hasattr(my_test_task, "task_def")
        assert hasattr(my_test_task, "enqueue")
        assert my_test_task.name is not None

    def test_task_with_options(self):
        """Task decorator should accept options."""

        @task(name="custom_name", max_retries=5, timeout=600)
        async def custom_task():
            pass

        assert custom_task.name == "custom_name"
        assert custom_task.task_def.options.max_retries == 5
        assert custom_task.task_def.options.timeout == 600

    def test_task_must_be_async(self):
        """Task decorator should reject non-async functions."""
        with pytest.raises(TypeError, match="must be an async function"):

            @task
            def sync_task():
                pass

    @pytest.mark.asyncio
    async def test_task_direct_execution(self):
        """Task can be called directly for testing."""

        @task
        async def direct_task(x: int, y: int):
            return x + y

        result = await direct_task(2, 3)
        assert result == 5


class TestPeriodicTaskDecorator:
    """Tests for the @periodic_task decorator."""

    def test_periodic_task_requires_schedule(self):
        """Periodic task requires cron or interval."""
        with pytest.raises(ValueError, match="Either 'cron' or 'interval'"):

            @periodic_task
            async def no_schedule_task():
                pass

    def test_periodic_task_with_cron(self):
        """Periodic task should accept cron expression."""

        @periodic_task(cron="0 9 * * *")
        async def daily_task():
            pass

        periodic = get_periodic_tasks()
        assert any(t[0].func == daily_task.__wrapped__ for t in periodic)

    def test_periodic_task_with_interval(self):
        """Periodic task should accept interval."""

        @periodic_task(interval=300)
        async def interval_task():
            pass

        periodic = get_periodic_tasks()
        found = [t for t in periodic if hasattr(t[0].func, "__name__")]
        assert len(found) > 0


# ============================================================================
# Test Queue Backends
# ============================================================================


class TestInMemoryQueue:
    """Tests for the in-memory queue backend."""

    @pytest.fixture
    def queue(self):
        """Create a fresh in-memory queue."""
        return InMemoryQueue()

    @pytest.mark.asyncio
    async def test_enqueue_and_execute(self, queue):
        """Tasks should be enqueued and executed."""
        executed = {"called": False}

        @task
        async def trackable_task():
            executed["called"] = True
            return "done"

        task_id = await queue.enqueue(
            trackable_task.name,
            args=(),
            kwargs={},
        )

        assert task_id is not None

        # Wait for execution
        await asyncio.sleep(0.1)

        result = await queue.get_result(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert executed["called"] is True

    @pytest.mark.asyncio
    async def test_failed_task(self, queue):
        """Failed tasks should be marked as failed."""

        @task
        async def failing_task():
            raise ValueError("Task failed!")

        task_id = await queue.enqueue(
            failing_task.name,
            args=(),
            kwargs={},
        )

        await asyncio.sleep(0.1)

        result = await queue.get_result(task_id)
        assert result.status == TaskStatus.FAILED
        assert "Task failed!" in result.error

    @pytest.mark.asyncio
    async def test_pending_count(self, queue):
        """Should track pending task count."""
        count = await queue.get_pending_count()
        assert count >= 0


# ============================================================================
# Test TaskQueue Manager
# ============================================================================


class TestTaskQueue:
    """Tests for the TaskQueue manager."""

    def test_setup_memory_backend(self):
        """TaskQueue.setup should configure memory backend."""
        q = TaskQueue.setup(backend="memory")
        assert isinstance(q, InMemoryQueue)

    def test_get_returns_queue(self):
        """TaskQueue.get should return the configured queue."""
        TaskQueue.setup(backend="memory")
        queue = TaskQueue.get()
        assert queue is not None

    def test_invalid_backend_raises_error(self):
        """Invalid backend should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            TaskQueue.setup(backend="invalid")


# ============================================================================
# Test Task Enqueue via Decorator
# ============================================================================


class TestTaskEnqueue:
    """Tests for enqueueing tasks via the decorator."""

    @pytest.fixture(autouse=True)
    def setup_queue(self):
        """Setup in-memory queue for tests."""
        TaskQueue.setup(backend="memory")

    @pytest.mark.asyncio
    async def test_enqueue_via_decorator(self):
        """Tasks can be enqueued via .enqueue() method."""

        @task
        async def enqueue_test_task(msg: str):
            return f"received: {msg}"

        task_id = await enqueue_test_task.enqueue(msg="hello")
        assert task_id is not None

        # Wait for execution
        await asyncio.sleep(0.1)

        result = await get_queue().get_result(task_id)
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "received: hello"


# ============================================================================
# Test Task Registry
# ============================================================================


class TestTaskRegistry:
    """Tests for task registration."""

    def test_tasks_are_registered(self):
        """Tasks should be registered globally."""

        @task(name="registry_test_task")
        async def registry_test():
            pass

        found = TaskDefinition.get("registry_test_task")
        assert found is not None
        assert found.name == "registry_test_task"

    def test_all_tasks(self):
        """Should return all registered tasks."""
        tasks = TaskDefinition.all()
        assert isinstance(tasks, dict)
        assert len(tasks) > 0
