# pipeline -- Pipeline Execution Patterns

Defines the three core execution patterns used by the orchestrator to run agent workflows: sequential, parallel, and critic-loop.

## Files

| File | Purpose |
|---|---|
| `sequential.py` | Agents execute one after another, each receiving the previous result |
| `parallel.py` | Agents execute concurrently via asyncio.gather, results are merged |
| `critic_loop.py` | Iterative generate-then-critique loop until quality threshold is met |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `SequentialPipeline` | sequential.py | Chain of stages executed in order with context accumulation |
| `run_sequential(task, stages)` | sequential.py | Convenience function for one-shot execution |
| `ParallelPipeline` | parallel.py | Fan-out / fan-in execution with configurable gather strategy |
| `run_parallel(task, agents)` | parallel.py | Convenience function for parallel dispatch |
| `CriticLoopPipeline` | critic_loop.py | Generator + critic + fixer with configurable max iterations |
| `run_critic_loop(task, gen, critic)` | critic_loop.py | Convenience function for a single critic loop |

## Usage

```python
from src.pipeline.sequential import SequentialPipeline
from src.pipeline.critic_loop import CriticLoopPipeline, run_auto_claude_qa_loop

# Sequential: planner -> coder -> reviewer
pipe = SequentialPipeline(stages=[planner_stage, coder_stage, reviewer_stage])
result = await pipe.execute(task, stages)

# Critic loop: coder generates, reviewer critiques, fixer applies fixes
loop = CriticLoopPipeline(generator=coder, critic=reviewer, fixer=fixer, max_iterations=5)
result = await loop.execute(task)

# Auto-Claude QA shortcut (coder + qa_reviewer + qa_fixer)
result = await run_auto_claude_qa_loop(task, context)
```

## Notes

- All pipelines share a common `execute(task, context) -> Result` interface.
- `PipelineBuilder` in the coordinator module selects the appropriate pattern automatically.
- Parallel pipelines support gather strategies: merge, list, first_success, majority.
- Critic loop defaults to `pass_threshold=0.8` and `max_iterations=5`.
