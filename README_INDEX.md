# 25_ACE README INDEX

AI가 이 프로젝트를 이해하기 위한 전체 문서 인덱스.
마지막 검증: 2026-02-08 (98 PASS, 7 team templates, 23 agents, 10 A2A, E2E 9/9 PASS, Platform UI 0 TS errors)

---

## 이 프로젝트가 뭔지 한줄 요약

AutoGen Studio에서 multi-agent 팀이 설계/분석/코딩/리뷰하면, Auto-Claude가 자동으로 감지해서 빌드 파이프라인을 실행하는 24/7 AI 코딩 공장.

---

## AI가 먼저 읽어야 할 파일 (우선순위)

| 순서 | 파일 | 왜 읽어야 하는지 |
|:----:|------|-----------------|
| 1 | **[README.md](README.md)** | 전체 아키텍처, agent 분해 로직, 24/7 auto-trigger, 데이터 흐름 |
| 2 | **[AG-frontend/](AG-frontend/)** | SaaS Frontend (Vite + React 19), API client, WebSocket, 6 pages |
| 3 | **[AG/Auto-Claude/CLAUDE.md](AG/Auto-Claude/CLAUDE.md)** | Auto-Claude SDK, agent 구조, 보안 모델 |
| 4 | **[JSON_MODULES/README.md](JSON_MODULES/README.md)** | JSON 컴포넌트 모듈, $ref 시스템, A2A 통합 |
| 5 | [docs/AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md) | 서버 시작 순서 |

---

## 전체 디렉토리 구조

```
25_ACE/
├── README.md                       # 메인 문서 (아키텍처, 데이터 흐름, agent 목록)
├── README_INDEX.md                 # 이 파일 (AI 네비게이션)
├── ARCHITECTURE.md                 # 시스템 아키텍처
│
├── AG-frontend/                       # ★ SaaS Frontend (Vite 7 + React 19 + Tailwind v4)
│   ├── src/
│   │   ├── app/                    # App shell (router, providers)
│   │   ├── features/               # Domain modules
│   │   │   ├── playground/         # 실시간 실행 (WebSocket + agent turn cards)
│   │   │   ├── teams/              # 팀 목록, 선택
│   │   │   ├── dashboard/          # 대시보드
│   │   │   ├── history/            # 실행 이력
│   │   │   ├── agents/             # 에이전트 마켓
│   │   │   └── settings/           # 설정
│   │   └── shared/                 # Cross-cutting
│   │       ├── api/                # client.ts (REST), ws.ts (WebSocket)
│   │       ├── types/              # datamodel.ts (AutoGen type system)
│   │       ├── ui/                 # 7 components (Button, Badge, Card, Input, etc.)
│   │       └── theme/              # 7색 × 2모드 테마
│   └── vite.config.ts              # /api/* -> localhost:8081 proxy
│
├── AG/Auto-Claude/                 # Electron 앱 + CLI 24/7 Hub
│   ├── CLAUDE.md                   # AI 컨텍스트
│   ├── README_INDEX.md             # Auto-Claude 문서 인덱스
│   └── apps/frontend/
│       ├── electron.vite.config.ts       # Vite proxy (/api/autogen -> 8081)
│       └── src/
│           ├── main/ipc-handlers/
│           │   ├── a2a-handlers.ts       # Electron IPC: AutoGen API (max 10 sessions)
│           │   └── task/
│           │       ├── worktree-handlers.ts   # Worktree 관리 (리팩토링됨)
│           │       ├── worktree-git-utils.ts  # ★ NEW: Git 유틸 함수 분리
│           │       ├── worktree-ide-tools.ts  # ★ NEW: IDE 도구 통합 분리
│           │       ├── worktree-pr-utils.ts   # ★ NEW: PR 유틸 함수 분리
│           │       ├── crud-handlers.ts       # Task CRUD (improved)
│           │       ├── execution-handlers.ts  # Task 실행 (improved)
│           │       └── shared.ts              # 공유 유틸
│           ├── renderer/
│           │   ├── components/
│           │   │   ├── KanbanBoard.tsx   # ★ 핵심: agent 분해, 24/7 auto-trigger, 폴링
│           │   │   ├── TaskCard.tsx      # 카드 렌더링, trigger status, memo comparator
│           │   │   ├── task-detail/
│           │   │   │   ├── TaskDetailModal.tsx  # Task 상세 모달 (improved)
│           │   │   │   ├── TaskWarnings.tsx     # Task 경고 표시 (improved)
│           │   │   │   └── hooks/useTaskDetail.ts # Task 상세 훅 (improved)
│           │   │   └── AutogenCollabPanel.tsx  # AutoGen 협업 패널
│           │   ├── lib/
│           │   │   └── browser-mock.ts   # AutoGen API 호출 (max 10 sessions)
│           │   └── stores/
│           │       └── task-store.ts     # Task 상태 관리 (improved)
│           ├── preload/api/modules/
│           │   └── a2a-api.ts            # Preload API bridge
│           └── shared/
│               ├── constants/ipc.ts      # IPC channel 상수
│               ├── types/ipc.ts          # IPC 타입 정의
│               └── i18n/locales/
│                   ├── en/tasks.json     # 영어 번역 (expanded)
│                   └── fr/tasks.json     # 프랑스어 번역 (expanded)
│
├── JSON_MODULES/                   # n8n-style 조합 가능한 JSON 컴포넌트
│   ├── agents/                     # 23 에이전트 정의
│   ├── a2a_agents/                 # 10 A2A 에이전트 (ports 8001-8120)
│   ├── models/                     # 7 모델 설정
│   ├── patterns/                   # 14 오케스트레이션 패턴
│   ├── templates_compact/          # 7 컴팩트 템플릿 ($ref 사용)
│   ├── resolved/                   # resolve 출력
│   ├── registry.json               # 중앙 레지스트리
│   ├── ref_resolver.py             # $ref 리졸버 엔진
│   ├── validate_json.py            # 98 파일 검증
│   ├── a2a_manager.py              # A2A 에이전트 관리 CLI
│   └── e2e_playwright_test.py      # E2E 테스트 (9/9 PASS)
│
├── AG/                             # 멀티 에이전트 시스템
│   ├── .claude/CLAUDE.md           # AI 컨텍스트
│   ├── README_INDEX.md             # AG 문서 인덱스
│   ├── autogen_a2a_kit/            # AutoGen + A2A 통합
│   │   ├── a2a_demo/               # 10개 A2A 에이전트
│   │   ├── AG_Cohub/               # 패턴 갤러리 (12 패턴)
│   │   └── AG-cli/                 # SharedMemory (8101)
│   ├── agent/                      # 에이전트 프로젝트
│   │   └── law-domain-agents/      # 법률 도메인 5개 에이전트
│   └── agent_core/                 # 공유 라이브러리
│
├── maintenance/                    # 유지보수 스크립트
│   ├── run_maintenance.py          # 전체 유지보수 실행
│   ├── health_check.py             # 서비스 헬스 체크
│   ├── port_map_validator.py       # 포트 매핑 검증
│   ├── doc_sync_checker.py         # 문서 동기화 체크
│   ├── agent_registry_sync.py      # 에이전트 레지스트리 동기화
│   └── model_field_checker.py      # 모델 필드 검증
│
├── docs/
│   ├── AI_STARTUP_GUIDE.md         # 서버 시작 순서
│   ├── PROJECT_START_GUIDE.md      # 3 UI 조정 가이드
│   ├── WORKFLOW_EXAMPLE.md         # GitHub Issue -> PR 예시
│   └── e2e_*.png, step*.png        # E2E 테스트 스크린샷
│
└── start_autogen.bat / .ps1        # AutoGen Studio 시작 스크립트
```

---

## 핵심 개념 (AI가 이해해야 할 것)

### 1. Agent-Level Decomposition

AutoGen 세션 1개 = Kanban 카드 N개. 세션 안의 각 agent 메시지가 개별 카드로 분해됨.

```
GET /api/sessions/136/runs -> runs[0].team_result.task_result.messages[]
  messages[0] { source: "user",              content: "TODO CLI 만들어줘" }
  messages[1] { source: "insights_agent",    content: "## Insights Report..." }
  messages[2] { source: "deep_research_agent", content: "## Research Report..." }
  messages[3] { source: "spec_writer_agent", content: "## Project Specification..." }
  messages[4] { source: "planner_agent",     content: "## Implementation Plan..." }
  messages[5] { source: "coder_agent",       content: "```python..." }
  messages[6] { source: "qa_reviewer_agent", content: "## QA Review Report PASS" }
```

`autogenRunToTasks()` in KanbanBoard.tsx:
- 1개 헤더 카드 (세션 전체 요약)
- N개 agent 카드 (각 agent의 출력, 300자 미리보기)

`agentToColumn()` in KanbanBoard.tsx:
- insight/plan/architect/research/spec -> Planning
- code/implement/develop/fix -> In Progress
- review/qa/test/critic -> AI Review
- complete 세션 -> Done
- error 세션 -> Human Review

### 2. 24/7 Auto-Trigger

KanbanBoard.tsx의 `fetchAutogenResults()` (3초 폴링):
1. AutoGen API에서 세션 목록 가져옴
2. 새로 complete된 세션 감지 (processedSessionsRef로 중복 방지)
3. triggerQueueRef에 추가
4. processQueue()가 순차적으로 workflowExecute() 호출
5. 10초마다 실행 상태 폴링 (workflowGetExecution)

안전장치:
- initialLoadDoneRef: 앱 시작 시 기존 세션 처리 안 함
- isProcessingQueueRef: 동시 실행 방지 mutex
- 1시간마다 메모리 정리 (max 100 entries)

### 3. Vite Proxy

```
브라우저 -> /api/autogen/sessions -> Vite dev server -> http://localhost:8081/api/sessions
```

electron.vite.config.ts에 설정. Electron에서는 IPC 경유.

### 4. MCP 인프라

MCP Overview 페이지에서 agent별 MCP 서버 설정 가능:
- Context7 (문서 검색) - 활성
- Graphiti Memory (세션간 메모리)
- Linear (프로젝트 관리)
- Electron (데스크톱 자동화)
- Puppeteer (웹 브라우저 자동화)
- Auto-Claude Tools (빌드 추적) - 활성
- Custom Server 추가 가능

각 Kanban 카드의 metadata.agent 필드로 agent 식별 -> 향후 agent별 MCP 라우팅 가능.

### 5. Team 저장 경로 (AutoGen Studio 데이터 흐름)

Team Builder에서 팀 생성 시 순차적 흐름:

```
UI (Team Builder /build/)
  → POST /api/teams/ (JSON body)
    → autogenstudio/web/routes/teams.py
      → DatabaseManager.upsert()
        → SQLite: ~/.autogenstudio/autogen04203.db (team 테이블)
          (Windows: C:\Users\<username>\.autogenstudio\autogen04203.db)
```

DB 테이블 구조:
- `team` 테이블: id, component(JSON=팀 전체 설정), user_id, created_at, updated_at
- `session` 테이블: team_id로 team 참조, 실행 세션 기록
- `message` 테이블: session_id로 session 참조, agent별 메시지 기록

핵심 파일:
- `autogenstudio/web/routes/teams.py` - Team CRUD API
- `autogenstudio/database/db_manager.py` - SQLAlchemy DB 관리
- `autogenstudio/datamodel/db.py` - 스키마 정의 (Team, Session, Message)
- `autogenstudio/teammanager/teammanager.py` - 팀 실행, JSON/YAML import

환경변수: `AUTOGENSTUDIO_APPDIR`, `AUTOGENSTUDIO_DATABASE_URI`로 경로 변경 가능.

---

## 서비스 포트

| 서비스 | 포트 | 필수 | 시작 명령 |
|--------|------|------|-----------|
| AutoGen Studio | 8081 | Yes (backend) | `autogenstudio ui --port 8081` |
| Platform UI (Vite) | 5173 | Yes (frontend) | `cd platform && npm run dev` |
| Auto-Claude (Electron) | - | Optional | `cd AG/Auto-Claude/apps/frontend && npm run dev` |
| SharedMemory | 8101 | Optional | `python mcp/shared_memory.py` |
| A2A Agents | 8003-8120 | Optional | `python run_all_agents.py` |

---

## 에이전트 전체 목록 (19+)

### Auto-Claude Pipeline (4)
| Agent | Role |
|-------|------|
| Planner | 태스크 분해, 구현 계획 |
| Coder | 24/7 자율 코딩 |
| QA Reviewer | E2E 테스트, 품질 검증 |
| QA Fixer | 이슈 수정, 디버깅 |

### AutoGen Studio Team (팀 설정에 따라 가변)
| Agent | Output Example |
|-------|----------------|
| insights_agent | Insights Report (프로젝트 분석) |
| deep_research_agent | Research Report (기술 리서치) |
| spec_writer_agent | Project Specification (spec.md) |
| planner_agent | Implementation Plan (서브태스크 분해) |
| coder_agent | Code implementation |
| qa_reviewer_agent | QA Review Report (PASS/FAIL) |
| qa_fixer_agent | QA Fix Report (수정 사항) |

### AG A2A Protocol (10)
| Agent | Port |
|-------|------|
| poetry_agent | 8003 |
| philosophy_agent | 8004 |
| history_agent | 8005 |
| calculator_agent | 8006 |
| math_agent | 8007 |
| graphics_agent | 8008 |
| gpu_agent | 8009 |
| research_agent | 8010 |
| code_agent | 8011 |
| gui_test_agent | 8120 |

### AG Law Domain (5)
| Agent | Role |
|-------|------|
| Case Analyzer | 판례 분석 |
| Legal Researcher | 법률 조사 |
| Risk Assessor | 리스크 평가 |
| Compliance Checker | 컴플라이언스 |
| Document Drafter | 문서 작성 |

---

## 핵심 파일 (수정 빈도 높은 순)

| 파일 | 역할 | 수정 빈도 |
|------|------|-----------|
| `AG-frontend/src/shared/api/client.ts` | REST API client (AutoGen Studio 1:1) | 높음 |
| `AG-frontend/src/shared/api/ws.ts` | WebSocket client (실행 스트리밍) | 높음 |
| `AG-frontend/src/features/playground/PlaygroundPage.tsx` | 실시간 실행 UI | 높음 |
| `AG-frontend/src/features/playground/executionStore.ts` | Zustand 실행 상태 | 높음 |
| `AG-frontend/src/shared/types/datamodel.ts` | AutoGen TypeScript 타입 시스템 | 중간 |
| `AG-frontend/vite.config.ts` | Vite + /api/* proxy 설정 | 낮음 |
| `AG/Auto-Claude/.../KanbanBoard.tsx` | Kanban + agent 분해 + auto-trigger | 매우 높음 |
| `AG/Auto-Claude/.../TaskCard.tsx` | 카드 UI + memo comparator | 높음 |
| `AG/Auto-Claude/.../task-detail/TaskDetailModal.tsx` | Task 상세 모달 | 높음 |
| `AG/Auto-Claude/.../task-detail/TaskWarnings.tsx` | Task 경고 표시 | 중간 |
| `AG/Auto-Claude/.../task/worktree-handlers.ts` | Worktree 관리 (리팩토링) | 높음 |
| `AG/Auto-Claude/.../task/worktree-git-utils.ts` | Git 유틸 (분리) | 중간 |
| `AG/Auto-Claude/.../task/worktree-ide-tools.ts` | IDE 도구 (분리) | 중간 |
| `AG/Auto-Claude/.../task/worktree-pr-utils.ts` | PR 유틸 (분리) | 중간 |
| `AG/Auto-Claude/.../browser-mock.ts` | AutoGen API 호출 | 중간 |
| `AG/Auto-Claude/.../a2a-handlers.ts` | Electron IPC | 중간 |
| `AG/Auto-Claude/.../stores/task-store.ts` | Task 상태 관리 | 중간 |
| `AG/Auto-Claude/.../electron.vite.config.ts` | Vite proxy | 낮음 |
| `JSON_MODULES/ref_resolver.py` | $ref 리졸버 엔진 | 높음 |
| `JSON_MODULES/validate_json.py` | 98 파일 검증 | 중간 |
| `JSON_MODULES/e2e_playwright_test.py` | E2E 테스트 (9/9 PASS) | 중간 |
| `AG/autogen_a2a_kit/AG_Cohub/model_factory.py` | ClaudeCLI ChatCompletionClient | 높음 |
| `AG/autogen_a2a_kit/AG_Cohub/sdk/` | SDK 패키지 (7 모듈) | 높음 |
| `maintenance/run_maintenance.py` | 전체 유지보수 실행 | 낮음 |

---

## 수정 시 반드시 확인할 것 (다음 AI 필독)

### KanbanBoard.tsx 수정 시
1. **useEffect 의존성 배열**: 함수를 deps에 넣으면 무한루프 발생 위험. useCallback + 안정적 deps 사용
2. **memo comparator**: TaskCard의 `taskCardPropsAreEqual()`에 새 필드 추가 시 비교 로직도 업데이트
3. **Ref vs State**: 24/7 로직은 전부 Ref 사용 (렌더링 트리거 없이 상태 유지)
4. **3초/10초/5초 폴링**: cleanup 함수에서 clearInterval 확인
5. **processedSessionsRef**: 세션 ID 형식 변경 시 기존 entries와 충돌 주의

### TaskCard.tsx 수정 시
1. **memo comparator**: 새 prop/field 추가 시 `taskCardPropsAreEqual()` 반드시 업데이트
2. **Stuck detection**: requestIdleCallback 사용 중 - setTimeout fallback 포함되어 있는지 확인
3. **trigger status badge**: triggerLogRef에서 읽는 값이 header card에만 표시

### browser-mock.ts / a2a-handlers.ts 수정 시
1. **이중 모드**: browser-mock.ts(Vite proxy)와 a2a-handlers.ts(Electron IPC) 양쪽 다 수정 필요
2. **max 10 sessions**: 두 곳 모두 최대 10 세션만 fetch
3. **content truncation**: messages 1000자, descriptions 300자 제한

### worktree-handlers.ts 수정 시 (★ 2026-02-03 리팩토링)
1. **3파일 분리**: worktree-handlers.ts에서 worktree-git-utils.ts, worktree-ide-tools.ts, worktree-pr-utils.ts로 분리됨
2. **import 확인**: worktree-handlers.ts가 3개 유틸 모듈을 import하는 구조
3. **함수 이동**: Git 관련 → git-utils, IDE 도구 → ide-tools, PR 관련 → pr-utils

### JSON_MODULES 수정 시
1. **$ref resolver**: `ref_resolver.py`로 compact template -> resolved JSON 변환. `--all`로 전체 resolve
2. **registry.json**: 에이전트/모델/패턴 중앙 레지스트리. 새 컴포넌트 추가 시 registry에도 등록 필요
3. **validate_json.py**: 98 파일 검증. 새 파일 추가 후 반드시 실행
4. **cohub_loader.py**: `--action compact`로 resolve + AutoGen Studio import
5. **AG-ACE-BRIDGE는 삭제됨**: CLI pipeline 기능은 AG/Auto-Claude로 이전

---

## 테스트

| 파일 | 내용 | 결과 |
|------|------|------|
| `JSON_MODULES/e2e_playwright_test.py` | Playwright + WebSocket E2E (9 tests) | 9 PASS |
| `JSON_MODULES/validate_json.py` | 98 JSON 파일 검증 | 98 PASS |
| `npm run build` | Auto-Claude 빌드 | OK |

---

## AutoGen Studio 참고사항

- AutoGen Studio의 내장 UI(web/ui/)는 더 이상 직접 수정하지 않음
- 커스텀 프론트엔드는 **`AG-frontend/`** (Vite + React 19)을 사용
- AutoGen Studio는 **백엔드 API 엔진으로만** 사용 (REST + WebSocket on :8081)

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-02-08 | Platform UI(Vite + React 19) 추가, Gatsby 참조 전면 제거, AG-frontend/ 디렉토리 구조/파일 목록 추가 |
| 2026-02-07 | README_INDEX 대규모 업데이트: AG-ACE-BRIDGE 삭제 반영, JSON_MODULES 섹션 추가 ($ref 시스템, 98 PASS, 7 templates), Auto-Claude 경로 AG/Auto-Claude로 이전, E2E 9/9 PASS, SDK 패키지 반영 |
| 2026-02-03 | README/INDEX 업데이트: AutoGen 6-team 반영, maintenance system 추가, worktree 리팩토링 (3파일 분리), AG-ACE-BRIDGE 개선사항 반영 |
| 2026-02-01 | Code review fixes + maintenance system (health_check, port_validator, doc_sync, agent_registry, model_field_checker) + AutoGen 6-team setup |
| 2026-01-31 | 전체 문서 딥 업데이트 (ARCHITECTURE.md 전면 재작성, AI_STARTUP_GUIDE.md 정리, README_INDEX에 수정 가이드/4-Layer 요약 추가) |
| 2026-01-31 | AutoGen Studio Team Storage 경로 문서화 (SQLite DB 구조, API endpoints) |
| 2026-01-31 | Team Builder (/build/) 페이지 수정 (page-data + index.html 생성) |
| 2026-01-31 | README/README_INDEX 전면 업데이트 (AI 이해용, 현재 상태 반영) |
| 2026-01-31 | 8개 Critical bug 수정 (useEffect 무한루프, memo comparator, 실행 폴링, 큐 직렬화) |
| 2026-01-31 | 24/7 auto-trigger pipeline 구현 (AutoGen 완료 -> 자동 빌드) |
| 2026-01-31 | Agent-level decomposition 구현 (세션 -> N개 agent 카드) |
| 2026-01-31 | E2E Playwright 듀얼 브라우저 테스트 작성 + 통과 |
| 2026-01-31 | AutoGen Studio Windows 빌드/패치 가이드 추가 |
| 2026-01-24 | Direct connection 구현 (SharedMemory 없이 AutoGen 직접 폴링) |
| 2025-01-23 | README_INDEX.md 생성 |
