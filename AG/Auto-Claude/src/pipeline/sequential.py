"""
Sequential Pipeline for AG/Auto-Claude

Executes stages one after another, passing context forward.
Based on Google ADK Sequential Pipeline pattern.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.utils.models import (
    Task, Result, ResultStatus, Pipeline, Stage, StageType, AgentType
)
from src.utils.logger import Loggers
from src.registry.agent_registry import get_registry


class SequentialPipeline:
    """
    Sequential pipeline executor.

    Executes stages in order, accumulating context.
    Each stage receives output from previous stages.

    Flow:
    Stage 1 → Stage 2 → Stage 3 → ... → Final Result

    Example:
        pipeline = SequentialPipeline()

        stages = [
            Stage(agent=AgentType.AUTO_CLAUDE_PLANNER),
            Stage(agent=AgentType.AUTO_CLAUDE_CODER),
            Stage(agent=AgentType.AUTO_CLAUDE_QA_REVIEWER),
        ]

        result = await pipeline.execute(task, stages)
    """

    def __init__(self):
        self.logger = Loggers.pipeline()
        self.registry = get_registry()

    async def execute(
        self,
        task: Task,
        stages: List[Stage],
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Result:
        """
        Execute stages sequentially.

        Args:
            task: Task to execute
            stages: List of stages to execute
            initial_context: Initial context (optional)

        Returns:
            Final result with accumulated context
        """
        context = initial_context or {}
        context["task"] = {
            "id": task.id,
            "type": task.type if isinstance(task.type, str) else task.type.value,
            "description": task.description,
        }

        start_time = datetime.now()
        self.logger.info(
            "sequential_pipeline_start",
            task_id=task.id,
            stage_count=len(stages),
        )

        results: List[Result] = []
        current_result: Optional[Result] = None

        for i, stage in enumerate(stages):
            stage_start = datetime.now()
            self.logger.info(
                "sequential_stage_start",
                task_id=task.id,
                stage_index=i,
                agent=stage.agent if isinstance(stage.agent, str) else stage.agent.value,
            )

            try:
                # Get adapter for this agent
                agent_type = AgentType(stage.agent) if isinstance(stage.agent, str) else stage.agent
                adapter = self.registry.get_adapter(agent_type)

                if not adapter:
                    self.logger.error(
                        "adapter_not_found",
                        agent_type=agent_type.value,
                    )
                    return Result(
                        task_id=task.id,
                        status=ResultStatus.FAILED,
                        error=f"Adapter not found for {agent_type.value}",
                    )

                # Mark agent as busy
                self.registry.mark_busy(agent_type, task.id)

                # Execute stage
                result = await self._execute_stage_with_timeout(
                    adapter, task, context, stage.timeout_seconds
                )

                stage_time = int((datetime.now() - stage_start).total_seconds() * 1000)

                # Update registry
                if result.status == ResultStatus.SUCCESS:
                    self.registry.record_success(agent_type, stage_time)
                else:
                    self.registry.record_failure(agent_type)

                results.append(result)
                current_result = result

                # Handle failure
                if result.status == ResultStatus.FAILED:
                    if stage.retry_on_failure:
                        self.logger.warning(
                            "sequential_stage_failed_will_retry",
                            task_id=task.id,
                            stage_index=i,
                            error=result.error,
                        )
                        # Retry logic could be added here
                    else:
                        self.logger.error(
                            "sequential_stage_failed",
                            task_id=task.id,
                            stage_index=i,
                            error=result.error,
                        )
                        return result

                # Accumulate context
                if result.output:
                    context[f"stage_{i}_output"] = result.output
                    if isinstance(result.output, dict):
                        context.update(result.output)

                # Add insights
                if result.insights:
                    context.setdefault("insights", []).extend(result.insights)

                self.logger.info(
                    "sequential_stage_complete",
                    task_id=task.id,
                    stage_index=i,
                    execution_time_ms=stage_time,
                    status=result.status.value if hasattr(result.status, 'value') else result.status,
                )

            except asyncio.TimeoutError:
                self.logger.error(
                    "sequential_stage_timeout",
                    task_id=task.id,
                    stage_index=i,
                    timeout=stage.timeout_seconds,
                )
                return Result(
                    task_id=task.id,
                    status=ResultStatus.FAILED,
                    error=f"Stage {i} timed out after {stage.timeout_seconds}s",
                )

            except Exception as e:
                self.logger.error(
                    "sequential_stage_error",
                    task_id=task.id,
                    stage_index=i,
                    error=str(e),
                )
                return Result(
                    task_id=task.id,
                    status=ResultStatus.FAILED,
                    error=str(e),
                )

        # Build final result
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)

        final_result = Result(
            task_id=task.id,
            status=ResultStatus.SUCCESS,
            output={
                "stages_completed": len(stages),
                "accumulated_context": context,
                "stage_results": [
                    {
                        "status": r.status.value if hasattr(r.status, 'value') else r.status,
                        "output": r.output,
                    }
                    for r in results
                ],
            },
            execution_time_ms=total_time,
            insights=context.get("insights", []),
        )

        # Collect next tasks from all stages
        for r in results:
            if r.next_tasks:
                final_result.next_tasks.extend(r.next_tasks)

        self.logger.info(
            "sequential_pipeline_complete",
            task_id=task.id,
            total_execution_time_ms=total_time,
            stages_completed=len(stages),
        )

        return final_result

    async def _execute_stage_with_timeout(
        self,
        adapter: Any,
        task: Task,
        context: Dict[str, Any],
        timeout: int,
    ) -> Result:
        """Execute stage with timeout"""
        return await asyncio.wait_for(
            adapter.execute(task, context),
            timeout=timeout,
        )


# Convenience function
async def run_sequential(
    task: Task,
    stages: List[Stage],
    context: Optional[Dict[str, Any]] = None,
) -> Result:
    """
    Run a sequential pipeline.

    Args:
        task: Task to execute
        stages: Stages to execute
        context: Initial context

    Returns:
        Final result
    """
    pipeline = SequentialPipeline()
    return await pipeline.execute(task, stages, context)
