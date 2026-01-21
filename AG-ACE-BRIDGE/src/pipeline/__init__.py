"""
Pipeline module for AG-ACE-BRIDGE

Provides pipeline execution patterns:
- Sequential: Execute stages in order
- Parallel: Execute agents simultaneously
- CriticLoop: Iterative refinement with feedback
"""

from .sequential import (
    SequentialPipeline,
    run_sequential,
)

from .parallel import (
    ParallelPipeline,
    ParallelFanOut,
    run_parallel,
)

from .critic_loop import (
    CriticLoopPipeline,
    CriticFeedback,
    run_critic_loop,
    run_auto_claude_qa_loop,
)

__all__ = [
    # Sequential
    "SequentialPipeline",
    "run_sequential",
    # Parallel
    "ParallelPipeline",
    "ParallelFanOut",
    "run_parallel",
    # Critic Loop
    "CriticLoopPipeline",
    "CriticFeedback",
    "run_critic_loop",
    "run_auto_claude_qa_loop",
]
