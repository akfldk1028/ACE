"""
Pattern Watcher - AutoGen Studio Output Monitor

Watches for new patterns from AutoGen Studio and triggers auto-import.
Uses watchdog library for cross-platform file system monitoring.

Usage:
    watcher = PatternWatcher(
        watch_paths=["/path/to/autogenstudio/patterns"],
        on_pattern_detected=callback_function,
    )
    await watcher.start()
"""

import asyncio
import json
import yaml
import os
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from src.utils.logger import Loggers


class PatternEventType(str, Enum):
    """Types of pattern events"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class PatternEvent:
    """Event representing a pattern file change"""
    event_type: PatternEventType
    file_path: str
    pattern_name: str
    pattern_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "file_path": self.file_path,
            "pattern_name": self.pattern_name,
            "pattern_data": self.pattern_data,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum,
        }


class PatternFileHandler(FileSystemEventHandler):
    """
    Handles file system events for pattern files.
    Filters for JSON/YAML pattern files and notifies callback.
    """

    def __init__(
        self,
        callback: Callable[[PatternEvent], None],
        extensions: List[str] = None,
    ):
        super().__init__()
        self.callback = callback
        self.extensions = extensions or [".json", ".yaml", ".yml"]
        self.logger = Loggers.watcher()
        self._processed_checksums: Dict[str, str] = {}

    def _is_pattern_file(self, path: str) -> bool:
        """Check if file is a pattern file"""
        return any(path.endswith(ext) for ext in self.extensions)

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _parse_pattern_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse pattern file (JSON or YAML)"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if file_path.endswith(".json"):
                return json.loads(content)
            elif file_path.endswith((".yaml", ".yml")):
                return yaml.safe_load(content)
            return None

        except Exception as e:
            self.logger.error(
                "pattern_parse_error",
                file_path=file_path,
                error=str(e),
            )
            return None

    def _create_event(
        self,
        event_type: PatternEventType,
        src_path: str,
    ) -> Optional[PatternEvent]:
        """Create a PatternEvent from file system event"""
        if not self._is_pattern_file(src_path):
            return None

        # Calculate checksum
        checksum = self._calculate_checksum(src_path)

        # Skip if same checksum (duplicate event)
        if event_type != PatternEventType.DELETED:
            if src_path in self._processed_checksums:
                if self._processed_checksums[src_path] == checksum:
                    return None
            self._processed_checksums[src_path] = checksum

        # Parse pattern data
        pattern_data = None
        if event_type != PatternEventType.DELETED:
            pattern_data = self._parse_pattern_file(src_path)

        # Extract pattern name from file or data
        pattern_name = Path(src_path).stem
        if pattern_data and "name" in pattern_data:
            pattern_name = pattern_data["name"]

        return PatternEvent(
            event_type=event_type,
            file_path=src_path,
            pattern_name=pattern_name,
            pattern_data=pattern_data,
            checksum=checksum,
        )

    def on_created(self, event):
        """Handle file creation"""
        if event.is_directory:
            return

        pattern_event = self._create_event(
            PatternEventType.CREATED,
            event.src_path,
        )
        if pattern_event:
            self.logger.info(
                "pattern_file_created",
                file_path=event.src_path,
                pattern_name=pattern_event.pattern_name,
            )
            self.callback(pattern_event)

    def on_modified(self, event):
        """Handle file modification"""
        if event.is_directory:
            return

        pattern_event = self._create_event(
            PatternEventType.MODIFIED,
            event.src_path,
        )
        if pattern_event:
            self.logger.info(
                "pattern_file_modified",
                file_path=event.src_path,
                pattern_name=pattern_event.pattern_name,
            )
            self.callback(pattern_event)

    def on_deleted(self, event):
        """Handle file deletion"""
        if event.is_directory:
            return

        if not self._is_pattern_file(event.src_path):
            return

        # Remove from processed checksums
        self._processed_checksums.pop(event.src_path, None)

        pattern_event = PatternEvent(
            event_type=PatternEventType.DELETED,
            file_path=event.src_path,
            pattern_name=Path(event.src_path).stem,
        )
        self.logger.info(
            "pattern_file_deleted",
            file_path=event.src_path,
        )
        self.callback(pattern_event)


class PatternWatcher:
    """
    Watches directories for pattern files from AutoGen Studio.

    Features:
    - Multi-directory watching
    - JSON/YAML pattern file detection
    - Duplicate event filtering (via checksum)
    - Async event callback support

    Example:
        async def on_pattern(event: PatternEvent):
            print(f"New pattern: {event.pattern_name}")
            await registry.register(event)

        watcher = PatternWatcher(
            watch_paths=["~/.autogenstudio/patterns"],
            on_pattern_detected=on_pattern,
        )
        await watcher.start()
    """

    # Default paths to watch for AutoGen Studio patterns
    DEFAULT_WATCH_PATHS = [
        "~/.autogenstudio/patterns",
        "~/.autogenstudio/workflows",
        "./patterns",  # Local patterns directory
    ]

    def __init__(
        self,
        watch_paths: List[str] = None,
        on_pattern_detected: Callable[[PatternEvent], Any] = None,
        extensions: List[str] = None,
    ):
        """
        Initialize PatternWatcher.

        Args:
            watch_paths: List of directories to watch
            on_pattern_detected: Callback function (sync or async)
            extensions: File extensions to watch
        """
        self.watch_paths = [
            os.path.expanduser(p)
            for p in (watch_paths or self.DEFAULT_WATCH_PATHS)
        ]
        self.on_pattern_detected = on_pattern_detected
        self.extensions = extensions or [".json", ".yaml", ".yml"]

        self.logger = Loggers.watcher()
        self._observer: Optional[Observer] = None
        self._running = False
        self._event_queue: asyncio.Queue = None
        self._process_task: Optional[asyncio.Task] = None

    def _sync_callback(self, event: PatternEvent):
        """Synchronous callback that queues events for async processing"""
        if self._event_queue:
            try:
                self._event_queue.put_nowait(event)
            except asyncio.QueueFull:
                self.logger.warning("event_queue_full", event=event.to_dict())

    async def _process_events(self):
        """Process events from queue asynchronously"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )

                if self.on_pattern_detected:
                    result = self.on_pattern_detected(event)
                    if asyncio.iscoroutine(result):
                        await result

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(
                    "event_processing_error",
                    error=str(e),
                )

    async def start(self):
        """Start watching for pattern files"""
        if self._running:
            return

        self._running = True
        self._event_queue = asyncio.Queue(maxsize=1000)

        # Create observer
        self._observer = Observer()

        # Create handler
        handler = PatternFileHandler(
            callback=self._sync_callback,
            extensions=self.extensions,
        )

        # Add watches for each path
        for path in self.watch_paths:
            if os.path.exists(path):
                self._observer.schedule(handler, path, recursive=True)
                self.logger.info("watching_path", path=path)
            else:
                # Create directory if it doesn't exist
                try:
                    os.makedirs(path, exist_ok=True)
                    self._observer.schedule(handler, path, recursive=True)
                    self.logger.info("created_and_watching_path", path=path)
                except Exception as e:
                    self.logger.warning(
                        "watch_path_not_found",
                        path=path,
                        error=str(e),
                    )

        # Start observer
        self._observer.start()
        self.logger.info("pattern_watcher_started")

        # Start async event processor
        self._process_task = asyncio.create_task(self._process_events())

    async def stop(self):
        """Stop watching"""
        self._running = False

        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None

        self.logger.info("pattern_watcher_stopped")

    async def scan_existing(self) -> List[PatternEvent]:
        """
        Scan existing pattern files in watch paths.

        Returns:
            List of PatternEvents for existing files
        """
        events = []

        for watch_path in self.watch_paths:
            if not os.path.exists(watch_path):
                continue

            for root, _, files in os.walk(watch_path):
                for filename in files:
                    if any(filename.endswith(ext) for ext in self.extensions):
                        file_path = os.path.join(root, filename)

                        # Parse pattern
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()

                            if filename.endswith(".json"):
                                data = json.loads(content)
                            else:
                                data = yaml.safe_load(content)

                            pattern_name = data.get("name", Path(filename).stem)

                            event = PatternEvent(
                                event_type=PatternEventType.CREATED,
                                file_path=file_path,
                                pattern_name=pattern_name,
                                pattern_data=data,
                                checksum=hashlib.md5(content.encode()).hexdigest(),
                            )
                            events.append(event)

                        except Exception as e:
                            self.logger.warning(
                                "scan_file_error",
                                file_path=file_path,
                                error=str(e),
                            )

        self.logger.info("scan_complete", pattern_count=len(events))
        return events

    def is_running(self) -> bool:
        """Check if watcher is running"""
        return self._running
