"""
Project folder watcher for AG-ACE-BRIDGE

Monitors projects/queue/ folder and automatically
submits new specs to the orchestrator.
"""

import asyncio
import shutil
from pathlib import Path
from typing import Optional, Callable, Awaitable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.utils.logger import Loggers
from src.utils.config import get_settings
from src.project.spec import (
    ProjectSpec,
    ProjectStatus,
    load_project_spec,
    save_project_spec,
)
from src.utils.models import Task, TaskType, Priority
from src.coordinator.task_queue import TaskQueue, create_task_queue


class ProjectFileHandler(FileSystemEventHandler):
    """
    Handles file system events in the projects/queue folder.

    When a new spec file is dropped, it:
    1. Validates the spec
    2. Creates tasks from goals
    3. Moves spec to appropriate folder
    """

    def __init__(
        self,
        queue: TaskQueue,
        projects_dir: Path,
        callback: Optional[Callable[[ProjectSpec], Awaitable[None]]] = None,
    ):
        super().__init__()
        self.queue = queue
        self.projects_dir = projects_dir
        self.callback = callback
        self.logger = Loggers.orchestrator()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set asyncio event loop for callbacks"""
        self._loop = loop

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process yaml/json files
        if file_path.suffix not in (".yaml", ".yml", ".json"):
            return

        self.logger.info("project_file_detected", file=str(file_path))

        # Process in event loop if available
        if self._loop and self.callback:
            asyncio.run_coroutine_threadsafe(
                self._process_spec_async(file_path),
                self._loop,
            )
        else:
            self._process_spec_sync(file_path)

    async def _process_spec_async(self, file_path: Path) -> None:
        """Process spec file asynchronously"""
        spec = self._load_and_validate(file_path)
        if spec and self.callback:
            await self.callback(spec)

    def _process_spec_sync(self, file_path: Path) -> None:
        """Process spec file synchronously"""
        spec = self._load_and_validate(file_path)
        if spec:
            self._create_tasks(spec, file_path)

    def _load_and_validate(self, file_path: Path) -> Optional[ProjectSpec]:
        """Load and validate project spec"""
        # Wait a moment for file to be fully written
        import time
        time.sleep(0.5)

        try:
            spec = load_project_spec(file_path)

            self.logger.info(
                "project_spec_loaded",
                project_id=spec.id,
                name=spec.name,
                goals=len(spec.goals),
            )

            return spec

        except Exception as e:
            self.logger.error(
                "project_spec_invalid",
                file=str(file_path),
                error=str(e),
            )

            # Move to failed folder
            failed_path = self.projects_dir / "failed" / file_path.name
            shutil.move(str(file_path), str(failed_path))

            return None

    def _create_tasks(self, spec: ProjectSpec, file_path: Path) -> None:
        """Create tasks from project spec and queue them"""
        # Update spec status
        spec.status = ProjectStatus.QUEUED
        spec.started_at = datetime.now()

        # Map priority
        priority_map = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
        }
        priority = priority_map.get(spec.priority, Priority.MEDIUM)

        # Create master planning task
        master_task = Task(
            type=TaskType.PLANNING,
            priority=priority,
            input={
                "project_id": spec.id,
                "project_name": spec.name,
                "description": spec.description,
                "goals": spec.goals,
                "requirements": spec.requirements.model_dump(),
                "tech_stack": spec.tech_stack,
                "output_path": spec.output_path,
                "agent_config": spec.agents.model_dump(),
                "pipeline_config": spec.pipeline.model_dump(),
            },
            context={
                "project_spec": spec.model_dump(mode="json"),
            },
            metadata={
                "source": "project_watcher",
                "spec_file": str(file_path.name),
            },
        )

        # Enqueue master task
        self.queue.enqueue(master_task)

        self.logger.info(
            "project_tasks_queued",
            project_id=spec.id,
            master_task_id=master_task.id,
        )

        # Move spec to in-progress or completed based on auto_start
        if spec.auto_start:
            dest_folder = "queue"  # Keep in queue folder but mark as processing
        else:
            dest_folder = "queue"

        # Save updated spec
        new_path = self.projects_dir / dest_folder / f"{spec.id}_{file_path.name}"
        save_project_spec(spec, new_path)

        # Remove original if different path
        if new_path != file_path:
            file_path.unlink()


class ProjectWatcher:
    """
    Watches the projects folder for new specs.

    Usage:
        watcher = ProjectWatcher()
        await watcher.start()  # Runs forever
    """

    def __init__(
        self,
        projects_dir: Optional[Path | str] = None,
        db_path: Optional[str] = None,
    ):
        settings = get_settings()
        self.projects_dir = Path(projects_dir or settings.projects_dir)
        self.queue_dir = self.projects_dir / "queue"
        self.logger = Loggers.orchestrator()

        # Create directories
        (self.projects_dir / "queue").mkdir(parents=True, exist_ok=True)
        (self.projects_dir / "completed").mkdir(parents=True, exist_ok=True)
        (self.projects_dir / "failed").mkdir(parents=True, exist_ok=True)

        # Task queue
        self.queue = create_task_queue(db_path)

        # File handler
        self._handler = ProjectFileHandler(
            queue=self.queue,
            projects_dir=self.projects_dir,
        )

        # Observer
        self._observer = Observer()
        self._running = False

    async def start(self) -> None:
        """Start watching for new project specs"""
        if self._running:
            self.logger.warning("watcher_already_running")
            return

        self._running = True

        # Set event loop for async callbacks
        self._handler.set_event_loop(asyncio.get_running_loop())

        # Schedule watcher
        self._observer.schedule(
            self._handler,
            str(self.queue_dir),
            recursive=False,
        )

        # Start observer
        self._observer.start()

        self.logger.info(
            "watcher_started",
            watch_dir=str(self.queue_dir),
        )

        # Process existing files
        await self._process_existing()

        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("watcher_cancelled")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the watcher"""
        self._running = False
        self._observer.stop()
        self._observer.join(timeout=5)
        self.logger.info("watcher_stopped")

    async def _process_existing(self) -> None:
        """Process any existing spec files in queue"""
        for file_path in self.queue_dir.glob("*.yaml"):
            self._handler._process_spec_sync(file_path)

        for file_path in self.queue_dir.glob("*.yml"):
            self._handler._process_spec_sync(file_path)

        for file_path in self.queue_dir.glob("*.json"):
            self._handler._process_spec_sync(file_path)

    def set_callback(
        self,
        callback: Callable[[ProjectSpec], Awaitable[None]],
    ) -> None:
        """Set callback for new projects"""
        self._handler.callback = callback


async def start_watcher(
    projects_dir: Optional[str] = None,
    db_path: Optional[str] = None,
) -> None:
    """
    Start the project watcher.

    Args:
        projects_dir: Directory to watch
        db_path: Task queue database path
    """
    watcher = ProjectWatcher(projects_dir, db_path)
    await watcher.start()


if __name__ == "__main__":
    asyncio.run(start_watcher())
