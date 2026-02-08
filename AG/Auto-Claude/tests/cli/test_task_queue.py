"""
Tests for src/coordinator/task_queue.py

Validates the SQLite-based priority task queue: enqueue/dequeue ordering,
status transitions, retry logic, statistics, child-task queries, JSON
safety, peek semantics, and async wrappers.
"""

import sys
import time
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import sqlite3
from datetime import datetime, timedelta

import pytest

from src.utils.models import Priority, Task, TaskType
from src.coordinator.task_queue import TaskQueue, TaskStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def task_queue(tmp_path: Path) -> TaskQueue:
    """Create an initialized TaskQueue backed by a temporary SQLite file."""
    db_file = tmp_path / "test_tasks.db"
    queue = TaskQueue(str(db_file))
    queue.initialize()
    return queue


@pytest.fixture
def sample_task() -> Task:
    """Return a reusable sample Task with sensible defaults."""
    return Task(
        type=TaskType.CODE,
        description="Implement the login endpoint",
        priority=Priority.MEDIUM,
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInitialize:
    def test_initialize_creates_table(self, task_queue: TaskQueue):
        """After initialize(), the 'tasks' table exists in the SQLite DB."""
        conn = sqlite3.connect(str(task_queue.db_path))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "tasks"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Enqueue / Dequeue basics
# ---------------------------------------------------------------------------

class TestEnqueueDequeue:
    def test_enqueue_returns_task_id(self, task_queue: TaskQueue, sample_task: Task):
        """enqueue() returns the task's id."""
        returned_id = task_queue.enqueue(sample_task)
        assert returned_id == sample_task.id

    def test_enqueue_dequeue_basic(self, task_queue: TaskQueue, sample_task: Task):
        """A single enqueue followed by dequeue yields the same task."""
        task_queue.enqueue(sample_task)
        dequeued = task_queue.dequeue()

        assert dequeued is not None
        assert dequeued.id == sample_task.id
        assert dequeued.type == sample_task.type
        assert dequeued.description == sample_task.description

    def test_dequeue_empty_returns_none(self, task_queue: TaskQueue):
        """Dequeuing from an empty queue returns None."""
        assert task_queue.dequeue() is None


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    def test_priority_ordering_high_first(self, task_queue: TaskQueue):
        """HIGH-priority tasks are dequeued before MEDIUM-priority tasks."""
        medium = Task(type=TaskType.CODE, description="medium", priority=Priority.MEDIUM)
        high = Task(type=TaskType.CODE, description="high", priority=Priority.HIGH)

        task_queue.enqueue(medium)
        task_queue.enqueue(high)

        first = task_queue.dequeue()
        assert first is not None
        assert first.id == high.id

    def test_priority_ordering_medium_before_low(self, task_queue: TaskQueue):
        """MEDIUM-priority tasks are dequeued before LOW-priority tasks."""
        low = Task(type=TaskType.CODE, description="low", priority=Priority.LOW)
        medium = Task(type=TaskType.CODE, description="medium", priority=Priority.MEDIUM)

        task_queue.enqueue(low)
        task_queue.enqueue(medium)

        first = task_queue.dequeue()
        assert first is not None
        assert first.id == medium.id

    def test_fifo_within_same_priority(self, task_queue: TaskQueue):
        """Tasks with the same priority are dequeued oldest-first (FIFO)."""
        first_task = Task(type=TaskType.CODE, description="first", priority=Priority.MEDIUM)
        # Tiny sleep to guarantee created_at ordering in the DB
        time.sleep(0.01)
        second_task = Task(type=TaskType.CODE, description="second", priority=Priority.MEDIUM)

        task_queue.enqueue(first_task)
        task_queue.enqueue(second_task)

        dequeued = task_queue.dequeue()
        assert dequeued is not None
        assert dequeued.id == first_task.id


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def test_dequeue_marks_in_progress(self, task_queue: TaskQueue, sample_task: Task):
        """Dequeuing a task transitions its status to IN_PROGRESS."""
        task_queue.enqueue(sample_task)
        task_queue.dequeue()

        status = task_queue.get_status(sample_task.id)
        assert status == TaskStatus.IN_PROGRESS

    def test_complete_task(self, task_queue: TaskQueue, sample_task: Task):
        """complete() sets status to COMPLETED."""
        task_queue.enqueue(sample_task)
        task_queue.dequeue()
        task_queue.complete(sample_task.id, output={"lines": 42})

        status = task_queue.get_status(sample_task.id)
        assert status == TaskStatus.COMPLETED

    def test_cancel_task(self, task_queue: TaskQueue, sample_task: Task):
        """cancel() sets status to CANCELLED."""
        task_queue.enqueue(sample_task)
        task_queue.cancel(sample_task.id)

        status = task_queue.get_status(sample_task.id)
        assert status == TaskStatus.CANCELLED


# ---------------------------------------------------------------------------
# Failure and retry logic
# ---------------------------------------------------------------------------

class TestFailureRetry:
    def test_fail_task_with_retry(self, task_queue: TaskQueue):
        """fail(retry=True) increments retry_count and returns task to PENDING."""
        task = Task(type=TaskType.CODE, description="flaky", max_retries=3)
        task_queue.enqueue(task)
        task_queue.dequeue()

        retried = task_queue.fail(task.id, error="timeout", retry=True)
        assert retried is True

        status = task_queue.get_status(task.id)
        assert status == TaskStatus.PENDING

        # retry_count should be incremented
        retrieved = task_queue.get_task(task.id)
        assert retrieved is not None
        assert retrieved.retry_count == 1

    def test_fail_task_no_retry(self, task_queue: TaskQueue):
        """fail(retry=False) immediately sets FAILED regardless of remaining retries."""
        task = Task(type=TaskType.CODE, description="fatal", max_retries=5)
        task_queue.enqueue(task)
        task_queue.dequeue()

        retried = task_queue.fail(task.id, error="fatal error", retry=False)
        assert retried is False

        status = task_queue.get_status(task.id)
        assert status == TaskStatus.FAILED

    def test_fail_task_max_retries_exceeded(self, task_queue: TaskQueue):
        """When retry_count >= max_retries, fail() marks FAILED even with retry=True."""
        task = Task(
            type=TaskType.CODE,
            description="exhausted",
            retry_count=3,
            max_retries=3,
        )
        task_queue.enqueue(task)
        task_queue.dequeue()

        retried = task_queue.fail(task.id, error="still broken", retry=True)
        assert retried is False

        status = task_queue.get_status(task.id)
        assert status == TaskStatus.FAILED


# ---------------------------------------------------------------------------
# Query methods
# ---------------------------------------------------------------------------

class TestQueryMethods:
    def test_get_task_by_id(self, task_queue: TaskQueue, sample_task: Task):
        """get_task() returns the correct task by ID."""
        task_queue.enqueue(sample_task)
        retrieved = task_queue.get_task(sample_task.id)

        assert retrieved is not None
        assert retrieved.id == sample_task.id
        assert retrieved.description == sample_task.description

    def test_get_task_by_id_missing(self, task_queue: TaskQueue):
        """get_task() returns None for a non-existent ID."""
        assert task_queue.get_task("does-not-exist") is None

    def test_get_status(self, task_queue: TaskQueue, sample_task: Task):
        """get_status() returns the current status string."""
        task_queue.enqueue(sample_task)
        assert task_queue.get_status(sample_task.id) == TaskStatus.PENDING

    def test_get_pending_count(self, task_queue: TaskQueue):
        """get_pending_count() returns the number of PENDING tasks."""
        for i in range(3):
            task_queue.enqueue(Task(type=TaskType.CODE, description=f"task-{i}"))

        assert task_queue.get_pending_count() == 3

        # Dequeue one -> pending should drop
        task_queue.dequeue()
        assert task_queue.get_pending_count() == 2

    def test_get_in_progress_count(self, task_queue: TaskQueue):
        """get_in_progress_count() returns the number of IN_PROGRESS tasks."""
        for i in range(2):
            task_queue.enqueue(Task(type=TaskType.CODE, description=f"task-{i}"))

        assert task_queue.get_in_progress_count() == 0

        task_queue.dequeue()
        assert task_queue.get_in_progress_count() == 1

        task_queue.dequeue()
        assert task_queue.get_in_progress_count() == 2

    def test_get_stats(self, task_queue: TaskQueue):
        """get_stats() returns a dict with counts for every status plus total."""
        t1 = Task(type=TaskType.CODE, description="pending")
        t2 = Task(type=TaskType.QA, description="in-progress")
        t3 = Task(type=TaskType.FIX, description="completed")

        task_queue.enqueue(t1)
        task_queue.enqueue(t2)
        task_queue.enqueue(t3)

        # Move t2 to in_progress
        task_queue.dequeue()  # highest by creation -> t1 (same priority, FIFO)
        # Actually let's just check the overall structure
        stats = task_queue.get_stats()

        assert "total" in stats
        assert TaskStatus.PENDING in stats
        assert TaskStatus.IN_PROGRESS in stats
        assert TaskStatus.COMPLETED in stats
        assert TaskStatus.FAILED in stats
        assert TaskStatus.CANCELLED in stats
        assert stats["total"] == 3

    def test_get_tasks_by_status(self, task_queue: TaskQueue):
        """get_tasks_by_status() filters correctly."""
        t1 = Task(type=TaskType.CODE, description="a")
        t2 = Task(type=TaskType.QA, description="b")
        task_queue.enqueue(t1)
        task_queue.enqueue(t2)

        # Both pending
        pending = task_queue.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending) == 2

        # Dequeue one
        task_queue.dequeue()
        pending = task_queue.get_tasks_by_status(TaskStatus.PENDING)
        in_progress = task_queue.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        assert len(pending) == 1
        assert len(in_progress) == 1

    def test_get_child_tasks(self, task_queue: TaskQueue):
        """get_child_tasks() returns tasks with matching parent_task_id."""
        parent = Task(type=TaskType.PLAN, description="parent task")
        child1 = Task(
            type=TaskType.CODE, description="child-1",
            parent_task_id=parent.id,
        )
        child2 = Task(
            type=TaskType.QA, description="child-2",
            parent_task_id=parent.id,
        )
        orphan = Task(type=TaskType.FIX, description="orphan")

        task_queue.enqueue(parent)
        task_queue.enqueue(child1)
        task_queue.enqueue(child2)
        task_queue.enqueue(orphan)

        children = task_queue.get_child_tasks(parent.id)
        assert len(children) == 2
        child_ids = {c.id for c in children}
        assert child1.id in child_ids
        assert child2.id in child_ids


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

class TestClearCompleted:
    def test_clear_completed(self, task_queue: TaskQueue):
        """clear_completed() removes old COMPLETED and CANCELLED tasks."""
        t1 = Task(type=TaskType.CODE, description="done")
        t2 = Task(type=TaskType.QA, description="cancelled")
        t3 = Task(type=TaskType.FIX, description="still pending")

        task_queue.enqueue(t1)
        task_queue.enqueue(t2)
        task_queue.enqueue(t3)

        # Complete t1 and cancel t2
        task_queue.dequeue()  # dequeues t1 (FIFO, same priority)
        task_queue.complete(t1.id)
        task_queue.cancel(t2.id)

        # Backdate completed_at so they appear older than the cutoff
        conn = sqlite3.connect(str(task_queue.db_path))
        try:
            old_date = (datetime.now() - timedelta(days=30)).isoformat()
            conn.execute(
                "UPDATE tasks SET completed_at = ? WHERE id IN (?, ?)",
                (old_date, t1.id, t2.id),
            )
            conn.commit()
        finally:
            conn.close()

        removed = task_queue.clear_completed(before_days=7)
        assert removed == 2

        # t3 should still be present
        assert task_queue.get_task(t3.id) is not None
        assert task_queue.get_task(t1.id) is None
        assert task_queue.get_task(t2.id) is None


# ---------------------------------------------------------------------------
# JSON safety helpers
# ---------------------------------------------------------------------------

class TestSafeJsonLoads:
    def test_safe_json_loads_valid(self, task_queue: TaskQueue):
        """Valid JSON string is parsed correctly."""
        result = task_queue._safe_json_loads('{"key": "value"}', "test_field")
        assert result == {"key": "value"}

    def test_safe_json_loads_invalid(self, task_queue: TaskQueue):
        """Invalid JSON returns the default value (empty dict)."""
        result = task_queue._safe_json_loads("not json {{{", "test_field")
        assert result == {}

        result_list = task_queue._safe_json_loads("bad", "test_field", default=[])
        assert result_list == []

    def test_safe_json_loads_too_large(self, task_queue: TaskQueue):
        """JSON strings exceeding MAX_JSON_FIELD_SIZE return the default."""
        huge = "x" * (task_queue.MAX_JSON_FIELD_SIZE + 1)
        result = task_queue._safe_json_loads(huge, "test_field")
        assert result == {}

    def test_safe_json_loads_empty(self, task_queue: TaskQueue):
        """Empty or None input returns the default."""
        assert task_queue._safe_json_loads("", "test_field") == {}
        assert task_queue._safe_json_loads(None, "test_field") == {}
        assert task_queue._safe_json_loads("", "test_field", default=[]) == []


# ---------------------------------------------------------------------------
# Peek semantics
# ---------------------------------------------------------------------------

class TestPeek:
    def test_peek_does_not_remove(self, task_queue: TaskQueue, sample_task: Task):
        """peek() returns the next task but leaves it in PENDING status."""
        task_queue.enqueue(sample_task)

        peeked = task_queue.peek()
        assert peeked is not None
        assert peeked.id == sample_task.id

        # Status should still be PENDING
        status = task_queue.get_status(sample_task.id)
        assert status == TaskStatus.PENDING

        # Subsequent dequeue should still return the same task
        dequeued = task_queue.dequeue()
        assert dequeued is not None
        assert dequeued.id == sample_task.id

    def test_peek_empty(self, task_queue: TaskQueue):
        """peek() on an empty queue returns None."""
        assert task_queue.peek() is None


# ---------------------------------------------------------------------------
# Async wrappers
# ---------------------------------------------------------------------------

class TestAsyncWrappers:
    @pytest.mark.asyncio
    async def test_async_enqueue_dequeue(self, task_queue: TaskQueue):
        """async_enqueue and async_dequeue round-trip a task correctly."""
        task = Task(type=TaskType.RESEARCH, description="async test")

        returned_id = await task_queue.async_enqueue(task)
        assert returned_id == task.id

        dequeued = await task_queue.async_dequeue()
        assert dequeued is not None
        assert dequeued.id == task.id
        assert dequeued.description == "async test"

    @pytest.mark.asyncio
    async def test_async_complete(self, task_queue: TaskQueue):
        """async_complete sets status to COMPLETED."""
        task = Task(type=TaskType.CODE, description="to complete")
        await task_queue.async_enqueue(task)
        await task_queue.async_dequeue()
        await task_queue.async_complete(task.id, output={"ok": True})

        status = task_queue.get_status(task.id)
        assert status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_async_fail(self, task_queue: TaskQueue):
        """async_fail with retry=False sets status to FAILED."""
        task = Task(type=TaskType.CODE, description="to fail")
        await task_queue.async_enqueue(task)
        await task_queue.async_dequeue()

        retried = await task_queue.async_fail(task.id, error="boom", retry=False)
        assert retried is False

        status = task_queue.get_status(task.id)
        assert status == TaskStatus.FAILED
