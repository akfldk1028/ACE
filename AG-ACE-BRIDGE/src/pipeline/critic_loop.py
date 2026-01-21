"""
Critic Loop Pipeline for AG-ACE-BRIDGE

Iterative refinement using Generator-Critic pattern.
Based on Google ADK Generator-Critic Loop pattern.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

from src.utils.models import (
    Task, Result, ResultStatus, AgentType
)
from src.utils.logger import Loggers
from src.utils.config import get_settings
from src.registry.agent_registry import get_registry


@dataclass
class CriticFeedback:
    """Feedback from critic agent"""
    passed: bool
    score: float  # 0.0 to 1.0
    issues: List[str]
    suggestions: List[str]
    details: Dict[str, Any]


class CriticLoopPipeline:
    """
    Generator-Critic loop executor.

    Iteratively refines output using a critic for feedback.
    Used for QA loops in Auto-Claude.

    Flow:
    ┌─────────────────────────────────────────┐
    │                                         │
    │  Generator → Critic → Pass? ──Yes──→ Done
    │      ↑          │
    │      └──No──────┘
    │     (with feedback)
    │                                         │
    └─────────────────────────────────────────┘

    Example:
        loop = CriticLoopPipeline(
            generator=AgentType.AUTO_CLAUDE_CODER,
            critic=AgentType.AUTO_CLAUDE_QA_REVIEWER,
            fixer=AgentType.AUTO_CLAUDE_QA_FIXER,
        )

        result = await loop.execute(task)
    """

    def __init__(
        self,
        generator: AgentType,
        critic: AgentType,
        fixer: Optional[AgentType] = None,
        max_iterations: int = 5,
        pass_threshold: float = 0.8,
    ):
        """
        Initialize critic loop.

        Args:
            generator: Agent that generates output
            critic: Agent that reviews output
            fixer: Agent that fixes issues (optional, defaults to generator)
            max_iterations: Maximum refinement iterations
            pass_threshold: Minimum score to pass (0.0 to 1.0)
        """
        self.generator = generator
        self.critic = critic
        self.fixer = fixer or generator
        self.max_iterations = max_iterations
        self.pass_threshold = pass_threshold

        self.logger = Loggers.pipeline()
        self.registry = get_registry()
        self.settings = get_settings()

    async def execute(
        self,
        task: Task,
        context: Optional[Dict[str, Any]] = None,
        feedback_parser: Optional[Callable[[Dict], CriticFeedback]] = None,
    ) -> Result:
        """
        Execute generator-critic loop.

        Args:
            task: Task to execute
            context: Initial context
            feedback_parser: Custom parser for critic feedback

        Returns:
            Final result after passing or max iterations
        """
        context = context or {}
        context["task"] = {
            "id": task.id,
            "type": task.type if isinstance(task.type, str) else task.type.value,
            "description": task.description,
        }

        start_time = datetime.now()
        self.logger.info(
            "critic_loop_start",
            task_id=task.id,
            generator=self.generator.value,
            critic=self.critic.value,
            max_iterations=self.max_iterations,
        )

        iteration = 0
        current_output = None
        iteration_history = []

        while iteration < self.max_iterations:
            iteration += 1
            iteration_start = datetime.now()

            self.logger.info(
                "critic_loop_iteration",
                task_id=task.id,
                iteration=iteration,
            )

            # Step 1: Generate (or fix if not first iteration)
            if iteration == 1:
                gen_result = await self._run_generator(task, context)
            else:
                # Use fixer with previous feedback
                gen_result = await self._run_fixer(task, context)

            if gen_result.status == ResultStatus.FAILED:
                return gen_result

            current_output = gen_result.output

            # Step 2: Critique
            critic_context = {
                **context,
                "generated_output": current_output,
                "iteration": iteration,
            }

            critic_result = await self._run_critic(task, critic_context)

            if critic_result.status == ResultStatus.FAILED:
                self.logger.error(
                    "critic_failed",
                    task_id=task.id,
                    iteration=iteration,
                    error=critic_result.error,
                )
                # Continue with previous output
                break

            # Parse feedback
            if feedback_parser:
                feedback = feedback_parser(critic_result.output)
            else:
                feedback = self._parse_default_feedback(critic_result.output)

            iteration_time = int((datetime.now() - iteration_start).total_seconds() * 1000)

            iteration_history.append({
                "iteration": iteration,
                "score": feedback.score,
                "passed": feedback.passed,
                "issues_count": len(feedback.issues),
                "execution_time_ms": iteration_time,
            })

            self.logger.info(
                "critic_loop_feedback",
                task_id=task.id,
                iteration=iteration,
                score=feedback.score,
                passed=feedback.passed,
                issues_count=len(feedback.issues),
            )

            # Check if passed
            if feedback.passed or feedback.score >= self.pass_threshold:
                total_time = int((datetime.now() - start_time).total_seconds() * 1000)

                self.logger.info(
                    "critic_loop_passed",
                    task_id=task.id,
                    iteration=iteration,
                    final_score=feedback.score,
                )

                return Result(
                    task_id=task.id,
                    status=ResultStatus.SUCCESS,
                    output={
                        "final_output": current_output,
                        "final_score": feedback.score,
                        "iterations": iteration,
                        "iteration_history": iteration_history,
                    },
                    execution_time_ms=total_time,
                    insights=[
                        f"Passed after {iteration} iteration(s)",
                        f"Final score: {feedback.score:.2f}",
                    ],
                )

            # Update context with feedback for next iteration
            context["previous_output"] = current_output
            context["critic_feedback"] = {
                "score": feedback.score,
                "issues": feedback.issues,
                "suggestions": feedback.suggestions,
                "details": feedback.details,
            }
            context["iteration"] = iteration

        # Max iterations reached without passing
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)

        self.logger.warning(
            "critic_loop_max_iterations",
            task_id=task.id,
            iterations=iteration,
        )

        return Result(
            task_id=task.id,
            status=ResultStatus.PARTIAL,
            output={
                "final_output": current_output,
                "max_iterations_reached": True,
                "iterations": iteration,
                "iteration_history": iteration_history,
            },
            execution_time_ms=total_time,
            insights=[
                f"Max iterations ({self.max_iterations}) reached",
                "Output may need manual review",
            ],
        )

    async def _run_generator(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Result:
        """Run generator agent"""
        adapter = self.registry.get_adapter(self.generator)
        if not adapter:
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"Generator adapter not found: {self.generator.value}",
            )

        self.registry.mark_busy(self.generator, task.id)
        start_time = datetime.now()

        try:
            result = await adapter.execute(task, context)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.status == ResultStatus.SUCCESS:
                self.registry.record_success(self.generator, execution_time)
            else:
                self.registry.record_failure(self.generator)

            return result

        except Exception as e:
            self.registry.record_failure(self.generator)
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=str(e),
            )

    async def _run_fixer(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Result:
        """Run fixer agent with feedback"""
        adapter = self.registry.get_adapter(self.fixer)
        if not adapter:
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"Fixer adapter not found: {self.fixer.value}",
            )

        self.registry.mark_busy(self.fixer, task.id)
        start_time = datetime.now()

        try:
            result = await adapter.execute(task, context)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.status == ResultStatus.SUCCESS:
                self.registry.record_success(self.fixer, execution_time)
            else:
                self.registry.record_failure(self.fixer)

            return result

        except Exception as e:
            self.registry.record_failure(self.fixer)
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=str(e),
            )

    async def _run_critic(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Result:
        """Run critic agent"""
        adapter = self.registry.get_adapter(self.critic)
        if not adapter:
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"Critic adapter not found: {self.critic.value}",
            )

        self.registry.mark_busy(self.critic, task.id)
        start_time = datetime.now()

        try:
            result = await adapter.execute(task, context)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.status == ResultStatus.SUCCESS:
                self.registry.record_success(self.critic, execution_time)
            else:
                self.registry.record_failure(self.critic)

            return result

        except Exception as e:
            self.registry.record_failure(self.critic)
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=str(e),
            )

    def _parse_default_feedback(self, output: Any) -> CriticFeedback:
        """Parse feedback from critic output using default format"""
        if not isinstance(output, dict):
            return CriticFeedback(
                passed=False,
                score=0.0,
                issues=["Unable to parse critic output"],
                suggestions=[],
                details={"raw_output": output},
            )

        # Extract fields with defaults
        passed = output.get("passed", output.get("review_passed", False))
        score = output.get("score", 0.0)

        # Calculate score from test results if available
        if "test_results" in output:
            tests = output["test_results"]
            total = tests.get("total", 0)
            passed_tests = tests.get("passed", 0)
            if total > 0:
                score = passed_tests / total

        issues = output.get("issues", output.get("issues_found", []))
        suggestions = output.get("suggestions", output.get("recommendations", []))

        return CriticFeedback(
            passed=passed,
            score=score,
            issues=issues if isinstance(issues, list) else [],
            suggestions=suggestions if isinstance(suggestions, list) else [],
            details=output,
        )


# Convenience function
async def run_critic_loop(
    task: Task,
    generator: AgentType,
    critic: AgentType,
    fixer: Optional[AgentType] = None,
    max_iterations: int = 5,
    context: Optional[Dict[str, Any]] = None,
) -> Result:
    """
    Run a generator-critic loop.

    Args:
        task: Task to execute
        generator: Generator agent
        critic: Critic agent
        fixer: Fixer agent (defaults to generator)
        max_iterations: Maximum iterations
        context: Initial context

    Returns:
        Final result
    """
    loop = CriticLoopPipeline(
        generator=generator,
        critic=critic,
        fixer=fixer,
        max_iterations=max_iterations,
    )
    return await loop.execute(task, context)


# Auto-Claude specific QA loop
async def run_auto_claude_qa_loop(
    task: Task,
    context: Optional[Dict[str, Any]] = None,
    max_iterations: Optional[int] = None,
) -> Result:
    """
    Run Auto-Claude specific QA loop.

    Uses:
    - Coder as generator
    - QA Reviewer as critic
    - QA Fixer as fixer

    Args:
        task: Task to execute
        context: Initial context
        max_iterations: Override max iterations

    Returns:
        Final result
    """
    settings = get_settings()

    loop = CriticLoopPipeline(
        generator=AgentType.AUTO_CLAUDE_CODER,
        critic=AgentType.AUTO_CLAUDE_QA_REVIEWER,
        fixer=AgentType.AUTO_CLAUDE_QA_FIXER,
        max_iterations=max_iterations or settings.max_qa_iterations,
    )

    return await loop.execute(task, context)
