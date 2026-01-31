# Task.md - 프로젝트 상태 및 다음 작업

## 목표 (완료!)
AutoGen Studio UI와 Auto-Claude UI 두 개가 협업하는 모습을 확인

---

## 현재 상태 (2026-01-24 업데이트)

| 항목 | 상태 | 비고 |
|------|------|------|
| AutoGen Studio | ✅ 완료 | http://localhost:8081 |
| Auto-Claude UI | ✅ 완료 | Electron 앱 (직접 연결) |
| **8081 직접 연결** | ✅ 완료 | SharedMemory 없이 작동! |
| **실시간 동기화** | ✅ 완료 | 2초 폴링 (바로바로) |
| **Kanban 컬럼 매핑** | ✅ 완료 | 시간 기반 자동 이동 |
| **Agent Terminals 협업** | ✅ 완료 | AutoGen 대화 실시간 스트리밍 |
| TypeScript 빌드 | ✅ 완료 | 에러 없음 |
| Calculator 앱 | ✅ 완료 | 12/12 테스트 통과 |
| **Bridge Module** | ✅ 완료 | AutoGen → Auto-Claude Spec 변환 |

### UI 연동 구현 완료

```
┌─────────────────────────────────────────────────────────────────┐
│                    완료된 아키텍처                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AutoGen Studio (8081)                                          │
│         │                                                        │
│         │ ★ 중앙화된 API 호출 (Main Process only!)              │
│         ▼                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Main Process (Node.js / Electron)                          │ │
│  │  └── a2a-handlers.ts (유일한 8081 호출점)                  │ │
│  │       ├── getAutogenLatest() → 8081 직접 → 8101 폴백       │ │
│  │       └── getAutogenRunsDetailed() → 8081 직접             │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                                                        │
│         │ IPC (electronAPI)                                     │
│         ▼                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Renderer Process (React UI) - 직접 fetch(8081) 금지!      │ │
│  │  ├── AutogenStatusBadge → electronAPI.getAutogenLatest()   │ │
│  │  ├── KanbanBoard → electronAPI.getAutogenLatest()          │ │
│  │  ├── AutogenResultsWidget → electronAPI.getAutogenLatest() │ │
│  │  └── AutogenCollabPanel → electronAPI.getAutogenRunsDetailed() ★ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  * CORS 문제 해결: Renderer에서 직접 8081 호출 제거            │
│  * SharedMemory(8101)는 폴백 옵션으로만 사용                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 완료된 작업

### 1. TypeScript 타입 수정
- [x] `src/shared/types/ipc.ts` - `getAutogenLatest` 반환 타입에 `source` 추가
- [x] `src/renderer/components/AutogenStatusBadge.tsx` - interface 수정
- [x] `src/renderer/components/AutogenResultsWidget.tsx` - interface 수정

### 2. Vite Proxy 설정
- [x] `electron.vite.config.ts` - `/api/autogen` → 8081 프록시 추가

### 3. browser-mock.ts 수정
- [x] `getAutogenLatest()` - 8081 직접 조회 → 8101 폴백

### 4. UI 컴포넌트 연동
- [x] AutogenStatusBadge - 사이드바에 연결 상태 표시
- [x] KanbanBoard - AutoGen 결과 Kanban 카드로 표시
- [x] AutogenResultsWidget - 플로팅 위젯 결과 미리보기

### 5. 문서 업데이트
- [x] README.md - 아키텍처 다이어그램 업데이트
- [x] README_INDEX.md - 비교 테이블, 핵심 파일 목록 추가
- [x] USER_ACTION_GUIDE.md - 최소 구성 가이드 추가

---

## 핵심 성과

### Before (복잡)
```
AutoGen Studio → run_autogen_sync_simple.py → SharedMemory(8101) → Auto-Claude UI
                            │
                   (별도 프로세스 필요)
```

### After (단순) ★
```
AutoGen Studio → Auto-Claude UI (Vite Proxy 직접 연결)
                         │
               (설정 없음, 바로 작동!)
```

| 항목 | 기존 | 신규 |
|------|------|------|
| 필요 서버 | 3개 | 2개 |
| 지연 시간 | ~7초 | ~5초 |
| 추가 설정 | 동기화 스크립트 필요 | 불필요 |

---

## Bridge Module 구현 완료 (★ Enhanced!)

### 완전 자동화 파이프라인

```
┌─────────────────┐
│  AutoGen Studio │  "계산기 앱 만들어줘"
│   (에이전트 설계) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AG-ACE-BRIDGE                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ WorkflowExecutor.execute_full_pipeline()                  │   │
│  │                                                           │   │
│  │  Phase 1: spec_runner.py (AI Spec 생성)                  │   │
│  │    → AI가 복잡도 평가                                    │   │
│  │    → requirements.json, context.json, spec.md 생성       │   │
│  │    → implementation_plan.json 생성                        │   │
│  │                                                           │   │
│  │  Phase 2: run.py (빌드 실행)                             │   │
│  │    → Planner Agent (계획 수립)                           │   │
│  │    → Coder Agent (코드 작성, subagent 병렬)              │   │
│  │    → QA Reviewer (검증)                                  │   │
│  │    → QA Fixer (수정 루프)                                │   │
│  │                                                           │   │
│  │  Phase 3: Git Worktree에서 안전하게 빌드                 │   │
│  │    → 브랜치: auto-claude/{spec-name}                     │   │
│  │    → 완료 후 --merge 또는 --review                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Auto-Claude   │  완성된 프로젝트!
│   (24/7 실행)   │
└─────────────────┘
```

### 두 가지 모드

| 모드 | 메서드 | 설명 |
|------|--------|------|
| **AI 모드** | `execute_full_pipeline()` | spec_runner.py + run.py (모든 기능) |
| 템플릿 모드 | `execute()` | 빠르지만 간단 |

### 핵심 파일

| 파일 | 역할 |
|------|------|
| `src/bridge/__init__.py` | 모듈 export |
| `src/bridge/autogen_to_spec.py` | AutoGen Workflow → Auto-Claude Spec 변환 |
| `src/bridge/auto_claude_runner.py` | Auto-Claude run.py 호출 래퍼 |
| `src/bridge/workflow_executor.py` | 전체 파이프라인 실행기 (Enhanced!) |
| `tests/test_bridge_module.py` | 유닛 테스트 (4/4 통과) |

### 사용법 (AI 모드 - 권장)

```python
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()

# AI 모드: Auto-Claude의 모든 기능 활용
result = executor.execute_full_pipeline_sync(
    task_description="계산기 앱 만들어줘",
    complexity="standard",  # simple, standard, complex
    auto_merge=False        # True면 완료 후 자동 병합
)

# 파이프라인:
# 1. spec_runner.py → AI가 Spec 생성
# 2. run.py → Planner → Coder → QA 파이프라인
# 3. Git Worktree에서 안전하게 빌드
```

### Auto-Claude 활용 기능

| 기능 | 설명 |
|------|------|
| **AI Spec 생성** | 복잡도 자동 평가, 정교한 Spec |
| **Planner Agent** | 구현 계획 수립 |
| **Coder Agent** | 코드 작성 (subagent 병렬 처리) |
| **QA Reviewer** | 검증 및 피드백 |
| **QA Fixer** | 수정 루프 |
| **Git Worktree** | 안전한 격리 빌드 |
| **Graphiti Memory** | 크로스 세션 컨텍스트 |

---

## UI → Bridge Module 연결 (★ 2026-01-24 완료!)

Auto-Claude UI에서 AG-ACE-BRIDGE의 WorkflowExecutor를 호출할 수 있게 되었습니다.

### 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│ Auto-Claude UI (Electron)                                        │
│  └── Renderer Process                                           │
│       ├── electronAPI.workflowExecute(task, complexity, autoMerge) │
│       ├── electronAPI.workflowGetExecution(execId)               │
│       ├── electronAPI.workflowListSpecs()                        │
│       ├── electronAPI.workflowReview(specId)                     │
│       └── electronAPI.workflowMerge(specId)                      │
└───────────────────────┬─────────────────────────────────────────┘
                        │ IPC (electronAPI)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Main Process (a2a-handlers.ts)                                   │
│  └── HTTP 호출 → AG-ACE-BRIDGE (8080)                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP (8080)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ AG-ACE-BRIDGE (FastAPI)                                          │
│  ├── /workflow/execute       → WorkflowExecutor.execute_full_pipeline() │
│  ├── /workflow/executions/{id} → 실행 상태 조회                  │
│  ├── /workflow/specs         → Spec 목록                        │
│  ├── /workflow/review/{id}   → run.py --review                  │
│  └── /workflow/merge/{id}    → run.py --merge                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Auto-Claude Backend                                              │
│  ├── spec_runner.py → AI Spec 생성                              │
│  └── run.py → Planner → Coder → QA 파이프라인                   │
└─────────────────────────────────────────────────────────────────┘
```

### 추가된 파일

| 파일 | 역할 |
|------|------|
| `AG-ACE-BRIDGE/src/server/workflow_routes.py` | REST API 엔드포인트 |
| `Auto-Claude/.../a2a-handlers.ts` | IPC 핸들러 (HTTP 호출) |
| `Auto-Claude/.../a2a-api.ts` | Preload API 노출 |
| `Auto-Claude/.../ipc.ts` (constants) | IPC 채널 상수 |
| `Auto-Claude/.../types/ipc.ts` | ElectronAPI 타입 정의 |

### 사용법 (UI 컴포넌트에서)

```typescript
// 워크플로우 실행
const result = await electronAPI.workflowExecute(
  '계산기 앱 만들어줘',
  'standard',  // simple, standard, complex
  false        // auto_merge
);

if (result.success && result.data?.exec_id) {
  // 실행 상태 폴링
  const status = await electronAPI.workflowGetExecution(result.data.exec_id);
  console.log(`Status: ${status.data?.status}`);
}

// Spec 목록 조회
const specs = await electronAPI.workflowListSpecs();

// Spec 리뷰
const review = await electronAPI.workflowReview('001-calculator');

// Spec 병합
const merge = await electronAPI.workflowMerge('001-calculator');
```

---

## 다음 가능 작업 (선택)

### Option A: E2E 테스트 (실제 Auto-Claude 실행)
```
1. test_workflow_execution.py 실행
2. Auto-Claude run.py가 실제 Spec 빌드
3. 결과 검증
```

### Option B: REST API 서버
```
1. pattern_routes.py 완성
2. project_routes.py 완성
3. FastAPI 대시보드 연동
```

### Option C: 스케줄러 통합
```
1. 패턴 자동 트리거
2. Cron/이벤트 기반 실행
3. 24/7 무인 운영
```

---

## 핵심 파일 위치

| 파일 | 경로 | 설명 |
|------|------|------|
| Vite 프록시 설정 | `Auto-Claude/.../electron.vite.config.ts` | /api/autogen → 8081 |
| API 호출 로직 | `Auto-Claude/.../browser-mock.ts` | getAutogenLatest() |
| 상태 뱃지 | `Auto-Claude/.../AutogenStatusBadge.tsx` | 사이드바 상태 |
| Kanban 통합 | `Auto-Claude/.../KanbanBoard.tsx` | AutoGen → Kanban 카드 |
| IPC 타입 | `Auto-Claude/.../types/ipc.ts` | source 속성 추가 |
| IPC 핸들러 | `Auto-Claude/.../a2a-handlers.ts` | 8081 직접 조회 + 8101 폴백 |
| **협업 패널** | `Auto-Claude/.../AutogenCollabPanel.tsx` | Agent Terminals 대화 스트리밍 ★ |
| **Bridge Module** | `AG-ACE-BRIDGE/src/bridge/` | AutoGen → Auto-Claude Spec 변환 ★ |

---

## 확인 명령어

```bash
# TypeScript 빌드 확인
cd D:/Data/25_ACE/Auto-Claude/apps/frontend && npx tsc --noEmit

# 프론트엔드 빌드
cd D:/Data/25_ACE/Auto-Claude/apps/frontend && npm run build

# AutoGen Studio 상태 확인
curl http://localhost:8081/api/version

# Auto-Claude UI 개발 서버 시작
cd D:/Data/25_ACE/Auto-Claude/apps/frontend && npm run dev

# ★ Bridge Module 테스트 (NEW!)
cd D:/Data/25_ACE/AG-ACE-BRIDGE && python tests/test_bridge_module.py
```

---

## 사용자 요청 요약
> "autogen studio ui 에서 팀 만들고 설계해서 계산기 앱 설계하고 auto-claude에서 진행되는지 확인"
> "두 개의 UI가 떠서 협업하는 모습 확인 가능하게"

**결과**: ✅ 완료 - AutoGen Studio + Auto-Claude UI 직접 연결 구현

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-01-24 | ✅ **UI 컴포넌트 추가** - AutogenCollabPanel에 "Create Spec from AutoGen" 폼 추가 |
| 2026-01-24 | ✅ **UI → Bridge Module 연결 완료** - workflow_routes.py + IPC 핸들러 + Preload API + ElectronAPI 타입 |
| 2026-01-24 | ✅ **CLAUDE.md 업데이트** - AG-ACE-BRIDGE + Auto-Claude CLAUDE.md에 Bridge Module 섹션 추가 |
| 2026-01-24 | ✅ **docs/ 전체 업데이트** - ARCHITECTURE.md 생성, AI_STARTUP_GUIDE/PROJECT_START_GUIDE/WORKFLOW_EXAMPLE 최신화 |
| 2026-01-24 | ✅ **Bridge Module 구현 완료** - AutogenToSpec, AutoClaudeRunner, WorkflowExecutor (4/4 테스트 통과) |
| 2026-01-24 | ✅ **MD 파일 전체 업데이트** - README, CLAUDE.md, USER_ACTION_GUIDE 최신화 |
| 2026-01-24 | ✅ Agent Terminals 탭 통합 - 터미널 없으면 AutoGen 협업 뷰 풀스크린 |
| 2026-01-24 | ✅ 아키텍처 리팩토링 - 8081 호출을 Main Process(a2a-handlers.ts)로 중앙화 |
| 2026-01-24 | ✅ Agent Terminals 협업 패널 추가 - AutogenCollabPanel 실시간 대화 스트리밍 |
| 2026-01-24 | ✅ 폴링 2초로 단축 - 바로바로 실시간 동기화 |
| 2026-01-24 | ✅ Kanban 시간 기반 컬럼 매핑 - pending→backlog, running→in_progress, complete→ai_review/human_review/done |
| 2026-01-24 | ✅ IPC 핸들러 개선 - 8081 직접 조회 + 8101 폴백 |
| 2026-01-24 | ✅ UI 연동 완료 - 8081 직접 연결, TypeScript 빌드 성공 |
| 2026-01-24 | ✅ 문서 업데이트 - README, USER_ACTION_GUIDE |
| 2026-01-24 | Calculator 파이프라인 완료 (12/12 테스트 통과) |
