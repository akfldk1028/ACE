# 25_ACE System Architecture

24/7 AI Project Factory - AutoGen Studio 엔진 + Platform UI (Vite + React 19)

마지막 검증: 2026-02-08 (빌드 OK, E2E PASS, 0 TS errors)

> 상세 아키텍처: [../ARCHITECTURE.md](../ARCHITECTURE.md)

---

## 전체 시스템 아키텍처

```
+=========================================================================+
|                        25_ACE ECOSYSTEM                                  |
+=========================================================================+
|                                                                          |
|  [1] Platform UI (5173/Vite)     [2] Auto-Claude (Electron)             |
|  +--------------------------+     +----------------------------------+  |
|  | Dashboard (통계)         |     | Kanban Board (5 columns)         |  |
|  | Teams (팀 관리)          |     |   Planning/InProgress/AIReview   |  |
|  | Playground (WS 실행)     |     |   HumanReview/Done               |  |
|  | History (이력)           |     | Agent Terminals                  |  |
|  | Agents (마켓)            |     | MCP Overview                     |  |
|  | Settings (설정)          |     | 24/7 Auto-Trigger Pipeline       |  |
|  +-----------+--------------+     +------+---------------------------+  |
|              |                           |                              |
|   Vite: /api/* -> 8081                   |  CLI direct invocation       |
|              |                           |                              |
|              v                           v                              |
|  +---------------------------+    +---------------------------+         |
|  | AutoGen Studio (:8081)    |    | [3] AG/Auto-Claude CLI    |         |
|  | Backend API Engine        |    | CLI Orchestrator +         |         |
|  |                           |    | Pipeline                   |         |
|  | REST + WebSocket API      |    |                           |         |
|  | Teams / Sessions / Runs   |    | Pipeline:                  |         |
|  | Gallery / A2A Registry    |    |   Planner -> Coder ->      |         |
|  |                           |    |   QA Reviewer -> QA Fixer  |         |
|  | SQLite DB                 |    |                           |         |
|  +---------------------------+    +---------------------------+         |
|                                                                          |
|  [Optional]                                                              |
|  +---------------------------+    +---------------------------+         |
|  | A2A Agents (8003-8120)    |    | SharedMemory (8101)        |         |
|  | 10 agents, JSON-RPC 2.0   |    | AG-CLI state sync          |         |
|  +---------------------------+    +---------------------------+         |
|                                                                          |
+=========================================================================+
```

---

## Platform UI (SaaS Frontend)

| 항목 | 값 |
|------|-----|
| URL | http://localhost:5173 |
| 스택 | Vite 7 + React 19 + TypeScript 5.9 + Tailwind v4 |
| Proxy | `/api/*` → `localhost:8081` (AutoGen Studio) |

### Feature-Based 구조
```
AG-frontend/src/
├── app/              # App shell (router, providers)
├── features/         # Domain modules
│   ├── playground/   # PlaygroundPage, executionStore (WS + turns)
│   ├── teams/        # TeamsPage, teamStore, useTeams (TanStack Query)
│   ├── dashboard/    # DashboardPage
│   ├── history/      # HistoryPage
│   ├── agents/       # AgentsPage
│   └── settings/     # SettingsPage
├── shared/           # Cross-cutting
│   ├── api/          # client.ts (REST), ws.ts (WebSocket)
│   ├── types/        # datamodel.ts (AutoGen type system)
│   ├── ui/           # 7 components + layout
│   └── theme/        # 7 themes x 2 modes
└── main.tsx
```

---

## 핵심 데이터 흐름

### Flow 1: Platform UI → AutoGen Studio 실행

```
1. Platform UI Playground에서 팀 선택 + 태스크 입력
2. POST /api/sessions/ → session.id
3. POST /api/runs/ → run.run_id
4. WS ws://localhost:5173/api/ws/runs/{run_id}?token=...
   → Vite proxy → ws://localhost:8081/api/ws/runs/{run_id}
5. Send: { type: "start", task: "...", team_config: {...} }
6. Receive: { type: "message", data: { source: "coder", content: "..." } }
7. AgentTurnCard로 각 agent 출력 실시간 표시
8. Receive: { type: "completion" }
```

### Flow 2: 24/7 Auto-Trigger Pipeline (Auto-Claude Electron)

```
1. AutoGen 세션 complete → 3초 폴링 감지
2. triggerQueueRef에 추가 → processQueue() 순차 실행
3. AG/Auto-Claude CLI가 파이프라인 실행
   Claude Agent SDK → Planner → Coder → QA Reviewer → QA Fixer
4. Kanban 카드에 trigger 상태 표시
```

---

## 서비스 포트

| Service | Port | Required | Start Command |
|---------|------|----------|---------------|
| AutoGen Studio | 8081 | **Yes** (backend) | `autogenstudio ui --port 8081` |
| Platform UI (Vite) | 5173 | **Yes** (frontend) | `cd platform && npm run dev` |
| Auto-Claude (Electron) | - | Optional | `cd AG/Auto-Claude/apps/frontend && npm run dev` |
| SharedMemory | 8101 | Optional | `python mcp/shared_memory.py` |
| A2A Agents | 8003-8120 | Optional | `python run_all_agents.py` |

---

## JSON_MODULES - n8n-Style Composable Components

### $ref Resolver System

```
templates_compact/*.json  →  ref_resolver.py  →  resolved/*.json
   ($ref + _defaults)          (resolve)            (full inline)
                                                         |
                                                    POST /api/teams/
                                                    AutoGen Studio DB
```

- 23 Agents + 10 A2A + 7 Models + 7 Team Templates
- 98 total JSON files, 0 validation failures

---

## 변경 이력

| Date | Change |
|------|--------|
| 2026-02-08 | Platform UI 추가, AG-ACE-BRIDGE 완전 제거, 아키텍처 전면 재작성 |
| 2026-02-07 | AG-ACE-BRIDGE 삭제 반영, AG/Auto-Claude CLI로 전환 |
| 2026-02-07 | JSON_MODULES $ref resolver, A2A 10개 확장 |
| 2026-01-31 | ARCHITECTURE.md 전면 재작성 |
