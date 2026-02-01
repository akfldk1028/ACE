"""
Project Executor - Project Level Execution Orchestration

Executes designed projects through pattern orchestration.
Handles phase-by-phase execution, dependency management, and result aggregation.

Usage:
    executor = ProjectExecutor(scheduler, registry, orchestrator)

    # Execute a complete project
    result = await executor.execute(project)

    # Execute specific phase
    phase_result = await executor.execute_phase(project, phase_id)
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from src.registry.pattern_registry import PatternRegistry
from src.scheduler.trigger import ScheduleTrigger
from src.designer.project_designer import ProjectSpec, ProjectTask, ProjectStatus
from src.designer.pattern_matcher import PatternMatcher, PatternMatch
from src.utils.logger import Loggers


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PhaseStatus(str, Enum):
    """Phase execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some tasks completed


@dataclass
class TaskResult:
    """Result of a single task execution"""
    task_id: str
    status: TaskStatus
    pattern_id: Optional[str]
    output: Any
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float


@dataclass
class PhaseResult:
    """Result of a phase execution"""
    phase_id: str
    status: PhaseStatus
    task_results: Dict[str, TaskResult]
    started_at: datetime
    completed_at: Optional[datetime]

    @property
    def success_rate(self) -> float:
        if not self.task_results:
            return 0.0
        completed = sum(1 for r in self.task_results.values()
                       if r.status == TaskStatus.COMPLETED)
        return completed / len(self.task_results)


@dataclass
class ProjectResult:
    """Result of a complete project execution"""
    project_id: str
    project_name: str
    status: ProjectStatus
    phase_results: Dict[str, PhaseResult]
    pattern_matches: Dict[str, PatternMatch]
    patterns_created: List[str]
    started_at: datetime
    completed_at: Optional[datetime]

    @property
    def overall_success_rate(self) -> float:
        if not self.phase_results:
            return 0.0
        rates = [p.success_rate for p in self.phase_results.values()]
        return sum(rates) / len(rates) if rates else 0.0


class ProjectExecutor:
    """
    Executes designed projects through pattern orchestration.

    Execution Flow:
    1. Match all tasks to patterns
    2. Create missing patterns if needed
    3. Execute phases in order
    4. For each phase, execute tasks respecting dependencies
    5. Aggregate results and update project status
    """

    def __init__(
        self,
        registry: PatternRegistry,
        scheduler: Optional[ScheduleTrigger] = None,
        orchestrator: Optional[Any] = None,  # Orchestrator for direct execution
        matcher: Optional[PatternMatcher] = None,
        adapters: Optional[Dict[str, Any]] = None,  # agent_type -> adapter mapping
        auto_create_patterns: bool = True,
        max_parallel_tasks: int = 4,
    ):
        """
        Initialize ProjectExecutor.

        Args:
            registry: Pattern registry for pattern lookup
            scheduler: Schedule trigger for pattern execution
            orchestrator: Direct orchestrator for immediate execution
            matcher: Pattern matcher (created if not provided)
            adapters: Dict mapping agent_type to adapter instances
            auto_create_patterns: Create missing patterns automatically
            max_parallel_tasks: Max concurrent task executions
        """
        self.registry = registry
        self.scheduler = scheduler
        self.orchestrator = orchestrator
        self.matcher = matcher or PatternMatcher(registry)
        self.adapters = adapters or {}  # agent_type -> adapter
        self.auto_create_patterns = auto_create_patterns
        self.max_parallel_tasks = max_parallel_tasks
        self.logger = Loggers.orchestrator()

        # Execution state
        self._current_project: Optional[ProjectSpec] = None
        self._execution_lock = asyncio.Lock()

        # Callbacks
        self._on_task_start: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_phase_complete: Optional[Callable] = None

    def on_task_start(self, callback: Callable):
        """Register callback for task start events"""
        self._on_task_start = callback

    def on_task_complete(self, callback: Callable):
        """Register callback for task completion events"""
        self._on_task_complete = callback

    def on_phase_complete(self, callback: Callable):
        """Register callback for phase completion events"""
        self._on_phase_complete = callback

    async def execute(
        self,
        project: ProjectSpec,
        start_phase: Optional[str] = None,
    ) -> ProjectResult:
        """
        Execute a complete project.

        Args:
            project: Project specification to execute
            start_phase: Optional phase ID to start from (for resume)

        Returns:
            ProjectResult with execution details
        """
        async with self._execution_lock:
            self._current_project = project

            self.logger.info(
                "project_execution_started",
                project_id=project.id,
                project_name=project.name,
                phase_count=len(project.phases),
            )

            started_at = datetime.utcnow()

            # Match all tasks to patterns
            pattern_matches = await self.matcher.match_project(project)

            # Create missing patterns if needed
            patterns_created = []
            if self.auto_create_patterns:
                patterns_created = await self._create_missing_patterns(
                    project, pattern_matches
                )

            # Execute phases in order
            phase_results = {}
            overall_status = ProjectStatus.EXECUTING

            should_start = start_phase is None

            for phase in project.phases:
                phase_id = phase.get("id", f"phase_{len(phase_results)}")

                if not should_start:
                    if phase_id == start_phase:
                        should_start = True
                    else:
                        continue

                phase_result = await self._execute_phase(
                    project, phase, pattern_matches
                )
                phase_results[phase_id] = phase_result

                # Check if we should continue
                if phase_result.status == PhaseStatus.FAILED:
                    self.logger.warning(
                        "phase_failed_stopping_execution",
                        project_id=project.id,
                        phase_id=phase_id,
                    )
                    overall_status = ProjectStatus.FAILED
                    break

            # Determine final status
            if overall_status != ProjectStatus.FAILED:
                all_completed = all(
                    p.status == PhaseStatus.COMPLETED
                    for p in phase_results.values()
                )
                overall_status = (
                    ProjectStatus.COMPLETED if all_completed
                    else ProjectStatus.PARTIAL
                )

            completed_at = datetime.utcnow()

            result = ProjectResult(
                project_id=project.id,
                project_name=project.name,
                status=overall_status,
                phase_results=phase_results,
                pattern_matches=pattern_matches,
                patterns_created=patterns_created,
                started_at=started_at,
                completed_at=completed_at,
            )

            self.logger.info(
                "project_execution_completed",
                project_id=project.id,
                status=overall_status.value,
                success_rate=f"{result.overall_success_rate*100:.1f}%",
                duration_seconds=(completed_at - started_at).total_seconds(),
            )

            self._current_project = None
            return result

    async def _execute_phase(
        self,
        project: ProjectSpec,
        phase: Dict[str, Any],
        pattern_matches: Dict[str, PatternMatch],
    ) -> PhaseResult:
        """Execute a single phase"""
        phase_id = phase.get("id", "unknown")
        phase_name = phase.get("name", phase_id)
        tasks = phase.get("tasks", [])

        self.logger.info(
            "phase_execution_started",
            project_id=project.id,
            phase_id=phase_id,
            phase_name=phase_name,
            task_count=len(tasks),
        )

        started_at = datetime.utcnow()
        task_results = {}

        # Build task dependency graph
        task_deps = self._build_task_dependencies(tasks)

        # Execute tasks respecting dependencies
        pending_tasks = set(t["id"] for t in tasks)
        completed_tasks = set()

        while pending_tasks:
            # Find tasks with satisfied dependencies
            ready_tasks = [
                tid for tid in pending_tasks
                if task_deps.get(tid, set()).issubset(completed_tasks)
            ]

            if not ready_tasks:
                # Deadlock - remaining tasks have unsatisfied deps
                self.logger.error(
                    "task_dependency_deadlock",
                    phase_id=phase_id,
                    pending=list(pending_tasks),
                )
                # Mark remaining as skipped
                for tid in pending_tasks:
                    task_results[tid] = TaskResult(
                        task_id=tid,
                        status=TaskStatus.SKIPPED,
                        pattern_id=None,
                        output=None,
                        error="Dependency deadlock",
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                        duration_seconds=0,
                    )
                break

            # Execute ready tasks in parallel (up to limit)
            batch = ready_tasks[:self.max_parallel_tasks]
            batch_tasks = [
                t for t in tasks if t["id"] in batch
            ]

            results = await asyncio.gather(
                *[
                    self._execute_task(project, t, pattern_matches.get(t["id"]))
                    for t in batch_tasks
                ],
                return_exceptions=True,
            )

            # Process results
            for task_dict, result in zip(batch_tasks, results):
                tid = task_dict["id"]

                if isinstance(result, Exception):
                    task_results[tid] = TaskResult(
                        task_id=tid,
                        status=TaskStatus.FAILED,
                        pattern_id=None,
                        output=None,
                        error=str(result),
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                        duration_seconds=0,
                    )
                else:
                    task_results[tid] = result

                pending_tasks.discard(tid)
                completed_tasks.add(tid)

        # Determine phase status
        statuses = [r.status for r in task_results.values()]
        if all(s == TaskStatus.COMPLETED for s in statuses):
            phase_status = PhaseStatus.COMPLETED
        elif all(s in (TaskStatus.FAILED, TaskStatus.SKIPPED) for s in statuses):
            phase_status = PhaseStatus.FAILED
        elif any(s == TaskStatus.COMPLETED for s in statuses):
            phase_status = PhaseStatus.PARTIAL
        else:
            phase_status = PhaseStatus.FAILED

        completed_at = datetime.utcnow()

        phase_result = PhaseResult(
            phase_id=phase_id,
            status=phase_status,
            task_results=task_results,
            started_at=started_at,
            completed_at=completed_at,
        )

        if self._on_phase_complete:
            try:
                await self._on_phase_complete(phase_result)
            except Exception as e:
                self.logger.warning(f"Phase complete callback error: {e}")

        self.logger.info(
            "phase_execution_completed",
            project_id=project.id,
            phase_id=phase_id,
            status=phase_status.value,
            success_rate=f"{phase_result.success_rate*100:.1f}%",
        )

        return phase_result

    async def _execute_task(
        self,
        project: ProjectSpec,
        task_dict: Dict[str, Any],
        match: Optional[PatternMatch],
    ) -> TaskResult:
        """Execute a single task"""
        task_id = task_dict["id"]
        started_at = datetime.utcnow()

        if self._on_task_start:
            try:
                await self._on_task_start(task_id, task_dict)
            except Exception as e:
                self.logger.warning(f"Task start callback error: {e}")

        self.logger.info(
            "task_execution_started",
            project_id=project.id,
            task_id=task_id,
            pattern_id=match.pattern_id if match else None,
        )

        try:
            # Execute based on match
            if match and match.pattern_id and not match.create_new:
                # Use matched pattern
                output = await self._execute_pattern(match.pattern_id, task_dict)
                status = TaskStatus.COMPLETED
                error = None
            else:
                # Direct execution without pattern
                output = await self._execute_direct(task_dict)
                status = TaskStatus.COMPLETED
                error = None

        except Exception as e:
            self.logger.error(
                "task_execution_failed",
                task_id=task_id,
                error=str(e),
            )
            output = None
            status = TaskStatus.FAILED
            error = str(e)

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        result = TaskResult(
            task_id=task_id,
            status=status,
            pattern_id=match.pattern_id if match else None,
            output=output,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
        )

        if self._on_task_complete:
            try:
                await self._on_task_complete(result)
            except Exception as e:
                self.logger.warning(f"Task complete callback error: {e}")

        return result

    async def _execute_pattern(
        self,
        pattern_id: str,
        task_dict: Dict[str, Any],
    ) -> Any:
        """
        Execute task using a pattern.

        This method executes the pattern's workflow nodes through appropriate adapters.
        AutoGen Studio에서 설계한 워크플로우를 Auto-Claude 어댑터로 실행합니다.
        """
        pattern = self.registry.get(pattern_id)
        if not pattern:
            self.logger.warning(f"Pattern not found: {pattern_id}")
            return {"error": f"Pattern {pattern_id} not found"}

        pattern_data = pattern.data
        nodes = pattern_data.get("nodes", [])

        if not nodes:
            # No nodes - execute as single task
            return await self._execute_direct(task_dict)

        self.logger.info(
            "pattern_workflow_execution_started",
            pattern_id=pattern_id,
            pattern_name=pattern_data.get("name", "unnamed"),
            node_count=len(nodes),
        )

        # Execute workflow nodes
        # 워크플로우 노드를 순차적으로 실행하며, 각 노드의 agent_type에 맞는 어댑터 호출
        results = []
        context = {
            "pattern_id": pattern_id,
            "pattern_name": pattern_data.get("name"),
            "task": task_dict,
        }

        # Build node dependency graph
        node_deps = {}
        for node in nodes:
            node_id = node.get("id", f"node_{len(node_deps)}")
            depends_on = node.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            node_deps[node_id] = set(depends_on)

        # Execute nodes respecting dependencies
        completed_nodes = set()
        pending_nodes = set(node_deps.keys())
        node_map = {n.get("id", f"node_{i}"): n for i, n in enumerate(nodes)}

        while pending_nodes:
            # Find ready nodes (dependencies satisfied)
            ready = [
                nid for nid in pending_nodes
                if node_deps.get(nid, set()).issubset(completed_nodes)
            ]

            if not ready:
                self.logger.error("Workflow node dependency deadlock")
                break

            # Execute ready nodes (can parallelize later)
            for node_id in ready:
                node = node_map.get(node_id, {})
                agent_type = node.get("agent", node.get("agent_type", "AUTO_CLAUDE_CODER"))
                node_task = node.get("task", task_dict.get("description", ""))

                # Create task dict for this node
                node_task_dict = {
                    "id": f"{task_dict['id']}_{node_id}",
                    "description": node_task if isinstance(node_task, str) else str(node_task),
                    "agent_type": agent_type,
                    "input": {
                        **task_dict.get("input", {}),
                        "node_id": node_id,
                        "previous_results": results,
                    },
                    "context": context,
                }

                # Execute via adapter
                node_result = await self._execute_direct(node_task_dict)
                results.append({
                    "node_id": node_id,
                    "agent_type": agent_type,
                    "result": node_result,
                })

                # Update context with node output
                context[f"node_{node_id}_output"] = node_result

                pending_nodes.discard(node_id)
                completed_nodes.add(node_id)

        self.logger.info(
            "pattern_workflow_execution_completed",
            pattern_id=pattern_id,
            nodes_executed=len(results),
        )

        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern_data.get("name"),
            "method": "workflow",
            "nodes_executed": len(results),
            "results": results,
        }

    async def _execute_direct(self, task_dict: Dict[str, Any]) -> Any:
        """Execute task directly using appropriate adapter"""
        agent_type = task_dict.get("agent_type", "AUTO_CLAUDE_CODER")
        description = task_dict.get("description", "")
        task_id = task_dict["id"]

        self.logger.info(
            "direct_task_execution_started",
            task_id=task_id,
            agent_type=agent_type,
        )

        # Try to get adapter for this agent type
        adapter = self.adapters.get(agent_type)

        if adapter:
            try:
                # Build task model for adapter
                from src.utils.models import Task, TaskType, Priority

                task = Task(
                    id=task_id,
                    type=self._infer_task_type(description),
                    description=description,
                    priority=Priority.MEDIUM,
                    input=task_dict.get("input", {}),
                    context=task_dict.get("context", {}),
                )

                # Execute via adapter
                result = await adapter.execute(task, task.context)

                self.logger.info(
                    "direct_task_execution_completed",
                    task_id=task_id,
                    success=result.success if hasattr(result, 'success') else True,
                )

                return {
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "method": "adapter",
                    "success": result.success if hasattr(result, 'success') else True,
                    "output": result.output if hasattr(result, 'output') else result,
                }

            except Exception as e:
                self.logger.error(
                    "direct_task_execution_failed",
                    task_id=task_id,
                    error=str(e),
                )
                return {
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "method": "adapter",
                    "success": False,
                    "error": str(e),
                }

        # Fallback: stub result when no adapter available
        self.logger.warning(
            "no_adapter_available",
            task_id=task_id,
            agent_type=agent_type,
            available_adapters=list(self.adapters.keys()),
        )

        return {
            "task_id": task_id,
            "agent_type": agent_type,
            "description": description,
            "method": "stub",
            "status": "no_adapter_available",
        }

    def _infer_task_type(self, description: str):
        """Infer task type from description"""
        from src.utils.models import TaskType

        desc_lower = description.lower()

        if any(k in desc_lower for k in ["plan", "design", "architect", "analyze"]):
            return TaskType.PLAN
        elif any(k in desc_lower for k in ["review", "check", "verify", "audit"]):
            return TaskType.REVIEW
        elif any(k in desc_lower for k in ["research", "search", "find", "gather"]):
            return TaskType.RESEARCH
        elif any(k in desc_lower for k in ["fix", "debug", "test", "repair"]):
            return TaskType.FIX
        else:
            return TaskType.CODE

    def _build_task_dependencies(
        self,
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, set]:
        """Build task dependency graph"""
        deps = {}
        for task in tasks:
            task_id = task["id"]
            depends_on = task.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            deps[task_id] = set(depends_on)
        return deps

    async def _create_missing_patterns(
        self,
        project: ProjectSpec,
        pattern_matches: Dict[str, PatternMatch],
    ) -> List[str]:
        """Create patterns for unmatched tasks"""
        created = []

        # Get suggestions
        suggestions = await self.matcher.suggest_patterns_to_create(project)

        for suggestion in suggestions:
            pattern_name = suggestion["name"]

            # Create pattern in registry
            from src.watcher.pattern_watcher import PatternEvent

            event = PatternEvent(
                path=f"auto_generated/{pattern_name}.json",
                name=pattern_name,
                event_type="created",
                data={
                    "name": pattern_name,
                    "description": suggestion["description"],
                    "type": suggestion["type"],
                    "nodes": [
                        {
                            "id": "main",
                            "agent": suggestion.get("agent", "AUTO_CLAUDE_CODER"),
                            "task": suggestion["description"],
                        }
                    ],
                },
            )

            try:
                registered = await self.registry.register(event)
                if registered:
                    created.append(registered.id)
                    self.logger.info(
                        "auto_created_pattern",
                        pattern_id=registered.id,
                        pattern_name=pattern_name,
                    )
            except Exception as e:
                self.logger.warning(f"Failed to create pattern {pattern_name}: {e}")

        return created

    async def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        if not self._current_project:
            return None

        return {
            "project_id": self._current_project.id,
            "project_name": self._current_project.name,
            "status": "running",
        }

    async def cancel_execution(self) -> bool:
        """Cancel current execution (best effort)"""
        if self._current_project:
            self.logger.warning(
                "execution_cancelled",
                project_id=self._current_project.id,
            )
            # Would need more sophisticated cancellation
            return True
        return False
