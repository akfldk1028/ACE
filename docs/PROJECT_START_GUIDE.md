# Project Start Guide

> 새 프로젝트를 처음부터 완성까지 - 간소화된 2 UI 가이드

## Overview: 새로운 단순화 아키텍처 (★ 2026-01-24)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    25_ACE 간소화 아키텍처 (2 UI)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: 에이전트 설계         STEP 2: 자동 빌드                            │
│  ┌─────────────────────────┐   ┌───────────────────────────────────────┐   │
│  │  AutoGen Studio (8081)  │   │  AG-ACE-BRIDGE                         │   │
│  │                         │   │    WorkflowExecutor                    │   │
│  │  - 팀 구성              │   │      │                                 │   │
│  │  - 패턴 선택            │──►│      ▼                                 │   │
│  │  - A2A 에이전트 추가    │   │    spec_runner.py (AI Spec 생성)       │   │
│  └─────────────────────────┘   │      │                                 │   │
│                                │      ▼                                 │   │
│                                │    run.py (Planner→Coder→QA)          │   │
│                                │      │                                 │   │
│                                │      ▼                                 │   │
│                                │    Git Worktree (격리 빌드)            │   │
│                                └───────────────────────────────────────┘   │
│                                         │                                   │
│                                         ▼                                   │
│                                ┌───────────────────────────────────────┐   │
│                                │  Auto-Claude UI (실시간 모니터링)      │   │
│                                │    - Kanban 보드                       │   │
│                                │    - Agent Terminals 협업 패널         │   │
│                                │    - 실시간 AutoGen 결과 표시          │   │
│                                └───────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 방법 A: Python API로 직접 실행 (★ 권장)

```python
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()

# AI 모드: Auto-Claude의 모든 기능 활용
result = executor.execute_full_pipeline_sync(
    task_description="계산기 앱 만들어줘",
    complexity="standard",  # simple, standard, complex
    auto_merge=False        # True면 완료 후 자동 병합
)

print(f"Success: {result['success']}")
print(f"Spec ID: {result['spec_id']}")
print(f"Review: python run.py --spec {result['spec_id']} --review")
print(f"Merge:  python run.py --spec {result['spec_id']} --merge")
```

---

## 방법 B: UI 협업 (기존 방식)

---

## Step 1: 시스템 시작 (AG-ACE-BRIDGE)

### 1.1 서비스 시작

```bash
# Terminal 1: AutoGen Studio (★ 필수)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio
autogenstudio ui --port 8081

# Terminal 2: Auto-Claude (Electron) (★ 필수)
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev

# Terminal 3: A2A Agents (선택)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\a2a_demo
python run_all_agents.py

# Note: SharedMemory(8101), AG-ACE Dashboard(8080) 모두 2026-01-25에 제거됨
```

### 1.2 서비스 상태 확인 (★ 2026-01-25 업데이트)

> **Note**: AG-ACE-BRIDGE Dashboard(8080)는 제거되었습니다.
> 상태 확인은 curl 또는 Auto-Claude UI에서 진행합니다.

```bash
# AutoGen Studio 상태 확인
curl http://localhost:8081/api/version

# Vite 프록시 확인 (브라우저 모드)
curl http://localhost:5173/api/autogen/version
```

**최소 필수 서비스:**
- [✓] AutoGen Studio (8081)
- [✓] Auto-Claude UI (5173)

**Action**: AutoGen Studio, Auto-Claude UI 실행 확인 → 다음 단계로

---

## Step 2: Task 생성 (Auto-Claude)

### 2.1 Auto-Claude Electron 앱 열기

Auto-Claude Electron 앱에서 새 프로젝트를 시작합니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Auto-Claude (Electron App)                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [+ New Task]  [Import from GitHub]  [Import from Linear]                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Create New Task                                                      │   │
│  │                                                                      │   │
│  │ Title: ___________________________________________________          │   │
│  │        "Build a Calculator with Percent Function"                   │   │
│  │                                                                      │   │
│  │ Description:                                                         │   │
│  │ ┌───────────────────────────────────────────────────────────────┐   │   │
│  │ │ Calculator 앱에 퍼센트 계산 기능을 추가합니다.                │   │   │
│  │ │                                                               │   │   │
│  │ │ 요구사항:                                                     │   │   │
│  │ │ - percentage(value, percent) 함수                             │   │   │
│  │ │ - discount(value, percent) 함수                               │   │   │
│  │ │ - what_percent(part, whole) 함수                              │   │   │
│  │ │                                                               │   │   │
│  │ │ 테스트 케이스 포함, README 업데이트 필요                      │   │   │
│  │ └───────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │ Target Folder: [Browse] D:\Data\25_ACE\Calculator                   │   │
│  │                                                                      │   │
│  │ Complexity:  ○ Simple  ● Standard  ○ Complex                        │   │
│  │                                                                      │   │
│  │              [Cancel]  [Create Task]                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 GitHub Issue에서 Import (선택적)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Import from GitHub                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Repository: [user/calculator] ▼                                           │
│                                                                             │
│  Open Issues:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ #42 - Add percent calculation feature         [enhancement]       │   │
│  │ ☐ #41 - Fix division by zero error              [bug]               │   │
│  │ ☐ #40 - Add square root function                [enhancement]       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Selected: 1 issue                                                          │
│                                                                             │
│              [Cancel]  [Import Selected]                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 SPEC 자동 생성

Task 생성 후 Auto-Claude가 자동으로 SPEC을 생성합니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPEC Generation                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task: Build a Calculator with Percent Function                            │
│  Status: Generating SPEC...                                                 │
│                                                                             │
│  Progress: ████████████░░░░░░░░ 60%                                        │
│                                                                             │
│  [Phase 1: Research]                                                        │
│  ├── Calling research_agent (8010)...                                      │
│  ├── Analyzing codebase structure...                                       │
│  └── ✓ Found 4 existing files, 3 functions                                 │
│                                                                             │
│  [Phase 2: Math Validation]                                                 │
│  ├── Calling calculator_agent (8006)...                                    │
│  └── ✓ Validated 3 percent formulas                                        │
│                                                                             │
│  [Phase 3: SPEC Document]                                                   │
│  └── Generating SPEC-042.yaml...                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Output**: `specs/SPEC-042.yaml` 생성됨

**Action**: SPEC 검토 후 "Approve" 버튼 클릭 → 다음 단계로

---

## Step 3: Pattern 설정 (AutoGen Studio)

### 3.1 AutoGen Studio 열기

http://localhost:8081 접속

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AutoGen Studio (http://localhost:8081)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Gallery] [Teams] [Agents] [Skills] [Settings]                            │
│                                                                             │
│  Pattern Gallery                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │ Sequential  │  │  Selector   │  │   Swarm     │                 │   │
│  │  │  (01)       │  │   (03)      │  │   (05)      │                 │   │
│  │  │ ─────────── │  │  ┌─►───┐   │  │  ◄──►◄──►  │                 │   │
│  │  │ A → B → C   │  │  │ LLM │   │  │  Handoffs   │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │  Magentic   │  │   Debate    │  │ Reflection  │                 │   │
│  │  │   (06)      │  │    (07)     │  │   (08)      │                 │   │
│  │  │  [Orch]     │  │  Pro ↔ Con  │  │  W → R      │                 │   │
│  │  │  /  |  \    │  │  Discussion │  │  Worker     │                 │   │
│  │  │ A   B   C   │  │             │  │  Reviewer   │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Task에 맞는 Pattern 선택/설정

이 프로젝트에 필요한 Pattern:

| Phase | Pattern | Why |
|-------|---------|-----|
| SPEC | Selector | research_agent, calculator_agent 동적 선택 |
| PLAN | Magentic | Orchestrator가 subtask 분배 |
| CODE | Sequential | 순차적 구현 (간단한 프로젝트) |
| QA | Reflection | Worker(Coder) + Reviewer(QA) 루프 |

### 3.3 Team 구성 (Drag & Drop)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Team Configuration                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Pattern: Reflection (08)                    [Change Pattern ▼]            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Available Agents                    Team Composition               │   │
│  │  ┌───────────────────┐              ┌───────────────────┐          │   │
│  │  │ • Planner         │   ──drag──►  │ Worker:           │          │   │
│  │  │ • Coder           │              │   [Coder]         │          │   │
│  │  │ • QA Reviewer     │              │                   │          │   │
│  │  │ • QA Fixer        │   ──drag──►  │ Reviewer:         │          │   │
│  │  │ • research_agent  │              │   [QA Reviewer]   │          │   │
│  │  │ • calculator_agent│              │                   │          │   │
│  │  │ • gui_test_agent  │              │ Fixer (optional): │          │   │
│  │  └───────────────────┘              │   [QA Fixer]      │          │   │
│  │                                     └───────────────────┘          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Selector Prompt (auto-generated):                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 다음 에이전트 중 적절한 에이전트를 선택하세요:                      │   │
│  │ - Coder: 24/7 자율 코딩, 구현 담당                                  │   │
│  │ - QA Reviewer: E2E 테스트, 품질 검증                                │   │
│  │ - QA Fixer: 이슈 수정, 디버깅                                       │   │
│  │                                                                     │   │
│  │ Worker가 코드를 구현하고, Reviewer가 검토합니다.                    │   │
│  │ 이슈 발견 시 Fixer가 수정합니다.                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│              [Cancel]  [Save Team]  [Apply to Current Task]                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Pattern Test (선택적)

실제 실행 전에 Pattern을 테스트할 수 있습니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Pattern Test                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Test Input:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ "Simple math: What is 15% of 100?"                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Run Test]                                                                 │
│                                                                             │
│  Test Results:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Turn 1: [Coder] "Calculating 15% of 100 = 15"                       │   │
│  │ Turn 2: [QA Reviewer] "Verified: 100 * 0.15 = 15 ✓"                 │   │
│  │ Turn 3: [TERMINATE] Task completed successfully                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Status: ✓ Pattern working correctly                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Action**: Team 저장 → "Apply to Current Task" 클릭 → 다음 단계로

---

## Step 4: 실행 제출 (AG-ACE-BRIDGE)

### 4.1 AG-ACE-BRIDGE Dashboard로 돌아가기

http://localhost:8080

### 4.2 Task Queue에서 Task 확인

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AG-ACE-BRIDGE Dashboard - Task Queue                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [+ Submit New]  [Refresh]  [Filter: All ▼]                                │
│                                                                             │
│  Task Queue                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ID         Title                          Status    Pattern        │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ TASK-001   Calculator Percent Function    READY     Reflection     │   │
│  │            SPEC: SPEC-042.yaml            Team: Configured ✓       │   │
│  │            Source: Auto-Claude                                     │   │
│  │            Created: 2024-01-15 10:30                              │   │
│  │                                                                    │   │
│  │            [View SPEC]  [Edit Pattern]  [▶ Start Execution]      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 실행 시작

"▶ Start Execution" 버튼 클릭

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Confirm Execution                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task: TASK-001 - Calculator Percent Function                               │
│                                                                             │
│  Execution Plan:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Phase 1: PLAN     │ Pattern: Magentic     │ Est: 15 min            │   │
│  │ Phase 2: CODE     │ Pattern: Sequential   │ Est: 2 hours           │   │
│  │ Phase 3: QA       │ Pattern: Reflection   │ Est: 30 min            │   │
│  │ Phase 4: MERGE    │ Pattern: Sequential   │ Est: 10 min            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Agents to be used:                                                         │
│  • Planner, Coder, QA Reviewer, QA Fixer (Auto-Claude)                     │
│  • research_agent, calculator_agent (A2A)                                  │
│  • gui_test_agent (E2E testing)                                            │
│                                                                             │
│  Options:                                                                   │
│  ☑ Auto-create PR on completion                                            │
│  ☑ Auto-close GitHub issue on merge                                        │
│  ☐ Require manual approval before merge                                    │
│                                                                             │
│              [Cancel]  [Start Execution]                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Action**: "Start Execution" 클릭 → 24/7 자동 실행 시작

---

## Step 5: 모니터링 & 개입 (All 3 UIs)

### 5.1 AG-ACE-BRIDGE: 전체 진행 상황

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AG-ACE-BRIDGE Dashboard - Execution Monitor                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task: TASK-001 - Calculator Percent Function                    [RUNNING] │
│                                                                             │
│  Progress: ████████████████████░░░░░ 80%                                   │
│                                                                             │
│  Phase Status:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [✓] PLAN      Completed    15 min                                  │   │
│  │ [✓] CODE      Completed    1h 45min                                │   │
│  │ [●] QA        In Progress  20 min...                               │   │
│  │ [○] MERGE     Pending                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Current Activity:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [12:15:32] QA Reviewer: Running unit tests...                      │   │
│  │ [12:15:45] pytest: 8 passed, 0 failed                              │   │
│  │ [12:15:50] QA Reviewer: Running E2E tests with gui_test_agent...   │   │
│  │ [12:16:10] gui_test_agent: Screenshot captured                     │   │
│  │ [12:16:15] gui_test_agent: Verifying output... ✓                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [View Logs]  [Pause]  [Cancel]  [Force QA Pass]  [Request Human Review]   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Auto-Claude: 상세 실행 로그

Auto-Claude Electron 앱에서 실시간 로그 확인:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Auto-Claude - Execution Details                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task: TASK-001                                    Status: CODE Phase      │
│                                                                             │
│  Subtasks:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [✓] ST-1: Add percentage() function              2024-01-15 11:00  │   │
│  │ [✓] ST-2: Add discount() function                2024-01-15 11:15  │   │
│  │ [✓] ST-3: Add what_percent() function            2024-01-15 11:30  │   │
│  │ [✓] ST-4: Add test cases                         2024-01-15 12:00  │   │
│  │ [●] ST-5: Update README                          In Progress...    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Git Activity:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ commit a1b2c3d: feat(calculator): add percentage() function        │   │
│  │ commit d4e5f6g: feat(calculator): add discount() function          │   │
│  │ commit h7i8j9k: feat(calculator): add what_percent() function      │   │
│  │ commit l0m1n2o: test(calculator): add percent function tests       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Files Changed:                                                             │
│  • Calculator/src/operations.py (+45 lines)                                │
│  • Calculator/tests/test_calculator.py (+30 lines)                         │
│  • Calculator/README.md (pending)                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 AutoGen Studio: Pattern 실행 시각화

AutoGen Studio에서 Agent 간 대화 시각화:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AutoGen Studio - Live Execution View                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Team: Reflection Pattern                         Active Agents: 2         │
│                                                                             │
│  Conversation Flow:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────┐                    ┌──────────┐                      │   │
│  │  │  Coder   │ ─── "Code done" ──►│QA Reviewer│                     │   │
│  │  │ (Worker) │                    │(Reviewer)│                      │   │
│  │  └──────────┘◄── "Fix this" ─────└──────────┘                      │   │
│  │       │                                │                           │   │
│  │       │                                │                           │   │
│  │       └──────────► [SharedMemory] ◄────┘                           │   │
│  │                    (Context Saved)                                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Message Log:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [Turn 1] Coder: "I've implemented the percentage() function..."    │   │
│  │ [Turn 2] QA Reviewer: "Test passed. Code looks good. ✓"            │   │
│  │ [Turn 3] Coder: "Moving to discount() function..."                 │   │
│  │ [Turn 4] QA Reviewer: "Approved. Continue to next."                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 문제 발생 시 개입

QA 실패 시 알림:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ QA FAILURE - Human Review Required                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task: TASK-001                                                             │
│  Phase: QA                                                                  │
│  Issue: E2E test failed - Expected output mismatch                         │
│                                                                             │
│  Details:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Test: test_discount_edge_case                                       │   │
│  │ Expected: 0.0                                                       │   │
│  │ Actual: -0.0                                                        │   │
│  │                                                                     │   │
│  │ File: Calculator/src/operations.py:25                               │   │
│  │ Code: return value * (1 - percent / 100)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Options:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ○ Auto-fix with QA Fixer                                           │   │
│  │ ○ Manual fix (opens VS Code)                                       │   │
│  │ ○ Ignore and continue (not recommended)                            │   │
│  │ ● Request Debate pattern review (Pro vs Con analysis)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│              [Cancel Task]  [Apply Selected Action]                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 6: 완료 & PR (자동)

### 6.1 실행 완료

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✅ TASK COMPLETED                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task: TASK-001 - Calculator Percent Function                               │
│  Status: COMPLETED                                                          │
│  Duration: 3 hours 25 minutes                                               │
│                                                                             │
│  Summary:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • 3 new functions added                                             │   │
│  │ • 8 test cases (100% pass)                                          │   │
│  │ • 95% code coverage                                                 │   │
│  │ • E2E tests passed                                                  │   │
│  │ • README updated                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PR Created: #123                                                           │
│  URL: https://github.com/user/calculator/pull/123                          │
│                                                                             │
│  GitHub Issue #42: Automatically closed                                     │
│                                                                             │
│              [View PR]  [View Logs]  [Start New Task]                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: UI Role Summary

| Step | Primary UI | Action | Other UIs Role |
|------|------------|--------|----------------|
| **1. Setup** | AG-ACE-BRIDGE | Service health check | - |
| **2. Create Task** | Auto-Claude | Create/Import task, SPEC generation | - |
| **3. Configure** | AutoGen Studio | Pattern selection, Team composition | - |
| **4. Submit** | AG-ACE-BRIDGE | Start execution | - |
| **5. Monitor** | All 3 | Watch progress, intervene if needed | Each shows different detail level |
| **6. Complete** | AG-ACE-BRIDGE | View results, PR link | Auto-Claude shows git history |

---

## Troubleshooting (★ 2026-01-25 업데이트)

### Service Not Connected
```bash
# Check if services are running (★ 필수 서비스만!)
curl http://localhost:8081/api/version  # AutoGen Studio
curl http://localhost:5173/api/autogen/version  # Vite 프록시

# A2A agents (선택)
curl http://localhost:8006/.well-known/agent.json  # calculator_agent
```

### Pattern Not Working
1. AutoGen Studio → Pattern Test로 먼저 테스트
2. Agent가 online인지 확인
3. selector_prompt가 올바른지 확인

### Task Stuck
1. AG-ACE-BRIDGE → View Logs로 에러 확인
2. Auto-Claude → 상세 로그 확인
3. "Pause" 후 수동 개입 또는 "Cancel" 후 재시작

---

*이 가이드는 25_ACE 시스템의 3개 UI를 조율하여 프로젝트를 완성하는 방법을 설명합니다.*
