"""
Project specification models for AG-ACE-BRIDGE

Defines the schema for project submissions that trigger
24/7 autonomous execution.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class ProjectPhase(str, Enum):
    """Project lifecycle phases"""
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"


class ProjectStatus(str, Enum):
    """Project execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectRequirements(BaseModel):
    """Project functional and non-functional requirements"""
    functional: List[str] = Field(default_factory=list, description="Functional requirements")
    non_functional: List[str] = Field(default_factory=list, description="Non-functional requirements")
    constraints: List[str] = Field(default_factory=list, description="Technical constraints")
    dependencies: List[str] = Field(default_factory=list, description="External dependencies")


class AgentConfig(BaseModel):
    """Agent configuration for project"""
    use_auto_claude: bool = Field(default=True, description="Use Auto-Claude agents")
    use_ag_autogen: bool = Field(default=True, description="Use AG Autogen agents")
    use_ag_law: bool = Field(default=False, description="Use AG Law Domain agents")
    preferred_agents: List[str] = Field(default_factory=list, description="Preferred agent types")
    excluded_agents: List[str] = Field(default_factory=list, description="Excluded agent types")


class PipelineConfig(BaseModel):
    """Pipeline configuration"""
    pattern: str = Field(default="auto", description="Pipeline pattern: auto, sequential, parallel, critic_loop")
    max_iterations: int = Field(default=5, description="Max critic loop iterations")
    parallel_limit: int = Field(default=3, description="Max parallel agents")
    timeout_minutes: int = Field(default=60, description="Task timeout in minutes")


class ProjectSpec(BaseModel):
    """
    Project specification for 24/7 AI Factory.

    Drop a YAML/JSON file in projects/ folder to trigger execution.

    Example:
        spec = ProjectSpec(
            name="My API Server",
            description="Build a REST API with FastAPI",
            goals=["Create CRUD endpoints", "Add authentication"],
        )
        save_project_spec(spec, "projects/queue/my-api.yaml")
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique project ID")
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")

    # Goals & Requirements
    goals: List[str] = Field(..., description="Project goals/objectives")
    requirements: ProjectRequirements = Field(default_factory=ProjectRequirements)

    # Technical Details
    tech_stack: List[str] = Field(default_factory=list, description="Technology stack")
    output_path: str = Field(default="./output", description="Output directory path")

    # Agent Configuration
    agents: AgentConfig = Field(default_factory=AgentConfig)

    # Pipeline Configuration
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)

    # Execution Control
    priority: str = Field(default="medium", description="Priority: high, medium, low")
    auto_start: bool = Field(default=True, description="Start immediately when queued")

    # State (managed by system)
    status: ProjectStatus = Field(default=ProjectStatus.PENDING)
    phase: ProjectPhase = Field(default=ProjectPhase.PLANNING)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress
    progress_percent: int = Field(default=0, ge=0, le=100)
    current_task: Optional[str] = None
    completed_tasks: List[str] = Field(default_factory=list)

    # Results
    artifacts: List[str] = Field(default_factory=list, description="Generated artifact paths")
    logs: List[str] = Field(default_factory=list, description="Log messages")
    errors: List[str] = Field(default_factory=list, description="Error messages")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


def load_project_spec(file_path: Path | str) -> ProjectSpec:
    """
    Load project spec from YAML or JSON file.

    Args:
        file_path: Path to spec file (.yaml, .yml, or .json)

    Returns:
        ProjectSpec instance

    Raises:
        ValueError: If file format not supported
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Spec file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    if file_path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(content)
    elif file_path.suffix == ".json":
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    return ProjectSpec(**data)


def save_project_spec(spec: ProjectSpec, file_path: Path | str) -> None:
    """
    Save project spec to YAML or JSON file.

    Args:
        spec: ProjectSpec instance
        file_path: Output file path
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict with proper datetime handling
    data = spec.model_dump(mode="json")

    if file_path.suffix in (".yaml", ".yml"):
        content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        content = json.dumps(data, indent=2, ensure_ascii=False)

    file_path.write_text(content, encoding="utf-8")


# Example spec for documentation
EXAMPLE_SPEC = """
# Project Specification Example
# Drop this file in projects/queue/ to trigger 24/7 execution

name: "Example REST API"
description: "Build a REST API server with FastAPI and PostgreSQL"

# Project Goals (what to achieve)
goals:
  - "Create user authentication with JWT"
  - "Implement CRUD endpoints for resources"
  - "Add database models and migrations"
  - "Write unit and integration tests"
  - "Generate API documentation"

# Requirements
requirements:
  functional:
    - "User registration and login"
    - "Token-based authentication"
    - "Resource CRUD operations"
    - "Input validation"
  non_functional:
    - "Response time < 200ms"
    - "Test coverage > 80%"
  constraints:
    - "Python 3.11+"
    - "PostgreSQL 14+"
  dependencies:
    - "FastAPI"
    - "SQLAlchemy"
    - "Pydantic"
    - "pytest"

# Technology Stack
tech_stack:
  - "Python 3.11"
  - "FastAPI"
  - "SQLAlchemy 2.0"
  - "PostgreSQL"
  - "Docker"

# Output Directory
output_path: "./output/example-api"

# Agent Configuration
agents:
  use_auto_claude: true
  use_ag_autogen: true
  use_ag_law: false
  preferred_agents:
    - "auto_claude_coder"
    - "auto_claude_qa_reviewer"

# Pipeline Configuration
pipeline:
  pattern: "auto"  # auto, sequential, parallel, critic_loop
  max_iterations: 5
  parallel_limit: 3
  timeout_minutes: 60

# Execution
priority: "medium"  # high, medium, low
auto_start: true
"""
