# agents -- Agent Implementations

Concrete agent implementations used within pipelines. Contains the Auto-Claude agent family for planning, coding, review, and automated fixing.

## Structure

```
agents/
  auto_claude/
    base.py          -- Shared Auto-Claude agent base class
    planner.py       -- Task decomposition and planning
    coder.py         -- Code generation and modification
    qa_reviewer.py   -- Automated quality review
    qa_fixer.py      -- Automated fix application from review feedback
```

## Key Classes

| Name | Location | Description |
|---|---|---|
| `AutoClaudePlanner` | auto_claude/planner.py | Breaks project specs into ordered subtasks |
| `AutoClaudeCoder` | auto_claude/coder.py | Generates or modifies code from subtask specs |
| `AutoClaudeQAReviewer` | auto_claude/qa_reviewer.py | Reviews code for correctness, style, security |
| `AutoClaudeQAFixer` | auto_claude/qa_fixer.py | Applies fixes based on reviewer feedback |

## Usage

```python
from src.agents.auto_claude.planner import AutoClaudePlanner
from src.agents.auto_claude.coder import AutoClaudeCoder

planner = AutoClaudePlanner()
plan = await planner.run(project_spec)

coder = AutoClaudeCoder()
result = await coder.run(plan.subtasks[0])
```

## Notes

- All agents in `auto_claude/` share a common base from `base.py`.
- The typical pipeline is: Planner -> Coder -> QAReviewer -> QAFixer (critic loop).
- Agents are registered in `AgentRegistry` and selected by `AgentSelector`.
