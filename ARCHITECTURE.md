# 25_ACE System Architecture

24/7 AI Project Factory - AutoGen Studio에서 multi-agent 팀이 설계하면, Auto-Claude가 자동 감지해서 빌드 파이프라인을 실행.

마지막 검증: 2026-01-31 (빌드 OK, E2E PASS)

---

## 전체 시스템 아키텍처

```
+=========================================================================+
|                        25_ACE ECOSYSTEM                                  |
+=========================================================================+
|                                                                          |
|  [1] AutoGen Studio (8081)        [2] Auto-Claude (5173/Electron)       |
|  +--------------------------+     +----------------------------------+  |
|  | Team Builder (/build)    |     | Kanban Board (5 columns)         |  |
|  |   - 드래그&드롭 팀 설계   |     |   Planning/InProgress/AIReview   |  |
|  |   - Agent 구성            |     |   HumanReview/Done               |  |
|  |                          |     |                                  |  |
|  | Playground (/)           |     | Agent Terminals                  |  |
|  |   - 세션 실행            |     | MCP Overview                     |  |
|  |   - Agent 대화 확인       |     | Pipeline Project                |  |
|  |                          |     |                                  |  |
|  | Gallery (/gallery)       |     | 24/7 Auto-Trigger:               |  |
|  |   - 12개 패턴 갤러리      |     |   3s polling -> detect complete  |  |
|  |                          |     |   -> workflowExecute()           |  |
|  | MCP (/mcp)               |     |   -> AG-ACE-BRIDGE pipeline      |  |
|  +-----------+--------------+     +------+------+--------------------+  |
|              |                           |      |                       |
|   GET /api/sessions (3s polling)         |      | POST /workflow/execute|
|   GET /api/sessions/{id}/runs            |      |                       |
|              |                           |      |                       |
|              v                           v      v                       |
|  +---------------------------+    +---------------------------+         |
|  | SQLite DB                 |    | [3] AG-ACE-BRIDGE (8080)  |         |
|  | ~/.autogenstudio/         |    | FastAPI + Orchestrator     |         |
|  |   autogen04203.db         |    |                           |         |
|  |                           |    | Pipeline:                  |         |
|  | Tables:                   |    |   Planner -> Coder ->      |         |
|  |   team (설정 JSON)        |    |   QA Reviewer -> QA Fixer  |         |
|  |   session (실행 기록)     |    |                           |         |
|  |   message (agent 대화)    |    | 3 Execution Patterns:      |         |
|  |   run (실행 결과)         |    |   Sequential / Parallel    |         |
|  +---------------------------+    |   / Critic Loop            |         |
|                                   +---------------------------+         |
|                                                                          |
|  [Optional]                                                              |
|  +---------------------------+    +---------------------------+         |
|  | A2A Agents (8003-8120)    |    | SharedMemory (8101)        |         |
|  | 10개 전문 에이전트         |    | AG-CLI state sync          |         |
|  | JSON-RPC 2.0 over HTTP    |    | (optional fallback)        |         |
|  +---------------------------+    +---------------------------+         |
|                                                                          |
+=========================================================================+
```

---

## 핵심 데이터 흐름 (순차적)

### Flow 1: AutoGen 세션 -> Kanban 카드 분해

```
1. 사용자가 AutoGen Studio에서 세션 실행
   POST /api/sessions/ -> team 실행 시작

2. AutoGen이 agent별로 순차 실행
   insights_agent -> planner_agent -> coder_agent -> qa_reviewer_agent
   각 agent 출력이 messages[] 배열에 순서대로 저장

3. Auto-Claude 3초 폴링이 감지
   GET /api/autogen/sessions/ (Vite proxy -> 8081)
   GET /api/autogen/sessions/{id}/runs/

4. autogenRunToTasks() 함수가 분해
   1개 세션 -> 1개 헤더카드 + N개 agent 카드

5. agentToColumn() 함수가 컬럼 배치
   insight/plan/research/spec -> Planning
   code/implement/develop     -> In Progress
   review/qa/test/critic      -> AI Review
   complete 세션              -> Done
   error 세션                 -> Human Review

6. Kanban 보드에 실시간 표시
```

### Flow 2: 24/7 Auto-Trigger Pipeline

```
1. AutoGen 세션이 complete 상태로 변경됨

2. fetchAutogenResults() 3초 폴링에서 감지
   - processedSessionsRef로 이미 처리한 세션 제외
   - initialLoadDoneRef: 앱 시작 시 기존 세션은 trigger 안 함

3. triggerQueueRef에 추가 (직렬 큐)
   { sessionId: "136", taskDesc: "Python으로 TODO CLI..." }

4. processQueue()가 순차 실행 (isProcessingQueueRef로 mutex)
   workflowExecute(taskDesc, 'standard', false)
   -> POST http://localhost:8080/workflow/execute

5. AG-ACE-BRIDGE가 파이프라인 실행
   spec_runner.py -> run.py
   Planner -> Coder -> QA Reviewer -> QA Fixer

6. 실행 상태 10초 폴링
   workflowGetExecution(exec_id)
   -> GET http://localhost:8080/workflow/executions/{execId}

7. triggerLogRef에 상태 기록
   'triggered' -> 'running' -> 'done' 또는 'error'

8. Kanban 헤더 카드에 trigger 상태 표시
   ⚡ Pipeline running / ✓ Pipeline done / ✗ Trigger failed
```

### Flow 3: Team 생성 -> 저장

```
1. Team Builder UI (/build/)에서 팀 구성

2. POST /api/teams/ (JSON body: component 필드에 전체 설정)

3. autogenstudio/web/routes/teams.py -> db.upsert(team)

4. SQLAlchemy -> SQLite
   ~/.autogenstudio/autogen04203.db
   (Windows: C:\Users\<username>\.autogenstudio\autogen04203.db)

5. team 테이블에 저장:
   id(PK) | component(JSON) | user_id | created_at | updated_at
```

---

## 4-Layer Architecture (AG-ACE-BRIDGE)

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
  └── SharedMemoryClient  AG-CLI 8101 동기화 (optional)
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

### Auto-Build 로직

```python
def _auto_build_stages(task):
    if task.needs_research:     -> research_first pipeline
    if task.type == CODE:       -> Planner -> Coder -> QA Critic Loop
    if task.type == SPEC/PLAN:  -> Planner only
    if task.type == QA:         -> QA Reviewer + QA Fixer
    if task.domain_validation:  -> + Legal validation stages appended
```

---

## 에이전트 전체 목록 (19개)

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

### AG A2A Protocol (5)

| Agent | AgentType | Port | Protocol |
|-------|-----------|------|----------|
| Poetry | `ag.a2a.poetry_agent` | 8003 | JSON-RPC 2.0 |
| Philosophy | `ag.a2a.philosophy_agent` | 8004 | JSON-RPC 2.0 |
| History | `ag.a2a.history_agent` | 8005 | JSON-RPC 2.0 |
| Calculator | `ag.a2a.calculator_agent` | 8006 | JSON-RPC 2.0 |
| GUI Test | `ag.a2a.gui_test_agent` | 8120 | JSON-RPC 2.0 |

---

## Auto-Claude Frontend 상세 아키텍처

### 이중 모드 (Electron vs Browser)

```
[Electron Mode]
  Renderer -> a2a-api.ts (preload) -> IPC -> a2a-handlers.ts (main) -> HTTP to 8081/8080

[Browser Mode]
  Renderer -> browser-mock.ts -> Vite Proxy (/api/autogen -> 8081, /api/bridge -> 8080)
                               -> Direct HTTP (http://localhost:8080/workflow/*)
```

### KanbanBoard.tsx 핵심 구조

```
State:
  autogenTasks: Task[]           AutoGen에서 변환된 카드들
  pipelineTasks: Task[]          AG-ACE-BRIDGE 파이프라인 카드들
  pipelineProjects: Project[]    활성 파이프라인 프로젝트

Refs (24/7 안전장치):
  processedSessionsRef: Set      이미 trigger한 세션 ID
  triggerLogRef: Record          trigger 상태 (triggered/running/done/error)
  triggerQueueRef: Array         trigger 대기 큐 (직렬 처리)
  isProcessingQueueRef: boolean  큐 처리 중 mutex
  initialLoadDoneRef: boolean    초기 로드 완료 (기존 세션 skip)

Polling Intervals:
  3초: AutoGen 세션 폴링 (autogenPollRef)
  10초: 실행 상태 폴링 (execPollRef)
  5초: 파이프라인 태스크 폴링 (pipelinePollRef)
  60분: 메모리 정리 (triggerLog max 100)

Key Functions:
  autogenRunToTasks(run, sessionId) -> Task[]     세션 -> N개 카드 분해
  agentToColumn(agentName) -> TaskStatus           agent -> 컬럼 매핑
  fetchAutogenResults()                            3초 폴링 메인 루프
  autoTriggerWorkflow()                            새 완료 세션 감지 -> 큐
  processQueue()                                   큐 순차 실행
  pipelineTaskToKanbanStatus(stage, status)        파이프라인 -> 컬럼
```

### TaskCard.tsx Memo 전략

```
taskCardPropsAreEqual() 비교 필드:
  - task.id, status, title, description
  - task.updatedAt (Date.getTime() 비교)
  - task.subtasks 길이 + 각 status
  - task.metadata (category, complexity, archivedAt, prUrl)
  - AutoGen 전용: triggerStatus, runStatus, isLastAgent, agentCount
  - isSelectable, isSelected (선택 모드)

Stuck Detection:
  - 5초 grace period 후 첫 체크
  - 30초마다 재확인
  - phase가 complete/failed/planning이면 skip
  - requestIdleCallback()으로 비차단 체크
```

### IPC 채널 매핑 (22개)

| Category | Channel | Method | Target |
|----------|---------|--------|--------|
| A2A | `a2a:discoverAgents` | GET | A2A agents |
| A2A | `a2a:checkAgentHealth` | GET | A2A agents |
| A2A | `a2a:sendMessage` | POST | A2A agents |
| AutoGen | `autogen:getRunsDetailed` | GET | 8081 |
| AutoGen | `sharedMemory:getAutogenLatest` | GET | 8081 (fallback: 8101) |
| Workflow | `workflow:execute` | POST | 8080 |
| Workflow | `workflow:getExecution` | GET | 8080 |
| Workflow | `workflow:listExecutions` | GET | 8080 |
| Workflow | `workflow:listSpecs` | GET | 8080 |
| Workflow | `workflow:review` | POST | 8080 |
| Workflow | `workflow:merge` | POST | 8080 |
| Pipeline | `pipeline:init` | POST | 8080 |
| Pipeline | `pipeline:plan` | POST | 8080 |
| Pipeline | `pipeline:status` | GET | 8080 |
| Pipeline | `pipeline:tasks` | GET | 8080 |
| SharedMem | `sharedMemory:health` | GET | 8101 |
| SharedMem | `sharedMemory:get` | GET | 8101 |
| SharedMem | `sharedMemory:store` | POST | 8101 |
| SharedMem | `sharedMemory:listKeys` | GET | 8101 |
| SharedMem | `sharedMemory:getA2AHistory` | GET | 8101 |

---

## AG-ACE-BRIDGE 상세 아키텍처

### Orchestrator 상태 머신

```
STOPPED -> STARTING -> RUNNING <-> PAUSED -> STOPPING -> STOPPED
```

### Task 모델

```python
Task:
  id: str (UUID)
  type: research | spec | plan | code | qa | fix | validate | merge | custom
  description: str
  priority: high(3) | medium(2) | low(1)
  input: Dict                    # 입력 데이터
  context: Dict                  # 누적 컨텍스트
  requirements: List[str]        # 필요 capability
  needs_research: bool           # research stage 추가 여부
  domain_validation: bool        # legal validation 추가 여부
  retry_count: int (max 3)
  parent_task_id: Optional[str]  # 서브태스크 연결
```

### Result 모델

```python
Result:
  task_id: str
  status: success | failed | needs_retry | partial | cancelled
  output: Any
  error: Optional[str]
  next_tasks: List[Task]         # 후속 태스크 큐잉
  insights: List[str]            # SharedMemory 저장용
  execution_time_ms: int
  agent_used: str
```

### TaskQueue (SQLite 우선순위 큐)

```
SQLite DB: ./data/tasks.db
  tasks 테이블:
    id, type, description, priority, priority_weight,
    status (pending/in_progress/completed/failed/cancelled),
    input(JSON), context(JSON), requirements(JSON), metadata(JSON),
    created_at, updated_at, started_at, completed_at,
    parent_task_id, retry_count, max_retries, output(JSON), error

  Dequeue: ORDER BY priority_weight DESC, created_at ASC
  Retry: retry_count < max_retries -> re-queue as PENDING
  Cleanup: clear_completed(before_days=7)
```

### Agent Selector 스코어링

```
confidence = 0.5 (baseline)
  + 0.2 if agent.is_available && agent.is_healthy
  + 0.2 * agent.success_rate
  + 0.1 * requirements_match_score
  = min(total, 1.0)

Fallback mapping:
  RESEARCH -> AG_RESEARCH
  SPEC/PLAN -> AUTO_CLAUDE_PLANNER
  CODE -> AUTO_CLAUDE_CODER
  QA -> AUTO_CLAUDE_QA_REVIEWER
  FIX -> AUTO_CLAUDE_QA_FIXER
  VALIDATE -> AG_REVIEWER
  CUSTOM -> AG_COORDINATOR
```

### Dashboard API (8080)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | HTML 대시보드 |
| GET | `/api/status` | Orchestrator 상태 |
| POST | `/api/start` | Orchestrator 시작 |
| POST | `/api/stop` | 정지 |
| POST | `/api/pause` | 일시정지 |
| POST | `/api/resume` | 재개 |
| POST | `/api/project/submit` | 프로젝트 제출 |
| GET | `/api/project/status` | 프로젝트 상태 |
| GET | `/api/a2a/health` | A2A 에이전트 헬스 |
| WS | `/ws` | 실시간 WebSocket (2초 polling) |
| POST | `/workflow/execute` | 워크플로우 실행 |
| GET | `/workflow/executions/{id}` | 실행 상태 |
| GET | `/workflow/executions` | 실행 목록 |
| GET | `/workflow/specs` | Spec 목록 |
| POST | `/workflow/review/{specId}` | 리뷰 |
| POST | `/workflow/merge/{specId}` | 머지 |
| POST | `/pipeline/init` | 파이프라인 프로젝트 생성 |
| POST | `/pipeline/plan` | AutoGen 세션 -> 태스크 분해 |
| GET | `/pipeline/status/{id}` | 파이프라인 상태 |
| GET | `/pipeline/tasks/{id}` | 파이프라인 태스크 목록 |

### SharedMemory 연동 (Optional)

```
SharedMemoryClient -> http://localhost:8101
  store(key, data)          -> POST /decisions/{key}
  get(key)                  -> GET /decisions/{key}
  publish_event(type, data) -> POST /events
  get_events(type, limit)   -> GET /events

Stage 완료 시:
  store_task_result(task_id, stage, result, agent_type)
  notify_stage_complete(task_id, stage, agent_type, success)

Task 완료 시:
  notify_task_complete(task_id, success, artifacts)
```

---

## Vite Proxy 설정

```typescript
// electron.vite.config.ts
'/api/autogen': {
  target: 'http://localhost:8081',
  changeOrigin: true,
  rewrite: (path) => path.replace(/^\/api\/autogen/, '/api'),
  // 307/301/302 redirect도 proxy 레벨에서 처리
}

'/api/bridge': {
  target: 'http://localhost:8080',
  changeOrigin: true,
  rewrite: (path) => path.replace(/^\/api\/bridge/, '')
}
```

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

## 서비스 포트

| Service | Port | Required | Start Command |
|---------|------|----------|---------------|
| AutoGen Studio | 8081 | **Yes** | `autogenstudio ui --port 8081` |
| Auto-Claude (dev) | 5173 | **Yes** | `cd Auto-Claude/apps/frontend && npm run dev` |
| AG-ACE-BRIDGE | 8080 | Pipeline용 | `cd AG-ACE-BRIDGE && python main.py` |
| SharedMemory | 8101 | Optional | `python mcp/shared_memory.py` |
| A2A Agents | 8003-8120 | Optional | `python run_all_agents.py` |

---

## Cross-System Workflow 예시

### Research-to-Code

```
AG Research Agent -> 정보 수집
AG Analyst Agent -> 기술 분석
  ↓ (context 전달)
Auto-Claude Planner -> 구현 계획
Auto-Claude Coder -> 코드 구현
Auto-Claude QA Reviewer -> 검증
  ↓ (critic loop)
Auto-Claude QA Fixer -> 수정
  ↓ (pass)
Git Worktree -> 격리 빌드 -> Merge
```

### Legal Software Development

```
AG Legal Researcher -> 법률 조사
AG Case Analyzer + Compliance (Parallel) -> 분석
AG Risk Assessor -> 리스크 평가
  ↓ (context 전달)
Auto-Claude Full Pipeline (Planner -> Coder -> QA)
AG Compliance Checker -> 최종 법적 검증
Auto-Claude Merge -> 병합
```

---

## 테스트

| File | Description | Status |
|------|-------------|--------|
| `test_e2e_dual_browser.py` | Playwright 2 브라우저 (AutoGen + Auto-Claude) | PASS |
| `test_functional.py` | 9 pages, 6 buttons, 38 cards, API proxy | PASS |
| `test_step_by_step.py` | 10 step 스크린샷 캡처 | PASS |
| `npm run build` | Auto-Claude 프로덕션 빌드 | OK |

---

## 변경 이력

| Date | Change |
|------|--------|
| 2026-01-31 | ARCHITECTURE.md 전면 재작성 (현재 구현 기준) |
| 2026-01-31 | Agent-level decomposition, 24/7 auto-trigger 반영 |
| 2026-01-31 | AG-ACE-BRIDGE 4-Layer 상세 아키텍처 추가 |
| 2026-01-31 | AutoGen Studio Team Storage 경로 문서화 |
| 2025-01-21 | 초기 아키텍처 설계 문서 작성 |
