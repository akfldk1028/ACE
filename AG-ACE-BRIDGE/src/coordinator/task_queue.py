"""
Task Queue for AG-ACE-BRIDGE

SQLite-based priority queue for task management.
Supports persistent storage, priority ordering, and async operations.
"""

import sqlite3
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from src.utils.models import Task, TaskType, Priority, ResultStatus
from src.utils.logger import Loggers


class TaskStatus:
    """Task status constants"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskQueue:
    """
    SQLite-based priority task queue.

    Features:
    - Persistent storage
    - Priority-based ordering (HIGH > MEDIUM > LOW)
    - FIFO within same priority
    - Atomic operations
    - Async-compatible

    Example:
        queue = TaskQueue("./data/tasks.db")
        queue.initialize()

        task = Task(type=TaskType.CODE, description="Implement feature")
        queue.enqueue(task)

        next_task = queue.dequeue()
        if next_task:
            # Process task
            queue.complete(next_task.id, output={"result": "success"})
    """

    # Priority weights for ordering (higher = more urgent)
    PRIORITY_WEIGHTS = {
        Priority.HIGH: 3,
        Priority.MEDIUM: 2,
        Priority.LOW: 1,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    def __init__(self, db_path: str = "./data/tasks.db"):
        """
        Initialize task queue.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = Loggers.queue()
        self._lock = asyncio.Lock()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    priority_weight INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    input TEXT DEFAULT '{}',
                    context TEXT DEFAULT '{}',
                    requirements TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    needs_research INTEGER DEFAULT 0,
                    domain_validation INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    parent_task_id TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    output TEXT,
                    error TEXT
                )
            """)

            # Create indexes for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_priority
                ON tasks(priority_weight DESC, created_at ASC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_parent
                ON tasks(parent_task_id)
            """)

            self.logger.info("task_queue_initialized", db_path=str(self.db_path))

    def enqueue(self, task: Task) -> str:
        """
        Add task to queue.

        Args:
            task: Task to enqueue

        Returns:
            Task ID
        """
        now = datetime.now().isoformat()
        priority_weight = self.PRIORITY_WEIGHTS.get(task.priority, 2)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO tasks (
                    id, type, description, priority, priority_weight,
                    status, input, context, requirements, metadata,
                    needs_research, domain_validation, created_at, updated_at,
                    parent_task_id, retry_count, max_retries
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.type if isinstance(task.type, str) else task.type.value,
                task.description,
                task.priority if isinstance(task.priority, str) else task.priority.value,
                priority_weight,
                TaskStatus.PENDING,
                json.dumps(task.input),
                json.dumps(task.context),
                json.dumps(task.requirements),
                json.dumps(task.metadata),
                1 if task.needs_research else 0,
                1 if task.domain_validation else 0,
                task.created_at.isoformat() if task.created_at else now,
                now,
                task.parent_task_id,
                task.retry_count,
                task.max_retries,
            ))

        self.logger.info(
            "task_enqueued",
            task_id=task.id,
            type=task.type,
            priority=task.priority,
        )
        return task.id

    def dequeue(self) -> Optional[Task]:
        """
        Get next task from queue (highest priority, oldest first).

        Returns:
            Next pending task or None if queue is empty
        """
        with self._get_connection() as conn:
            # Select highest priority pending task
            cursor = conn.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY priority_weight DESC, created_at ASC
                LIMIT 1
            """, (TaskStatus.PENDING,))

            row = cursor.fetchone()
            if not row:
                return None

            # Mark as in progress
            now = datetime.now().isoformat()
            conn.execute("""
                UPDATE tasks
                SET status = ?, started_at = ?, updated_at = ?
                WHERE id = ?
            """, (TaskStatus.IN_PROGRESS, now, now, row["id"]))

            task = self._row_to_task(row)

            self.logger.info(
                "task_dequeued",
                task_id=task.id,
                type=task.type,
                priority=task.priority,
            )
            return task

    def peek(self) -> Optional[Task]:
        """
        Peek at next task without removing it.

        Returns:
            Next pending task or None
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY priority_weight DESC, created_at ASC
                LIMIT 1
            """, (TaskStatus.PENDING,))

            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def complete(
        self,
        task_id: str,
        output: Optional[Any] = None,
    ) -> None:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
            output: Task output data
        """
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE tasks
                SET status = ?, completed_at = ?, updated_at = ?, output = ?
                WHERE id = ?
            """, (
                TaskStatus.COMPLETED,
                now,
                now,
                json.dumps(output) if output else None,
                task_id,
            ))

        self.logger.info("task_completed", task_id=task_id)

    def fail(
        self,
        task_id: str,
        error: Optional[str] = None,
        retry: bool = True,
    ) -> bool:
        """
        Mark task as failed, optionally retry.

        Args:
            task_id: Task ID
            error: Error message
            retry: Whether to retry if retries remaining

        Returns:
            True if task was requeued for retry
        """
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT retry_count, max_retries FROM tasks WHERE id = ?
            """, (task_id,))
            row = cursor.fetchone()

            if not row:
                return False

            retry_count = row["retry_count"]
            max_retries = row["max_retries"]

            if retry and retry_count < max_retries:
                # Requeue for retry
                conn.execute("""
                    UPDATE tasks
                    SET status = ?, retry_count = ?, updated_at = ?, error = ?
                    WHERE id = ?
                """, (
                    TaskStatus.PENDING,
                    retry_count + 1,
                    now,
                    error,
                    task_id,
                ))
                self.logger.warning(
                    "task_retry",
                    task_id=task_id,
                    retry_count=retry_count + 1,
                    error=error,
                )
                return True
            else:
                # Mark as failed
                conn.execute("""
                    UPDATE tasks
                    SET status = ?, completed_at = ?, updated_at = ?, error = ?
                    WHERE id = ?
                """, (
                    TaskStatus.FAILED,
                    now,
                    now,
                    error,
                    task_id,
                ))
                self.logger.error(
                    "task_failed",
                    task_id=task_id,
                    error=error,
                )
                return False

    def cancel(self, task_id: str) -> None:
        """Cancel a task"""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE tasks
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (TaskStatus.CANCELLED, now, task_id))

        self.logger.info("task_cancelled", task_id=task_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def get_status(self, task_id: str) -> Optional[str]:
        """Get task status"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT status FROM tasks WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            return row["status"] if row else None

    def get_pending_count(self) -> int:
        """Get count of pending tasks"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
                (TaskStatus.PENDING,)
            )
            return cursor.fetchone()["count"]

    def get_in_progress_count(self) -> int:
        """Get count of in-progress tasks"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
                (TaskStatus.IN_PROGRESS,)
            )
            return cursor.fetchone()["count"]

    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        with self._get_connection() as conn:
            stats = {}
            for status in [
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
                    (status,)
                )
                stats[status] = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM tasks")
            stats["total"] = cursor.fetchone()["count"]

            return stats

    def get_tasks_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> List[Task]:
        """Get tasks by status"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY priority_weight DESC, created_at ASC
                LIMIT ?
            """, (status, limit))

            return [self._row_to_task(row) for row in cursor.fetchall()]

    def get_child_tasks(self, parent_task_id: str) -> List[Task]:
        """Get all child tasks of a parent"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM tasks
                WHERE parent_task_id = ?
                ORDER BY created_at ASC
            """, (parent_task_id,))

            return [self._row_to_task(row) for row in cursor.fetchall()]

    def clear_completed(self, before_days: int = 7) -> int:
        """
        Clear old completed tasks.

        Args:
            before_days: Remove tasks completed more than N days ago

        Returns:
            Number of tasks removed
        """
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=before_days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM tasks
                WHERE status IN (?, ?) AND completed_at < ?
            """, (TaskStatus.COMPLETED, TaskStatus.CANCELLED, cutoff))

            count = cursor.rowcount
            self.logger.info("tasks_cleared", count=count, before_days=before_days)
            return count

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert database row to Task model"""
        return Task(
            id=row["id"],
            type=TaskType(row["type"]),
            description=row["description"],
            priority=Priority(row["priority"]),
            input=json.loads(row["input"]) if row["input"] else {},
            context=json.loads(row["context"]) if row["context"] else {},
            requirements=json.loads(row["requirements"]) if row["requirements"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            needs_research=bool(row["needs_research"]),
            domain_validation=bool(row["domain_validation"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            parent_task_id=row["parent_task_id"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
        )

    # Async wrappers for compatibility
    async def async_enqueue(self, task: Task) -> str:
        """Async wrapper for enqueue"""
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self.enqueue, task
            )

    async def async_dequeue(self) -> Optional[Task]:
        """Async wrapper for dequeue"""
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self.dequeue
            )

    async def async_complete(
        self,
        task_id: str,
        output: Optional[Any] = None,
    ) -> None:
        """Async wrapper for complete"""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.complete(task_id, output)
            )

    async def async_fail(
        self,
        task_id: str,
        error: Optional[str] = None,
        retry: bool = True,
    ) -> bool:
        """Async wrapper for fail"""
        async with self._lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.fail(task_id, error, retry)
            )


# Convenience function
def create_task_queue(db_path: Optional[str] = None) -> TaskQueue:
    """
    Create and initialize a task queue.

    Args:
        db_path: Database path (uses config default if None)

    Returns:
        Initialized TaskQueue
    """
    from src.utils.config import get_settings

    settings = get_settings()
    path = db_path or settings.queue_db_path

    queue = TaskQueue(path)
    queue.initialize()
    return queue
