"""
Schedule Trigger - Pattern Execution Scheduler

Provides cron-based and event-based scheduling for pattern execution.
Integrates with PatternRegistry and Orchestrator for 24/7 automation.

Features:
- Cron expression scheduling (APScheduler)
- Event-based triggers (SharedMemory events)
- One-time execution
- Execution history tracking

Usage:
    trigger = ScheduleTrigger(
        registry=pattern_registry,
        orchestrator=orchestrator,
        shared_memory_url="http://localhost:8101",
    )
    await trigger.start()

    # Schedule pattern
    await trigger.schedule_pattern(
        pattern_id="abc123",
        cron="0 9 * * *",  # Every day at 9 AM
    )

    # Trigger on event
    await trigger.add_event_trigger(
        pattern_id="def456",
        event_type="task_completed",
    )
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.registry.pattern_registry import PatternRegistry, RegisteredPattern, PatternStatus
from src.memory import SharedMemoryClient
from src.utils.logger import Loggers


class TriggerType(str, Enum):
    """Types of execution triggers"""
    CRON = "cron"              # Cron expression
    INTERVAL = "interval"      # Fixed interval
    EVENT = "event"            # SharedMemory event
    ONCE = "once"              # One-time execution
    MANUAL = "manual"          # Manual trigger


@dataclass
class ScheduledJob:
    """A scheduled job for pattern execution"""
    id: str
    pattern_id: str
    trigger_type: TriggerType
    trigger_config: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pattern_id": self.pattern_id,
            "trigger_type": self.trigger_type.value,
            "trigger_config": self.trigger_config,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
        }


class ScheduleTrigger:
    """
    Pattern execution scheduler.

    Manages scheduled and event-based execution of patterns.
    Integrates with:
    - PatternRegistry: Pattern definitions
    - Orchestrator: Task execution
    - SharedMemory: Event subscriptions
    """

    def __init__(
        self,
        registry: PatternRegistry,
        orchestrator: Any = None,  # Avoid circular import
        shared_memory_url: str = "http://localhost:8101",
        enable_shared_memory: bool = True,
    ):
        """
        Initialize ScheduleTrigger.

        Args:
            registry: PatternRegistry instance
            orchestrator: Orchestrator instance for task execution
            shared_memory_url: SharedMemory server URL
            enable_shared_memory: Enable event-based triggers
        """
        self.registry = registry
        self.orchestrator = orchestrator
        self.shared_memory_url = shared_memory_url
        self.enable_shared_memory = enable_shared_memory

        self.logger = Loggers.scheduler()

        self._scheduler: Optional[AsyncIOScheduler] = None
        self._shared_memory: Optional[SharedMemoryClient] = None
        self._jobs: Dict[str, ScheduledJob] = {}
        self._event_handlers: Dict[str, List[str]] = {}  # event_type -> [pattern_ids]
        self._running = False
        self._event_poll_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler"""
        if self._running:
            return

        self._running = True

        # Initialize APScheduler
        self._scheduler = AsyncIOScheduler()
        self._scheduler.start()

        # Initialize SharedMemory for event triggers
        if self.enable_shared_memory:
            self._shared_memory = SharedMemoryClient(
                base_url=self.shared_memory_url,
                source_name="schedule_trigger",
            )
            # Start event polling
            self._event_poll_task = asyncio.create_task(self._poll_events())

        # Load scheduled patterns from registry
        await self._load_scheduled_patterns()

        self.logger.info("schedule_trigger_started")

    async def stop(self):
        """Stop the scheduler"""
        self._running = False

        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None

        if self._event_poll_task:
            self._event_poll_task.cancel()
            try:
                await self._event_poll_task
            except asyncio.CancelledError:
                pass
            self._event_poll_task = None

        if self._shared_memory:
            await self._shared_memory.close()
            self._shared_memory = None

        self.logger.info("schedule_trigger_stopped")

    async def _load_scheduled_patterns(self):
        """Load patterns with schedules from registry"""
        scheduled = self.registry.list_scheduled()

        for pattern in scheduled:
            if pattern.schedule:
                await self.schedule_pattern(
                    pattern_id=pattern.id,
                    cron=pattern.schedule,
                )

        self.logger.info(
            "loaded_scheduled_patterns",
            count=len(scheduled),
        )

    async def _poll_events(self):
        """Poll SharedMemory for events (event-based triggers)"""
        last_event_id = None

        while self._running:
            try:
                if not self._shared_memory:
                    await asyncio.sleep(1)
                    continue

                # Get recent events
                events = await self._shared_memory.get_events(
                    limit=50,
                    after=last_event_id,
                )

                for event in events:
                    event_type = event.get("event_type")
                    event_id = event.get("id")

                    # Check if any patterns are triggered by this event
                    if event_type in self._event_handlers:
                        for pattern_id in self._event_handlers[event_type]:
                            await self._execute_pattern(
                                pattern_id,
                                trigger_type=TriggerType.EVENT,
                                trigger_data={"event": event},
                            )

                    if event_id:
                        last_event_id = event_id

                await asyncio.sleep(1)  # Poll interval

            except Exception as e:
                self.logger.error(
                    "event_poll_error",
                    error=str(e),
                )
                await asyncio.sleep(5)  # Back off on error

    async def schedule_pattern(
        self,
        pattern_id: str,
        cron: str = None,
        interval_seconds: int = None,
        run_at: datetime = None,
    ) -> Optional[ScheduledJob]:
        """
        Schedule a pattern for execution.

        Args:
            pattern_id: Pattern to schedule
            cron: Cron expression (e.g., "0 9 * * *")
            interval_seconds: Fixed interval in seconds
            run_at: One-time execution datetime

        Returns:
            ScheduledJob if successful
        """
        pattern = self.registry.get(pattern_id)
        if not pattern:
            self.logger.warning("pattern_not_found", pattern_id=pattern_id)
            return None

        # Determine trigger type and create APScheduler trigger
        job_id = str(uuid.uuid4())
        trigger_type = TriggerType.MANUAL
        trigger_config = {}
        apscheduler_trigger = None

        if cron:
            trigger_type = TriggerType.CRON
            trigger_config = {"cron": cron}
            apscheduler_trigger = CronTrigger.from_crontab(cron)

        elif interval_seconds:
            trigger_type = TriggerType.INTERVAL
            trigger_config = {"seconds": interval_seconds}
            apscheduler_trigger = IntervalTrigger(seconds=interval_seconds)

        elif run_at:
            trigger_type = TriggerType.ONCE
            trigger_config = {"run_at": run_at.isoformat()}
            apscheduler_trigger = DateTrigger(run_date=run_at)

        if not apscheduler_trigger:
            self.logger.warning(
                "no_trigger_specified",
                pattern_id=pattern_id,
            )
            return None

        # Create job record
        job = ScheduledJob(
            id=job_id,
            pattern_id=pattern_id,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
        )

        # Add to APScheduler
        self._scheduler.add_job(
            self._execute_pattern,
            trigger=apscheduler_trigger,
            args=[pattern_id],
            kwargs={"trigger_type": trigger_type},
            id=job_id,
            name=f"pattern_{pattern.name}",
        )

        # Get next run time
        apscheduler_job = self._scheduler.get_job(job_id)
        if apscheduler_job and apscheduler_job.next_run_time:
            job.next_run_at = apscheduler_job.next_run_time

        # Store job
        self._jobs[job_id] = job

        # Update pattern status
        await self.registry.set_schedule(pattern_id, cron or str(trigger_config))

        self.logger.info(
            "pattern_scheduled",
            job_id=job_id,
            pattern_id=pattern_id,
            trigger_type=trigger_type.value,
            next_run=job.next_run_at.isoformat() if job.next_run_at else None,
        )

        return job

    async def add_event_trigger(
        self,
        pattern_id: str,
        event_type: str,
    ) -> bool:
        """
        Add event-based trigger for pattern.

        Args:
            pattern_id: Pattern to trigger
            event_type: SharedMemory event type to listen for

        Returns:
            True if successful
        """
        pattern = self.registry.get(pattern_id)
        if not pattern:
            return False

        # Register event handler
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []

        if pattern_id not in self._event_handlers[event_type]:
            self._event_handlers[event_type].append(pattern_id)

        # Create job record
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            id=job_id,
            pattern_id=pattern_id,
            trigger_type=TriggerType.EVENT,
            trigger_config={"event_type": event_type},
        )
        self._jobs[job_id] = job

        self.logger.info(
            "event_trigger_added",
            pattern_id=pattern_id,
            event_type=event_type,
        )

        return True

    async def remove_schedule(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]

        # Remove from APScheduler
        if self._scheduler:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass

        # Remove from event handlers
        if job.trigger_type == TriggerType.EVENT:
            event_type = job.trigger_config.get("event_type")
            if event_type and event_type in self._event_handlers:
                self._event_handlers[event_type] = [
                    pid for pid in self._event_handlers[event_type]
                    if pid != job.pattern_id
                ]

        del self._jobs[job_id]

        self.logger.info("schedule_removed", job_id=job_id)
        return True

    async def trigger_now(self, pattern_id: str) -> bool:
        """Manually trigger pattern execution"""
        return await self._execute_pattern(
            pattern_id,
            trigger_type=TriggerType.MANUAL,
        )

    async def _execute_pattern(
        self,
        pattern_id: str,
        trigger_type: TriggerType = TriggerType.MANUAL,
        trigger_data: Dict[str, Any] = None,
    ) -> bool:
        """
        Execute a pattern.

        Args:
            pattern_id: Pattern to execute
            trigger_type: What triggered the execution
            trigger_data: Additional trigger context

        Returns:
            True if execution started successfully
        """
        pattern = self.registry.get(pattern_id)
        if not pattern:
            self.logger.warning("execute_pattern_not_found", pattern_id=pattern_id)
            return False

        if pattern.status not in [PatternStatus.ACTIVE, PatternStatus.SCHEDULED]:
            self.logger.warning(
                "execute_pattern_not_active",
                pattern_id=pattern_id,
                status=pattern.status.value,
            )
            return False

        self.logger.info(
            "executing_pattern",
            pattern_id=pattern_id,
            pattern_name=pattern.name,
            trigger_type=trigger_type.value,
        )

        try:
            # Build task from pattern
            task_data = self._pattern_to_task(pattern, trigger_data)

            # Execute via orchestrator
            if self.orchestrator:
                await self.orchestrator.submit_task(task_data)

            # Record successful start
            await self.registry.record_execution(pattern_id, success=True)

            # Update job stats
            for job in self._jobs.values():
                if job.pattern_id == pattern_id:
                    job.last_run_at = datetime.now()
                    job.run_count += 1

            # Publish execution event
            if self._shared_memory:
                await self._shared_memory.publish_event(
                    event_type="pattern_triggered",
                    data={
                        "pattern_id": pattern_id,
                        "pattern_name": pattern.name,
                        "trigger_type": trigger_type.value,
                    },
                )

            return True

        except Exception as e:
            self.logger.error(
                "pattern_execution_error",
                pattern_id=pattern_id,
                error=str(e),
            )

            # Record failure
            await self.registry.record_execution(
                pattern_id,
                success=False,
                error_message=str(e),
            )

            # Update job error count
            for job in self._jobs.values():
                if job.pattern_id == pattern_id:
                    job.error_count += 1

            return False

    def _pattern_to_task(
        self,
        pattern: RegisteredPattern,
        trigger_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Convert pattern to orchestrator task.

        Args:
            pattern: Pattern to convert
            trigger_data: Additional trigger context

        Returns:
            Task data dictionary
        """
        from src.utils.models import TaskType, Priority

        # Determine task type from pattern type
        task_type = TaskType.CODE  # Default
        if "research" in pattern.name.lower():
            task_type = TaskType.RESEARCH
        elif "plan" in pattern.name.lower():
            task_type = TaskType.PLAN
        elif "review" in pattern.name.lower():
            task_type = TaskType.REVIEW

        return {
            "id": str(uuid.uuid4()),
            "type": task_type.value,
            "description": f"Execute pattern: {pattern.name}",
            "priority": Priority.MEDIUM.value,
            "input_data": pattern.data,
            "context": {
                "pattern_id": pattern.id,
                "pattern_name": pattern.name,
                "pattern_version": pattern.version,
                "trigger_data": trigger_data or {},
            },
        }

    def list_jobs(self) -> List[ScheduledJob]:
        """Get all scheduled jobs"""
        return list(self._jobs.values())

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get job by ID"""
        return self._jobs.get(job_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        jobs = list(self._jobs.values())

        return {
            "total_jobs": len(jobs),
            "by_trigger_type": {
                tt.value: len([j for j in jobs if j.trigger_type == tt])
                for tt in TriggerType
            },
            "total_runs": sum(j.run_count for j in jobs),
            "total_errors": sum(j.error_count for j in jobs),
            "enabled_jobs": len([j for j in jobs if j.enabled]),
            "event_types_watched": list(self._event_handlers.keys()),
        }
