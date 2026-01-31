"""
Workflow REST API Routes (Bridge Module)

Provides HTTP endpoints for Auto-Claude workflow execution via AG-ACE-BRIDGE.

Endpoints:
    POST /workflow/execute - Execute full pipeline (spec_runner.py + run.py)
    GET /workflow/status/{spec_id} - Get spec execution status
    GET /workflow/specs - List all specs
    POST /workflow/review/{spec_id} - Review a spec
    POST /workflow/merge/{spec_id} - Merge a completed spec
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio

from src.bridge import WorkflowExecutor
from src.utils.logger import Loggers

router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = Loggers.dashboard()

# Global executor instance
_executor: Optional[WorkflowExecutor] = None
_active_executions: Dict[str, Dict[str, Any]] = {}


class WorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    task: str = Field(..., description="Task description (e.g., 'Create a calculator app')")
    complexity: Literal["simple", "standard", "complex"] = Field(
        default="standard",
        description="Task complexity level"
    )
    auto_merge: bool = Field(
        default=False,
        description="Whether to auto-merge after successful build"
    )
    project_path: Optional[str] = Field(
        default=None,
        description="Target project path (defaults to Auto-Claude itself)"
    )


class WorkflowResponse(BaseModel):
    """Response from workflow execution"""
    success: bool
    spec_id: Optional[str] = None
    status: str
    message: str
    phases: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class SpecStatusResponse(BaseModel):
    """Status of a spec"""
    spec_id: str
    status: str
    details: Optional[Dict[str, Any]] = None


class SpecListResponse(BaseModel):
    """List of specs"""
    specs: List[Dict[str, Any]]
    total: int


def initialize(auto_claude_path: str = "D:/Data/25_ACE/Auto-Claude"):
    """Initialize workflow routes with executor"""
    global _executor
    _executor = WorkflowExecutor(auto_claude_path=auto_claude_path)
    logger.info("workflow_routes_initialized", auto_claude_path=auto_claude_path)


def get_executor() -> WorkflowExecutor:
    """Get or create executor instance"""
    global _executor
    if not _executor:
        _executor = WorkflowExecutor()
    return _executor


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
):
    """
    Execute full Auto-Claude pipeline.

    This calls:
    1. spec_runner.py - AI-powered spec creation
    2. run.py - Planner -> Coder -> QA pipeline
    3. Git Worktree - Safe isolated build

    The execution runs in the background. Use /workflow/status/{spec_id} to check progress.

    Example:
        POST /workflow/execute
        {
            "task": "Create a calculator app with basic operations",
            "complexity": "standard",
            "auto_merge": false
        }
    """
    executor = get_executor()

    # Generate a temporary execution ID
    exec_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Store execution state
    _active_executions[exec_id] = {
        "task": request.task,
        "complexity": request.complexity,
        "status": "starting",
        "started_at": datetime.now().isoformat(),
        "spec_id": None,
        "result": None,
    }

    # Define background execution
    async def run_workflow():
        try:
            _active_executions[exec_id]["status"] = "running"

            # Run the full pipeline
            result = await executor.execute_full_pipeline(
                task_description=request.task,
                complexity=request.complexity,
                auto_merge=request.auto_merge,
            )

            _active_executions[exec_id]["result"] = result
            _active_executions[exec_id]["spec_id"] = result.get("spec_id")

            if result.get("success"):
                _active_executions[exec_id]["status"] = "completed"
            else:
                _active_executions[exec_id]["status"] = "failed"

            logger.info(
                "workflow_completed",
                exec_id=exec_id,
                success=result.get("success"),
                spec_id=result.get("spec_id"),
            )

        except Exception as e:
            _active_executions[exec_id]["status"] = "error"
            _active_executions[exec_id]["error"] = str(e)
            logger.error(f"Workflow execution failed: {e}")

    # Start in background
    background_tasks.add_task(run_workflow)

    logger.info(
        "workflow_started",
        exec_id=exec_id,
        task=request.task[:50],
        complexity=request.complexity,
    )

    return WorkflowResponse(
        success=True,
        spec_id=None,  # Will be available after spec creation
        status="started",
        message=f"Workflow started. Execution ID: {exec_id}. Use GET /workflow/executions/{exec_id} to track progress.",
        phases=None,
    )


@router.post("/execute-sync", response_model=WorkflowResponse)
async def execute_workflow_sync(request: WorkflowRequest):
    """
    Execute full Auto-Claude pipeline synchronously.

    WARNING: This can take a long time (minutes to hours).
    Use /workflow/execute for background execution instead.

    Example:
        POST /workflow/execute-sync
        {
            "task": "Fix a simple typo",
            "complexity": "simple"
        }
    """
    executor = get_executor()

    try:
        logger.info(
            "workflow_sync_started",
            task=request.task[:50],
            complexity=request.complexity,
        )

        # Run synchronously (blocking)
        result = executor.execute_full_pipeline_sync(
            task_description=request.task,
            complexity=request.complexity,
            auto_merge=request.auto_merge,
        )

        logger.info(
            "workflow_sync_completed",
            success=result.get("success"),
            spec_id=result.get("spec_id"),
        )

        return WorkflowResponse(
            success=result.get("success", False),
            spec_id=result.get("spec_id"),
            status="completed" if result.get("success") else "failed",
            message="Workflow completed" if result.get("success") else result.get("error", "Unknown error"),
            phases=result.get("phases"),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Workflow sync execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{exec_id}")
async def get_execution_status(exec_id: str):
    """
    Get status of a background workflow execution.

    Returns current status, spec_id (if created), and result (if completed).
    """
    execution = _active_executions.get(exec_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution


@router.get("/executions")
async def list_executions():
    """
    List all workflow executions (active and completed).
    """
    return {
        "executions": list(_active_executions.values()),
        "total": len(_active_executions),
    }


@router.get("/status/{spec_id}", response_model=SpecStatusResponse)
async def get_spec_status(spec_id: str):
    """
    Get status of a specific spec.

    Returns worktree status, QA results, etc.
    """
    executor = get_executor()

    try:
        status = executor.get_status(spec_id)
        return SpecStatusResponse(
            spec_id=spec_id,
            status=status.get("status", "unknown"),
            details=status,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/specs", response_model=SpecListResponse)
async def list_specs():
    """
    List all available specs.

    Returns specs from .auto-claude/specs/ directory.
    """
    executor = get_executor()

    try:
        specs = executor.list_specs()
        return SpecListResponse(
            specs=specs,
            total=len(specs),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/{spec_id}")
async def review_spec(spec_id: str):
    """
    Review a spec (run.py --review).

    Shows diff and changes in the worktree.
    """
    executor = get_executor()

    try:
        result = executor.review_spec(spec_id)
        return {
            "spec_id": spec_id,
            "success": result.get("success", False),
            "output": result.get("output", ""),
            "error": result.get("error"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge/{spec_id}")
async def merge_spec(spec_id: str):
    """
    Merge a completed spec (run.py --merge).

    Merges the worktree branch into main.
    """
    executor = get_executor()

    try:
        result = executor._merge_spec(spec_id)
        return {
            "spec_id": spec_id,
            "success": result.get("success", False),
            "error": result.get("error"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check for workflow service.
    """
    executor = get_executor()

    return {
        "status": "healthy",
        "executor": "initialized" if executor else "not_initialized",
        "active_executions": len(_active_executions),
        "auto_claude_path": str(executor.auto_claude_path) if executor else None,
    }
