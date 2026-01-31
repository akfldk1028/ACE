# 25_ACE Architecture

> 자연어 → 에이전트 설계 → 자동 빌드 → 완성된 프로젝트

---

## 핵심 아키텍처 (3단계)

```
                        사용자
                          │
                          │ "계산기 앱 만들어줘"
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 1: AutoGen Studio                                    │
│                         (에이전트 설계)                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │   Team/Workflow 설계                                                │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐              │   │
│  │   │ Planner │→ │ Coder   │→ │QA Review│→ │QA Fixer │              │   │
│  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘              │   │
│  │                                                                     │   │
│  │   + A2A Agents: calculator_agent, gui_test_agent                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  URL: http://localhost:8081                                                 │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    │ Workflow JSON
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 2: AG-ACE-BRIDGE                                     │
│                         (중개자 / 변환)                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │   WorkflowExecutor.execute_full_pipeline()                          │   │
│  │                                                                     │   │
│  │   Phase 1: spec_runner.py 호출 (AI Spec 생성)                       │   │
│  │     → AI가 복잡도 자동 평가 (simple/standard/complex)               │   │
│  │     → requirements.json, context.json, spec.md 생성                 │   │
│  │     → implementation_plan.json 생성                                  │   │
│  │                                                                     │   │
│  │   Phase 2: run.py 호출 (빌드 실행)                                  │   │
│  │     → Planner Agent: 구현 계획 수립                                 │   │
│  │     → Coder Agent: 코드 작성 (subagent 병렬 처리)                   │   │
│  │     → QA Reviewer: 검증 및 피드백                                   │   │
│  │     → QA Fixer: 수정 루프 (필요시)                                  │   │
│  │                                                                     │   │
│  │   Phase 3: Git Worktree 관리                                        │   │
│  │     → auto-claude/{spec-name} 브랜치에서 안전하게 빌드               │   │
│  │     → 완료 후 --merge 또는 --review                                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Python: src/bridge/workflow_executor.py                                    │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    │ subprocess
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 3: Auto-Claude                                       │
│                         (24/7 자율 실행)                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │   Claude Agent SDK + OAuth 2.0                                      │   │
│  │                                                                     │   │
│  │   Planner Agent ────────────────────────────────────────────────►   │   │
│  │     │ 구현 계획 수립, subtask 분해                                  │   │
│  │     ▼                                                               │   │
│  │   Coder Agent (24/7) ────────────────────────────────────────────►  │   │
│  │     │ 코드 작성, subagent 병렬 처리                                 │   │
│  │     ▼                                                               │   │
│  │   QA Reviewer ───────────────────────────────────────────────────►  │   │
│  │     │ 코드 리뷰, 테스트 실행, E2E 검증                              │   │
│  │     ▼                                                               │   │
│  │   QA Fixer (필요시) ─────────────────────────────────────────────►  │   │
│  │     │ 이슈 수정, 재검증                                             │   │
│  │     ▼                                                               │   │
│  │   Git Worktree 병합 ─────────────────────────────────────────────►  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Electron UI: npm run dev (Auto-Claude/apps/frontend)                       │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                          완성된 프로젝트!
                     (Git commit, PR, 테스트 통과)
```

---

## 핵심 컴포넌트

### 1. AutoGen Studio (에이전트 설계)

| 항목 | 값 |
|------|-----|
| URL | http://localhost:8081 |
| 역할 | 에이전트 팀/워크플로우 설계 |
| 기능 | 드래그 앤 드롭, 패턴 갤러리, 테스트 실행 |

**지원 패턴:**
- Sequential: A → B → C
- Selector: LLM이 에이전트 선택
- Swarm: 핸드오프 기반 협업
- Magentic One: Orchestrator가 작업 분배
- Reflection: Worker + Reviewer 루프

### 2. AG-ACE-BRIDGE (중개자)

| 항목 | 값 |
|------|-----|
| 위치 | D:/Data/25_ACE/AG-ACE-BRIDGE |
| 역할 | AutoGen → Auto-Claude 변환 |
| 핵심 파일 | src/bridge/workflow_executor.py |

**두 가지 모드:**

| 모드 | 메서드 | 설명 |
|------|--------|------|
| **AI 모드** | `execute_full_pipeline()` | spec_runner.py + run.py (추천) |
| 템플릿 모드 | `execute()` | 빠르지만 간단 |

**사용법:**
```python
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()

# AI 모드: Auto-Claude의 모든 기능 활용
result = executor.execute_full_pipeline_sync(
    task_description="계산기 앱 만들어줘",
    complexity="standard",  # simple, standard, complex
    auto_merge=False        # True면 완료 후 자동 병합
)
```

### 3. Auto-Claude (24/7 실행)

| 항목 | 값 |
|------|-----|
| 위치 | D:/Data/25_ACE/Auto-Claude |
| 역할 | 24/7 자율 코딩 |
| 핵심 파일 | apps/backend/run.py, apps/backend/runners/spec_runner.py |

**에이전트 파이프라인:**
1. **Planner Agent**: 구현 계획 수립, subtask 분해
2. **Coder Agent**: 코드 작성 (subagent 병렬 처리)
3. **QA Reviewer**: 코드 리뷰, 테스트 실행
4. **QA Fixer**: 이슈 수정 (필요시)

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
│     └─ "계산기 앱 만들어줘" (자연어)                                        │
│                                                                             │
│  2. AutoGen Studio (선택적)                                                 │
│     └─ 팀/워크플로우 설계                                                   │
│     └─ 패턴 선택 (Reflection, Magentic, etc.)                              │
│     └─ workflow.json 저장                                                   │
│                                                                             │
│  3. AG-ACE-BRIDGE                                                           │
│     ├─ WorkflowExecutor.execute_full_pipeline()                             │
│     │                                                                       │
│     ├─ Phase 1: spec_runner.py 호출                                         │
│     │   ├─ AI가 태스크 복잡도 평가 (SIMPLE/STANDARD/COMPLEX)               │
│     │   ├─ analyzer.py → project_index.json                                │
│     │   ├─ spec_gatherer.md → requirements.json                            │
│     │   ├─ context.py → context.json                                       │
│     │   ├─ spec_writer.md → spec.md                                        │
│     │   └─ planner.py → implementation_plan.json                           │
│     │                                                                       │
│     └─ Phase 2: run.py 호출                                                 │
│         ├─ Planner Agent: subtask 분해                                      │
│         ├─ Coder Agent: 코드 작성 (24/7 루프)                               │
│         ├─ QA Reviewer: 검증                                                │
│         └─ QA Fixer: 수정 (필요시)                                          │
│                                                                             │
│  4. Auto-Claude                                                             │
│     ├─ Git Worktree 생성 (격리)                                             │
│     ├─ 코드 작성 및 커밋                                                    │
│     ├─ 테스트 실행                                                          │
│     └─ QA 통과 시 완료                                                      │
│                                                                             │
│  5. 완료                                                                    │
│     ├─ run.py --review (리뷰)                                               │
│     └─ run.py --merge (병합)                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 포트 맵 (★ 2026-01-25 업데이트)

| 서비스 | 포트 | 설명 |
|--------|------|------|
| AutoGen Studio | 8081 | 에이전트 설계 UI (★ 필수) |
| Auto-Claude UI | 5173 (dev) | Electron 데스크톱 앱 (★ 필수) |
| A2A Agents | 8003-8009, 8120 | 전문 에이전트들 (선택) |

> **Note (2026-01-25)**: SharedMemory(8101), AG-ACE Dashboard(8080) 모두 제거됨. 8081 직접 연결만 사용.

---

## CORS 처리 (★ 2026-01-25)

Auto-Claude UI가 브라우저 모드에서 AutoGen Studio(8081)에 접근할 때 CORS 문제가 발생합니다.

### 해결: Vite 프록시

```
브라우저 → fetch('/api/autogen/...') → Vite(5173) 프록시 → 8081
```

**설정 위치**: `Auto-Claude/apps/frontend/electron.vite.config.ts`

```typescript
proxy: {
  '/api/autogen': {
    target: 'http://localhost:8081',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/autogen/, '/api')
  }
}
```

### 모드별 API 호출 방법

| 모드 | API 호출 | 파일 |
|------|----------|------|
| Electron | `window.electronAPI.*` | a2a-handlers.ts |
| Browser | `fetch('/api/autogen/...')` | browser-mock.ts |
| ❌ 금지 | `fetch('http://localhost:8081/...')` | CORS 차단됨! |

---

## Spec 파일 구조

```
.auto-claude/specs/XXX-feature-name/
├── project_index.json      # 프로젝트 구조 분석
├── requirements.json       # 요구사항
├── context.json           # 컨텍스트 (수정할 파일 등)
├── spec.md                # 스펙 문서
├── implementation_plan.json # 구현 계획 (phases, chunks)
└── autogen_workflow.json   # AutoGen 원본 (선택)
```

---

## Auto-Claude 활용 기능

| 기능 | 설명 |
|------|------|
| **AI Spec 생성** | 복잡도 자동 평가, 정교한 Spec |
| **Planner Agent** | 구현 계획 수립, subtask 분해 |
| **Coder Agent** | 코드 작성 (subagent 병렬 처리) |
| **QA Reviewer** | 검증 및 피드백 |
| **QA Fixer** | 수정 루프 |
| **Git Worktree** | 안전한 격리 빌드 |
| **Graphiti Memory** | 크로스 세션 컨텍스트 |
| **Electron MCP** | E2E 테스트 (선택) |

---

## 빠른 시작

```bash
# 1. AutoGen Studio 시작 (선택)
cd D:/Data/25_ACE/AG/autogen_a2a_kit/autogen_source/python/packages/autogen-studio
autogenstudio ui --port 8081

# 2. Auto-Claude UI 시작 (선택)
cd D:/Data/25_ACE/Auto-Claude/apps/frontend
npm run dev

# 3. AG-ACE-BRIDGE에서 실행
cd D:/Data/25_ACE/AG-ACE-BRIDGE
python -c "
from src.bridge import WorkflowExecutor
executor = WorkflowExecutor()
result = executor.execute_full_pipeline_sync(
    task_description='계산기 앱 만들어줘',
    complexity='standard'
)
print(result)
"
```

---

## 관련 프로젝트

| 프로젝트 | 경로 | 역할 |
|---------|------|------|
| AG-ACE-BRIDGE | D:/Data/25_ACE/AG-ACE-BRIDGE | 중개자/변환 |
| Auto-Claude | D:/Data/25_ACE/Auto-Claude | 24/7 실행 엔진 |
| AG (AutoGen) | D:/Data/25_ACE/AG | 멀티에이전트 프레임워크 |

---

*이 문서는 25_ACE 시스템의 전체 아키텍처를 설명합니다.*
