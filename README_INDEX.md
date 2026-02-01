# 25_ACE README INDEX

AI가 이 프로젝트를 이해하기 위한 전체 문서 인덱스.
마지막 검증: 2026-01-31 (빌드 OK, E2E PASS, 38 cards, 100+ sessions)

---

## 이 프로젝트가 뭔지 한줄 요약

AutoGen Studio에서 multi-agent 팀이 설계/분석/코딩/리뷰하면, Auto-Claude가 자동으로 감지해서 빌드 파이프라인을 실행하는 24/7 AI 코딩 공장.

---

## AI가 먼저 읽어야 할 파일 (우선순위)

| 순서 | 파일 | 왜 읽어야 하는지 |
|:----:|------|-----------------|
| 1 | **[README.md](README.md)** | 전체 아키텍처, agent 분해 로직, 24/7 auto-trigger, 데이터 흐름 |
| 2 | **[Auto-Claude/CLAUDE.md](Auto-Claude/CLAUDE.md)** | Auto-Claude SDK, agent 구조, 보안 모델 |
| 3 | **[AG-ACE-BRIDGE/CLAUDE.md](AG-ACE-BRIDGE/CLAUDE.md)** | Bridge 오케스트레이터, 파이프라인, 어댑터 |
| 4 | [docs/AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md) | 서버 시작 순서 |

---

## 전체 디렉토리 구조

```
25_ACE/
├── README.md                       # 메인 문서 (아키텍처, 데이터 흐름, agent 목록)
├── README_INDEX.md                 # 이 파일 (AI 네비게이션)
├── ARCHITECTURE.md                 # 시스템 아키텍처
│
├── Auto-Claude/                    # Electron 앱 (Kanban, Pipeline, MCP)
│   ├── CLAUDE.md                   # AI 컨텍스트
│   ├── README_INDEX.md             # Auto-Claude 문서 인덱스
│   └── apps/frontend/
│       ├── electron.vite.config.ts       # Vite proxy (/api/autogen -> 8081)
│       └── src/
│           ├── main/ipc-handlers/
│           │   └── a2a-handlers.ts       # Electron IPC: AutoGen API (max 10 sessions)
│           ├── renderer/
│           │   ├── components/
│           │   │   ├── KanbanBoard.tsx   # ★ 핵심: agent 분해, 24/7 auto-trigger, 폴링
│           │   │   └── TaskCard.tsx      # 카드 렌더링, trigger status, memo comparator
│           │   └── lib/
│           │       └── browser-mock.ts   # AutoGen API 호출 (max 10 sessions)
│           ├── preload/api/modules/
│           │   └── a2a-api.ts            # Preload API bridge
│           └── shared/
│               ├── constants/ipc.ts      # IPC channel 상수
│               └── types/ipc.ts          # IPC 타입 정의
│
├── AG-ACE-BRIDGE/                  # Pipeline 서버 (FastAPI, 8080)
│   ├── CLAUDE.md                   # AI 컨텍스트
│   ├── README_INDEX.md             # Bridge 문서 인덱스
│   ├── main.py                     # 엔트리포인트
│   └── src/
│       ├── server/
│       │   ├── __init__.py         # FastAPI 서버 설정
│       │   ├── dashboard.py        # 대시보드 라우트
│       │   └── pipeline_routes.py  # 파이프라인 API 라우트
│       ├── coordinator/
│       │   └── orchestrator.py     # 24/7 메인 루프
│       ├── pipeline/               # 실행 파이프라인
│       ├── adapters/               # Agent 어댑터 (A2A, Claude SDK, AutoGen)
│       └── memory/                 # Memory sync (Graphiti, Neo4j)
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
├── Calculator/                     # 예제 프로젝트 (agent 데모)
│
├── docs/
│   ├── AI_STARTUP_GUIDE.md         # 서버 시작 순서
│   ├── PROJECT_START_GUIDE.md      # 3 UI 조정 가이드
│   ├── WORKFLOW_EXAMPLE.md         # GitHub Issue -> PR 예시
│   └── e2e_*.png, step*.png        # E2E 테스트 스크린샷
│
├── test_e2e_dual_browser.py        # Playwright 듀얼 브라우저 E2E 테스트
├── test_functional.py              # 기능 검증 테스트
└── test_step_by_step.py            # 단계별 스크린샷 테스트
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
| AutoGen Studio | 8081 | Yes | `autogenstudio ui --port 8081` |
| Auto-Claude (dev) | 5173 | Yes | `cd Auto-Claude/apps/frontend && npm run dev` |
| AG-ACE-BRIDGE | 8080 | Pipeline용 | `cd AG-ACE-BRIDGE && python main.py` |
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
| `Auto-Claude/.../KanbanBoard.tsx` | Kanban + agent 분해 + auto-trigger | 매우 높음 |
| `Auto-Claude/.../TaskCard.tsx` | 카드 UI + memo comparator | 높음 |
| `Auto-Claude/.../browser-mock.ts` | AutoGen API 호출 | 중간 |
| `Auto-Claude/.../a2a-handlers.ts` | Electron IPC | 중간 |
| `Auto-Claude/.../electron.vite.config.ts` | Vite proxy | 낮음 |
| `AG-ACE-BRIDGE/src/server/pipeline_routes.py` | Pipeline API | 중간 |
| `AG-ACE-BRIDGE/src/server/dashboard.py` | Dashboard | 중간 |
| `AG-ACE-BRIDGE/src/coordinator/orchestrator.py` | 24/7 메인 루프 | 중간 |
| `AG-ACE-BRIDGE/src/coordinator/pipeline_builder.py` | 동적 파이프라인 | 낮음 |
| `AG-ACE-BRIDGE/src/coordinator/agent_selector.py` | 에이전트 스코어링 | 낮음 |

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

### AG-ACE-BRIDGE 수정 시
1. **Orchestrator state machine**: STOPPED -> STARTING -> RUNNING -> PAUSED 전이 순서 준수
2. **Pipeline stage context**: 각 stage output이 다음 stage의 context로 전달됨
3. **TaskQueue retry**: max 3회 재시도, 그 이후 FAILED
4. **Critic loop**: max 5 iterations, QA Reviewer가 PASS 하면 즉시 종료

---

## AG-ACE-BRIDGE 4-Layer 요약

```
Layer 1: Coordinator
  Orchestrator(24/7 loop) + TaskQueue(SQLite) + AgentSelector(scoring) + PipelineBuilder(dynamic)

Layer 2: Pipeline
  Sequential(chain) + Parallel(fan-out/gather) + CriticLoop(generator-critic-fixer, max 5)

Layer 3: Adapters
  AutoClaudeAdapter(SDK) + AGAutogenAdapter(REST) + AGA2AAdapter(JSON-RPC) + AGLawDomainAdapter + AutogenStudioAdapter

Layer 4: Registry
  AgentRegistry(19 agents, health, success rate) + SharedMemoryClient(8101, optional)
```

### Pipeline Templates

| Template | Stages | Use Case |
|----------|--------|----------|
| `auto_claude_full` | Planner -> Coder -> QA Critic Loop(x5) | 일반 코딩 |
| `research` | Research + Analyst (Parallel) -> Writer | 리서치 기반 |
| `legal_validation` | Researcher -> Analyzer + Compliance (Parallel) -> Risk | 법률 검증 |
| `qa_loop` | Coder -> QA Reviewer -> QA Fixer (Critic Loop) | QA 집중 |

### Task Priority & Retry

```
Priority: high(3) > medium(2) > low(1), ORDER BY priority_weight DESC, created_at ASC
Retry: max 3회, 실패 시 PENDING으로 re-queue
Timeout: stage당 300초 (5분)
Cleanup: completed/cancelled 7일 후 자동 삭제
```

---

## 테스트

| 파일 | 내용 | 결과 |
|------|------|------|
| `test_e2e_dual_browser.py` | Playwright 2 브라우저 (AutoGen + Auto-Claude) | PASS |
| `test_functional.py` | 기능별 검증 (9 pages, 6 buttons, API) | PASS |
| `test_step_by_step.py` | 단계별 스크린샷 캡처 | PASS |
| `npm run build` | Auto-Claude 프로덕션 빌드 | OK (에러 없음) |

---

## AutoGen Studio Windows 주의사항

- `npm run build` 실행 금지 -> `web/ui/` 삭제됨
- 소스 수정은 minified JS 직접 패치 방식
- 상세: [frontend/README.md](../22_AG/autogen_a2a_kit/autogen_source/python/packages/autogen-studio/frontend/README.md)

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
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
