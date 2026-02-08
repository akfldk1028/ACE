# 25_ACE Architecture

> 자연어 → 에이전트 설계 → 자동 빌드 → 완성된 프로젝트

---

## 핵심 아키텍처

```
                        사용자
                          │
                          │ "계산기 앱 만들어줘"
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Platform UI (Vite + React 19)                             │
│                    http://localhost:5173                                      │
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Dashboard │ │ Teams    │ │Playground│ │ History  │ │ Agents   │        │
│  │(통계)    │ │(팀 관리) │ │(WS 실행) │ │(이력)    │ │(마켓)    │        │
│  └──────────┘ └──────────┘ └────┬─────┘ └──────────┘ └──────────┘        │
│                                  │                                         │
│  Vite Proxy: /api/* ─────────────┼─────────────────────────────────────►  │
└──────────────────────────────────┼─────────────────────────────────────────┘
                                   │ REST + WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AutoGen Studio Engine (:8081)                             │
│                                                                             │
│  Teams / Sessions / Runs / Gallery / A2A Registry                          │
│  7 Team Templates (Sequential/Selector/Handoff/Debate/Reflection/etc.)     │
│  98 JSON Components ($ref resolver system)                                  │
│  SQLite: ~/.autogenstudio/autogen04203.db                                   │
│                                                                             │
└────────────────┬──────────────────────────────┬─────────────────────────────┘
                 │                              │
                 ▼                              ▼
┌────────────────────────────┐   ┌──────────────────────────────┐
│  Claude SDK                │   │  A2A Agents (8003-8120)      │
│  (code execution)          │   │  10 agents, JSON-RPC 2.0     │
│                            │   │  Google ADK                   │
│  Planner → Coder →         │   └──────────────────────────────┘
│  QA Reviewer → QA Fixer    │
│                            │
│  AG/Auto-Claude CLI        │
│  (24/7 orchestrator)       │
└────────────────────────────┘
```

---

## 핵심 컴포넌트

### 1. Platform UI (SaaS Frontend)

| 항목 | 값 |
|------|-----|
| URL | http://localhost:5173 |
| 스택 | Vite 7 + React 19 + TypeScript 5.9 + Tailwind v4 |
| 역할 | 커스텀 SaaS 프론트엔드 (AutoGen Studio API 프록시) |

**6 Pages** (lazy-loaded):
- Dashboard, Teams, Playground, History, Agents, Settings

**핵심 파일:**
- `AG-frontend/src/shared/api/client.ts` - REST API client (AutoGen Studio 1:1 match)
- `AG-frontend/src/shared/api/ws.ts` - WebSocket client (execution streaming)
- `AG-frontend/src/features/playground/PlaygroundPage.tsx` - Real-time execution UI
- `AG-frontend/vite.config.ts` - Vite proxy: `/api/*` → `:8081`

### 2. AutoGen Studio (Backend API Engine)

| 항목 | 값 |
|------|-----|
| URL | http://localhost:8081 |
| 역할 | 에이전트 팀 실행 엔진 (REST + WebSocket API) |
| 기능 | 팀/세션/런 관리, 패턴 갤러리, A2A 연동 |

**지원 패턴:**
- Sequential: A → B → C
- Selector: LLM이 에이전트 선택
- Swarm: 핸드오프 기반 협업
- Magentic One: Orchestrator가 작업 분배
- Reflection: Worker + Reviewer 루프

### 3. Auto-Claude (24/7 실행)

| 항목 | 값 |
|------|-----|
| 위치 | AG/Auto-Claude |
| 역할 | 24/7 자율 코딩 (CLI + Electron Kanban) |
| 핵심 파일 | `cli.py`, `src/bridge/workflow_executor.py` |

**에이전트 파이프라인:**
1. **Planner Agent**: 구현 계획 수립, subtask 분해
2. **Coder Agent**: 코드 작성 (subagent 병렬 처리)
3. **QA Reviewer**: 코드 리뷰, 테스트 실행
4. **QA Fixer**: 이슈 수정 (필요시)

**사용법 (CLI):**
```bash
cd AG/Auto-Claude
python cli.py run --task "계산기 앱 만들어줘"  # single task
python cli.py                                    # 24/7 factory
```

**Git Worktree:**
- 브랜치: `auto-claude/{spec-name}`
- 디렉토리: `.worktrees/{spec-name}/`
- 안전한 격리 빌드 후 병합

---

## 실행 흐름 (상세)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           전체 실행 흐름                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 사용자 입력                                                             │
│     └─ "계산기 앱 만들어줘" (Platform UI Playground 또는 CLI)              │
│                                                                             │
│  2. AutoGen Studio Engine                                                   │
│     └─ POST /api/sessions/ → POST /api/runs/                              │
│     └─ WS ws://localhost:8081/api/ws/runs/{run_id}                        │
│     └─ Team 실행 (pattern에 따라 agent 순차/선택/핸드오프)                │
│                                                                             │
│  3. Platform UI (Playground)                                                │
│     └─ WebSocket으로 실시간 agent turn 수신                               │
│     └─ AgentTurnCard로 각 agent 출력 표시                                 │
│                                                                             │
│  4. Auto-Claude CLI (24/7 mode, optional)                                  │
│     ├─ AG/Auto-Claude CLI가 파이프라인 실행                               │
│     │   Claude Agent SDK (query()) 기반                                    │
│     │   Planner -> Coder -> QA Reviewer -> QA Fixer                       │
│     ├─ Git Worktree 생성 (격리)                                           │
│     ├─ 코드 작성 및 커밋                                                  │
│     └─ QA 통과 시 완료                                                    │
│                                                                             │
│  5. 완료                                                                    │
│     ├─ Platform UI Dashboard에서 통계 확인                                │
│     ├─ run.py --review (리뷰)                                             │
│     └─ run.py --merge (병합)                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 포트 맵

| 서비스 | 포트 | 설명 |
|--------|------|------|
| AutoGen Studio | 8081 | Backend API Engine (필수) |
| Platform UI (Vite) | 5173 | SaaS Frontend (필수) |
| Auto-Claude (Electron) | - | Kanban + 24/7 Pipeline (선택) |
| A2A Agents | 8003-8009, 8120 | 전문 에이전트들 (선택) |
| SharedMemory | 8101 | AG-CLI state sync (선택, fallback) |

---

## Vite Proxy 설정

### Platform UI
```typescript
// AG-frontend/vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8081',
    changeOrigin: true,
  }
}
```

Platform calls `/api/teams` → proxied to `http://localhost:8081/api/teams`.

### Auto-Claude Electron
```typescript
// electron.vite.config.ts
'/api/autogen': {
  target: 'http://localhost:8081',
  changeOrigin: true,
  rewrite: (path) => path.replace(/^\/api\/autogen/, '/api'),
}
```

---

## 4-Layer Architecture (AG/Auto-Claude CLI)

```
Layer 1: Coordinator (coordinator/)
  ├── Orchestrator      24/7 메인 루프, 태스크 디스패치
  ├── TaskQueue          SQLite 우선순위 큐 (high/medium/low)
  ├── AgentSelector      에이전트 스코어링 & 선택 알고리즘
  └── PipelineBuilder    동적 파이프라인 구성

Layer 2: Pipeline (pipeline/)
  ├── SequentialPipeline  순차 실행 (stage output -> next stage context)
  ├── ParallelPipeline    병렬 실행 (fan-out -> gather)
  └── CriticLoopPipeline  생성-비평-수정 반복 (max 5 iterations)

Layer 3: Adapters (adapters/)
  ├── AutoClaudeAdapter     Claude Agent SDK + OAuth
  ├── AGAutogenAdapter      HTTP REST
  ├── AGA2AAdapter          JSON-RPC 2.0 (Google ADK)
  ├── AGLawDomainAdapter    HTTP REST
  └── AutogenStudioAdapter  AutoGen Studio 연동

Layer 4: Registry (coordinator/)
  ├── AgentRegistry     에이전트 상태, 헬스체크, 성공률 추적
  └── SharedMemoryClient  AG/Auto-Claude 8101 동기화 (optional)
```

### Pipeline Templates (사전 정의)

```
auto_claude_full:
  Planner (Sequential) -> Coder (Sequential) -> QA (Critic Loop, max 5)
    QA Loop: Coder -> QA Reviewer -> QA Fixer -> (반복)

research:
  Research + Analyst (Parallel) -> Writer (Sequential)

legal_validation:
  Legal Researcher (Sequential) -> Case Analyzer + Compliance (Parallel) -> Risk Assessor

qa_loop:
  Coder (Critic Loop): Coder -> QA Reviewer -> QA Fixer -> (반복)
```

---

## 에이전트 전체 목록 (24개)

### Auto-Claude Pipeline (4)

| Agent | AgentType | Role | Adapter |
|-------|-----------|------|---------|
| Planner | `auto_claude.planner` | 태스크 분해, 구현 계획 | Claude Agent SDK |
| Coder | `auto_claude.coder` | 24/7 자율 코딩 | Claude Agent SDK |
| QA Reviewer | `auto_claude.qa_reviewer` | E2E 테스트, 품질 검증 | Claude Agent SDK |
| QA Fixer | `auto_claude.qa_fixer` | 이슈 수정, 디버깅 | Claude Agent SDK |

### AG AutoGen (5)

| Agent | AgentType | Role |
|-------|-----------|------|
| Research | `ag.research` | 정보 수집, 웹 검색 |
| Analyst | `ag.analyst` | 데이터 분석, 패턴 탐지 |
| Writer | `ag.writer` | 문서 작성 |
| Reviewer | `ag.reviewer` | 피드백, 품질 평가 |
| Coordinator | `ag.coordinator` | 작업 조율 |

### AG Law Domain (5)

| Agent | AgentType | Role | Neo4j |
|-------|-----------|------|-------|
| Case Analyzer | `ag.case_analyzer` | 판례 분석 | 판례 지식 그래프 |
| Legal Researcher | `ag.legal_researcher` | 법률 조사 | 법령 DB |
| Risk Assessor | `ag.risk_assessor` | 리스크 평가 | 리스크 패턴 |
| Compliance | `ag.compliance_checker` | 컴플라이언스 검증 | 규정 DB |
| Document Drafter | `ag.document_drafter` | 문서 초안 | 템플릿 |

### AG A2A Protocol (10)

| Agent | AgentType | Port | Protocol |
|-------|-----------|------|----------|
| Poetry | `ag.a2a.poetry_agent` | 8003 | JSON-RPC 2.0 |
| Philosophy | `ag.a2a.philosophy_agent` | 8004 | JSON-RPC 2.0 |
| History | `ag.a2a.history_agent` | 8005 | JSON-RPC 2.0 |
| Calculator | `ag.a2a.calculator_agent` | 8006 | JSON-RPC 2.0 |
| Math | `ag.a2a.math_agent` | 8007 | JSON-RPC 2.0 |
| Graphics | `ag.a2a.graphics_agent` | 8008 | JSON-RPC 2.0 |
| GPU | `ag.a2a.gpu_agent` | 8009 | JSON-RPC 2.0 |
| History Helper | `ag.a2a.history_helper_agent` | 8001 | JSON-RPC 2.0 |
| Prime Checker | `ag.a2a.prime_checker_agent` | 8002 | JSON-RPC 2.0 |
| GUI Test | `ag.a2a.gui_test_agent` | 8120 | JSON-RPC 2.0 |

---

## Platform UI Frontend 아키텍처

### Feature-Based 구조
```
AG-frontend/src/
├── app/              # Shell: App.tsx, router.tsx, providers.tsx
├── features/         # Domain modules (self-contained)
│   ├── agents/       # AgentsPage
│   ├── auth/         # auth.ts, authStore (Zustand)
│   ├── dashboard/    # DashboardPage
│   ├── history/      # HistoryPage
│   ├── playground/   # PlaygroundPage, executionStore, useExecution
│   ├── settings/     # SettingsPage
│   └── teams/        # TeamsPage, teamStore, useTeams (TanStack Query)
├── shared/           # Cross-cutting
│   ├── api/          # client.ts (REST), ws.ts (WebSocket), index.ts
│   ├── animations/   # Framer Motion presets
│   ├── hooks/        # useUsage (health/version)
│   ├── lib/          # utils (cn)
│   ├── theme/        # 7 themes × 2 modes (14 configs)
│   ├── types/        # datamodel.ts (AutoGen type system), index.ts
│   └── ui/           # 7 components (Button, Badge, Card, Input, Avatar, Toggle, ProgressCircle)
└── main.tsx
```

### API Client 흐름
```
Platform UI -> fetch('/api/teams') -> Vite Proxy -> http://localhost:8081/api/teams
                                                             ↓
                                                    AutoGen Studio Engine
                                                             ↓
                                              { status: true, data: [...teams] }
```

### WebSocket 실행 흐름
```
1. POST /api/sessions/ -> session.id
2. POST /api/runs/ -> run.run_id
3. WS ws://localhost:5173/api/ws/runs/{run_id}?token=...
   -> Vite proxy -> ws://localhost:8081/api/ws/runs/{run_id}
4. Send: { type: "start", task: "...", team_config: {...} }
5. Receive: { type: "message", data: { source: "coder", content: "..." } }
6. Receive: { type: "completion" }
```

---

## Auto-Claude Frontend 상세 아키텍처 (Electron)

### 이중 모드 (Electron vs Browser)

```
[Electron Mode]
  Renderer -> a2a-api.ts (preload) -> IPC -> a2a-handlers.ts (main) -> HTTP to 8081

[Browser Mode]
  Renderer -> browser-mock.ts -> Vite Proxy (/api/autogen -> 8081)
                               -> AG/Auto-Claude CLI (direct Python import)
```

### KanbanBoard.tsx 핵심 구조

```
State:
  autogenTasks: Task[]           AutoGen에서 변환된 카드들
  pipelineTasks: Task[]          AG/Auto-Claude 파이프라인 카드들
  pipelineProjects: Project[]    활성 파이프라인 프로젝트

Refs (24/7 안전장치):
  processedSessionsRef: Set      이미 trigger한 세션 ID
  triggerLogRef: Record          trigger 상태 (triggered/running/done/error)
  triggerQueueRef: Array         trigger 대기 큐 (직렬 처리)
  isProcessingQueueRef: boolean  큐 처리 중 mutex
  initialLoadDoneRef: boolean    초기 로드 완료 (기존 세션 skip)
```

---

## JSON_MODULES - n8n-Style Composable Components

### $ref Resolver System

```
templates_compact/*.json  ->  ref_resolver.py  ->  resolved/*.json
   ($ref + _defaults)          (resolve)            (full inline)
                                                         |
                                                    POST /api/teams/
                                                    AutoGen Studio DB
```

### Component Hierarchy

- 23 Agents (7 Auto-Claude + 5 Debate/Reflection + 11 Sequential/Selector/Handoff)
- 10 A2A Agents (Google ADK, ports 8001-8120)
- 7 Models (3 Claude + 4 Default)
- 7 Team Templates (compact $ref format)
- 98 total JSON files, 0 validation failures

---

## AutoGen Studio 데이터 저장

```
~/.autogenstudio/
├── autogen04203.db          # SQLite (teams, sessions, messages, runs)
├── .env                     # 환경 설정
├── files/user/              # 업로드 파일
└── configs/                 # JSON/YAML 팀 설정 import

환경변수:
  AUTOGENSTUDIO_APPDIR          -> 앱 루트 (default: ~/.autogenstudio)
  AUTOGENSTUDIO_DATABASE_URI    -> DB 경로 (default: sqlite:///./autogen04203.db)
  AUTOGENSTUDIO_DEFAULT_USER_ID -> 사용자 (default: guestuser@gmail.com)
```

---

## 테스트

| File | Description | Status |
|------|-------------|--------|
| `AG-frontend/e2e/*.spec.ts` | Platform Playwright E2E (navigation, theme, playground) | Configured |
| `JSON_MODULES/e2e_playwright_test.py` | Playwright + WebSocket E2E (9 tests, 598s) | 9 PASS |
| `JSON_MODULES/validate_json.py` | 98 JSON 파일 검증 | 98 PASS, 0 FAIL |
| `cd platform && npm run build` | Platform 프로덕션 빌드 | OK (0 TS errors) |

---

## 변경 이력

| Date | Change |
|------|--------|
| 2026-02-08 | Platform UI (Vite + React 19) 추가, AG-ACE-BRIDGE 완전 제거, 아키텍처 전면 재작성 |
| 2026-02-07 | AG-ACE-BRIDGE 삭제 반영, AG/Auto-Claude CLI로 전환 |
| 2026-02-07 | JSON_MODULES $ref resolver 아키텍처 추가 |
| 2026-02-07 | A2A agents 5 -> 10개 확장, 서비스 포트 정리 |
| 2026-01-31 | ARCHITECTURE.md 전면 재작성 (현재 구현 기준) |
