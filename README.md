# 25_ACE

AI Agent Coordination Ecosystem - 24/7 AI Project Factory

## Overview

```
+-----------------------------------------------------------------------+
|                         25_ACE ECOSYSTEM                               |
|                    AI Agent Coordination Ecosystem                     |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-------------------+                      +-------------------+     |
|  |   Auto-Claude     |                      |       AG          |     |
|  |   24/7 Engine     |                      |  Multi-Agent      |     |
|  |                   |                      |                   |     |
|  |  * Planner        |    AG-ACE-BRIDGE    |  * autogen_a2a    |     |
|  |  * Coder (24/7)   |<------------------->|    (10 agents)    |     |
|  |  * QA Reviewer    |                      |  * law-domain     |     |
|  |  * QA Fixer       |                      |    (5 agents)     |     |
|  +-------------------+                      +-------------------+     |
|          |                                          |                 |
|          v                                          v                 |
|  +-------------------+                      +-------------------+     |
|  |    Graphiti       |        Sync          |     Neo4j         |     |
|  |   (LadybugDB)     |<-------------------->|  Knowledge        |     |
|  +-------------------+                      +-------------------+     |
|                                                                       |
|  Total: 19 Coordinated Agents                                         |
|                                                                       |
+-----------------------------------------------------------------------+
```

## Triple UI Architecture

**3개의 UI를 함께 실행**하여 Task 관리, Pattern 개발, 운영을 분리합니다:

```
+-----------------------------------------------------------------------------+
|                         TRIPLE UI ARCHITECTURE                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +---------------------+  +---------------------+  +---------------------+  |
|  |    Auto-Claude      |  |   AutoGen Studio    |  |   AG-ACE-BRIDGE    |  |
|  |    (Electron)       |  |      (Web)          |  |    Dashboard       |  |
|  |                     |  |                     |  |      (Web)         |  |
|  |  [Task Management]  |  |  [Pattern Dev]      |  |  [Operations]      |  |
|  |                     |  |                     |  |                    |  |
|  |  * SPEC Creation    |  |  * Pattern Gallery  |  |  * 24/7 Queue      |  |
|  |  * Task Queue       |  |  * Team Config      |  |  * Orchestrator    |  |
|  |  * Execution View   |  |  * A2A Testing      |  |  * Agent Status    |  |
|  |  * GitHub/Linear    |  |  * Drag & Drop      |  |  * Memory Sync     |  |
|  |                     |  |                     |  |                    |  |
|  |  npm run dev        |  |  autogenstudio ui   |  |  python main.py    |  |
|  |  (Electron App)     |  |  (Port 8081)        |  |  (Port 8080)       |  |
|  +---------------------+  +---------------------+  +---------------------+  |
|           |                        |                        |               |
|           +------------------------+------------------------+               |
|                                    |                                        |
|                    +---------------v---------------+                        |
|                    |      Shared Infrastructure    |                        |
|                    |   A2A Agents (8003-8120)      |                        |
|                    |   SharedMemory (8101)         |                        |
|                    |   Neo4j / Graphiti            |                        |
|                    +-------------------------------+                        |
|                                                                             |
+-----------------------------------------------------------------------------+
```

| UI | Type | Port | Purpose | When to Use |
|----|------|------|---------|-------------|
| **Auto-Claude** | Electron | - | Task management, SPEC creation, GitHub/Linear | Creating tasks, Monitoring execution |
| **AutoGen Studio** | Web | 8081 | Pattern development, Team config, A2A testing | Developing patterns, Agent experiments |
| **AG-ACE-BRIDGE** | Web | 8080 | 24/7 orchestration, Agent coordination | Running 24/7 operations, Status monitoring |

## Quick Start

### 1. Start All Services

```bash
# Terminal 1: A2A Agents
cd AG/autogen_a2a_kit/a2a_demo
python run_all_agents.py  # 8003-8120

# Terminal 2: SharedMemory
cd AG/autogen_a2a_kit/AG-cli
python shared_memory_server.py  # 8101

# Terminal 3: AutoGen Studio (Optional - Development)
cd AG/autogen_a2a_kit/autogen_source
npm run dev  # 8081

# Terminal 4: AG-ACE-BRIDGE (Main Operations)
cd AG-ACE-BRIDGE
python main.py  # 8080 + Orchestrator
```

### 2. Access Dashboards

- **Operations**: http://localhost:8080 (AG-ACE-BRIDGE)
- **Development**: http://localhost:8081 (AutoGen Studio)

### 3. Submit a Project

```bash
# Via CLI
cd AG-ACE-BRIDGE
python -m src.coordinator.orchestrator --spec "Build a REST API"

# Or via Dashboard
# Open http://localhost:8080 -> Submit New Task
```

## Projects

| Project | Description | Docs |
|---------|-------------|------|
| [Auto-Claude](Auto-Claude/) | 24/7 Autonomous Coding Framework | [README_INDEX](Auto-Claude/README_INDEX.md) |
| [AG](AG/) | Multi-Agent System Hub | [README.md](AG/README.md) |
| [AG-ACE-BRIDGE](AG-ACE-BRIDGE/) | Auto-Claude + AG Integration Bridge | [README_INDEX](AG-ACE-BRIDGE/README_INDEX.md) |
| [Calculator](Calculator/) | Example Project (Agent Demo) | - |

## Complete Workflow Example

**GitHub Issue -> PR Merge 완전 자동화 예시**: [WORKFLOW_EXAMPLE.md](docs/WORKFLOW_EXAMPLE.md)

```
GitHub Issue #42: "Calculator에 퍼센트 기능 추가"
    |
    v
+--------+   +--------+   +--------+   +--------+   +--------+
|  SPEC  | > |  PLAN  | > |  CODE  | > |   QA   | > | MERGE  |
| 30min  |   | 15min  |   |  2hr   |   | 30min  |   |  5min  |
+--------+   +--------+   +--------+   +--------+   +--------+
    |            |            |            |            |
AG Selector  AG Magentic  Auto-Claude  AG Reflection  Auto PR
+ Research   Orchestrator Coder 24/7   + gui_test     Creation

Total: ~3.5 hours (Fully Automated)
```

## Architecture

### Core Concepts

1. **Auto-Claude**: 24/7 Autonomous Coding Engine
   - SPEC -> PLAN -> CODE -> QA -> MERGE pipeline
   - `while True:` infinite loop for autonomous operation
   - Claude Agent SDK based

2. **AG**: Multi-Agent Expert Teams
   - autogen_a2a_kit: 10 A2A protocol agents
   - law-domain-agents: 5 legal domain agents
   - 11 MAS patterns (Sequential, Selector, Swarm, Debate, etc.)

3. **AG-ACE-BRIDGE**: Integration Bridge
   - Central Orchestrator for 19 agents
   - Pattern-based task routing
   - Graphiti <-> Neo4j memory sync

### Flow Model Integration

```
+-----------------------------------------------------------------------------+
|                    UNIFIED FLOW MODEL ARCHITECTURE                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|  [Phase 1: Task Intake]                                                     |
|  +---------------------------------------------------------------------+   |
|  |  GitHub Issues/PRs  ->  Auto-Claude SPEC  ->  Task Queue             |   |
|  |  Linear Tasks       ->  Planner Agent    ->  Subtask Decomposition   |   |
|  +---------------------------------------------------------------------+   |
|                                      |                                      |
|                                      v                                      |
|  [Phase 2: MAS Pattern Selection]                                          |
|  +---------------------------------------------------------------------+   |
|  |  AG autogen_a2a_kit Patterns:                                        |   |
|  |  +-- Sequential (01): Linear conversation -> Simple pipeline         |   |
|  |  +-- Selector  (03): LLM selects next agent -> Dynamic routing       |   |
|  |  +-- Swarm     (05): Agent handoffs -> Complex delegation            |   |
|  |  +-- Debate    (07): Discussion/rebuttal -> Code review              |   |
|  |  +-- Reflection(08): Worker+Reviewer -> QA loop                      |   |
|  |  +-- Magentic  (06): Orchestrator -> Large-scale distribution        |   |
|  +---------------------------------------------------------------------+   |
|                                      |                                      |
|                                      v                                      |
|  [Phase 3: Agent Execution]                                                |
|  +---------------------------------------------------------------------+   |
|  |  Auto-Claude Pipeline:                AG A2A Agents:                 |   |
|  |  +-- Planner   (plan)     <------>  +-- research_agent               |   |
|  |  +-- Coder     (impl 24/7)<------>  +-- calculator_agent             |   |
|  |  +-- QA Reviewer (verify) <------>  +-- philosophy_agent             |   |
|  |  +-- QA Fixer  (fix)      <------>  +-- gui_test_agent (PyAutoGUI)   |   |
|  +---------------------------------------------------------------------+   |
|                                      |                                      |
|                                      v                                      |
|  [Phase 4: Memory & Sync]                                                  |
|  +---------------------------------------------------------------------+   |
|  |  Graphiti (LadybugDB)           <------->          Neo4j             |   |
|  |  +-- Code Patterns              <------->   +-- Domain Knowledge     |   |
|  |  +-- Session Insights           <------->   +-- Legal Rules          |   |
|  |  +-- Project Context            <------->   +-- Compliance           |   |
|  +---------------------------------------------------------------------+   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Pattern-Pipeline Mapping

| Auto-Claude Stage | Recommended AG Pattern | Use Case |
|-------------------|------------------------|----------|
| SPEC Generation | Selector | Dynamic selection of expert agents |
| PLAN Creation | Magentic | Orchestrator distributes work |
| CODE Implementation | Sequential / Swarm | Linear or complex delegation |
| QA Validation | Reflection / Debate | Reviewer pattern, discussion |
| MERGE | Sequential | Final merge confirmation |

## Agent Registry (19 Agents)

### Auto-Claude (4)
| Agent | Function |
|-------|----------|
| Planner | Implementation planning, subtask decomposition |
| Coder | 24/7 autonomous coding |
| QA Reviewer | E2E testing, quality verification |
| QA Fixer | Issue fixing, debugging |

### AG autogen_a2a_kit (10 A2A Agents)
| Agent | Port | Function |
|-------|------|----------|
| poetry_agent | 8003 | Poetry/Literature |
| philosophy_agent | 8004 | Philosophy |
| history_agent | 8005 | History |
| calculator_agent | 8006 | Calculation |
| math_agent | 8007 | Mathematics |
| graphics_agent | 8008 | Graphics |
| gpu_agent | 8009 | GPU Computing |
| research_agent | 8010 | Research |
| code_agent | 8011 | Code Analysis |
| gui_test_agent | 8120 | GUI Automation (PyAutoGUI) |

### AG law-domain (5)
| Agent | Function |
|-------|----------|
| Case Analyzer | Case law analysis |
| Legal Researcher | Legal research |
| Risk Assessor | Risk assessment |
| Compliance Checker | Compliance verification |
| Document Drafter | Legal document drafting |

## Directory Structure

```
D:/Data/25_ACE/
|
+-- Auto-Claude/              # 24/7 Autonomous Coding
|   +-- apps/backend/         # Python Backend
|   +-- apps/frontend/        # Electron Frontend
|   +-- CLAUDE.md             # Claude Code Guide
|   +-- README_INDEX.md       # Documentation Index
|
+-- AG/                       # Multi-Agent System Hub
|   +-- agent/                # 18+ Agent Projects
|   |   +-- law-domain-agents/# Legal Domain Agents
|   |   +-- README_INDEX.md   # Documentation Index
|   +-- autogen_a2a_kit/      # AutoGen + A2A Integration
|   |   +-- a2a_demo/         # 10 A2A Agents
|   |   +-- AG_Cohub/         # Pattern Gallery (12 patterns)
|   |   +-- AG-cli/           # Claude CLI Collaboration
|   +-- agent_core/           # Shared Libraries
|   +-- README_INDEX.md       # Documentation Index
|
+-- AG-ACE-BRIDGE/            # Integration Bridge
|   +-- main.py               # Main Entry Point
|   +-- src/                  # Source Code
|   |   +-- coordinator/      # 24/7 Orchestrator
|   |   +-- pipeline/         # Execution Flow
|   |   +-- adapters/         # Agent Adapters
|   |   +-- memory/           # Memory Sync
|   |   +-- server/           # Dashboard Server
|   +-- docs/ARCHITECTURE.md  # Detailed Architecture
|   +-- README_INDEX.md       # Documentation Index
|
+-- docs/
|   +-- WORKFLOW_EXAMPLE.md   # Complete Project Example
|
+-- ARCHITECTURE.md           # Overall Architecture
+-- README.md                 # This File
```

## Use Cases

### 1. Legal Software Development
```
AG Legal Research -> Auto-Claude SPEC -> CODE -> AG Compliance -> QA -> MERGE
Pattern: Selector (legal expert selection) + Reflection (compliance review)
```

### 2. Research-Based Development
```
AG Research -> AG Analyst -> Auto-Claude Full Pipeline
Pattern: Sequential (research->analysis->implementation) + Debate (approach discussion)
```

### 3. 24/7 GitHub Automation
```
GitHub Issue -> Auto-Claude SPEC -> Planner -> Coder(24/7) -> QA -> PR
Pattern: Magentic (orchestrator-based work distribution)
```

### 4. Complex Domain Integration
```
AG law-domain + AG autogen_a2a_kit -> AG-ACE-BRIDGE -> Auto-Claude
Pattern: Swarm (domain expert handoffs) + Selector (dynamic routing)
```

## Requirements

- Python 3.10+
- Node.js 18+ (Auto-Claude frontend)
- Neo4j (AG law-domain)
- Claude API Key (ANTHROPIC_API_KEY)
- OpenAI API Key (AG)

## Documentation

| Document | Description |
|----------|-------------|
| [AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md) | **AI용 시작 가이드 - 서버 시작 순서, 2 UI 운영** |
| [PROJECT_START_GUIDE.md](docs/PROJECT_START_GUIDE.md) | 3 UI coordination guide - How to use all UIs together |
| [WORKFLOW_EXAMPLE.md](docs/WORKFLOW_EXAMPLE.md) | Complete project workflow (GitHub Issue -> PR) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Overall system architecture |
| [Auto-Claude CLAUDE.md](Auto-Claude/CLAUDE.md) | Auto-Claude core guide |
| [AG-ACE-BRIDGE Architecture](AG-ACE-BRIDGE/docs/ARCHITECTURE.md) | Bridge detailed design |

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| AG-ACE-BRIDGE Dashboard | 8080 | Operations monitoring |
| AutoGen Studio | 8081 | Pattern development |
| SharedMemory | 8101 | Context sharing |
| poetry_agent | 8003 | A2A agent |
| philosophy_agent | 8004 | A2A agent |
| history_agent | 8005 | A2A agent |
| calculator_agent | 8006 | A2A agent |
| math_agent | 8007 | A2A agent |
| graphics_agent | 8008 | A2A agent |
| gpu_agent | 8009 | A2A agent |
| gui_test_agent | 8120 | E2E testing |

## Agent Collaboration & Data Flow

### Design vs Execution Architecture

The system separates **design** (AutoGen Studio) from **execution** (Auto-Claude + AG-ACE-BRIDGE):

```
+-----------------------------------------------------------------------------+
|                     DESIGN → EXECUTION ARCHITECTURE                          |
|                    ★ 직접 연결 - 중간 서버 불필요!                             |
+-----------------------------------------------------------------------------+
|                                                                             |
|  ┌─────────────────────────────────┐                                        |
|  │      AutoGen Studio (8081)      │   ← DESIGN PHASE                       |
|  │   +--------------------------+  │                                        |
|  │   │  Pattern/Workflow Editor │  │   * Drag & drop agent config           |
|  │   │  Team Configuration      │  │   * Visual workflow builder            |
|  │   │  Test & Iterate          │  │   * Run test sessions                  |
|  │   +--------------------------+  │                                        |
|  └───────────────┬─────────────────┘                                        |
|                  │                                                          |
|                  │ ★ Direct API Call (Vite Proxy)                           |
|                  │   /api/autogen → localhost:8081                          |
|                  ▼                                                          |
|  ┌─────────────────────────────────┐                                        |
|  │      Auto-Claude (Electron)     │   ← EXECUTION PHASE                    |
|  │   +--------------------------+  │                                        |
|  │   │ Kanban Board             │  │   * AutoGen 결과 직접 표시              |
|  │   │ AutogenStatusBadge       │  │   * 5초마다 8081 폴링                   |
|  │   │ Task Management          │  │   * SharedMemory 폴백 지원              |
|  │   +--------------------------+  │                                        |
|  └───────────────┬─────────────────┘                                        |
|                  │                                                          |
|     ┌────────────┴────────────┐                                             |
|     ▼                         ▼                                             |
|  ┌─────────────────┐   ┌─────────────────┐                                  |
|  │ AG-ACE-BRIDGE   │   │ SharedMemory    │   ← OPTIONAL                     |
|  │  Orchestrator   │   │    (8101)       │                                  |
|  │                 │   │                 │                                  |
|  │ * 24/7 Loop     │   │ * Fallback only │                                  |
|  │ * Agent Select  │   │ * AG-CLI sync   │                                  |
|  │ * Pipeline Exec │   │ * Event pub/sub │                                  |
|  └────────┬────────┘   └─────────────────┘                                  |
|           │                                                                 |
|           ▼                                                                 |
|  ┌──────────────────────────────────────────────────────────────────┐       |
|  │                    Agent Layer (19 Agents)                        │       |
|  │  +----------------+  +----------------+  +----------------------+  │       |
|  │  │ Auto-Claude    │  │  A2A Protocol  │  │  AG Law Domain       │  │       |
|  │  │ (SDK-based)    │  │  (HTTP/RPC)    │  │  (HTTP/REST)         │  │       |
|  │  │                │  │                │  │                      │  │       |
|  │  │ - Planner      │  │ - poetry 8003  │  │ - Case Analyzer      │  │       |
|  │  │ - Coder 24/7   │  │ - philosophy   │  │ - Legal Researcher   │  │       |
|  │  │ - QA Reviewer  │  │ - history      │  │ - Risk Assessor      │  │       |
|  │  │ - QA Fixer     │  │ - calculator   │  │ - Compliance         │  │       |
|  │  │                │  │ - gui_test     │  │ - Document Drafter   │  │       |
|  │  +----------------+  +----------------+  +----------------------+  │       |
|  └──────────────────────────────────────────────────────────────────┘       |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Direct Connection (★ 권장 - 단순!)

**Auto-Claude UI가 AutoGen Studio(8081)에 직접 연결:**

```
Auto-Claude UI  ──────────────────────►  AutoGen Studio (8081)
                  Vite Proxy
                  /api/autogen                GET /api/sessions/
                                              GET /api/sessions/{id}/runs/
```

**장점:**
- SharedMemory(8101) 서버 불필요
- run_autogen_sync_simple.py 스크립트 불필요
- AutoGen Studio만 실행하면 즉시 연동

**Vite Proxy 설정 (electron.vite.config.ts):**
```typescript
proxy: {
  '/api/autogen': {
    target: 'http://localhost:8081',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/autogen/, '/api')
  }
}
```

### SharedMemory (Optional Fallback)

**SharedMemory (8101)** is optional - used as fallback when direct connection fails:

```bash
# Optional: Start SharedMemory server for AG-CLI integration
cd AG/autogen_a2a_kit/AG-cli
python mcp/shared_memory.py  # → http://localhost:8101
```

**Fallback Flow:**
```
Auto-Claude UI
     │
     ├─(1)─► AutoGen Studio (8081) - 직접 연결 시도
     │           ↓ 실패 시
     └─(2)─► SharedMemory (8101) - 폴백
```

**Stored Keys (when using SharedMemory):**
| Key | Description |
|-----|-------------|
| `autogen_session_{id}` | Each session result |
| `autogen_latest` | Most recent result |
| `task_{id}_stage_{n}` | Pipeline stage results |

### Agent Adapter Types

The system uses three adapter types to connect different agent systems:

| Adapter | Protocol | Agents | Features |
|---------|----------|--------|----------|
| **AutoClaudeAdapter** | Claude Agent SDK + OAuth | Planner, Coder, QA | 24/7 autonomous, security sandbox |
| **AGA2AAdapter** | JSON-RPC 2.0 over HTTP | poetry, philosophy, calc, etc. | Google ADK A2A Protocol |
| **AutogenStudioAdapter** | Python/HTTP | AutoGen Teams | Workflow execution |

### Pipeline Execution Patterns

The Orchestrator supports three execution patterns:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Sequential** | Stage1 → Stage2 → Stage3 | Simple linear workflows |
| **Parallel** | [Stage1, Stage2, Stage3] → Gather | Fan-out/gather for research |
| **CriticLoop** | Generator → Critic → Fix → Repeat | QA validation loops |

**Example Pipeline:**
```python
# QA Loop with Auto-Claude agents
await run_auto_claude_qa_loop(
    task=task,
    stages=[
        Stage(AgentType.AUTO_CLAUDE_CODER, StageType.SEQUENTIAL),
        Stage(AgentType.AUTO_CLAUDE_QA_REVIEWER, StageType.CRITIC_LOOP),
    ],
    max_iterations=5
)
```

### Auto-Claude UI Integration

The Auto-Claude Electron app displays AutoGen results in the Kanban board:

```typescript
// In KanbanBoard.tsx - Polls SharedMemory every 5 seconds
useEffect(() => {
  const fetchAutogenResults = async () => {
    const response = await window.electronAPI.getAutogenLatest();
    if (response.success && response.data) {
      // Convert to virtual task for display
      const virtualTask = autogenResultToTask(response.data);
      setAutogenTasks([virtualTask]);
    }
  };
  const interval = setInterval(fetchAutogenResults, 5000);
  return () => clearInterval(interval);
}, []);
```

**Result displayed as Kanban card:**
```
┌─────────────────────────────────────────┐
│ [AutoGen] calculator_workflow           │
│                                         │
│ Task: Calculate 100 + 200               │
│ Result: The result is 300.              │
│                                         │
│ Agents: assistant_agent                 │
│ Status: ● complete                      │
│ Time: Jan 24, 2:16 PM                   │
└─────────────────────────────────────────┘
```

## Complete Startup Sequence

### 최소 구성 (★ 권장 - 2개만 실행)

```bash
# 1. AutoGen Studio (port 8081) - 워크플로우 설계
autogenstudio ui --port 8081

# 2. Auto-Claude (Electron) - Task UI
cd Auto-Claude/apps/frontend
npm run dev

# 끝! AutoGen 결과가 Auto-Claude Kanban에 바로 표시됨
```

### 전체 구성 (24/7 운영 + A2A 에이전트)

```bash
# 1. A2A Agents (ports 8003-8120) - Optional
cd AG/autogen_a2a_kit
python run_all_agents.py --subset

# 2. SharedMemory (port 8101) - Optional (AG-CLI 연동용)
cd AG/autogen_a2a_kit/AG-cli
python mcp/shared_memory.py

# 3. AutoGen Studio (port 8081) - Design UI
autogenstudio ui --port 8081

# 4. AG-ACE-BRIDGE Dashboard (port 8080) - 24/7 Orchestrator
cd AG-ACE-BRIDGE
python main.py --dashboard

# 5. Auto-Claude (Electron) - Task UI
cd Auto-Claude/apps/frontend
npm run dev
```

## License

- Auto-Claude: AGPL-3.0
- AG: Various
- AG-ACE-BRIDGE: MIT