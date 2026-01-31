"""
Pipeline Routes - E2E Project Pipeline API

Thin orchestration layer:
- Creates project folders (git init + .auto-claude/ structure)
- Reads AutoGen Studio sessions and decomposes into tasks
- Reports task status by mapping AutoGen agent messages to pipeline stages

AutoGen Studio does ALL the AI work (Planner -> Coder -> QA -> Fixer).
This module just creates folders, reads status, and maps to Kanban columns.
"""

import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.utils.logger import get_logger

logger = get_logger("pipeline")

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# In-memory project store
_projects: Dict[str, Dict[str, Any]] = {}

# AutoGen Studio base URL
AUTOGEN_STUDIO_URL = "http://localhost:8081"
AUTOGEN_USER_ID = "guestuser@gmail.com"


# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────

class PipelineInitRequest(BaseModel):
    path: str               # e.g. "D:\\AutoClaude\\01_TEST"
    name: str               # e.g. "calculator"
    description: str = ""   # project description


class PipelinePlanRequest(BaseModel):
    project_id: str
    session_id: Optional[int] = None  # AutoGen Studio session ID (None = latest)


class PipelineInitResponse(BaseModel):
    project_id: str
    path: str
    name: str
    status: str
    created_at: str


class TaskInfo(BaseModel):
    id: str
    title: str
    description: str
    stage: str        # planning | coding | reviewing | testing | done | error
    agent: str        # which agent is/was working
    status: str       # pending | in_progress | completed | failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    project_id: str
    name: str
    path: str
    status: str       # init | planning | executing | completed | error
    current_stage: Optional[str] = None
    current_agent: Optional[str] = None
    tasks_total: int = 0
    tasks_completed: int = 0
    created_at: str
    updated_at: str


class PipelineTasksResponse(BaseModel):
    project_id: str
    tasks: List[TaskInfo]


# ──────────────────────────────────────────────
# Helper: AutoGen Studio API client
# ──────────────────────────────────────────────

async def _fetch_autogen_sessions(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent sessions from AutoGen Studio (8081)."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(
                f"{AUTOGEN_STUDIO_URL}/api/sessions/",
                params={"user_id": AUTOGEN_USER_ID},
            )
            if resp.status_code == 200:
                data = resp.json()
                sessions = data.get("data", [])
                return sessions[:limit]
    except Exception as e:
        logger.debug(f"Failed to fetch AutoGen sessions: {e}")
    return []


async def _fetch_autogen_runs(session_id: int) -> List[Dict[str, Any]]:
    """Fetch runs for a specific AutoGen Studio session."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(
                f"{AUTOGEN_STUDIO_URL}/api/sessions/{session_id}/runs/",
                params={"user_id": AUTOGEN_USER_ID},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("runs", [])
    except Exception as e:
        logger.debug(f"Failed to fetch AutoGen runs for session {session_id}: {e}")
    return []


def _extract_agent_messages(run: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract agent messages from an AutoGen run result."""
    messages = []
    result_msgs = (
        run.get("team_result", {})
        .get("task_result", {})
        .get("messages", [])
    )
    for msg in result_msgs:
        source = msg.get("source", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    content = item.get("text", "")
                    break
                elif isinstance(item, str):
                    content = item
                    break
        if isinstance(content, str) and source != "user":
            messages.append({
                "source": source,
                "content": content[:500] if len(content) > 500 else content,
            })
    return messages


def _map_agent_to_stage(agent_name: str) -> str:
    """Map AutoGen agent name to pipeline stage."""
    name_lower = agent_name.lower()
    if any(kw in name_lower for kw in ["planner", "planning", "plan", "architect"]):
        return "planning"
    elif any(kw in name_lower for kw in ["coder", "code", "implement", "developer", "writer"]):
        return "coding"
    elif any(kw in name_lower for kw in ["review", "qa", "test", "check", "critic"]):
        return "reviewing"
    elif any(kw in name_lower for kw in ["fix", "fixer", "debug", "patch"]):
        return "testing"
    else:
        return "coding"  # default


def _map_stage_to_kanban(stage: str) -> str:
    """Map pipeline stage to Kanban column status."""
    mapping = {
        "planning": "backlog",
        "coding": "in_progress",
        "reviewing": "ai_review",
        "testing": "ai_review",
        "done": "done",
        "error": "human_review",
    }
    return mapping.get(stage, "in_progress")


# ──────────────────────────────────────────────
# POST /pipeline/init - Create project folder
# ──────────────────────────────────────────────

@router.post("/init", response_model=PipelineInitResponse)
async def pipeline_init(req: PipelineInitRequest):
    """
    Create a project folder with git init and .auto-claude/ structure.

    This does NOT start any AI work - it just prepares the folder.
    AutoGen Studio handles all AI orchestration.
    """
    project_path = Path(req.path)
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()

    try:
        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)

        # Create .auto-claude/ structure
        auto_claude_dir = project_path / ".auto-claude"
        auto_claude_dir.mkdir(exist_ok=True)
        (auto_claude_dir / "specs").mkdir(exist_ok=True)
        (auto_claude_dir / "logs").mkdir(exist_ok=True)

        # Write project metadata
        metadata = {
            "id": project_id,
            "name": req.name,
            "description": req.description,
            "created_at": now,
            "status": "init",
            "autogen_session_id": None,
            "tasks": [],
        }
        (auto_claude_dir / "project.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Git init if not already a repo
        git_dir = project_path / ".git"
        if not git_dir.exists():
            subprocess.run(
                ["git", "init"],
                cwd=str(project_path),
                capture_output=True,
                timeout=10,
            )
            # Create .gitignore
            gitignore = project_path / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text(
                    ".auto-claude/logs/\n*.pyc\n__pycache__/\n.env\nnode_modules/\n",
                    encoding="utf-8",
                )
            logger.info(f"Git initialized at {project_path}")

        # Store in memory
        _projects[project_id] = {
            **metadata,
            "path": str(project_path),
        }

        logger.info(f"Project initialized: {project_id} at {project_path}")

        return PipelineInitResponse(
            project_id=project_id,
            path=str(project_path),
            name=req.name,
            status="init",
            created_at=now,
        )

    except Exception as e:
        logger.error(f"Failed to init project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# POST /pipeline/plan - Read AutoGen session → tasks
# ──────────────────────────────────────────────

@router.post("/plan", response_model=PipelineTasksResponse)
async def pipeline_plan(req: PipelinePlanRequest):
    """
    Read AutoGen Studio session results and decompose into pipeline tasks.

    This does NOT run any AI - it reads what AutoGen already produced
    and maps agent messages to pipeline stages (planning/coding/reviewing/etc).
    """
    project = _projects.get(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine which session to read
    session_id = req.session_id
    if session_id is None:
        # Use the latest session
        sessions = await _fetch_autogen_sessions(limit=1)
        if not sessions:
            raise HTTPException(
                status_code=404,
                detail="No AutoGen Studio sessions found. Run a session in AutoGen Studio first.",
            )
        session_id = sessions[0].get("id")

    # Fetch runs from the session
    runs = await _fetch_autogen_runs(session_id)
    if not runs:
        raise HTTPException(
            status_code=404,
            detail=f"No runs found for session {session_id}",
        )

    # Decompose runs into tasks based on agent messages
    tasks: List[TaskInfo] = []
    now = datetime.now().isoformat()

    for run_idx, run in enumerate(runs):
        run_status = (run.get("status") or "").upper()
        agent_messages = _extract_agent_messages(run)

        if not agent_messages:
            # Single task from the run itself
            task_content = ""
            task_msgs = run.get("task", {}).get("content", [])
            for msg in task_msgs:
                if msg.get("source") == "user":
                    task_content = msg.get("content", "AutoGen Task")
                    break

            stage = "done" if run_status == "COMPLETE" else "coding"
            status = "completed" if run_status == "COMPLETE" else "in_progress"
            if run_status in ("ERROR", "FAILED"):
                stage = "error"
                status = "failed"

            tasks.append(TaskInfo(
                id=f"task_{req.project_id}_{run_idx}",
                title=task_content[:100] if task_content else f"Run #{run_idx + 1}",
                description=task_content,
                stage=stage,
                agent="autogen",
                status=status,
                started_at=run.get("created_at", now),
                completed_at=now if status == "completed" else None,
            ))
        else:
            # Create a task per distinct agent phase
            seen_stages: Dict[str, int] = {}
            for msg in agent_messages:
                agent = msg["source"]
                stage = _map_agent_to_stage(agent)

                if stage not in seen_stages:
                    seen_stages[stage] = len(tasks)
                    task_status = "completed" if run_status == "COMPLETE" else "in_progress"
                    if run_status in ("ERROR", "FAILED"):
                        task_status = "failed"

                    tasks.append(TaskInfo(
                        id=f"task_{req.project_id}_{run_idx}_{stage}",
                        title=f"[{stage.capitalize()}] {agent}",
                        description=msg["content"][:200],
                        stage=stage,
                        agent=agent,
                        status=task_status,
                        started_at=run.get("created_at", now),
                        completed_at=now if task_status == "completed" else None,
                    ))

    # Update project state
    project["status"] = "planned"
    project["autogen_session_id"] = session_id
    project["tasks"] = [t.dict() for t in tasks]
    project["updated_at"] = now

    # Persist to project.json
    _persist_project(project)

    return PipelineTasksResponse(
        project_id=req.project_id,
        tasks=tasks,
    )


# ──────────────────────────────────────────────
# GET /pipeline/status/{project_id}
# ──────────────────────────────────────────────

@router.get("/status/{project_id}", response_model=PipelineStatusResponse)
async def pipeline_status(project_id: str):
    """
    Get pipeline status. Reads current AutoGen run state to determine
    which stage is active and which agent is currently working.
    """
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    now = datetime.now().isoformat()
    tasks = project.get("tasks", [])
    completed = sum(1 for t in tasks if t.get("status") == "completed")

    # Determine current stage from active AutoGen session
    current_stage = None
    current_agent = None
    session_id = project.get("autogen_session_id")

    if session_id:
        runs = await _fetch_autogen_runs(session_id)
        for run in runs:
            run_status = (run.get("status") or "").upper()
            if run_status in ("RUNNING", "IN_PROGRESS", "ACTIVE"):
                # Find the latest agent message to determine current stage
                messages = _extract_agent_messages(run)
                if messages:
                    last_agent = messages[-1]["source"]
                    current_agent = last_agent
                    current_stage = _map_agent_to_stage(last_agent)
                break

    # Determine overall status
    status = project.get("status", "init")
    if current_stage:
        status = "executing"
    elif tasks and all(t.get("status") == "completed" for t in tasks):
        status = "completed"

    return PipelineStatusResponse(
        project_id=project_id,
        name=project.get("name", ""),
        path=project.get("path", ""),
        status=status,
        current_stage=current_stage,
        current_agent=current_agent,
        tasks_total=len(tasks),
        tasks_completed=completed,
        created_at=project.get("created_at", now),
        updated_at=project.get("updated_at", now),
    )


# ──────────────────────────────────────────────
# GET /pipeline/tasks/{project_id}
# ──────────────────────────────────────────────

@router.get("/tasks/{project_id}", response_model=PipelineTasksResponse)
async def pipeline_tasks(project_id: str):
    """
    Get task list with current status from AutoGen Studio.

    Re-reads AutoGen session to get live status of each task/agent.
    """
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    session_id = project.get("autogen_session_id")
    stored_tasks = project.get("tasks", [])

    if not session_id or not stored_tasks:
        return PipelineTasksResponse(
            project_id=project_id,
            tasks=[TaskInfo(**t) for t in stored_tasks],
        )

    # Re-read AutoGen runs for live status
    runs = await _fetch_autogen_runs(session_id)

    # Update task statuses based on current run state
    updated_tasks: List[TaskInfo] = []
    now = datetime.now().isoformat()

    for task_data in stored_tasks:
        task = TaskInfo(**task_data)

        # Find corresponding run and update status
        for run in runs:
            run_status = (run.get("status") or "").upper()

            if run_status == "COMPLETE":
                task.status = "completed"
                task.completed_at = now
            elif run_status in ("RUNNING", "IN_PROGRESS", "ACTIVE"):
                # Check if this task's agent has spoken yet
                messages = _extract_agent_messages(run)
                agent_names = [m["source"] for m in messages]

                if task.agent in agent_names:
                    # Agent has produced output - task is at least in_progress
                    last_agent = agent_names[-1] if agent_names else ""
                    if last_agent == task.agent:
                        task.status = "in_progress"  # Currently active
                    else:
                        task.status = "completed"  # Another agent took over
                else:
                    task.status = "pending"  # Not started yet
            elif run_status in ("ERROR", "FAILED"):
                task.status = "failed"
                task.stage = "error"

        updated_tasks.append(task)

    return PipelineTasksResponse(
        project_id=project_id,
        tasks=updated_tasks,
    )


# ──────────────────────────────────────────────
# Helper: Persist project to .auto-claude/project.json
# ──────────────────────────────────────────────

def _persist_project(project: Dict[str, Any]):
    """Write project state to .auto-claude/project.json."""
    try:
        project_path = Path(project.get("path", ""))
        meta_file = project_path / ".auto-claude" / "project.json"
        if meta_file.parent.exists():
            meta_file.write_text(
                json.dumps(project, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    except Exception as e:
        logger.debug(f"Failed to persist project: {e}")
