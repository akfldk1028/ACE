# 25_ACE

AI Agent Coordination Ecosystem - 24/7 AI Project Factory

## System State (2026-01-31 Verified)

```
Servers:       AutoGen Studio (8081)  Auto-Claude (5173/Electron)  AG-ACE-BRIDGE (8080)
Build:         OK (main 3MB + preload 79KB + renderer 5.3MB)
E2E Test:      PASS (Playwright dual-browser, 38 cards, 6 pages navigated)
AutoGen Data:  100+ sessions, agent-level decomposition working
```

## Overview

```
+-----------------------------------------------------------------------+
|                         25_ACE ECOSYSTEM                               |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-------------------+    Direct API     +-------------------+        |
|  |   Auto-Claude     |<---------------->|  AutoGen Studio   |        |
|  |   Electron App    |  Vite Proxy      |    (8081)         |        |
|  |                   |  /api/autogen     |                   |        |
|  |  Kanban Board     |  3s polling       |  Pattern Gallery  |        |
|  |  Agent Terminals  |                   |  Team Config      |        |
|  |  MCP Overview     |                   |  Session Runs     |        |
|  |  Pipeline Project |                   |                   |        |
|  +-------------------+                   +-------------------+        |
|          |                                        |                   |
|          | IPC / workflowExecute                   |                   |
|          v                                        v                   |
|  +-------------------+                   +-------------------+        |
|  |  AG-ACE-BRIDGE    |                   |  Agent Layer      |        |
|  |  Pipeline (8080)  |                   |  A2A (8003-8120)  |        |
|  |  spec_runner.py   |                   |  SharedMemory     |        |
|  |  run.py           |                   |  (8101, optional) |        |
|  +-------------------+                   +-------------------+        |
|                                                                       |
+-----------------------------------------------------------------------+
```

## Key Feature: Agent-Level Decomposition

AutoGen sessions are not shown as 1 card per session. Each agent's output becomes an individual Kanban card:

```
AutoGen Session 136 (complete, 7 messages)
  |
  +-- [AutoGen] Session 136          -> Done (header card)
  |     "Python으로 TODO CLI 앱..."
  |
  +-- insights_agent                  -> Planning column
  |     "## Insights Report..."
  |
  +-- deep_research_agent             -> Planning column
  |     "## Research Report..."
  |
  +-- spec_writer_agent               -> Planning column
  |     "## Project Specification..."
  |
  +-- planner_agent                   -> Planning column
  |     "## Implementation Plan..."
  |
  +-- coder_agent                     -> In Progress column
  |     "```python def main()..."
  |
  +-- qa_reviewer_agent               -> AI Review column
        "## QA Review Report PASS..."
```

**Agent name -> Kanban column mapping** (in `KanbanBoard.tsx` `agentToColumn()`):

| Agent name contains | Column | Why |
|---------------------|--------|-----|
| insight, plan, architect, research, spec | Planning (backlog) | Design/analysis agents |
| code, implement, develop, fix | In Progress | Implementation agents |
| review, qa, test, critic | AI Review | Validation agents |
| user | Planning | User prompt |
| (default) | In Progress | Unknown agents |
| (error sessions) | Human Review | Needs attention |
| (complete sessions, all agents) | Done | Finished work |

## Key Feature: 24/7 Auto-Trigger Pipeline

When AutoGen completes a session, Auto-Claude **automatically** starts the build pipeline. No button click needed.

```
AutoGen Studio                Auto-Claude (3s polling)           AG-ACE-BRIDGE
     |                              |                                  |
     | Session completes            |                                  |
     |----------------------------->| Detects new completion           |
     |                              | (processedSessionsRef tracks)    |
     |                              |                                  |
     |                              | workflowExecute()                |
     |                              |--------------------------------->|
     |                              |                                  | spec_runner.py
     |                              |                                  | run.py
     |                              |                                  | Planner -> Coder -> QA
     |                              |                                  |
     |                              | 10s execution polling            |
     |                              |<---------------------------------|
     |                              | Status: running -> done/error    |
     |                              |                                  |
```

**Safety mechanisms:**
- `processedSessionsRef` - tracks which sessions already triggered (no double-trigger)
- `initialLoadDoneRef` - prevents old sessions from triggering on app start
- `triggerQueueRef` - serialized queue prevents concurrent pipeline executions
- `isProcessingQueueRef` - mutex for queue processing
- Hourly memory cleanup (max 100 entries) for 24/7 operation

## Auto-Claude UI Pages (All Verified Working)

| Page | Description |
|------|-------------|
| **Kanban Board** | 5 columns: Planning / In Progress / AI Review / Human Review / Done. AutoGen agent cards + native task cards |
| **Agent Terminals** | Live AutoGen Studio connection. Shows session runs with agent messages |
| **Insights** | Project insights dashboard |
| **Roadmap** | Project roadmap view |
| **Ideation** | Idea capture |
| **Changelog** | Version changelog |
| **Context** | Project structure visualization |
| **MCP Overview** | MCP server configuration. Context7 (ON), Graphiti Memory, Linear, Electron, Puppeteer, Auto-Claude Tools (ON). Custom server add supported |
| **Worktrees** | Git worktree management |

## Quick Start (Minimum - 2 services)

```bash
# 1. AutoGen Studio (port 8081)
autogenstudio ui --port 8081

# 2. Auto-Claude
cd Auto-Claude/apps/frontend
npm run dev
# Opens Electron app + Vite dev server at localhost:5173

# Done. AutoGen sessions auto-appear on Kanban board.
# Completed sessions auto-trigger build pipeline.
```

## Full Start (All services)

```bash
# 1. A2A Agents (8003-8120) - optional
cd AG/autogen_a2a_kit/a2a_demo
python run_all_agents.py

# 2. SharedMemory (8101) - optional, fallback only
cd AG/autogen_a2a_kit/AG-cli
python mcp/shared_memory.py

# 3. AutoGen Studio (8081)
autogenstudio ui --port 8081

# 4. AG-ACE-BRIDGE (8080)
cd AG-ACE-BRIDGE
python main.py --dashboard

# 5. Auto-Claude
cd Auto-Claude/apps/frontend
npm run dev
```

## Projects

| Project | Description | Key Files |
|---------|-------------|-----------|
| [Auto-Claude](Auto-Claude/) | Electron app, Kanban, Pipeline | `KanbanBoard.tsx`, `TaskCard.tsx`, `browser-mock.ts` |
| [AG-ACE-BRIDGE](AG-ACE-BRIDGE/) | Pipeline server, spec_runner, run.py | `main.py`, `src/server/`, `src/pipeline/` |
| [AG](AG/) | Multi-Agent System, A2A agents | `autogen_a2a_kit/`, `agent/` |
| [Calculator](Calculator/) | Example project for agent demos | - |

## Architecture

### Data Flow: AutoGen -> Auto-Claude Kanban

```
AutoGen Studio (8081)
  GET /api/sessions          -> list of sessions (id, name, team_id)
  GET /api/sessions/{id}/runs -> run details with team_result.task_result.messages[]

Auto-Claude Frontend
  electron.vite.config.ts    -> Vite proxy: /api/autogen -> localhost:8081
  browser-mock.ts            -> getAutogenSessions(), getAutogenRunsDetailed()
                                fetches up to 10 sessions, returns messages array
  a2a-handlers.ts            -> IPC handlers for Electron main process (same logic)

  KanbanBoard.tsx
    autogenRunToTasks(run, sessionId)  -> converts 1 run to N task cards
    agentToColumn(agentName)           -> maps agent name to kanban column
    fetchAutogenResults()              -> 3s polling, calls autogenRunToTasks
    autoTriggerWorkflow()              -> detects new completions, queues pipeline
    processQueue()                     -> serialized pipeline execution

  TaskCard.tsx
    renders task cards with:
    - agent name as title ("└ coder_agent")
    - agent output as description (first 300 chars)
    - trigger status on header cards (running/done/error)
    - Incomplete/Needs Recovery tags on error sessions
    - Resume button on error sessions
```

### Agent Adapter Types

| Adapter | Protocol | Agents |
|---------|----------|--------|
| AutoClaudeAdapter | Claude Agent SDK + OAuth | Planner, Coder, QA Reviewer, QA Fixer |
| AGA2AAdapter | JSON-RPC 2.0 over HTTP | poetry, philosophy, calculator, etc. |
| AutogenStudioAdapter | Python/HTTP | AutoGen Teams |

### MCP Integration (Current + Future)

**Current MCP servers** (visible in MCP Overview page):
- Context7 - Documentation lookup (enabled)
- Graphiti Memory - Cross-session memory
- Linear - Project management
- Electron - Desktop automation
- Puppeteer - Web browser automation
- Auto-Claude Tools - Build progress tracking (enabled)

**Future**: Each AutoGen agent can be assigned MCP servers. The `metadata.agent` field on each Kanban card identifies the agent, enabling per-agent MCP routing.

### Pipeline Execution

```
workflowExecute(taskDescription, 'standard', false)
  |
  +-> AG-ACE-BRIDGE (8080)
       |
       +-> spec_runner.py   # Generate specification
       +-> run.py            # Execute pipeline
            |
            +-> Planner agent     # Decompose into subtasks
            +-> Coder agent       # Implement (24/7)
            +-> QA Reviewer agent # Validate
            +-> QA Fixer agent    # Fix issues
            |
            +-> Git worktree (isolated build)
```

### Agent Registry

**Auto-Claude (4 agents)**
| Agent | Function |
|-------|----------|
| Planner | Task decomposition, implementation planning |
| Coder | 24/7 autonomous coding |
| QA Reviewer | E2E testing, quality verification |
| QA Fixer | Issue fixing, debugging |

**AutoGen Studio agents** (configured per team, example from Session 136):
| Agent | Output |
|-------|--------|
| insights_agent | Insights Report - project context analysis |
| deep_research_agent | Research Report - technology research |
| spec_writer_agent | Project Specification (spec.md) |
| planner_agent | Implementation Plan with subtasks |
| coder_agent | Code implementation |
| qa_reviewer_agent | QA Review Report (PASS/FAIL) |
| qa_fixer_agent | QA Fix Report (when FAIL) |

**AG A2A (10 agents, ports 8003-8120)**
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

**AG Law Domain (5 agents)**
| Agent | Function |
|-------|----------|
| Case Analyzer | Case law analysis |
| Legal Researcher | Legal research |
| Risk Assessor | Risk assessment |
| Compliance Checker | Compliance verification |
| Document Drafter | Legal document drafting |

## Service Ports

| Service | Port | Required |
|---------|------|----------|
| AutoGen Studio | 8081 | Yes |
| Auto-Claude (Vite dev) | 5173 | Yes (dev mode) |
| AG-ACE-BRIDGE | 8080 | For pipeline execution |
| SharedMemory | 8101 | Optional (fallback) |
| A2A Agents | 8003-8120 | Optional |

## Key File Paths

### Auto-Claude Frontend (most actively modified)
| File | Purpose |
|------|---------|
| `Auto-Claude/apps/frontend/src/renderer/components/KanbanBoard.tsx` | Kanban board, agent decomposition, 24/7 auto-trigger, polling |
| `Auto-Claude/apps/frontend/src/renderer/components/TaskCard.tsx` | Card rendering, trigger status display, memo comparator |
| `Auto-Claude/apps/frontend/src/renderer/lib/browser-mock.ts` | AutoGen API calls, session fetching (max 10) |
| `Auto-Claude/apps/frontend/src/main/ipc-handlers/a2a-handlers.ts` | Electron IPC for AutoGen API (max 10 sessions) |
| `Auto-Claude/apps/frontend/electron.vite.config.ts` | Vite proxy config (/api/autogen -> 8081) |

### AG-ACE-BRIDGE
| File | Purpose |
|------|---------|
| `AG-ACE-BRIDGE/main.py` | Entry point |
| `AG-ACE-BRIDGE/src/server/__init__.py` | FastAPI server setup |
| `AG-ACE-BRIDGE/src/server/dashboard.py` | Dashboard routes |
| `AG-ACE-BRIDGE/src/server/pipeline_routes.py` | Pipeline API routes |
| `AG-ACE-BRIDGE/src/coordinator/orchestrator.py` | 24/7 main loop |

## Vite Proxy Configuration

```typescript
// electron.vite.config.ts
proxy: {
  '/api/autogen': {
    target: 'http://localhost:8081',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/autogen/, '/api')
  }
}
```

Auto-Claude calls `/api/autogen/sessions` -> proxied to `http://localhost:8081/api/sessions`.

## E2E Test

`test_e2e_dual_browser.py` - Playwright dual-browser test:
1. AutoGen Studio: verify sessions, teams, agent messages
2. Auto-Claude: skip wizard, verify Kanban cards
3. Session 136 detail: 6 unique agents verified
4. Agent decomposition: 1 header + 29 agent cards
5. Side-by-side screenshots
6. New session creation -> Auto-Claude auto-detection

`test_functional.py` - Single browser functional verification:
- All 9 sidebar pages navigate correctly
- All buttons active (Pipeline, Start, Recover, Resume, New Task, Refresh)
- 38 total cards on Kanban
- API proxy working

## AutoGen Studio Team Storage (데이터 저장 경로)

### 저장 흐름 (순차적)

```
1. UI (Team Builder /build/)
   └─ POST /api/teams/  (team config JSON body)

2. FastAPI Route
   └─ autogenstudio/web/routes/teams.py → db.upsert(team)

3. DatabaseManager (SQLAlchemy)
   └─ autogenstudio/database/db_manager.py → INSERT/UPDATE `team` table

4. SQLite Database
   └─ ~/.autogenstudio/autogen04203.db
      (Windows: C:\Users\<username>\.autogenstudio\autogen04203.db)
```

### DB 스키마 (team 테이블)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK, autoincrement) | Team ID |
| component | JSON | 팀 설정 전체 (agents, models, tools 포함) |
| user_id | TEXT | 사용자 ID (default: `guestuser@gmail.com`) |
| version | TEXT | 버전 (`0.0.1`) |
| created_at | DATETIME | 생성 시간 |
| updated_at | DATETIME | 수정 시간 |

### 관련 테이블

| Table | 역할 | 관계 |
|-------|------|------|
| `team` | 팀 설정 (agents, models, tools) | - |
| `session` | 실행 세션 | `team_id` → team.id |
| `message` | 세션 메시지 (agent 대화) | `session_id` → session.id |
| `run` | 실행 결과 | `session_id` → session.id |

### 디렉토리 구조

```
~/.autogenstudio/                   (AUTOGENSTUDIO_APPDIR 환경변수로 변경 가능)
├── autogen04203.db                 # SQLite DB (teams, sessions, messages, runs)
├── .env                            # 환경 설정
├── files/user/                     # 업로드 파일
└── configs/                        # JSON/YAML 팀 설정 import 경로
```

### 환경변수 (prefix: AUTOGENSTUDIO_)

| Variable | Purpose | Default |
|----------|---------|---------|
| `AUTOGENSTUDIO_APPDIR` | 앱 루트 디렉토리 | `~/.autogenstudio` |
| `AUTOGENSTUDIO_DATABASE_URI` | DB 경로 | `sqlite:///./autogen04203.db` |
| `AUTOGENSTUDIO_DEFAULT_USER_ID` | 기본 사용자 | `guestuser@gmail.com` |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/teams/?user_id=xxx` | 팀 목록 |
| GET | `/api/teams/{team_id}` | 팀 상세 |
| POST | `/api/teams/` | 팀 생성/수정 |
| DELETE | `/api/teams/{team_id}` | 팀 삭제 |
| GET | `/api/sessions/` | 세션 목록 |
| GET | `/api/sessions/{id}/runs` | 세션 실행 결과 (agent messages 포함) |

### 핵심 소스 파일

| File | Role |
|------|------|
| `autogenstudio/web/routes/teams.py` | Team CRUD API |
| `autogenstudio/database/db_manager.py` | SQLAlchemy DB 관리 |
| `autogenstudio/datamodel/db.py` | Team/Session/Message 스키마 |
| `autogenstudio/web/config.py` | DB 경로, 기본 설정 |
| `autogenstudio/web/initialization.py` | 앱 초기화, DB 연결 |
| `autogenstudio/teammanager/teammanager.py` | JSON/YAML import, 팀 실행 |
| `frontend/src/components/views/teambuilder/api.ts` | 프론트엔드 API 호출 |

## AutoGen Studio Windows Notes

> **`npm run build` 금지!** -> `web/ui/` 폴더가 삭제됨. 복구: `git checkout HEAD -- autogenstudio/web/ui/`

Source modification uses **minified JS direct patch** instead of Gatsby full build.

## Documentation

| Document | Path | Description |
|----------|------|-------------|
| AI Startup Guide | [docs/AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md) | Server start sequence |
| Project Start Guide | [docs/PROJECT_START_GUIDE.md](docs/PROJECT_START_GUIDE.md) | 3 UI coordination |
| Workflow Example | [docs/WORKFLOW_EXAMPLE.md](docs/WORKFLOW_EXAMPLE.md) | GitHub Issue -> PR flow |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| Auto-Claude CLAUDE.md | [Auto-Claude/CLAUDE.md](Auto-Claude/CLAUDE.md) | Auto-Claude AI context |
| AG-ACE-BRIDGE Architecture | [AG-ACE-BRIDGE/docs/ARCHITECTURE.md](AG-ACE-BRIDGE/docs/ARCHITECTURE.md) | Bridge design |

## Requirements

- Python 3.10+
- Node.js 18+ (Auto-Claude frontend)
- Neo4j (AG law-domain, optional)
- Claude API Key (ANTHROPIC_API_KEY)
- OpenAI API Key (AG agents)

## 다음 AI에게 (Critical Context)

이 프로젝트는 **24/7 무중단 AI 코딩 공장**입니다. 수정 전 반드시 이해해야 할 것:

### 순차적 이해 순서
1. 이 README.md (전체 구조, 데이터 흐름)
2. ARCHITECTURE.md (4-Layer, 19 agents, 3 pipeline patterns, IPC 22채널)
3. KanbanBoard.tsx (핵심 로직: 3초 폴링, agent 분해, auto-trigger, 5개 Ref 안전장치)
4. `npm run build` 확인 (빌드 깨지면 안 됨)

### 수정 시 지뢰밭
- **useEffect 무한루프**: KanbanBoard.tsx에서 함수를 deps에 넣으면 무한 렌더링 (2026-01-31에 8개 수정함)
- **memo comparator**: TaskCard.tsx의 `taskCardPropsAreEqual()`에 새 필드 추가 시 비교 로직도 업데이트
- **이중 모드**: browser-mock.ts(Vite proxy) + a2a-handlers.ts(Electron IPC) 양쪽 다 수정 필요
- **AutoGen Studio**: `npm run build` 실행 금지 (web/ui/ 삭제됨), minified JS 직접 패치 방식

### 핵심 원칙
- AutoGen 세션 1개 = Kanban 카드 N개 (agent-level decomposition)
- 완료된 세션은 자동으로 빌드 파이프라인 trigger (24/7)
- Ref로 상태 관리 (렌더링 없이 24/7 안정성 유지)
- 향후: agent별 MCP 라우팅 (metadata.agent 필드 활용)

### AG-ACE-BRIDGE Pipeline 이해
```
Task → PipelineBuilder.auto_build() → Pipeline stages
  → Orchestrator._execute_pipeline()
    → Sequential: stage output → next stage context
    → Parallel: fan-out → gather
    → CriticLoop: Generator → Critic(score) → Fixer → (반복 max 5)
  → Result → SharedMemory(optional) → next_tasks queue
```

## License

- Auto-Claude: AGPL-3.0
- AG: Various
- AG-ACE-BRIDGE: MIT
