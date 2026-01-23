"""
Orchestrator for AG-ACE-BRIDGE

24/7 main loop coordinating all agents.
Implements Coordinator/Dispatcher pattern from Microsoft.
"""

import asyncio
import signal
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from src.utils.models import (
    Task, Result, ResultStatus, Pipeline, Stage, StageType, AgentType
)
from src.utils.logger import Loggers, bind_context, clear_context
from src.utils.config import get_settings
from src.coordinator.task_queue import TaskQueue, TaskStatus, create_task_queue
from src.coordinator.pipeline_builder import get_builder, build_pipeline
from src.coordinator.agent_selector import get_selector
from src.registry.agent_registry import get_registry
from src.memory import SharedMemoryClient
from src.pipeline import (
    SequentialPipeline,
    ParallelPipeline,
    CriticLoopPipeline,
    run_auto_claude_qa_loop,
)
from src.adapters import (
    create_planner_adapter,
    create_coder_adapter,
    create_qa_reviewer_adapter,
    create_qa_fixer_adapter,
    create_research_adapter,
    create_analyst_adapter,
    create_writer_adapter,
    create_reviewer_adapter,
    create_coordinator_adapter,
    create_case_analyzer_adapter,
    create_legal_researcher_adapter,
    create_risk_assessor_adapter,
    create_compliance_checker_adapter,
    create_document_drafter_adapter,
    # AG A2A Protocol adapters
    A2AAdapterManager,
    A2AAgentType,
    create_poetry_adapter,
    create_philosophy_adapter,
    create_history_adapter,
    create_calculator_adapter,
    create_gui_test_adapter,
)


class OrchestratorState(str, Enum):
    """Orchestrator lifecycle states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


class Orchestrator:
    """
    24/7 AI Project Factory Orchestrator.

    Central coordinator managing:
    - Task queue processing
    - Agent selection and dispatch
    - Pipeline execution
    - Result handling
    - Health monitoring

    Main loop pattern:
        while True:
            task = queue.dequeue()
            pipeline = build_pipeline(task)
            result = execute_pipeline(pipeline)
            handle_result(result)
            queue_new_tasks(result.next_tasks)

    Example:
        orchestrator = Orchestrator()
        await orchestrator.start()  # Runs forever
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize orchestrator.

        Args:
            db_path: Optional task queue database path
        """
        self.logger = Loggers.orchestrator()
        self.settings = get_settings()

        # Core components
        self.queue = create_task_queue(db_path)
        self.registry = get_registry()
        self.builder = get_builder()
        self.selector = get_selector()

        # State
        self.state = OrchestratorState.STOPPED
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially

        # Metrics
        self.metrics = {
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_execution_time_ms": 0,
            "start_time": None,
        }

        # Pipeline executors
        self._sequential = SequentialPipeline()
        self._parallel = ParallelPipeline()

        # SharedMemory client (AG-CLI 연동)
        self._shared_memory: Optional[SharedMemoryClient] = None
        self._enable_shared_memory = self.settings.enable_shared_memory

    async def start(self) -> None:
        """
        Start the 24/7 orchestration loop.

        Runs indefinitely until stop() is called.
        """
        if self.state == OrchestratorState.RUNNING:
            self.logger.warning("orchestrator_already_running")
            return

        self.state = OrchestratorState.STARTING
        self.metrics["start_time"] = datetime.now()

        self.logger.info(
            "orchestrator_starting",
            db_path=str(self.queue.db_path),
        )

        # Initialize adapters
        await self._initialize_adapters()

        # Initialize SharedMemory (AG-CLI 연동)
        await self._initialize_shared_memory()

        # Setup signal handlers
        self._setup_signal_handlers()

        self.state = OrchestratorState.RUNNING
        self.logger.info("orchestrator_started")

        # Main loop
        try:
            await self._main_loop()
        except asyncio.CancelledError:
            self.logger.info("orchestrator_cancelled")
        except Exception as e:
            self.logger.error("orchestrator_error", error=str(e))
            raise
        finally:
            await self._shutdown()

    async def stop(self) -> None:
        """Stop the orchestrator gracefully"""
        if self.state != OrchestratorState.RUNNING:
            return

        self.state = OrchestratorState.STOPPING
        self.logger.info("orchestrator_stopping")
        self._stop_event.set()

    def pause(self) -> None:
        """Pause task processing"""
        self._pause_event.clear()
        self.state = OrchestratorState.PAUSED
        self.logger.info("orchestrator_paused")

    def resume(self) -> None:
        """Resume task processing"""
        self._pause_event.set()
        self.state = OrchestratorState.RUNNING
        self.logger.info("orchestrator_resumed")

    async def _main_loop(self) -> None:
        """Main orchestration loop"""
        poll_interval = self.settings.orchestrator_poll_interval

        while not self._stop_event.is_set():
            # Wait if paused
            await self._pause_event.wait()

            if self._stop_event.is_set():
                break

            # Get next task
            task = self.queue.dequeue()

            if task:
                bind_context(task_id=task.id)

                try:
                    await self._process_task(task)
                except Exception as e:
                    self.logger.error(
                        "task_processing_error",
                        task_id=task.id,
                        error=str(e),
                    )
                    self.queue.fail(task.id, error=str(e))
                finally:
                    clear_context()
            else:
                # No tasks, wait before polling again
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=poll_interval,
                    )
                except asyncio.TimeoutError:
                    pass  # Continue loop

            # Periodic health check
            if self.metrics["tasks_processed"] % 10 == 0:
                await self._health_check()

    async def _process_task(self, task: Task) -> None:
        """Process a single task"""
        start_time = datetime.now()

        self.logger.info(
            "task_processing_start",
            task_id=task.id,
            type=task.type,
            priority=task.priority,
        )

        # Build pipeline
        pipeline = self.builder.build(task)

        self.logger.info(
            "pipeline_created",
            task_id=task.id,
            pipeline_id=pipeline.id,
            stages=len(pipeline.stages),
        )

        # Execute pipeline
        result = await self._execute_pipeline(task, pipeline)

        # Calculate metrics
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        self.metrics["tasks_processed"] += 1
        self.metrics["total_execution_time_ms"] += execution_time

        # Handle result
        if result.status == ResultStatus.SUCCESS:
            self.queue.complete(task.id, output=result.output)
            self.metrics["tasks_succeeded"] += 1

            # Share to SharedMemory
            await self._share_task_complete(task, success=True, output=result.output)

            self.logger.info(
                "task_completed",
                task_id=task.id,
                execution_time_ms=execution_time,
            )

        elif result.status == ResultStatus.PARTIAL:
            self.queue.complete(task.id, output=result.output)
            self.metrics["tasks_succeeded"] += 1

            # Share to SharedMemory
            await self._share_task_complete(task, success=True, output=result.output)

            self.logger.warning(
                "task_partial_success",
                task_id=task.id,
                insights=result.insights,
            )

        else:
            retried = self.queue.fail(task.id, error=result.error)
            if not retried:
                self.metrics["tasks_failed"] += 1

                # Share to SharedMemory (only if not retrying)
                await self._share_task_complete(task, success=False)

            self.logger.error(
                "task_failed",
                task_id=task.id,
                error=result.error,
                retried=retried,
            )

        # Queue new tasks
        if result.next_tasks:
            for next_task in result.next_tasks:
                self.queue.enqueue(next_task)
                self.logger.info(
                    "task_queued",
                    task_id=next_task.id,
                    parent_id=task.id,
                )

    async def _execute_pipeline(
        self,
        task: Task,
        pipeline: Pipeline,
    ) -> Result:
        """Execute a pipeline"""
        context = pipeline.accumulated_context.copy()
        results = []

        for i, stage in enumerate(pipeline.stages):
            self.logger.debug(
                "stage_start",
                stage_index=i,
                stage_type=stage.stage_type.value if hasattr(stage.stage_type, 'value') else stage.stage_type,
                agent=stage.agent.value if hasattr(stage.agent, 'value') else stage.agent,
            )

            stage_type = StageType(stage.stage_type) if isinstance(stage.stage_type, str) else stage.stage_type

            if stage.critic_loop:
                result = await self._execute_critic_stage(task, stage, context)
            elif stage_type == StageType.PARALLEL:
                result = await self._execute_parallel_stage(task, stage, context)
            else:
                result = await self._execute_sequential_stage(task, stage, context)

            results.append(result)

            # Check for failure
            if result.status == ResultStatus.FAILED:
                return result

            # Accumulate context
            if result.output:
                context[f"stage_{i}"] = result.output
                if isinstance(result.output, dict):
                    context.update(result.output)

            # Update pipeline state
            pipeline.current_stage_index = i + 1
            pipeline.accumulated_context = context

            # Store stage result to SharedMemory (AG-CLI 연동)
            await self._share_stage_result(task, i, stage, result)

        # Build final result
        pipeline.is_complete = True

        return Result(
            task_id=task.id,
            status=ResultStatus.SUCCESS,
            output={
                "pipeline_id": pipeline.id,
                "stages_completed": len(pipeline.stages),
                "final_context": context,
            },
            insights=[r.insights[0] if r.insights else "" for r in results if r.insights],
            next_tasks=[t for r in results for t in r.next_tasks],
        )

    async def _execute_sequential_stage(
        self,
        task: Task,
        stage: Stage,
        context: Dict[str, Any],
    ) -> Result:
        """Execute a sequential stage"""
        agent_type = AgentType(stage.agent) if isinstance(stage.agent, str) else stage.agent
        adapter = self.registry.get_adapter(agent_type)

        if not adapter:
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"Adapter not found: {agent_type.value}",
            )

        self.registry.mark_busy(agent_type, task.id)
        start_time = datetime.now()

        try:
            result = await asyncio.wait_for(
                adapter.execute(task, context),
                timeout=stage.timeout_seconds,
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.status == ResultStatus.SUCCESS:
                self.registry.record_success(agent_type, execution_time)
            else:
                self.registry.record_failure(agent_type)

            return result

        except asyncio.TimeoutError:
            self.registry.record_failure(agent_type)
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"Stage timeout after {stage.timeout_seconds}s",
            )

        except Exception as e:
            self.registry.record_failure(agent_type)
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=str(e),
            )

    async def _execute_parallel_stage(
        self,
        task: Task,
        stage: Stage,
        context: Dict[str, Any],
    ) -> Result:
        """Execute a parallel stage"""
        agents = stage.parallel_agents or [
            AgentType(stage.agent) if isinstance(stage.agent, str) else stage.agent
        ]

        return await self._parallel.execute(
            task,
            agents,
            context,
            timeout=stage.timeout_seconds,
        )

    async def _execute_critic_stage(
        self,
        task: Task,
        stage: Stage,
        context: Dict[str, Any],
    ) -> Result:
        """Execute a critic loop stage"""
        generator = AgentType(stage.agent) if isinstance(stage.agent, str) else stage.agent
        critic = stage.critic_agent or AgentType.AUTO_CLAUDE_QA_REVIEWER
        fixer = stage.fixer_agent or AgentType.AUTO_CLAUDE_QA_FIXER

        loop = CriticLoopPipeline(
            generator=generator,
            critic=critic,
            fixer=fixer,
            max_iterations=stage.max_iterations,
        )

        return await loop.execute(task, context)

    async def _initialize_adapters(self) -> None:
        """Initialize all adapters and register with registry"""
        # ★ SharedMemory 동기화 플래그 - 모든 A2A 어댑터에 전달
        sm = self._enable_shared_memory

        adapters = [
            # Auto-Claude
            (AgentType.AUTO_CLAUDE_PLANNER, create_planner_adapter()),
            (AgentType.AUTO_CLAUDE_CODER, create_coder_adapter()),
            (AgentType.AUTO_CLAUDE_QA_REVIEWER, create_qa_reviewer_adapter()),
            (AgentType.AUTO_CLAUDE_QA_FIXER, create_qa_fixer_adapter()),
            # AG Autogen
            (AgentType.AG_RESEARCH, create_research_adapter()),
            (AgentType.AG_ANALYST, create_analyst_adapter()),
            (AgentType.AG_WRITER, create_writer_adapter()),
            (AgentType.AG_REVIEWER, create_reviewer_adapter()),
            (AgentType.AG_COORDINATOR, create_coordinator_adapter()),
            # AG Law Domain
            (AgentType.AG_CASE_ANALYZER, create_case_analyzer_adapter()),
            (AgentType.AG_LEGAL_RESEARCHER, create_legal_researcher_adapter()),
            (AgentType.AG_RISK_ASSESSOR, create_risk_assessor_adapter()),
            (AgentType.AG_COMPLIANCE_CHECKER, create_compliance_checker_adapter()),
            (AgentType.AG_DOCUMENT_DRAFTER, create_document_drafter_adapter()),
            # AG A2A Protocol (autogen_a2a_kit demo agents) - ★ SharedMemory 연동
            (AgentType.AG_A2A_POETRY, create_poetry_adapter(enable_shared_memory=sm)),
            (AgentType.AG_A2A_PHILOSOPHY, create_philosophy_adapter(enable_shared_memory=sm)),
            (AgentType.AG_A2A_HISTORY, create_history_adapter(enable_shared_memory=sm)),
            (AgentType.AG_A2A_CALCULATOR, create_calculator_adapter(enable_shared_memory=sm)),
            (AgentType.AG_A2A_GUI_TEST, create_gui_test_adapter(enable_shared_memory=sm)),
        ]

        for agent_type, adapter in adapters:
            try:
                await adapter.initialize()
                self.registry.register_adapter(agent_type, adapter)
                self.logger.debug("adapter_initialized", agent_type=agent_type.value)
            except Exception as e:
                self.logger.warning(
                    "adapter_init_failed",
                    agent_type=agent_type.value,
                    error=str(e),
                )

        self.logger.info(
            "adapters_initialized",
            count=len(adapters),
        )

    async def _initialize_shared_memory(self) -> None:
        """Initialize SharedMemory client for AG-CLI integration"""
        if not self._enable_shared_memory:
            self.logger.info("shared_memory_disabled")
            return

        try:
            self._shared_memory = SharedMemoryClient(
                base_url=self.settings.shared_memory_url,
                source_name="ag-ace-bridge-orchestrator",
            )

            # Check connection
            if await self._shared_memory.health_check():
                self.logger.info(
                    "shared_memory_connected",
                    url=self.settings.shared_memory_url,
                )
            else:
                self.logger.warning(
                    "shared_memory_not_available",
                    url=self.settings.shared_memory_url,
                )
                self._shared_memory = None

        except Exception as e:
            self.logger.warning(
                "shared_memory_init_failed",
                error=str(e),
            )
            self._shared_memory = None

    async def _share_stage_result(
        self,
        task: Task,
        stage_index: int,
        stage: Stage,
        result: Result,
    ) -> None:
        """Share stage result to SharedMemory"""
        if not self._shared_memory:
            return

        try:
            agent_type = stage.agent.value if hasattr(stage.agent, 'value') else str(stage.agent)

            # Store result
            await self._shared_memory.store_task_result(
                task_id=task.id,
                stage=stage_index,
                result=result.output or {},
                agent_type=agent_type,
            )

            # Notify stage completion
            await self._shared_memory.notify_stage_complete(
                task_id=task.id,
                stage=stage_index,
                agent_type=agent_type,
                success=result.status == ResultStatus.SUCCESS,
            )

            self.logger.debug(
                "stage_result_shared",
                task_id=task.id,
                stage=stage_index,
                agent=agent_type,
            )

        except Exception as e:
            # Don't fail task if SharedMemory fails
            self.logger.debug(
                "stage_share_failed",
                task_id=task.id,
                error=str(e),
            )

    async def _share_task_complete(
        self,
        task: Task,
        success: bool,
        output: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Share task completion to SharedMemory"""
        if not self._shared_memory:
            return

        try:
            await self._shared_memory.notify_task_complete(
                task_id=task.id,
                success=success,
                artifacts=output or {},
            )

            self.logger.debug(
                "task_complete_shared",
                task_id=task.id,
                success=success,
            )

        except Exception as e:
            self.logger.debug(
                "task_share_failed",
                task_id=task.id,
                error=str(e),
            )

    async def _health_check(self) -> None:
        """Perform health check on all agents"""
        stats = self.registry.get_stats()
        self.logger.debug(
            "health_check",
            **stats,
            **self.metrics,
        )

    async def _shutdown(self) -> None:
        """Shutdown orchestrator"""
        self.state = OrchestratorState.STOPPED

        # Close SharedMemory connection
        if self._shared_memory:
            try:
                await self._shared_memory.close()
                self.logger.debug("shared_memory_closed")
            except Exception:
                pass

        # Shutdown all adapters
        for agent_type in self.registry.get_all_agents():
            adapter = self.registry.get_adapter(agent_type)
            if adapter:
                try:
                    await adapter.shutdown()
                except Exception:
                    pass

        self.logger.info(
            "orchestrator_shutdown",
            **self.metrics,
        )

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self.stop()),
                )
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "state": self.state.value,
            "queue_stats": self.queue.get_stats(),
            "registry_stats": self.registry.get_stats(),
            "metrics": self.metrics,
            "uptime_seconds": (
                (datetime.now() - self.metrics["start_time"]).total_seconds()
                if self.metrics["start_time"]
                else 0
            ),
        }


# Entry point
async def run_orchestrator(db_path: Optional[str] = None) -> None:
    """
    Run the orchestrator.

    Args:
        db_path: Optional task queue database path
    """
    orchestrator = Orchestrator(db_path)
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(run_orchestrator())
