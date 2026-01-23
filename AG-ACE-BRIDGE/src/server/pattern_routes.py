"""
Pattern REST API Routes

Provides HTTP endpoints for pattern management:
- List/Get patterns
- Register patterns manually
- Schedule patterns
- Trigger pattern execution
- Monitor pattern status

Integrates with:
- PatternRegistry for storage
- ScheduleTrigger for scheduling
- SharedMemory for sync
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.registry.pattern_registry import PatternRegistry, PatternStatus, PatternType
from src.scheduler.trigger import ScheduleTrigger, TriggerType
from src.utils.logger import Loggers


router = APIRouter(prefix="/patterns", tags=["patterns"])
logger = Loggers.dashboard()

# These will be set by the dashboard during initialization
_registry: Optional[PatternRegistry] = None
_scheduler: Optional[ScheduleTrigger] = None


def set_dependencies(
    registry: PatternRegistry,
    scheduler: ScheduleTrigger,
):
    """Set dependencies (called during app initialization)"""
    global _registry, _scheduler
    _registry = registry
    _scheduler = scheduler


# --- Request/Response Models ---

class PatternRegisterRequest(BaseModel):
    """Request to register a pattern manually"""
    name: str = Field(..., description="Pattern name")
    pattern_type: str = Field("workflow", description="Pattern type")
    data: Dict[str, Any] = Field(..., description="Pattern data/definition")
    tags: List[str] = Field(default=[], description="Tags for categorization")


class PatternScheduleRequest(BaseModel):
    """Request to schedule a pattern"""
    cron: Optional[str] = Field(None, description="Cron expression")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds")
    run_at: Optional[datetime] = Field(None, description="One-time run datetime")


class PatternEventTriggerRequest(BaseModel):
    """Request to add event-based trigger"""
    event_type: str = Field(..., description="SharedMemory event type")


class PatternResponse(BaseModel):
    """Pattern response model"""
    id: str
    name: str
    pattern_type: str
    status: str
    source_path: str
    version: int
    schedule: Optional[str]
    created_at: str
    updated_at: str
    last_executed_at: Optional[str]
    execution_count: int
    tags: List[str]


class JobResponse(BaseModel):
    """Scheduled job response model"""
    id: str
    pattern_id: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    enabled: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    run_count: int
    error_count: int


# --- Endpoints ---

@router.get("/", response_model=List[PatternResponse])
async def list_patterns(
    status: Optional[str] = None,
    pattern_type: Optional[str] = None,
):
    """
    List all registered patterns.

    Args:
        status: Filter by status (pending, active, scheduled, disabled, error)
        pattern_type: Filter by type (workflow, agent, skill, template)
    """
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    patterns = _registry.list_all()

    # Apply filters
    if status:
        try:
            status_enum = PatternStatus(status)
            patterns = [p for p in patterns if p.status == status_enum]
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    if pattern_type:
        try:
            type_enum = PatternType(pattern_type)
            patterns = [p for p in patterns if p.pattern_type == type_enum]
        except ValueError:
            raise HTTPException(400, f"Invalid pattern_type: {pattern_type}")

    return [
        PatternResponse(
            id=p.id,
            name=p.name,
            pattern_type=p.pattern_type.value,
            status=p.status.value,
            source_path=p.source_path,
            version=p.version,
            schedule=p.schedule,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
            last_executed_at=p.last_executed_at.isoformat() if p.last_executed_at else None,
            execution_count=p.execution_count,
            tags=p.tags,
        )
        for p in patterns
    ]


@router.get("/stats")
async def get_pattern_stats():
    """Get pattern registry statistics"""
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    stats = _registry.get_stats()

    if _scheduler:
        stats["scheduler"] = _scheduler.get_stats()

    return stats


@router.get("/{pattern_id}", response_model=PatternResponse)
async def get_pattern(pattern_id: str):
    """Get pattern by ID"""
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    pattern = _registry.get(pattern_id)
    if not pattern:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    return PatternResponse(
        id=pattern.id,
        name=pattern.name,
        pattern_type=pattern.pattern_type.value,
        status=pattern.status.value,
        source_path=pattern.source_path,
        version=pattern.version,
        schedule=pattern.schedule,
        created_at=pattern.created_at.isoformat(),
        updated_at=pattern.updated_at.isoformat(),
        last_executed_at=pattern.last_executed_at.isoformat() if pattern.last_executed_at else None,
        execution_count=pattern.execution_count,
        tags=pattern.tags,
    )


@router.get("/{pattern_id}/data")
async def get_pattern_data(pattern_id: str):
    """Get full pattern data/definition"""
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    pattern = _registry.get(pattern_id)
    if not pattern:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    return {
        "id": pattern.id,
        "name": pattern.name,
        "data": pattern.data,
        "metadata": pattern.metadata,
    }


@router.post("/", response_model=PatternResponse)
async def register_pattern(request: PatternRegisterRequest):
    """
    Register a pattern manually.

    Use this endpoint to register patterns programmatically
    (patterns from AutoGen Studio are auto-registered via PatternWatcher).
    """
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    from src.watcher.pattern_watcher import PatternEvent, PatternEventType
    import hashlib
    import json

    # Create pattern event
    checksum = hashlib.md5(json.dumps(request.data, sort_keys=True).encode()).hexdigest()

    event = PatternEvent(
        event_type=PatternEventType.CREATED,
        file_path="manual://api",
        pattern_name=request.name,
        pattern_data={
            "name": request.name,
            "type": request.pattern_type,
            "tags": request.tags,
            **request.data,
        },
        checksum=checksum,
    )

    # Register
    pattern = await _registry.register(event)
    if not pattern:
        raise HTTPException(400, "Failed to register pattern")

    logger.info(
        "pattern_registered_via_api",
        pattern_id=pattern.id,
        name=pattern.name,
    )

    return PatternResponse(
        id=pattern.id,
        name=pattern.name,
        pattern_type=pattern.pattern_type.value,
        status=pattern.status.value,
        source_path=pattern.source_path,
        version=pattern.version,
        schedule=pattern.schedule,
        created_at=pattern.created_at.isoformat(),
        updated_at=pattern.updated_at.isoformat(),
        last_executed_at=pattern.last_executed_at.isoformat() if pattern.last_executed_at else None,
        execution_count=pattern.execution_count,
        tags=pattern.tags,
    )


@router.delete("/{pattern_id}")
async def unregister_pattern(pattern_id: str):
    """Unregister a pattern"""
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    success = await _registry.unregister(pattern_id)
    if not success:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    return {"message": f"Pattern {pattern_id} unregistered"}


@router.post("/{pattern_id}/schedule", response_model=JobResponse)
async def schedule_pattern(pattern_id: str, request: PatternScheduleRequest):
    """
    Schedule pattern execution.

    Provide one of:
    - cron: Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
    - interval_seconds: Run every N seconds
    - run_at: One-time execution at specific datetime
    """
    if not _scheduler:
        raise HTTPException(500, "Scheduler not initialized")

    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    pattern = _registry.get(pattern_id)
    if not pattern:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    job = await _scheduler.schedule_pattern(
        pattern_id=pattern_id,
        cron=request.cron,
        interval_seconds=request.interval_seconds,
        run_at=request.run_at,
    )

    if not job:
        raise HTTPException(400, "Failed to schedule pattern. Provide cron, interval_seconds, or run_at.")

    return JobResponse(
        id=job.id,
        pattern_id=job.pattern_id,
        trigger_type=job.trigger_type.value,
        trigger_config=job.trigger_config,
        enabled=job.enabled,
        last_run_at=job.last_run_at.isoformat() if job.last_run_at else None,
        next_run_at=job.next_run_at.isoformat() if job.next_run_at else None,
        run_count=job.run_count,
        error_count=job.error_count,
    )


@router.post("/{pattern_id}/event-trigger")
async def add_event_trigger(pattern_id: str, request: PatternEventTriggerRequest):
    """
    Add event-based trigger for pattern.

    The pattern will execute when the specified SharedMemory event occurs.
    """
    if not _scheduler:
        raise HTTPException(500, "Scheduler not initialized")

    success = await _scheduler.add_event_trigger(
        pattern_id=pattern_id,
        event_type=request.event_type,
    )

    if not success:
        raise HTTPException(400, "Failed to add event trigger")

    return {
        "message": f"Event trigger added for pattern {pattern_id}",
        "event_type": request.event_type,
    }


@router.post("/{pattern_id}/trigger")
async def trigger_pattern(pattern_id: str, background_tasks: BackgroundTasks):
    """
    Trigger pattern execution immediately.

    Execution runs in background; returns immediately.
    """
    if not _scheduler:
        raise HTTPException(500, "Scheduler not initialized")

    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    pattern = _registry.get(pattern_id)
    if not pattern:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    # Run in background
    background_tasks.add_task(_scheduler.trigger_now, pattern_id)

    return {
        "message": f"Pattern {pattern_id} triggered",
        "pattern_name": pattern.name,
    }


@router.patch("/{pattern_id}/status")
async def update_pattern_status(pattern_id: str, status: str):
    """Update pattern status"""
    if not _registry:
        raise HTTPException(500, "Pattern registry not initialized")

    try:
        status_enum = PatternStatus(status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {status}")

    success = await _registry.update_status(pattern_id, status_enum)
    if not success:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    return {"message": f"Pattern {pattern_id} status updated to {status}"}


# --- Job Management ---

@router.get("/jobs/", response_model=List[JobResponse])
async def list_jobs():
    """List all scheduled jobs"""
    if not _scheduler:
        raise HTTPException(500, "Scheduler not initialized")

    jobs = _scheduler.list_jobs()

    return [
        JobResponse(
            id=job.id,
            pattern_id=job.pattern_id,
            trigger_type=job.trigger_type.value,
            trigger_config=job.trigger_config,
            enabled=job.enabled,
            last_run_at=job.last_run_at.isoformat() if job.last_run_at else None,
            next_run_at=job.next_run_at.isoformat() if job.next_run_at else None,
            run_count=job.run_count,
            error_count=job.error_count,
        )
        for job in jobs
    ]


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str):
    """Remove a scheduled job"""
    if not _scheduler:
        raise HTTPException(500, "Scheduler not initialized")

    success = await _scheduler.remove_schedule(job_id)
    if not success:
        raise HTTPException(404, f"Job not found: {job_id}")

    return {"message": f"Job {job_id} removed"}
