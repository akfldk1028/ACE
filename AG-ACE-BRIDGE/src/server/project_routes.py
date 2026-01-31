"""
Project REST API Routes

Provides HTTP endpoints for project design, execution, and monitoring.

Endpoints:
    POST /projects/design - Design a new project from natural language
    GET /projects/ - List all projects
    GET /projects/{project_id} - Get project details
    POST /projects/{project_id}/execute - Execute a project
    GET /projects/{project_id}/status - Get execution status
    POST /projects/{project_id}/cancel - Cancel execution
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.designer import ProjectDesigner, ProjectExecutor, PatternMatcher, ProjectSpec
from src.registry.pattern_registry import PatternRegistry
from src.scheduler.trigger import ScheduleTrigger
from src.utils.logger import Loggers

router = APIRouter(prefix="/projects", tags=["projects"])
logger = Loggers.dashboard()

# Global instances (set by dashboard on startup)
_designer: Optional[ProjectDesigner] = None
_executor: Optional[ProjectExecutor] = None
_planner_adapter: Optional[Any] = None
_a2a_adapters: Optional[Any] = None
_projects: Dict[str, ProjectSpec] = {}
_results: Dict[str, Any] = {}


class DesignRequest(BaseModel):
    """Request to design a new project"""
    request: str = Field(..., description="Natural language project request")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional design options (priority, agents, etc.)"
    )


class DesignResponse(BaseModel):
    """Response from project design"""
    project_id: str
    name: str
    phases: List[Dict[str, Any]]
    estimated_tasks: int
    status: str


class ExecuteRequest(BaseModel):
    """Request to execute a project"""
    start_phase: Optional[str] = Field(
        default=None,
        description="Phase ID to start from (for resume)"
    )


class ExecuteResponse(BaseModel):
    """Response from project execution"""
    project_id: str
    status: str
    message: str


class ProjectListResponse(BaseModel):
    """List of projects"""
    projects: List[Dict[str, Any]]
    total: int


class ProjectStatusResponse(BaseModel):
    """Project execution status"""
    project_id: str
    status: str
    phase_results: Optional[Dict[str, Any]]
    overall_success_rate: Optional[float]


def initialize(
    registry: PatternRegistry,
    scheduler: Optional[ScheduleTrigger] = None,
    planner_adapter: Optional[Any] = None,
    orchestrator: Optional[Any] = None,
    a2a_adapters: Optional[Any] = None,
):
    """Initialize project routes with required dependencies"""
    global _designer, _executor, _planner_adapter, _a2a_adapters

    _planner_adapter = planner_adapter
    _a2a_adapters = a2a_adapters

    matcher = PatternMatcher(registry)
    _designer = ProjectDesigner(planner_adapter)
    _executor = ProjectExecutor(
        registry=registry,
        scheduler=scheduler,
        orchestrator=orchestrator,
        matcher=matcher,
        adapters=_build_adapter_map(planner_adapter, a2a_adapters),
    )

    logger.info(
        "project_routes_initialized",
        planner_available=planner_adapter is not None,
        a2a_available=a2a_adapters is not None,
    )


def _build_adapter_map(planner_adapter, a2a_adapters) -> Dict[str, Any]:
    """Build agent_type -> adapter mapping"""
    adapters = {}

    # Auto-Claude adapters
    if planner_adapter:
        adapters["AUTO_CLAUDE_PLANNER"] = planner_adapter

    # A2A adapters from manager
    if a2a_adapters:
        try:
            for agent_type in a2a_adapters.available_agents():
                adapters[agent_type.value] = a2a_adapters.get_adapter(agent_type)
        except Exception:
            pass

    return adapters


@router.post("/design", response_model=DesignResponse)
async def design_project(request: DesignRequest):
    """
    Design a new project from natural language request.

    The AI-powered designer will:
    1. Analyze the request
    2. Break it down into phases
    3. Define tasks for each phase
    4. Assign appropriate agents

    Example:
        POST /projects/design
        {
            "request": "Create a REST API for user management",
            "options": {"priority": "high"}
        }
    """
    if not _designer:
        raise HTTPException(
            status_code=503,
            detail="Project designer not initialized"
        )

    try:
        project = await _designer.design(
            request=request.request,
            options=request.options,
        )

        # Store project
        _projects[project.id] = project

        # Count tasks
        task_count = sum(
            len(phase.get("tasks", []))
            for phase in project.phases
        )

        logger.info(
            "project_designed",
            project_id=project.id,
            name=project.name,
            phases=len(project.phases),
            tasks=task_count,
        )

        return DesignResponse(
            project_id=project.id,
            name=project.name,
            phases=[
                {
                    "id": p.get("id", f"phase_{i}"),
                    "name": p.get("name", "Unnamed"),
                    "tasks": len(p.get("tasks", [])),
                }
                for i, p in enumerate(project.phases)
            ],
            estimated_tasks=task_count,
            status=project.status.value,
        )

    except Exception as e:
        logger.error(f"Project design failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ProjectListResponse)
async def list_projects():
    """
    List all designed projects.

    Returns projects with basic info (id, name, status, task count).
    """
    projects_list = []

    for project in _projects.values():
        task_count = sum(
            len(phase.get("tasks", []))
            for phase in project.phases
        )

        projects_list.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "phases": len(project.phases),
            "tasks": task_count,
            "created_at": project.created_at.isoformat() if hasattr(project, 'created_at') else None,
        })

    return ProjectListResponse(
        projects=projects_list,
        total=len(projects_list),
    )


@router.get("/{project_id}")
async def get_project(project_id: str):
    """
    Get detailed project information.

    Returns full project spec including all phases and tasks.
    """
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "goals": project.goals,
        "status": project.status.value,
        "phases": project.phases,
        "metadata": project.metadata,
    }


@router.post("/{project_id}/execute", response_model=ExecuteResponse)
async def execute_project(
    project_id: str,
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
):
    """
    Execute a designed project.

    Optionally specify a start_phase to resume from a specific phase.
    Execution runs in the background.
    """
    if not _executor:
        raise HTTPException(
            status_code=503,
            detail="Project executor not initialized"
        )

    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if already running
    status = await _executor.get_execution_status()
    if status and status.get("project_id") == project_id:
        raise HTTPException(
            status_code=409,
            detail="Project is already running"
        )

    # Execute in background
    async def run_execution():
        try:
            result = await _executor.execute(
                project=project,
                start_phase=request.start_phase,
            )
            _results[project_id] = result
        except Exception as e:
            logger.error(f"Project execution failed: {e}")
            _results[project_id] = {"error": str(e)}

    background_tasks.add_task(run_execution)

    logger.info(
        "project_execution_started",
        project_id=project_id,
        start_phase=request.start_phase,
    )

    return ExecuteResponse(
        project_id=project_id,
        status="started",
        message="Project execution started in background",
    )


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
async def get_execution_status(project_id: str):
    """
    Get project execution status.

    Returns current status, phase results, and success rate.
    """
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if currently running
    if _executor:
        status = await _executor.get_execution_status()
        if status and status.get("project_id") == project_id:
            return ProjectStatusResponse(
                project_id=project_id,
                status="running",
                phase_results=None,
                overall_success_rate=None,
            )

    # Check completed results
    result = _results.get(project_id)
    if result:
        if isinstance(result, dict) and "error" in result:
            return ProjectStatusResponse(
                project_id=project_id,
                status="failed",
                phase_results={"error": result["error"]},
                overall_success_rate=0.0,
            )

        # Convert ProjectResult to dict
        phase_results = {}
        if hasattr(result, 'phase_results'):
            for phase_id, phase_result in result.phase_results.items():
                phase_results[phase_id] = {
                    "status": phase_result.status.value,
                    "success_rate": phase_result.success_rate,
                    "task_count": len(phase_result.task_results),
                }

        return ProjectStatusResponse(
            project_id=project_id,
            status=result.status.value if hasattr(result, 'status') else "completed",
            phase_results=phase_results,
            overall_success_rate=result.overall_success_rate if hasattr(result, 'overall_success_rate') else None,
        )

    return ProjectStatusResponse(
        project_id=project_id,
        status=project.status.value,
        phase_results=None,
        overall_success_rate=None,
    )


@router.post("/{project_id}/cancel")
async def cancel_execution(project_id: str):
    """
    Cancel project execution.

    Best-effort cancellation - running tasks may complete.
    """
    if not _executor:
        raise HTTPException(
            status_code=503,
            detail="Project executor not initialized"
        )

    cancelled = await _executor.cancel_execution()

    if cancelled:
        logger.info("project_execution_cancelled", project_id=project_id)
        return {"status": "cancelled", "project_id": project_id}
    else:
        return {"status": "not_running", "project_id": project_id}


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project.

    Cannot delete running projects.
    """
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if running
    if _executor:
        status = await _executor.get_execution_status()
        if status and status.get("project_id") == project_id:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete running project"
            )

    del _projects[project_id]
    _results.pop(project_id, None)

    logger.info("project_deleted", project_id=project_id)

    return {"status": "deleted", "project_id": project_id}


@router.get("/{project_id}/matches")
async def get_pattern_matches(project_id: str):
    """
    Get pattern matches for a project's tasks.

    Shows which patterns were matched to each task,
    and which tasks need new patterns.
    """
    result = _results.get(project_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="No execution results found"
        )

    if hasattr(result, 'pattern_matches'):
        matches = {}
        for task_id, match in result.pattern_matches.items():
            matches[task_id] = {
                "pattern_id": match.pattern_id,
                "pattern_name": match.pattern_name,
                "confidence": match.confidence,
                "reason": match.reason,
                "create_new": match.create_new,
            }

        return {
            "project_id": project_id,
            "matches": matches,
            "patterns_created": result.patterns_created if hasattr(result, 'patterns_created') else [],
        }

    raise HTTPException(
        status_code=404,
        detail="Pattern match data not available"
    )
