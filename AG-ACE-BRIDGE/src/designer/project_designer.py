"""
Project Designer - AI-Powered Project Design

Uses Auto-Claude Planner to design entire projects from natural language requests.
Decomposes projects into phases, tasks, and patterns for automated execution.

Usage:
    designer = ProjectDesigner(planner_adapter)

    # Design a project from natural language
    project = await designer.design(
        request="Create a Python calculator with unit tests",
        options={"language": "python", "include_tests": True}
    )

    # Project contains phases, tasks, and recommended patterns
    for phase in project.phases:
        print(f"Phase: {phase.name}")
        for task in phase.tasks:
            print(f"  - {task.description}")
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

from src.utils.logger import Loggers


class ProjectStatus(str, Enum):
    """Project lifecycle status"""
    DRAFT = "draft"              # Designed but not started
    PLANNING = "planning"        # Being planned by AI
    READY = "ready"              # Ready to execute
    EXECUTING = "executing"      # Currently running
    PAUSED = "paused"            # Paused
    COMPLETED = "completed"      # Successfully finished
    FAILED = "failed"            # Failed with errors
    CANCELLED = "cancelled"      # Cancelled by user


class PhaseType(str, Enum):
    """Standard project phases"""
    ANALYSIS = "analysis"        # Requirements analysis
    DESIGN = "design"            # Architecture design
    IMPLEMENTATION = "implementation"  # Code writing
    TESTING = "testing"          # Testing & QA
    DEPLOYMENT = "deployment"    # Deployment
    DOCUMENTATION = "documentation"  # Documentation


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ProjectTask:
    """A single task within a project phase"""
    id: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    agent_type: Optional[str] = None  # Recommended agent
    pattern_id: Optional[str] = None  # Matched pattern
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    estimated_minutes: int = 10
    status: str = "pending"
    output: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority.value,
            "agent_type": self.agent_type,
            "pattern_id": self.pattern_id,
            "dependencies": self.dependencies,
            "estimated_minutes": self.estimated_minutes,
            "status": self.status,
            "output": self.output,
        }


@dataclass
class ProjectPhase:
    """A phase in the project lifecycle"""
    id: str
    name: str
    phase_type: PhaseType
    description: str
    tasks: List[ProjectTask] = field(default_factory=list)
    order: int = 0
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "phase_type": self.phase_type.value,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "order": self.order,
            "status": self.status,
        }


class ProjectSpec(BaseModel):
    """Complete project specification"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    request: str  # Original user request
    status: ProjectStatus = ProjectStatus.DRAFT
    phases: List[Dict[str, Any]] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class ProjectDesigner:
    """
    AI-Powered Project Designer.

    Uses Auto-Claude Planner to design projects from natural language requests.
    Produces structured ProjectSpec with phases, tasks, and pattern recommendations.

    Design Flow:
    1. Receive natural language request
    2. Send to Planner for analysis
    3. Parse response into structured spec
    4. Identify required patterns
    5. Return complete ProjectSpec
    """

    # Default project template
    DEFAULT_PHASES = [
        (PhaseType.ANALYSIS, "Requirements Analysis", "Analyze and clarify project requirements"),
        (PhaseType.DESIGN, "Architecture Design", "Design system architecture and components"),
        (PhaseType.IMPLEMENTATION, "Implementation", "Write code and implement features"),
        (PhaseType.TESTING, "Testing & QA", "Test code and ensure quality"),
        (PhaseType.DOCUMENTATION, "Documentation", "Create project documentation"),
    ]

    # Agent mapping for different task types
    TASK_AGENT_MAPPING = {
        "plan": "AUTO_CLAUDE_PLANNER",
        "design": "AUTO_CLAUDE_PLANNER",
        "analyze": "AUTO_CLAUDE_PLANNER",
        "code": "AUTO_CLAUDE_CODER",
        "implement": "AUTO_CLAUDE_CODER",
        "write": "AUTO_CLAUDE_CODER",
        "review": "AUTO_CLAUDE_QA_REVIEWER",
        "check": "AUTO_CLAUDE_QA_REVIEWER",
        "test": "AUTO_CLAUDE_QA_FIXER",
        "fix": "AUTO_CLAUDE_QA_FIXER",
        "debug": "AUTO_CLAUDE_QA_FIXER",
        "research": "AG_RESEARCH",
        "calculate": "AG_A2A_CALCULATOR",
    }

    def __init__(
        self,
        planner_adapter=None,
        shared_memory_client=None,
    ):
        """
        Initialize ProjectDesigner.

        Args:
            planner_adapter: Auto-Claude Planner adapter for AI design
            shared_memory_client: SharedMemory client for persistence
        """
        self.planner = planner_adapter
        self.shared_memory = shared_memory_client
        self.logger = Loggers.orchestrator()

    async def design(
        self,
        request: str,
        options: Dict[str, Any] = None,
    ) -> ProjectSpec:
        """
        Design a project from natural language request.

        Args:
            request: Natural language project request
            options: Additional options (language, framework, etc.)

        Returns:
            Complete ProjectSpec ready for execution
        """
        options = options or {}

        self.logger.info(
            "project_design_started",
            request=request[:100],
        )

        # Generate project name from request
        project_name = self._generate_project_name(request)

        # Create base project spec
        project = ProjectSpec(
            name=project_name,
            description=request,
            request=request,
            status=ProjectStatus.PLANNING,
            config=options,
        )

        # If we have a planner, use AI to design
        if self.planner:
            project = await self._ai_design(project, request, options)
        else:
            # Fallback to template-based design
            project = self._template_design(project, request, options)

        project.status = ProjectStatus.READY
        project.updated_at = datetime.now()

        # Save to SharedMemory
        if self.shared_memory:
            await self._save_to_shared_memory(project)

        self.logger.info(
            "project_design_completed",
            project_id=project.id,
            name=project.name,
            phase_count=len(project.phases),
            task_count=sum(len(p.get("tasks", [])) for p in project.phases),
        )

        return project

    def _generate_project_name(self, request: str) -> str:
        """Generate project name from request"""
        # Extract key words
        words = request.lower().split()

        # Common project types
        project_types = ["app", "api", "website", "tool", "system", "service"]

        name_parts = []
        for word in words:
            # Skip common words
            if word in ["a", "an", "the", "create", "build", "make", "with"]:
                continue
            # Keep meaningful words
            if len(word) > 2:
                name_parts.append(word.capitalize())
            if len(name_parts) >= 3:
                break

        return "_".join(name_parts) if name_parts else "Project"

    async def _ai_design(
        self,
        project: ProjectSpec,
        request: str,
        options: Dict[str, Any],
    ) -> ProjectSpec:
        """Use AI Planner to design project"""
        from src.utils.models import Task, TaskType

        # Create planning task
        plan_task = Task(
            id=str(uuid.uuid4()),
            type=TaskType.PLAN,
            description=f"""Design a complete project based on this request:

REQUEST: {request}

OPTIONS: {json.dumps(options, indent=2)}

Please provide:
1. Project phases (analysis, design, implementation, testing, documentation)
2. Tasks for each phase with descriptions
3. Dependencies between tasks
4. Recommended agents for each task
5. Estimated time for each task

Format your response as JSON with this structure:
{{
    "phases": [
        {{
            "name": "Phase Name",
            "type": "analysis|design|implementation|testing|documentation",
            "description": "Phase description",
            "tasks": [
                {{
                    "description": "Task description",
                    "agent": "AUTO_CLAUDE_PLANNER|AUTO_CLAUDE_CODER|...",
                    "dependencies": [],
                    "estimated_minutes": 10
                }}
            ]
        }}
    ]
}}
""",
            priority="high",
        )

        try:
            # Execute planning
            result = await self.planner.execute(plan_task, {})

            if result.success and result.output:
                # Parse AI response
                project = self._parse_ai_response(project, result.output)
            else:
                # Fallback to template
                project = self._template_design(project, request, options)

        except Exception as e:
            self.logger.warning(
                "ai_design_failed",
                error=str(e),
            )
            project = self._template_design(project, request, options)

        return project

    def _parse_ai_response(
        self,
        project: ProjectSpec,
        response: Dict[str, Any],
    ) -> ProjectSpec:
        """Parse AI planner response into ProjectSpec"""
        try:
            # Try to extract JSON from response
            if isinstance(response, dict):
                data = response
            elif isinstance(response, str):
                # Try to find JSON in response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in response")
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")

            phases = []
            for i, phase_data in enumerate(data.get("phases", [])):
                phase_id = str(uuid.uuid4())

                # Determine phase type
                phase_type_str = phase_data.get("type", "implementation").lower()
                try:
                    phase_type = PhaseType(phase_type_str)
                except ValueError:
                    phase_type = PhaseType.IMPLEMENTATION

                # Create tasks
                tasks = []
                for j, task_data in enumerate(phase_data.get("tasks", [])):
                    task = ProjectTask(
                        id=f"{phase_id}_task_{j}",
                        description=task_data.get("description", ""),
                        priority=TaskPriority.MEDIUM,
                        agent_type=task_data.get("agent"),
                        dependencies=task_data.get("dependencies", []),
                        estimated_minutes=task_data.get("estimated_minutes", 10),
                    )
                    tasks.append(task)

                phase = ProjectPhase(
                    id=phase_id,
                    name=phase_data.get("name", f"Phase {i+1}"),
                    phase_type=phase_type,
                    description=phase_data.get("description", ""),
                    tasks=tasks,
                    order=i,
                )
                phases.append(phase.to_dict())

            project.phases = phases

        except Exception as e:
            self.logger.warning(
                "parse_ai_response_failed",
                error=str(e),
            )
            # Fallback to template
            project = self._template_design(project, project.request, project.config)

        return project

    def _template_design(
        self,
        project: ProjectSpec,
        request: str,
        options: Dict[str, Any],
    ) -> ProjectSpec:
        """Create project using default template"""
        phases = []

        for i, (phase_type, name, description) in enumerate(self.DEFAULT_PHASES):
            phase_id = str(uuid.uuid4())

            # Generate tasks based on phase type
            tasks = self._generate_phase_tasks(
                phase_id, phase_type, request, options
            )

            phase = ProjectPhase(
                id=phase_id,
                name=name,
                phase_type=phase_type,
                description=description,
                tasks=tasks,
                order=i,
            )
            phases.append(phase.to_dict())

        project.phases = phases
        return project

    def _generate_phase_tasks(
        self,
        phase_id: str,
        phase_type: PhaseType,
        request: str,
        options: Dict[str, Any],
    ) -> List[ProjectTask]:
        """Generate tasks for a phase based on type"""
        tasks = []

        if phase_type == PhaseType.ANALYSIS:
            tasks = [
                ProjectTask(
                    id=f"{phase_id}_task_0",
                    description="Analyze project requirements and constraints",
                    agent_type="AUTO_CLAUDE_PLANNER",
                    estimated_minutes=5,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_1",
                    description="Identify key features and components",
                    agent_type="AUTO_CLAUDE_PLANNER",
                    dependencies=[f"{phase_id}_task_0"],
                    estimated_minutes=5,
                ),
            ]

        elif phase_type == PhaseType.DESIGN:
            tasks = [
                ProjectTask(
                    id=f"{phase_id}_task_0",
                    description="Design system architecture",
                    agent_type="AUTO_CLAUDE_PLANNER",
                    estimated_minutes=10,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_1",
                    description="Define data models and interfaces",
                    agent_type="AUTO_CLAUDE_PLANNER",
                    dependencies=[f"{phase_id}_task_0"],
                    estimated_minutes=10,
                ),
            ]

        elif phase_type == PhaseType.IMPLEMENTATION:
            tasks = [
                ProjectTask(
                    id=f"{phase_id}_task_0",
                    description="Implement core functionality",
                    agent_type="AUTO_CLAUDE_CODER",
                    estimated_minutes=30,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_1",
                    description="Implement supporting modules",
                    agent_type="AUTO_CLAUDE_CODER",
                    dependencies=[f"{phase_id}_task_0"],
                    estimated_minutes=20,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_2",
                    description="Add error handling and edge cases",
                    agent_type="AUTO_CLAUDE_CODER",
                    dependencies=[f"{phase_id}_task_1"],
                    estimated_minutes=15,
                ),
            ]

        elif phase_type == PhaseType.TESTING:
            tasks = [
                ProjectTask(
                    id=f"{phase_id}_task_0",
                    description="Write unit tests",
                    agent_type="AUTO_CLAUDE_CODER",
                    estimated_minutes=20,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_1",
                    description="Review code quality",
                    agent_type="AUTO_CLAUDE_QA_REVIEWER",
                    dependencies=[f"{phase_id}_task_0"],
                    estimated_minutes=10,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_2",
                    description="Fix issues from review",
                    agent_type="AUTO_CLAUDE_QA_FIXER",
                    dependencies=[f"{phase_id}_task_1"],
                    estimated_minutes=15,
                ),
            ]

        elif phase_type == PhaseType.DOCUMENTATION:
            tasks = [
                ProjectTask(
                    id=f"{phase_id}_task_0",
                    description="Create README documentation",
                    agent_type="AUTO_CLAUDE_CODER",
                    estimated_minutes=10,
                ),
                ProjectTask(
                    id=f"{phase_id}_task_1",
                    description="Add code comments and docstrings",
                    agent_type="AUTO_CLAUDE_CODER",
                    estimated_minutes=10,
                ),
            ]

        return tasks

    def _infer_agent(self, task_description: str) -> str:
        """Infer best agent for a task based on description"""
        description_lower = task_description.lower()

        for keyword, agent in self.TASK_AGENT_MAPPING.items():
            if keyword in description_lower:
                return agent

        return "AUTO_CLAUDE_CODER"  # Default

    async def _save_to_shared_memory(self, project: ProjectSpec):
        """Save project to SharedMemory"""
        try:
            await self.shared_memory.store(
                key=f"project:{project.id}",
                data=project.dict(),
            )

            # Update project index
            index = await self.shared_memory.get("projects:index") or {}
            project_ids = set(index.get("project_ids", []))
            project_ids.add(project.id)

            await self.shared_memory.store(
                key="projects:index",
                data={"project_ids": list(project_ids)},
            )

            # Publish event
            await self.shared_memory.publish_event(
                event_type="project_designed",
                data={
                    "project_id": project.id,
                    "name": project.name,
                    "phase_count": len(project.phases),
                },
            )

        except Exception as e:
            self.logger.warning(
                "shared_memory_save_failed",
                error=str(e),
            )

    def get_task_count(self, project: ProjectSpec) -> int:
        """Get total task count in project"""
        return sum(len(phase.get("tasks", [])) for phase in project.phases)

    def estimate_duration(self, project: ProjectSpec) -> int:
        """Estimate total project duration in minutes"""
        total = 0
        for phase in project.phases:
            for task in phase.get("tasks", []):
                total += task.get("estimated_minutes", 10)
        return total
