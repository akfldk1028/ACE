"""
Parallel Pipeline for AG-ACE-BRIDGE

Executes multiple agents in parallel, then gathers results.
Based on Microsoft Parallel Fan-Out/Gather pattern.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from src.utils.models import (
    Task, Result, ResultStatus, Stage, AgentType
)
from src.utils.logger import Loggers
from src.registry.agent_registry import get_registry


class ParallelPipeline:
    """
    Parallel pipeline executor (Fan-Out/Gather pattern).

    Executes multiple agents simultaneously, then gathers results.
    Useful for independent operations like multi-agent research.

    Flow:
              ┌─→ Agent 1 ─┐
    Task ──→  ├─→ Agent 2 ─┼──→ Gather → Combined Result
              └─→ Agent 3 ─┘

    Example:
        pipeline = ParallelPipeline()

        agents = [
            AgentType.AG_RESEARCH,
            AgentType.AG_ANALYST,
            AgentType.AG_WRITER,
        ]

        result = await pipeline.execute(task, agents)
    """

    def __init__(self, gather_strategy: str = "merge"):
        """
        Initialize parallel pipeline.

        Args:
            gather_strategy: How to combine results
                - "merge": Merge all outputs into single dict
                - "list": Keep results as list
                - "first_success": Return first successful result
                - "majority": Return if majority succeed
        """
        self.logger = Loggers.pipeline()
        self.registry = get_registry()
        self.gather_strategy = gather_strategy

    async def execute(
        self,
        task: Task,
        agents: List[AgentType],
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
    ) -> Result:
        """
        Execute agents in parallel.

        Args:
            task: Task to execute
            agents: List of agents to run in parallel
            context: Shared context
            timeout: Overall timeout in seconds

        Returns:
            Combined result from all agents
        """
        context = context or {}
        context["task"] = {
            "id": task.id,
            "type": task.type if isinstance(task.type, str) else task.type.value,
            "description": task.description,
        }

        start_time = datetime.now()
        self.logger.info(
            "parallel_pipeline_start",
            task_id=task.id,
            agent_count=len(agents),
            agents=[a.value for a in agents],
        )

        # Create tasks for parallel execution
        agent_tasks = []
        for agent_type in agents:
            adapter = self.registry.get_adapter(agent_type)
            if adapter:
                agent_tasks.append(
                    self._execute_agent(adapter, agent_type, task, context.copy())
                )
            else:
                self.logger.warning(
                    "adapter_not_found_skipping",
                    agent_type=agent_type.value,
                )

        if not agent_tasks:
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error="No adapters available for parallel execution",
            )

        try:
            # Execute all agents in parallel
            results = await asyncio.wait_for(
                asyncio.gather(*agent_tasks, return_exceptions=True),
                timeout=timeout,
            )

            # Process results
            successful_results = []
            failed_results = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        "parallel_agent_exception",
                        agent=agents[i].value if i < len(agents) else "unknown",
                        error=str(result),
                    )
                    failed_results.append({
                        "agent": agents[i].value if i < len(agents) else "unknown",
                        "error": str(result),
                    })
                elif isinstance(result, Result):
                    if result.status == ResultStatus.SUCCESS:
                        successful_results.append(result)
                    else:
                        failed_results.append({
                            "agent": result.agent_used,
                            "error": result.error,
                        })

            # Gather results based on strategy
            final_result = self._gather_results(
                task, successful_results, failed_results
            )

            total_time = int((datetime.now() - start_time).total_seconds() * 1000)
            final_result.execution_time_ms = total_time

            self.logger.info(
                "parallel_pipeline_complete",
                task_id=task.id,
                total_execution_time_ms=total_time,
                successful=len(successful_results),
                failed=len(failed_results),
            )

            return final_result

        except asyncio.TimeoutError:
            self.logger.error(
                "parallel_pipeline_timeout",
                task_id=task.id,
                timeout=timeout,
            )
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"Parallel execution timed out after {timeout}s",
            )

    async def _execute_agent(
        self,
        adapter: Any,
        agent_type: AgentType,
        task: Task,
        context: Dict[str, Any],
    ) -> Result:
        """Execute single agent and track metrics"""
        start_time = datetime.now()

        try:
            self.registry.mark_busy(agent_type, task.id)
            result = await adapter.execute(task, context)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.status == ResultStatus.SUCCESS:
                self.registry.record_success(agent_type, execution_time)
            else:
                self.registry.record_failure(agent_type)

            return result

        except Exception as e:
            self.registry.record_failure(agent_type)
            raise

    def _gather_results(
        self,
        task: Task,
        successful: List[Result],
        failed: List[Dict],
    ) -> Result:
        """
        Gather results based on strategy.

        Args:
            task: Original task
            successful: List of successful results
            failed: List of failed agent info

        Returns:
            Combined result
        """
        total = len(successful) + len(failed)

        if self.gather_strategy == "first_success":
            if successful:
                return successful[0]
            else:
                return Result(
                    task_id=task.id,
                    status=ResultStatus.FAILED,
                    error="All parallel agents failed",
                    output={"failed_agents": failed},
                )

        elif self.gather_strategy == "majority":
            if len(successful) > total / 2:
                return self._merge_results(task, successful, failed)
            else:
                return Result(
                    task_id=task.id,
                    status=ResultStatus.FAILED,
                    error="Majority of parallel agents failed",
                    output={
                        "successful": len(successful),
                        "failed": len(failed),
                        "failed_agents": failed,
                    },
                )

        elif self.gather_strategy == "list":
            return Result(
                task_id=task.id,
                status=ResultStatus.SUCCESS if successful else ResultStatus.PARTIAL,
                output={
                    "results": [
                        {
                            "agent": r.agent_used,
                            "output": r.output,
                        }
                        for r in successful
                    ],
                    "failed_agents": failed,
                },
            )

        else:  # "merge" (default)
            return self._merge_results(task, successful, failed)

    def _merge_results(
        self,
        task: Task,
        successful: List[Result],
        failed: List[Dict],
    ) -> Result:
        """Merge all successful results into single output"""
        merged_output = {}
        all_insights = []
        all_next_tasks = []

        for result in successful:
            if result.output:
                if isinstance(result.output, dict):
                    # Namespace output by agent
                    agent_key = result.agent_used or "unknown"
                    merged_output[agent_key] = result.output
                else:
                    merged_output[result.agent_used or "unknown"] = result.output

            if result.insights:
                all_insights.extend(result.insights)

            if result.next_tasks:
                all_next_tasks.extend(result.next_tasks)

        merged_output["_summary"] = {
            "total_agents": len(successful) + len(failed),
            "successful": len(successful),
            "failed": len(failed),
        }

        if failed:
            merged_output["_failed_agents"] = failed

        return Result(
            task_id=task.id,
            status=ResultStatus.SUCCESS if successful else ResultStatus.FAILED,
            output=merged_output,
            insights=all_insights,
            next_tasks=all_next_tasks,
        )


class ParallelFanOut:
    """
    Fan-out executor for parallel task distribution.

    Creates subtasks for multiple agents from a single task.
    """

    def __init__(self):
        self.logger = Loggers.pipeline()

    def fan_out(
        self,
        task: Task,
        agents: List[AgentType],
        task_modifier: Optional[Callable[[Task, AgentType], Task]] = None,
    ) -> List[Task]:
        """
        Create subtasks for parallel execution.

        Args:
            task: Original task
            agents: Agents to distribute to
            task_modifier: Optional function to modify task per agent

        Returns:
            List of subtasks
        """
        import uuid

        subtasks = []
        for agent in agents:
            subtask = Task(
                id=str(uuid.uuid4()),
                type=task.type,
                description=task.description,
                priority=task.priority,
                context={
                    **task.context,
                    "parent_task_id": task.id,
                    "assigned_agent": agent.value,
                },
                requirements=task.requirements,
                parent_task_id=task.id,
            )

            if task_modifier:
                subtask = task_modifier(subtask, agent)

            subtasks.append(subtask)

        self.logger.info(
            "fan_out_created",
            parent_task_id=task.id,
            subtask_count=len(subtasks),
        )

        return subtasks


# Convenience functions
async def run_parallel(
    task: Task,
    agents: List[AgentType],
    context: Optional[Dict[str, Any]] = None,
    gather_strategy: str = "merge",
) -> Result:
    """
    Run a parallel pipeline.

    Args:
        task: Task to execute
        agents: Agents to run in parallel
        context: Shared context
        gather_strategy: How to combine results

    Returns:
        Combined result
    """
    pipeline = ParallelPipeline(gather_strategy=gather_strategy)
    return await pipeline.execute(task, agents, context)
