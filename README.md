# 25_ACE

AI Agent Coordination Ecosystem - 24/7 AI Project Factory

● 에이전트 성능 평가 — 일반적인 방법들

  크게 3가지 계열로 나뉩니다:

  1. 정답이 있는 벤치마크 (객관식/코드)

  MMLU: 문제 → 정답 맞히기 → 정답률%
  HumanEval: 코딩 문제 → unit test 통과율%
  GSM8K: 수학 문제 → 정답 일치 여부
  → 공식 있음. 맞으면 1, 틀리면 0. 단순.

  2. 에이전트 벤치마크 (멀티스텝 태스크)

  https://arxiv.org/abs/2308.03688 — OS 조작, DB 쿼리, 웹 브라우징 등 5-50턴 걸리는 실제 환경에서 목표
  달성률 측정.

  https://arxiv.org/abs/2503.01935 — 멀티에이전트 협업/경쟁 시나리오. milestone-based KPI로 "몇 단계까지
  달성했나" 측정.

  → 이것도 결국 성공/실패 또는 달성 단계 수로 정량화.

  3. 개방형 품질 평가 (우리가 하는 것)

  정답이 없는 과제 (에세이, 분석, 설계 등)는 LLM-as-Judge밖에 방법이 없음:
  - G-Eval: LLM이 CoT로 평가 (우리 방식)
  - MT-Bench: GPT-4가 1-10점 매김
  - Chatbot Arena: 사람이 A vs B 직접 비교 (ELO 레이팅)
  - Human eval: 사람이 직접 채점 (가장 신뢰, 가장 비쌈)
  ┌────────────┬────────────────────────────────┬─────────────────────────────────────┐
  │    항목    │     원본 논문 (Liu et al.)     │           우리 scorer.py            │
  ├────────────┼────────────────────────────────┼─────────────────────────────────────┤
  │ CoT 생성   │ ✅ LLM이 평가 단계를 자동 생성 │ ❌ 프롬프트에 평가기준 직접 제공    │
  ├────────────┼────────────────────────────────┼─────────────────────────────────────┤
  │ 점수 계산  │ 토큰 확률 가중합 Σ(score × P)  │ 정수 직접 출력 후 파싱              │
  ├────────────┼────────────────────────────────┼─────────────────────────────────────┤
  │ 스케일     │ 1-5                            │ 1-5 ✅ 동일                         │
  ├────────────┼────────────────────────────────┼─────────────────────────────────────┤
  │ 차원       │ task별 커스텀                  │ 5개 고정 (accuracy~overall) ✅ 유사 │
  ├────────────┼────────────────────────────────┼─────────────────────────────────────┤
  │ Judge 모델 │ GPT-4                          │ Claude Sonnet ✅ 동급               │
  └────────────┴────────────────────────────────┴─────────────────────────────────────┘

  문제가 되는 부분

  1. 토큰 확률 안 씀 — 이게 제일 큰 차이. 원본은 P("4")=0.6, P("5")=0.3 이런 식으로 연속값을 만드는데,
  우리는 그냥 "4" 파싱. 하지만 Claude API는 토큰 logprob을 제공하지 않아서 구현 자체가 불가능합니다.

  2. CoT 자동 생성 안 함 — 원본은 먼저 "어떻게 평가할지 단계를 생각해봐"를 시키고, 그 CoT를 평가에 포함.
  우리는 바로 점수 매기라고 함.

  논문에서 방어 가능한가?

  네, 충분합니다. 이유:

  1. MT-Bench, Chatbot Arena 등 대부분의 LLM-as-Judge 논문도 토큰 확률 안 씀 — 직접 점수 출력이 업계 표준
  2. 논문에서 "G-Eval inspired LLM-as-Judge"라고 쓰면 됨 — 원본 그대로 복제했다고 안 하면 문제 없음
  3. 5-model cross-validation이 신뢰도를 보완 — 채점 방법이 좀 거칠어도 5개 모델이 같은 패턴 보이면 OK

  논문에 쓸 문구 제안

  ▎ "We employ an LLM-as-Judge approach inspired by G-Eval (Liu et al., 2023), where Claude Sonnet evaluates
   each response on five dimensions (accuracy, completeness, coherence, usefulness, overall) using a 1-5
  scale."

  이러면 위배 아닙니다. "G


## System State (2026-02-07 Updated)

```
Servers:       AutoGen Studio (8081)  Platform UI (5173/Vite)  Auto-Claude (Electron)
CLI:           AG/Auto-Claude (python cli.py)
Model Client:  claude-agent-sdk (OAuth, 15s/call vs 59s subprocess)
Platform UI:   Vite 7 + React 19 + TypeScript 5.9 + Tailwind v4 (0 TS errors, 2s build)
E2E Test:      PASS (Playwright dual-browser, 38 cards, 6 pages navigated)
AutoGen Data:  100+ sessions, agent-level decomposition working
AutoGen Teams: 7 team templates (Sequential/Selector/Handoff/Debate/Reflection/DevTeam/Hybrid) + $ref DRY system
JSON_MODULES:  98 components (23 agents, 10 A2A, 7 models, 14 patterns) + $ref resolver
Maintenance:   health_check, port_validator, doc_sync, agent_registry_sync, model_field_checker
Branch:        DK-BB
```

## Overview

```
+-----------------------------------------------------------------------+
|                         25_ACE ECOSYSTEM                               |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-------------------+    REST + WS      +-------------------+        |
|  |   Platform UI     |<---------------->|  AutoGen Studio   |        |
|  |   (Vite + React)  |  /api/* proxy    |    (8081)         |        |
|  |   :5173            |                  |                   |        |
|  |  Dashboard         |                  |  Team Config      |        |
|  |  Team Builder      |                  |  Session Runs     |        |
|  |  Playground (WS)   |                  |  Pattern Gallery  |        |
|  |  History/Agents    |                  |  A2A Registry     |        |
|  +-------------------+                   +-------------------+        |
|                                                   |                   |
|  +-------------------+                            |                   |
|  |   Auto-Claude     |  IPC / workflowExecute     |                   |
|  |   Electron App    |                            |                   |
|  |  Kanban Board     |                            v                   |
|  |  Agent Terminals  |                   +-------------------+        |
|  +--------+----------+                   |  Agent Layer      |        |
|           |                              |  A2A (8003-8120)  |        |
|           v                              |  SharedMemory     |        |
|  +-------------------+                   |  (8101, optional) |        |
|  |  AG/Auto-Claude   |                   +-------------------+        |
|  |  CLI (cli.py)     |                                                |
|  |  spec_runner.py   |                                                |
|  |  run.py           |                                                |
|  +-------------------+                                                |
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
AutoGen Studio                Auto-Claude (3s polling)           AG/Auto-Claude CLI
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
| **Worktrees** | Git worktree management (refactored: git-utils, ide-tools, pr-utils 분리) |

## Quick Start: CLI-Only (★ 권장 - UI 없이 24/7)

```bash
# 1. Claude CLI 인증 (최초 1회)
claude
# /login 입력 → 브라우저 OAuth

# 2. AG/Auto-Claude CLI 24/7 실행
cd AG/Auto-Claude
pip install -r requirements.txt
cp .env.example .env
python cli.py                              # 24/7 factory
python cli.py run --task "계산기 앱 만들어줘"  # single task

# 3. 또는 Python에서 직접 호출
python -c "
from src.bridge import WorkflowExecutor
executor = WorkflowExecutor()
result = executor.execute_full_pipeline_sync('계산기 앱 만들어줘')
print(result)
"

# 끝. Auto-Claude UI 없이도 모든 에이전트 사용 가능!
# Planner → Coder → QA Reviewer → QA Fixer 파이프라인 자동 실행
```

## Quick Start: Platform UI 모드 (★ SaaS Frontend)

```bash
# 1. AutoGen Studio (port 8081)
autogenstudio ui --port 8081

# 2. Platform UI (port 5173)
cd platform
npm install    # 최초 1회
npm run dev    # http://localhost:5173 (Vite proxy -> 8081)

# Done. Teams/Playground/Dashboard 모두 사용 가능.
# Playground에서 팀 선택 -> WebSocket 실시간 실행.
```

## Quick Start: Auto-Claude Electron (Kanban + 24/7 Pipeline)

```bash
# 1. AutoGen Studio (port 8081)
autogenstudio ui --port 8081

# 2. Auto-Claude Electron
cd AG/Auto-Claude/apps/AG-Frontend
npm run dev
# Opens Electron app. AutoGen sessions auto-appear on Kanban board.
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

# 3. AutoGen Studio (8081) - backend API engine
autogenstudio ui --port 8081

# 4. Platform UI (5173) - SaaS frontend
cd platform
npm run dev

# 5. AG/Auto-Claude CLI (24/7 orchestrator) - optional
cd AG/Auto-Claude
python cli.py

# 6. Auto-Claude Electron (Kanban) - optional
cd AG/Auto-Claude/apps/AG-Frontend
npm run dev
```

## Projects

| Project | Description | Key Files |
|---------|-------------|-----------|
| [platform](AG-frontend/) | SaaS Frontend (Vite 7 + React 19 + Tailwind v4) | `src/shared/api/client.ts`, `src/features/playground/` |
| [AG/Auto-Claude](AG/Auto-Claude/) | Electron app + CLI-Only 24/7 Hub | `cli.py`, `KanbanBoard.tsx`, `src/bridge/` |
| [AG](AG/) | Multi-Agent System, A2A agents | `autogen_a2a_kit/`, `agent/` |
| [JSON_MODULES](JSON_MODULES/) | n8n-style composable JSON components + $ref resolver | `ref_resolver.py`, `validate_json.py`, `a2a_manager.py` |
| [maintenance](maintenance/) | Health check, port validation, doc sync | `run_maintenance.py`, `health_check.py` |

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
  +-> AG/Auto-Claude CLI
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

**AutoGen Studio 7 Teams** (JSON_MODULES $ref compact templates):
| Team | Type | Agents |
|------|------|--------|
| Sequential Team | SequentialGroupChat | planner -> coder -> qa_reviewer |
| Selector Team | SelectorGroupChat | planner, coder, qa_reviewer (AI-routed) |
| Handoff Team | HandoffGroupChat | triage, refund_agent, support_agent |
| Debate Team | SelectorGroupChat | advocate, critic, judge |
| Reflection Team | SequentialGroupChat | generator, critic (nested inner/outer) |
| DevTeam | SequentialGroupChat | planner(reader) -> coder(coder) -> qa_reviewer(reader) -> qa_fixer(coder) |
| Hybrid Team | SelectorGroupChat | researcher, planner, coder, qa_reviewer |

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

**AG A2A (10 agents, ports 8001-8120)**
| Agent | Port | Function |
|-------|------|----------|
| history_helper_agent | 8001 | History Helper |
| prime_checker | 8002 | Prime Number Checker |
| poetry_agent | 8003 | Poetry/Literature |
| philosophy_agent | 8004 | Philosophy |
| history_agent | 8005 | History |
| calculator_agent | 8006 | Calculation |
| math_agent | 8007 | Mathematics |
| graphics_agent | 8008 | Graphics |
| gpu_agent | 8009 | GPU Computing |
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
| AutoGen Studio | 8081 | Yes (backend API) |
| Platform UI (Vite) | 5173 | Yes (SaaS frontend) |
| Auto-Claude (Electron) | - | Optional (Kanban + 24/7 pipeline) |
| AG/Auto-Claude CLI | - | CLI-based (no HTTP server) |
| SharedMemory | 8101 | Optional (fallback) |
| A2A Agents | 8003-8120 | Optional |

## Key File Paths

### Auto-Claude Frontend (most actively modified)
| File | Purpose |
|------|---------|
| `AG/Auto-Claude/apps/frontend/src/renderer/components/KanbanBoard.tsx` | Kanban board, agent decomposition, 24/7 auto-trigger, polling |
| `AG/Auto-Claude/apps/frontend/src/renderer/components/TaskCard.tsx` | Card rendering, trigger status display, memo comparator |
| `AG/Auto-Claude/apps/frontend/src/renderer/components/task-detail/TaskDetailModal.tsx` | Task detail modal (improved) |
| `AG/Auto-Claude/apps/frontend/src/renderer/components/task-detail/TaskWarnings.tsx` | Task warning display |
| `AG/Auto-Claude/apps/frontend/src/renderer/lib/browser-mock.ts` | AutoGen API calls, session fetching (max 10) |
| `AG/Auto-Claude/apps/frontend/src/main/ipc-handlers/a2a-handlers.ts` | Electron IPC for AutoGen API (max 10 sessions) |
| `AG/Auto-Claude/apps/frontend/src/main/ipc-handlers/task/worktree-handlers.ts` | Worktree management (refactored) |
| `AG/Auto-Claude/apps/frontend/electron.vite.config.ts` | Vite proxy config (/api/autogen -> 8081) |

### AG/Auto-Claude CLI
| File | Purpose |
|------|---------|
| `AG/Auto-Claude/cli.py` | Unified CLI entry point |
| `AG/Auto-Claude/src/bridge/workflow_executor.py` | Workflow execution bridge |
| `AG/Auto-Claude/src/coordinator/orchestrator.py` | 24/7 main loop |
| `AG/Auto-Claude/src/coordinator/task_queue.py` | Task queue |
| `AG/Auto-Claude/src/adapters/ag_autogen.py` | AutoGen adapter |
| `AG/Auto-Claude/src/project/binding_store.py` | AutoGen session binding |

### Maintenance (NEW)
| File | Purpose |
|------|---------|
| `maintenance/run_maintenance.py` | Run all maintenance checks |
| `maintenance/health_check.py` | Service health check (ports, connectivity) |
| `maintenance/port_map_validator.py` | Validate port mappings across docs/code |
| `maintenance/doc_sync_checker.py` | Check documentation sync with code |
| `maintenance/agent_registry_sync.py` | Verify agent registry consistency |
| `maintenance/model_field_checker.py` | Check model field definitions |

## Vite Proxy Configuration

### Platform UI (SaaS Frontend)
```typescript
// AG-frontend/vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8081',
    changeOrigin: true,
  }
}
```
Platform calls `/api/teams` -> proxied to `http://localhost:8081/api/teams`.

### Auto-Claude Electron
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

`JSON_MODULES/e2e_playwright_test.py` - Playwright E2E test:
1. AutoGen Studio: verify sessions, teams, agent messages
2. Auto-Claude: skip wizard, verify Kanban cards
3. Agent decomposition: header + agent cards verified
4. WebSocket run submission and result verification
5. Side-by-side screenshots

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

### Platform UI (SaaS Frontend)
| File | Purpose |
|------|---------|
| `AG-frontend/src/shared/api/client.ts` | REST API client (AutoGen Studio 1:1 match) |
| `AG-frontend/src/shared/api/ws.ts` | WebSocket client (execution streaming) |
| `AG-frontend/src/shared/types/datamodel.ts` | TypeScript type system (ported from AutoGen Studio) |
| `AG-frontend/src/features/playground/PlaygroundPage.tsx` | Real-time execution UI (team select + WS chat) |
| `AG-frontend/src/features/playground/executionStore.ts` | Zustand execution state (turns, status) |
| `AG-frontend/src/features/teams/TeamsPage.tsx` | Team list + management |
| `AG-frontend/src/app/router.tsx` | React Router (6 lazy-loaded pages) |
| `AG-frontend/vite.config.ts` | Vite config + /api/* proxy to :8081 |

## AutoGen Studio Notes

> AutoGen Studio의 내장 UI(web/ui/)는 더 이상 직접 수정하지 않습니다.
> 커스텀 프론트엔드는 `AG-frontend/` (Vite + React 19)을 사용합니다.
> AutoGen Studio는 백엔드 API 엔진으로만 사용됩니다 (REST + WebSocket on :8081).

## Documentation

| Document | Path | Description |
|----------|------|-------------|
| AI Startup Guide | [docs/AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md) | Server start sequence |
| Project Start Guide | [docs/PROJECT_START_GUIDE.md](docs/PROJECT_START_GUIDE.md) | 3 UI coordination |
| Workflow Example | [docs/WORKFLOW_EXAMPLE.md](docs/WORKFLOW_EXAMPLE.md) | GitHub Issue -> PR flow |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| Auto-Claude CLAUDE.md | [AG/Auto-Claude/CLAUDE.md](AG/Auto-Claude/CLAUDE.md) | Auto-Claude AI context |
| AG/Auto-Claude CLI | [AG/Auto-Claude/README.md](AG/Auto-Claude/README.md) | CLI 24/7 Hub |
| JSON_MODULES | [JSON_MODULES/README.md](JSON_MODULES/README.md) | Composable JSON components, $ref resolver, validation |
| Platform UI | [AG-frontend/](AG-frontend/) | SaaS Frontend (Vite + React 19 + Tailwind v4) |
| Maintenance Scripts | [maintenance/](maintenance/) | Health check, port validation, doc sync, agent registry |

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
3. AG-frontend/ (SaaS Frontend: `src/shared/api/client.ts`, `src/features/playground/`)
4. KanbanBoard.tsx (핵심 로직: 3초 폴링, agent 분해, auto-trigger, 5개 Ref 안전장치)
5. `cd platform && npm run build` 확인 (빌드 깨지면 안 됨)

### 수정 시 지뢰밭
- **useEffect 무한루프**: KanbanBoard.tsx에서 함수를 deps에 넣으면 무한 렌더링 (2026-01-31에 8개 수정함)
- **memo comparator**: TaskCard.tsx의 `taskCardPropsAreEqual()`에 새 필드 추가 시 비교 로직도 업데이트
- **이중 모드**: browser-mock.ts(Vite proxy) + a2a-handlers.ts(Electron IPC) 양쪽 다 수정 필요
- **AutoGen Studio**: 내장 UI 수정 금지. 커스텀 프론트엔드는 `AG-frontend/` 사용
- **worktree-handlers.ts**: 리팩토링됨 - git-utils, ide-tools, pr-utils로 분리. 수정 시 3개 파일 모두 확인
- **i18n**: 새 UI 텍스트 추가 시 en/tasks.json + fr/tasks.json 양쪽 업데이트 필수

### 핵심 원칙
- **Platform UI**: SaaS 프론트엔드 (`AG-frontend/` Vite + React 19). AutoGen Studio API를 직접 프록시
- AutoGen 세션 1개 = Kanban 카드 N개 (agent-level decomposition)
- 완료된 세션은 자동으로 빌드 파이프라인 trigger (24/7)
- Ref로 상태 관리 (렌더링 없이 24/7 안정성 유지)
- 향후: Team Builder (비주얼), Dashboard (사용량/비용), Agent Market

### AG/Auto-Claude CLI Pipeline 이해
```
python cli.py run --task "..." → WorkflowExecutor
  → spec_runner.py (AI Spec 생성)
  → run.py (Planner → Coder → QA Reviewer → QA Fixer)
  → Git Worktree 격리 빌드
  → python run.py --spec XXX --review / --merge

python cli.py (24/7 모드)
  → ProjectWatcher + Orchestrator
  → PipelineBuilder.auto_build() → Pipeline stages
    → Sequential / Parallel / CriticLoop
  → Result → SharedMemory(optional) → next_tasks queue
```

## License

- Auto-Claude: AGPL-3.0
- AG: Various
