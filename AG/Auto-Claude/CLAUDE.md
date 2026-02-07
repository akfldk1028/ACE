# CLAUDE.md - AI Agent Context File

This is the AI agent context file for the **Auto-Claude** unified project.
All AI agents working in this codebase must read and follow this document.

---

## Critical Rules

### 8101 SharedMemory -- UI does NOT use it directly
- The Electron UI does NOT call 8101 SharedMemory. Only the CLI orchestrator uses it.
- `browser-mock.ts` sharedMemory* functions return empty values (no network requests).

### CORS Rules (Electron Frontend)
| Mode | API call method | File |
|------|----------------|------|
| Electron | `window.electronAPI.*` | a2a-handlers.ts (Main Process) |
| Browser | `fetch('/api/autogen/...')` | browser-mock.ts (Vite proxy) |
| Forbidden | `fetch('http://localhost:8081/...')` | Blocked by browser CORS! |

### Vite Proxy (electron.vite.config.ts)
```typescript
'/api/autogen' -> 'http://localhost:8081/api'
```

### AutoGen <-> Project Binding (2026-02)
- AutoGen sessions are filterable per project.
- AG-ACE-BRIDGE (8080) `/bridge/bindings/` API manages mapping.
- `getAutogenRunsDetailed(projectId)` returns sessions for that project only.
- Falls back to returning all sessions when Bridge is not running.
- 24/7 Auto-trigger auto-binds sessions.

---

## Project Overview

**Auto-Claude** is a unified autonomous coding platform combining:
1. **CLI Orchestrator** (`cli.py`) -- 24/7 factory coordinating 20 AI agents
2. **Electron Desktop UI** (`apps/frontend/`) -- Visual task management (Kanban, terminals)
3. **Python Backend** (`apps/backend/`) -- Agent logic (planner, coder, QA)

```
AutoGen Studio (8081)     <- Strategy/Design (CEO - decides WHAT to build)
    |
Auto-Claude               <- Pipeline/QA/UI (PM+DevOps - manages HOW to build)
  |- CLI (cli.py)            24/7 factory, 20 agents, 3 pipeline patterns
  |- Electron UI             Kanban, Agent Terminals, real-time AutoGen streaming
  |- Python Backend          Claude Agent SDK agents
    |
Claude Agent SDK /        <- Code Execution (Developer - WRITES the code)
Claude Code CLI
```

- **Location**: `D:\Data\25_ACE\AG\Auto-Claude\`
- **CLI entry point**: `cli.py`
- **UI entry point**: `npm run dev` (Electron)
- **Languages**: Python 3.13+ (CLI/backend), TypeScript/React (frontend)

---

## Architecture

### CLI: 4-Layer Architecture

**Coordinator -> Pipeline -> Adapters -> Registry + Memory**

```
+================================================================+
|                    Auto-Claude CLI                               |
|                   (4-Layer Architecture)                        |
+================================================================+
| Layer 1: Coordinator (24/7 Main Loop)                          |
|   ProjectWatcher -> TaskQueue (SQLite) -> AgentSelector        |
|   -> PipelineBuilder -> Orchestrator.execute()                 |
+----------------------------------------------------------------+
| Layer 2: Pipeline (Execution Patterns)                         |
|   Sequential | Parallel (Fan-Out/Gather) | CriticLoop (QA)    |
+----------------------------------------------------------------+
| Layer 3: Adapters (Agent Connections)                          |
|   AutoClaudeAdapter (OAuth) | AGAutogenAdapter (HTTP/A2A)     |
|   AGA2AAdapter (Google ADK) | AGLawDomainAdapter (REST)       |
|   AutogenStudioAdapter (HTTP)                                  |
+----------------------------------------------------------------+
| Layer 4: Registry + Memory                                     |
|   AgentRegistry (20 agents) | SharedMemoryClient (AG-CLI)     |
|   PatternRegistry (AutoGen Studio patterns)                    |
+================================================================+
```

### UI: 3-Tier Architecture

```
AutoGen Studio (8081)  ->  Auto-Claude Electron  ->  Claude SDK/CLI
   Strategy                 Pipeline + UI               Execution
```

#### Electron Mode
```
AutoGen Studio (8081)
        | HTTP (CORS ignored - Node.js)
Main Process (a2a-handlers.ts) -- sole 8081 caller
        | IPC (electronAPI)
Renderer Process (React UI)
```

#### Browser Mode (dev server localhost:5173)
```
AutoGen Studio (8081)
        |
Vite Dev Server (5173) -- proxy resolves CORS
  /api/autogen/* -> http://localhost:8081/api/*
        |
Browser (React UI) -- uses fetch('/api/autogen/...')
```

---

## Directory Structure

```
AG/Auto-Claude/
|-- cli.py                 # CLI entry point (24/7 factory)
|-- requirements.txt       # Python dependencies
|-- package.json           # Monorepo root (npm scripts)
|-- .env.example           # Environment variable template
|
|-- apps/
|   |-- backend/           # Python backend - ALL agent logic
|   |   |-- core/          # Client, auth, security
|   |   |-- agents/        # Agent implementations (planner, coder, QA)
|   |   |-- spec_agents/   # Spec creation agents
|   |   |-- integrations/  # Graphiti memory, Linear, GitHub
|   |   +-- prompts/       # Agent system prompts
|   +-- frontend/          # Electron desktop application
|       |-- src/main/      # Main process (IPC handlers, worktree mgmt)
|       |-- src/renderer/  # React UI (Kanban, terminals, settings)
|       +-- src/shared/    # Shared types, constants, i18n
|
|-- src/
|   |-- coordinator/       # Layer 1: 24/7 orchestration
|   |   |-- orchestrator.py     # Main loop
|   |   |-- task_queue.py       # SQLite priority queue
|   |   |-- agent_selector.py   # Score-based agent selection
|   |   +-- pipeline_builder.py # Dynamic pipeline construction
|   |
|   |-- pipeline/          # Layer 2: Execution patterns
|   |   |-- sequential.py       # Sequential execution
|   |   |-- parallel.py         # Parallel fan-out/gather
|   |   +-- critic_loop.py      # Generator-critic QA loop
|   |
|   |-- adapters/          # Layer 3: Agent connections (20 agents)
|   |   |-- base.py             # Abstract base (AgentAdapter)
|   |   |-- auto_claude.py      # Claude Agent SDK + OAuth
|   |   |-- ag_autogen.py       # HTTP/A2A Protocol
|   |   |-- ag_a2a_adapter.py   # Google ADK A2A Protocol
|   |   |-- ag_law_domain.py    # HTTP/FastAPI (law domain)
|   |   +-- autogen_studio_adapter.py  # AutoGen Studio integration
|   |
|   |-- bridge/            # WorkflowExecutor (spec_runner + run.py)
|   |-- agents/auto_claude/ # Agent implementations
|   |-- registry/          # Agent capabilities and patterns
|   |-- project/           # Spec, watcher, binding store
|   |-- memory/            # SharedMemory client
|   |-- modules/           # Auto-Claude prompts
|   +-- utils/             # Config, models, logger
|
|-- ag_cli/                # AG-CLI tools (SharedMemory, MessageBus)
|-- projects/              # Drop folder for project specs
|-- patterns/              # AutoGen Studio patterns
|-- data/                  # Runtime data (SQLite DB)
|-- scripts/               # Build and release utilities
|-- tests/                 # Test suite
|-- guides/                # Documentation
+-- .github/               # CI workflows
```

---

## Commands

### CLI (Python)

```bash
# 24/7 factory mode
python cli.py
python cli.py --debug

# Single task
python cli.py run --task "Build a calculator app" --complexity standard
python cli.py run -t "Fix the login bug" -c simple --auto-merge

# Project management
python cli.py submit --spec project.yaml
python cli.py list
python cli.py status <project_id>

# AG-CLI services
python cli.py services

# Example spec
python cli.py example
```

### Electron UI

```bash
# Install dependencies
npm run install:all

# Development
npm run dev          # Electron + hot reload (includes --remote-debugging-port=9222)

# Build
npm start            # Production build + run
npm run package      # Package for current platform
npm run package:win  # Package for Windows
npm run package:mac  # Package for macOS
npm run package:linux # Package for Linux
```

### Backend (Python Agents)

```bash
cd apps/backend

# Create spec interactively
python spec_runner.py --interactive

# Create spec from task description
python spec_runner.py --task "Add user authentication" --complexity standard

# Run autonomous build
python run.py --spec 001

# Review and merge
python run.py --spec 001 --review
python run.py --spec 001 --merge
```

### Testing

```bash
# Backend tests
apps/backend/.venv/bin/pytest tests/ -v
apps/backend/.venv/bin/pytest tests/ -m "not slow"

# Or from root
npm run test:backend
```

---

## Key Imports (CLI)

```python
# Coordinator (Layer 1)
from src.coordinator import Orchestrator, OrchestratorState, run_orchestrator
from src.coordinator import TaskQueue, TaskStatus, create_task_queue
from src.coordinator import AgentSelector, AgentSelection, get_selector
from src.coordinator import PipelineBuilder, PipelineTemplate, get_builder, build_pipeline

# Pipeline (Layer 2)
from src.pipeline import SequentialPipeline, run_sequential
from src.pipeline import ParallelPipeline, ParallelFanOut, run_parallel
from src.pipeline import CriticLoopPipeline, CriticFeedback, run_critic_loop, run_auto_claude_qa_loop

# Adapters (Layer 3)
from src.adapters import AutoClaudeAdapter, AGAutogenAdapter, AGA2AAdapter, AGLawDomainAdapter
from src.adapters import AutogenStudioAdapter, WorkflowResult, execute_pattern_with_autogen

# Bridge
from src.bridge import WorkflowExecutor, AutoClaudeRunner, AutogenToSpec

# Registry (Layer 4)
from src.registry import AgentRegistry, AgentStatus, get_registry, reset_registry
from src.registry import Capability, AgentCapabilities, find_best_agents

# Utils
from src.utils.config import get_settings, Settings
from src.utils.models import Task, Result, Pipeline, Stage, AgentType, TaskType
```

---

## 20 Agent Mapping

### Auto-Claude Agents (4) -- Claude Agent SDK + OAuth

| AgentType Enum | Value | Role | Adapter |
|----------------|-------|------|---------|
| `AUTO_CLAUDE_PLANNER` | `auto_claude.planner` | Project planning, task decomposition | AutoClaudeAdapter |
| `AUTO_CLAUDE_CODER` | `auto_claude.coder` | Code writing, implementation | AutoClaudeAdapter |
| `AUTO_CLAUDE_QA_REVIEWER` | `auto_claude.qa_reviewer` | Code review, quality validation | AutoClaudeAdapter |
| `AUTO_CLAUDE_QA_FIXER` | `auto_claude.qa_fixer` | Issue fixing, refactoring | AutoClaudeAdapter |

### AG Autogen Agents (5) -- HTTP/A2A Protocol

| AgentType Enum | Value | Role | Adapter |
|----------------|-------|------|---------|
| `AG_RESEARCH` | `ag.research` | Information gathering, web search | AGAutogenAdapter |
| `AG_ANALYST` | `ag.analyst` | Data analysis, pattern detection | AGAutogenAdapter |
| `AG_WRITER` | `ag.writer` | Document writing, content generation | AGAutogenAdapter |
| `AG_REVIEWER` | `ag.reviewer` | Review feedback, quality evaluation | AGAutogenAdapter |
| `AG_COORDINATOR` | `ag.coordinator` | Task coordination, routing | AGAutogenAdapter |

### AG Law Domain Agents (5) -- HTTP/REST (FastAPI)

| AgentType Enum | Value | Role | Adapter |
|----------------|-------|------|---------|
| `AG_CASE_ANALYZER` | `ag.case_analyzer` | Case analysis | AGLawDomainAdapter |
| `AG_LEGAL_RESEARCHER` | `ag.legal_researcher` | Legal research | AGLawDomainAdapter |
| `AG_RISK_ASSESSOR` | `ag.risk_assessor` | Risk assessment | AGLawDomainAdapter |
| `AG_COMPLIANCE_CHECKER` | `ag.compliance_checker` | Compliance checking | AGLawDomainAdapter |
| `AG_DOCUMENT_DRAFTER` | `ag.document_drafter` | Legal document drafting | AGLawDomainAdapter |

### AG A2A Protocol Agents (5) -- Google ADK A2A

| AgentType Enum | Value | Role | Port | Adapter |
|----------------|-------|------|------|---------|
| `AG_A2A_POETRY` | `ag.a2a.poetry_agent` | Poetry analysis | 8003 | AGA2AAdapter |
| `AG_A2A_PHILOSOPHY` | `ag.a2a.philosophy_agent` | Philosophical reasoning | 8004 | AGA2AAdapter |
| `AG_A2A_HISTORY` | `ag.a2a.history_agent` | Historical context | 8005 | AGA2AAdapter |
| `AG_A2A_CALCULATOR` | `ag.a2a.calculator_agent` | Mathematical computation | 8006 | AGA2AAdapter |
| `AG_A2A_GUI_TEST` | `ag.a2a.gui_test_agent` | GUI automation (PyAutoGUI) | 8120 | AGA2AAdapter |

### Claude Code CLI Agent (1) -- A2A Protocol

| AgentType Enum | Value | Role | Port |
|----------------|-------|------|------|
| `CLAUDE_CLI_PLAN` | `claude_cli.plan` | Code analysis, planning | 9018 |

---

## Pipeline Patterns

### 1. Sequential
```python
from src.pipeline import run_sequential
result = await run_sequential(task, stages=[
    Stage(agent=AgentType.AUTO_CLAUDE_PLANNER, stage_type=StageType.SEQUENTIAL),
    Stage(agent=AgentType.AUTO_CLAUDE_CODER, stage_type=StageType.SEQUENTIAL),
])
```

### 2. Parallel (Fan-Out/Gather)
```python
from src.pipeline import run_parallel
result = await run_parallel(task, agents=[
    AgentType.AG_RESEARCH, AgentType.AG_ANALYST,
], gather_strategy="merge")
```

### 3. CriticLoop (Generator-Critic QA)
```python
from src.pipeline import run_auto_claude_qa_loop
result = await run_auto_claude_qa_loop(task, max_iterations=5)
```

---

## Backend Agent Architecture (apps/backend/)

**CRITICAL: All AI interactions use Claude Agent SDK (`claude-agent-sdk`), NOT the Anthropic API directly.**

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| `core/client.py` | Claude SDK client factory with security hooks |
| `core/security.py` | Dynamic command allowlisting |
| `agents/` | planner, coder, qa_reviewer, qa_fixer |
| `spec_agents/` | gatherer, researcher, writer, critic |
| `integrations/graphiti/` | Graphiti memory (knowledge graph) |
| `cli/worktree.py` | Git worktree isolation |

### Spec Creation Pipeline (spec_runner.py)
- SIMPLE (3 phases): Discovery -> Quick Spec -> Validate
- STANDARD (6-7 phases): Discovery -> Requirements -> [Research] -> Context -> Spec -> Plan -> Validate
- COMPLEX (8 phases): Full pipeline with Research and Self-Critique

### Build Pipeline (run.py -> agent.py)
1. Planner Agent creates implementation plan
2. Coder Agent implements subtasks (can spawn subagents)
3. QA Reviewer validates acceptance criteria
4. QA Fixer resolves issues in a loop

---

## Frontend Development Guidelines

### i18n (Internationalization)
All user-facing text MUST use translation keys via `react-i18next`:
```tsx
const { t } = useTranslation(['navigation', 'common']);
<span>{t('navigation:items.githubPRs')}</span>  // Correct
<span>GitHub PRs</span>                          // Wrong
```

Translation files: `apps/frontend/src/shared/i18n/locales/{en,fr}/*.json`

### Cross-Platform
Platform-specific code lives in dedicated modules:
- Frontend: `apps/frontend/src/main/platform/`
- Backend: `apps/backend/core/platform/`

Use `isWindows()`, `findExecutable()` etc. instead of raw `process.platform` checks.

---

## A2A Integration & AutoGen Studio

### Key Files (UI side)

| File | Role |
|------|------|
| `a2a-handlers.ts` | Main Process: sole 8081 caller |
| `a2a-api.ts` | Preload API (IPC) |
| `AutogenCollabPanel.tsx` | Agent Terminals collaboration panel |
| `KanbanBoard.tsx` | AutoGen session -> Task card conversion |
| `AutogenStatusBadge.tsx` | Connection status + NEW badge |
| `browser-mock.ts` | Browser mode fallback |

### Project Binding (IPC channels)

| Channel | Description |
|---------|-------------|
| `AUTOGEN_GET_RUNS_DETAILED` | Filter by projectId |
| `AUTOGEN_BIND_SESSION` | Bind session to project |
| `AUTOGEN_UNBIND_SESSION` | Unbind session |
| `AUTOGEN_GET_UNBOUND_SESSIONS` | List unbound sessions |

---

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| AG-ACE Dashboard | 8080 | Bridge monitoring (legacy, optional) |
| AutoGen Studio | 8081 | Web-based agent builder |
| MessageBus | 8100 | Agent-to-agent message routing |
| SharedMemory | 8101 | Shared state server |
| Poetry Agent | 8003 | A2A demo agent |
| Philosophy Agent | 8004 | A2A demo agent |
| History Agent | 8005 | A2A demo agent |
| Calculator Agent | 8006 | A2A demo agent |
| GUI Test Agent | 8120 | A2A GUI automation agent |
| Claude CLI Plan | 9018 | Claude Code CLI A2A agent |
| Vite Dev Server | 5173 | Frontend dev (browser mode) |

---

## Configuration

Settings loaded from `.env` via `pydantic-settings`. Access with `get_settings()`.

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_CLAUDE_PATH` | `./apps/backend` (relative) | Path to backend |
| `SHARED_MEMORY_URL` | `http://localhost:8101` | SharedMemory URL |
| `AG_AUTOGEN_URL` | `http://localhost:8000` | AG Autogen URL |
| `AG_LAW_DOMAIN_URL` | `http://localhost:8001` | AG Law Domain URL |
| `ADAPTER_TIMEOUT` | `120.0` | HTTP timeout (seconds) |
| `QUEUE_DB_PATH` | `./data/tasks.db` | SQLite queue path |
| `PROJECTS_DIR` | `./projects` | Project drop folder |
| `MAX_QA_ITERATIONS` | `5` | Max QA loop iterations |
| `ANTHROPIC_API_KEY` | (none) | For Claude SDK |
| `GRAPHITI_ENABLED` | `true` | Enable Graphiti memory |

---

## Security Model

Three-layer defense:
1. **OS Sandbox** -- Bash command isolation
2. **Filesystem Permissions** -- Operations restricted to project directory
3. **Command Allowlist** -- Dynamic allowlist from project analysis

All agent work happens in isolated git worktrees. Main branch is never touched until explicit merge.

---

## Mandatory Rules

1. **Documentation Sync** -- Update docs when changing code/APIs
2. **Import Conventions** -- Import from module `__init__.py`, not internal files
3. **Adapter Pattern** -- All adapters inherit `AgentAdapter`, implement `execute()` + `health_check()`
4. **Error Handling** -- Use `Result(success=False, error="...")`, never raise unhandled exceptions
5. **Context Accumulation** -- Sequential pipelines: `context["stage_N_output"]`, never mutate originals
6. **i18n** -- All frontend text uses translation keys
7. **Platform** -- Use platform abstraction modules, not raw `process.platform`
8. **CORS** -- Electron: IPC, Browser: Vite proxy. Never direct fetch to 8081 from browser.

---

## Contributing to Upstream

**When submitting PRs to AndyMik90/Auto-Claude, always target `develop` branch, NOT `main`.**

```bash
git fetch upstream
git checkout -b fix/my-fix upstream/develop
git commit -s -m "fix: description"
git push origin fix/my-fix
gh pr create --repo AndyMik90/Auto-Claude --base develop
```
