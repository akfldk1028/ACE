# 25_ACE Workflow Example

> 자연어 → 완성된 프로젝트 - AG-ACE-BRIDGE 완전 자동화 예시

## Overview (★ 2026-01-24 업데이트)

이 문서는 **"계산기 앱 만들어줘"** 라는 자연어 요청이 어떻게 완성된 프로젝트로 변환되는지 보여줍니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AG-ACE-BRIDGE 완전 자동화 파이프라인                       │
│                                                                             │
│  자연어 요청: "계산기 앱 만들어줘"                                           │
│       │                                                                     │
│       ▼                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  AG-ACE-BRIDGE: WorkflowExecutor.execute_full_pipeline()               │ │
│  │                                                                        │ │
│  │  Phase 1: spec_runner.py (AI Spec 생성)                               │ │
│  │    → AI가 복잡도 자동 평가 (SIMPLE/STANDARD/COMPLEX)                   │ │
│  │    → requirements.json, context.json, spec.md 생성                    │ │
│  │    → implementation_plan.json 생성                                    │ │
│  │                                                                        │ │
│  │  Phase 2: run.py (24/7 빌드 실행)                                     │ │
│  │    → Planner Agent: 구현 계획 수립                                    │ │
│  │    → Coder Agent: 코드 작성 (subagent 병렬 처리)                      │ │
│  │    → QA Reviewer: 검증 및 피드백                                      │ │
│  │    → QA Fixer: 수정 루프 (필요시)                                     │ │
│  │                                                                        │ │
│  │  Phase 3: Git Worktree 관리                                           │ │
│  │    → auto-claude/{spec-name} 브랜치에서 안전하게 빌드                 │ │
│  │    → 완료 후 --merge 또는 --review                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│       │                                                                     │
│       ▼                                                                     │
│  완성된 프로젝트! (Git commit, PR, 테스트 통과)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 빠른 시작: 한 줄 실행

```python
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()
result = executor.execute_full_pipeline_sync(
    task_description="계산기 앱 만들어줘",
    complexity="standard"
)
# → 자동으로 spec 생성, 코드 작성, QA, Git 커밋까지 완료!
```

---

## 상세 예시: Calculator 퍼센트 기능 추가

---

## Phase 0: 시스템 시작

### 0.1 최소 구성 (★ 권장)

```bash
# Terminal 1: AutoGen Studio (에이전트 설계)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio
autogenstudio ui --port 8081

# Terminal 2: Auto-Claude UI (24/7 모니터링)
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

### 0.2 서비스 상태 확인 (★ 2026-01-25 업데이트)

```
┌─────────────────────────────────────────────────────────────────┐
│ Service Health Check                                             │
├─────────────────────────────────────────────────────────────────┤
│ [★필수] AutoGen Studio         http://localhost:8081            │
│ [★필수] Auto-Claude UI         npm run dev (Electron)           │
│ [선택] A2A Agents              http://localhost:8003-8120       │
├─────────────────────────────────────────────────────────────────┤
│ [제거됨] AG-ACE Dashboard (8080)                                 │
│ [제거됨] SharedMemory (8101)                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Task Intake (GitHub Issue 감지)

### 1.1 GitHub Issue 등록

```markdown
# GitHub Issue #42

**Title**: Calculator에 퍼센트(%) 계산 기능 추가

**Description**:
현재 Calculator 앱에는 기본 사칙연산만 있습니다.
퍼센트 계산 기능이 필요합니다.

**요구사항**:
- 100의 15% = 15
- 200에서 10% 할인 = 180
- 50은 200의 몇 %? = 25%

**Labels**: enhancement, calculator
```

### 1.2 Auto-Claude Backend 감지

```python
# Auto-Claude가 GitHub Webhook을 통해 Issue 감지
{
    "event": "issue.created",
    "issue_number": 42,
    "title": "Calculator에 퍼센트(%) 계산 기능 추가",
    "labels": ["enhancement", "calculator"],
    "priority": "medium"
}
```

### 1.3 AG-ACE-BRIDGE Task Queue 등록

```json
// AG-ACE-BRIDGE Orchestrator가 Task Queue에 추가
{
    "task_id": "TASK-2024-001",
    "source": "github",
    "issue_number": 42,
    "title": "Calculator 퍼센트 기능",
    "status": "queued",
    "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Phase 2: SPEC Generation (AG Selector Pattern)

### 2.1 Pattern Selection: Selector

Orchestrator가 SPEC 생성에 **Selector Pattern**을 선택합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│ AG Selector Pattern for SPEC Generation                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Orchestrator]                                                 │
│       │                                                         │
│       ├─→ "코드 분석 필요" ──→ [research_agent]                 │
│       │                              │                          │
│       │                              ▼                          │
│       │                    "Calculator/ 폴더 분석 완료"         │
│       │                    "기존 함수: add, sub, mul, div"      │
│       │                              │                          │
│       ├─→ "수학 로직 검토" ──→ [calculator_agent :8006]         │
│       │                              │                          │
│       │                              ▼                          │
│       │                    "퍼센트 공식:"                       │
│       │                    "percent(a,b) = a * (b/100)"        │
│       │                    "discount(a,b) = a * (1 - b/100)"   │
│       │                              │                          │
│       └─→ [SPEC 생성 완료]                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Research Agent 코드베이스 분석

```python
# AG research_agent가 코드베이스 분석
# HTTP POST to localhost:8006

analysis_result = {
    "repository": "Calculator",
    "affected_files": [
        "Calculator/src/calculator.py",
        "Calculator/src/operations.py",
        "Calculator/tests/test_calculator.py"
    ],
    "existing_functions": ["add", "subtract", "multiply", "divide"],
    "suggested_location": "Calculator/src/operations.py",
    "complexity": "simple"
}
```

### 2.3 Calculator Agent 수학 로직 검증

```python
# AG calculator_agent가 퍼센트 공식 검증
# HTTP POST to localhost:8006

math_validation = {
    "formulas": {
        "percentage": "value * (percent / 100)",
        "discount": "value * (1 - percent / 100)",
        "what_percent": "(part / whole) * 100"
    },
    "edge_cases": [
        "percent = 0 → 원래 값 유지",
        "percent = 100 → 전체",
        "negative percent → 증가"
    ],
    "test_cases": [
        {"input": [100, 15], "expected": 15},
        {"input": [200, 10], "expected": 180, "type": "discount"},
        {"input": [50, 200], "expected": 25, "type": "what_percent"}
    ]
}
```

### 2.4 SPEC 문서 생성

```yaml
# Auto-Claude가 생성한 SPEC (specs/SPEC-042.yaml)

spec_id: "SPEC-042"
title: "Calculator 퍼센트 기능 추가"
github_issue: 42
created_at: "2024-01-15T10:30:00Z"

analysis:
  source: "AG research_agent + calculator_agent"
  complexity: "simple"
  estimated_time: "2-3 hours"

requirements:
  - id: REQ-1
    description: "percentage(value, percent) 함수 구현"
    formula: "value * (percent / 100)"
    example: "percentage(100, 15) = 15"

  - id: REQ-2
    description: "discount(value, percent) 함수 구현"
    formula: "value * (1 - percent / 100)"
    example: "discount(200, 10) = 180"

  - id: REQ-3
    description: "what_percent(part, whole) 함수 구현"
    formula: "(part / whole) * 100"
    example: "what_percent(50, 200) = 25"

affected_files:
  - path: "Calculator/src/operations.py"
    action: "modify"
    changes: "Add 3 new functions"

  - path: "Calculator/tests/test_calculator.py"
    action: "modify"
    changes: "Add test cases for percent functions"

acceptance_criteria:
  - "모든 테스트 통과"
  - "edge case 처리 (0%, 100%, negative)"
  - "기존 기능 regression 없음"
```

---

## Phase 3: PLAN Generation (AG Magentic Pattern)

### 3.1 Pattern Selection: Magentic One

Orchestrator가 PLAN 수립에 **Magentic One Pattern**을 선택합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│ AG Magentic One Pattern for PLAN Generation                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    [Orchestrator Agent]                         │
│                           │                                     │
│            ┌──────────────┼──────────────┐                      │
│            │              │              │                      │
│            ▼              ▼              ▼                      │
│     [WebSurfer]    [FileSurfer]   [Coder Agent]                │
│     (API 조사)     (파일 분석)    (구현 계획)                   │
│            │              │              │                      │
│            └──────────────┼──────────────┘                      │
│                           ▼                                     │
│                    [Plan Document]                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Auto-Claude Planner Agent 실행

```python
# Auto-Claude Planner가 SPEC 기반 상세 계획 수립

plan = {
    "spec_id": "SPEC-042",
    "total_subtasks": 5,
    "subtasks": [
        {
            "id": "ST-1",
            "title": "operations.py에 percentage() 함수 추가",
            "estimated_lines": 10,
            "dependencies": []
        },
        {
            "id": "ST-2",
            "title": "operations.py에 discount() 함수 추가",
            "estimated_lines": 10,
            "dependencies": ["ST-1"]
        },
        {
            "id": "ST-3",
            "title": "operations.py에 what_percent() 함수 추가",
            "estimated_lines": 10,
            "dependencies": ["ST-1"]
        },
        {
            "id": "ST-4",
            "title": "test_calculator.py에 테스트 케이스 추가",
            "estimated_lines": 30,
            "dependencies": ["ST-1", "ST-2", "ST-3"]
        },
        {
            "id": "ST-5",
            "title": "README.md 사용법 업데이트",
            "estimated_lines": 15,
            "dependencies": ["ST-4"]
        }
    ]
}
```

---

## Phase 4: CODE Implementation (Auto-Claude Coder 24/7)

### 4.1 Coder Agent 24/7 Loop 시작

```python
# Auto-Claude Coder Agent의 24/7 루프

class CoderAgent:
    async def run_forever(self):
        while True:
            task = await self.get_next_subtask()
            if task:
                await self.implement(task)
                await self.commit_changes(task)
            else:
                await asyncio.sleep(10)  # 10초 대기 후 재확인
```

### 4.2 Subtask 1: percentage() 구현

```python
# Calculator/src/operations.py (수정)

def percentage(value: float, percent: float) -> float:
    """
    Calculate percentage of a value.

    Args:
        value: The base value
        percent: The percentage to calculate

    Returns:
        The calculated percentage

    Example:
        >>> percentage(100, 15)
        15.0
    """
    return value * (percent / 100)
```

### 4.3 Subtask 2: discount() 구현

```python
def discount(value: float, percent: float) -> float:
    """
    Apply discount to a value.

    Args:
        value: The original value
        percent: The discount percentage

    Returns:
        The discounted value

    Example:
        >>> discount(200, 10)
        180.0
    """
    return value * (1 - percent / 100)
```

### 4.4 Subtask 3: what_percent() 구현

```python
def what_percent(part: float, whole: float) -> float:
    """
    Calculate what percentage part is of whole.

    Args:
        part: The partial value
        whole: The total value

    Returns:
        The percentage

    Example:
        >>> what_percent(50, 200)
        25.0
    """
    if whole == 0:
        raise ValueError("Whole cannot be zero")
    return (part / whole) * 100
```

### 4.5 Subtask 4: 테스트 케이스 추가

```python
# Calculator/tests/test_calculator.py (추가)

import pytest
from src.operations import percentage, discount, what_percent

class TestPercentFunctions:

    def test_percentage_basic(self):
        assert percentage(100, 15) == 15.0
        assert percentage(200, 50) == 100.0

    def test_percentage_edge_cases(self):
        assert percentage(100, 0) == 0.0
        assert percentage(100, 100) == 100.0
        assert percentage(100, -10) == -10.0  # negative percent

    def test_discount_basic(self):
        assert discount(200, 10) == 180.0
        assert discount(100, 50) == 50.0

    def test_discount_edge_cases(self):
        assert discount(100, 0) == 100.0
        assert discount(100, 100) == 0.0

    def test_what_percent_basic(self):
        assert what_percent(50, 200) == 25.0
        assert what_percent(25, 100) == 25.0

    def test_what_percent_zero_whole(self):
        with pytest.raises(ValueError):
            what_percent(50, 0)
```

### 4.6 Git Commit (각 Subtask 완료 시)

```bash
# Auto-Claude가 각 subtask 완료 시 자동 commit

git add Calculator/src/operations.py
git commit -m "feat(calculator): add percentage() function

- Implements REQ-1 from SPEC-042
- Formula: value * (percent / 100)
- Handles edge cases: 0%, 100%, negative

Refs: #42"
```

---

## Phase 5: QA Validation (AG Reflection + gui_test_agent)

### 5.1 Pattern Selection: Reflection

Orchestrator가 QA에 **Reflection Pattern**을 선택합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│ AG Reflection Pattern for QA                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [QA Reviewer]                                                  │
│       │                                                         │
│       ├─→ "코드 리뷰" ──→ [Code Analysis]                       │
│       │                         │                               │
│       │                         ▼                               │
│       │                  "함수 3개 구현 확인"                   │
│       │                  "docstring 완비"                       │
│       │                  "type hints 적용"                      │
│       │                         │                               │
│       ├─→ "테스트 실행" ──→ [Test Runner]                       │
│       │                         │                               │
│       │                         ▼                               │
│       │                  "pytest: 8 passed"                     │
│       │                         │                               │
│       ├─→ "E2E 테스트" ──→ [gui_test_agent :8120]              │
│       │                         │                               │
│       │                         ▼                               │
│       │                  "GUI 버튼 클릭 테스트 통과"            │
│       │                         │                               │
│       └─→ [QA PASS] ────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Auto-Claude QA Reviewer 실행

```python
# Auto-Claude QA Reviewer가 코드 검증

qa_result = {
    "spec_id": "SPEC-042",
    "status": "PASS",
    "checks": {
        "code_review": {
            "status": "PASS",
            "details": "All functions implemented with proper docstrings"
        },
        "unit_tests": {
            "status": "PASS",
            "passed": 8,
            "failed": 0,
            "coverage": "95%"
        },
        "type_check": {
            "status": "PASS",
            "tool": "mypy",
            "errors": 0
        },
        "lint": {
            "status": "PASS",
            "tool": "ruff",
            "warnings": 0
        }
    }
}
```

### 5.3 gui_test_agent E2E 테스트

```python
# gui_test_agent (localhost:8120)가 PyAutoGUI로 E2E 테스트

# HTTP POST to localhost:8120/a2a
{
    "task": "E2E test for Calculator percent functions",
    "steps": [
        {"action": "launch", "app": "Calculator"},
        {"action": "click", "element": "percent_button"},
        {"action": "type", "value": "100"},
        {"action": "click", "element": "percent_input"},
        {"action": "type", "value": "15"},
        {"action": "click", "element": "calculate"},
        {"action": "verify", "expected": "15.0"}
    ]
}

# Response
{
    "status": "PASS",
    "steps_completed": 7,
    "screenshots": ["step1.png", "step2.png", ...],
    "final_result": "15.0",
    "expected": "15.0",
    "match": true
}
```

### 5.4 QA Fix (필요시)

만약 QA에서 실패하면 **QA Fixer Agent**가 자동 수정합니다:

```
┌─────────────────────────────────────────────────────────────────┐
│ QA Fix Loop (if needed)                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [QA Reviewer] ──→ FAIL ──→ [QA Fixer]                          │
│       ▲                          │                              │
│       │                          ▼                              │
│       │                    Fix the issue                        │
│       │                          │                              │
│       └──────────── Re-review ───┘                              │
│                                                                 │
│  Max iterations: 3                                              │
│  If still fails: Human review requested                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 6: PR Creation & Merge

### 6.1 Auto-Claude PR 생성

```python
# Auto-Claude가 GitHub PR 자동 생성

pr_data = {
    "title": "feat(calculator): Add percent calculation functions",
    "body": """
## Summary
Implements percentage calculation functions for Calculator app.

Closes #42

## Changes
- Added `percentage(value, percent)` function
- Added `discount(value, percent)` function
- Added `what_percent(part, whole)` function
- Added comprehensive test cases (8 tests, 95% coverage)
- Updated README with usage examples

## Test Results
```
pytest: 8 passed in 0.42s
mypy: Success
ruff: All checks passed
E2E: All scenarios passed
```

## Screenshots
![E2E Test Result](screenshots/e2e_result.png)

---
*This PR was automatically generated by 25_ACE (Auto-Claude + AG)*
    """,
    "head": "feature/SPEC-042-percent-functions",
    "base": "main",
    "labels": ["enhancement", "auto-generated"]
}
```

### 6.2 PR Review (Debate Pattern - 선택적)

복잡한 PR의 경우 **AG Debate Pattern**으로 코드 리뷰:

```
┌─────────────────────────────────────────────────────────────────┐
│ AG Debate Pattern for PR Review (Optional)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Pro Agent]                    [Con Agent]                     │
│       │                              │                          │
│       ├─→ "코드 품질 좋음" ◄────────►─┤ "edge case 더 필요"     │
│       │                              │                          │
│       ├─→ "테스트 충분" ◄────────────►─┤ "음수 테스트 추가?"    │
│       │                              │                          │
│       └─→ [Consensus: APPROVE with minor suggestions]           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Auto-Merge

```bash
# CI/CD 통과 후 자동 머지

gh pr merge 123 --squash --auto

# Merge commit message
"feat(calculator): Add percent calculation functions (#123)

* Add percentage(), discount(), what_percent() functions
* Add 8 test cases with 95% coverage
* Update README

Closes #42

Co-authored-by: Auto-Claude <auto-claude@25ace.ai>
Co-authored-by: AG-ACE-BRIDGE <ag-ace@25ace.ai>"
```

### 6.4 GitHub Issue 자동 Close

```python
# PR merge 시 GitHub Issue #42 자동 close
# "Closes #42" 키워드로 자동 처리

# 추가로 Auto-Claude가 완료 코멘트 추가
comment = """
## Resolved by PR #123

### Implementation Summary
- Added 3 new percentage functions
- All tests passing (8/8)
- E2E validation complete

### Usage
```python
from calculator.operations import percentage, discount, what_percent

percentage(100, 15)  # → 15.0
discount(200, 10)    # → 180.0
what_percent(50, 200)  # → 25.0
```

---
*Automatically resolved by 25_ACE system*
"""
```

---

## Phase 7: Memory & Learning

### 7.1 Graphiti (LadybugDB) 패턴 학습

```python
# Graphiti에 코드 패턴 저장 (향후 재사용)

pattern_learned = {
    "type": "percent_calculation",
    "language": "python",
    "functions": ["percentage", "discount", "what_percent"],
    "test_pattern": "parametrized pytest",
    "success_rate": 1.0,
    "reusable": True
}
```

---

## Complete Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE TIMELINE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  10:00  GitHub Issue #42 생성                                               │
│    │                                                                        │
│  10:05  AG-ACE-BRIDGE 감지 → Task Queue 등록                                │
│    │                                                                        │
│  10:10  [SPEC Phase] AG Selector Pattern 시작                               │
│    │    └─ research_agent: 코드베이스 분석                                  │
│    │    └─ calculator_agent: 수학 로직 검증                                 │
│  10:30  SPEC-042.yaml 생성 완료                                             │
│    │                                                                        │
│  10:35  [PLAN Phase] AG Magentic Pattern 시작                               │
│    │    └─ Planner Agent: 5개 subtask 분해                                  │
│  10:45  Plan 생성 완료                                                      │
│    │                                                                        │
│  10:50  [CODE Phase] Auto-Claude Coder 24/7 시작                            │
│    │    └─ ST-1: percentage() 구현                                          │
│    │    └─ ST-2: discount() 구현                                            │
│    │    └─ ST-3: what_percent() 구현                                        │
│    │    └─ ST-4: 테스트 케이스 작성                                         │
│    │    └─ ST-5: README 업데이트                                            │
│  12:50  코드 구현 완료                                                      │
│    │                                                                        │
│  12:55  [QA Phase] AG Reflection Pattern 시작                               │
│    │    └─ QA Reviewer: 코드 리뷰                                           │
│    │    └─ gui_test_agent: E2E 테스트                                       │
│  13:20  QA PASS                                                             │
│    │                                                                        │
│  13:25  [MERGE Phase] PR 생성                                               │
│  13:30  PR Merge + Issue Close                                              │
│    │                                                                        │
│  13:35  Memory Sync 완료                                                    │
│                                                                             │
│  Total: 3시간 35분 (완전 자동)                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Monitoring (★ 2026-01-25 업데이트)

> **Note**: AG-ACE-BRIDGE Dashboard(8080)는 제거되었습니다.
> 모니터링은 Auto-Claude UI에서 진행합니다.

Auto-Claude UI에서 실시간 모니터링:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Auto-Claude UI - Agent Terminals + AutoGen Collab Panel                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Current Task: SPEC-042 - Calculator 퍼센트 기능           [RUNNING] │   │
│  │ Progress: ████████████████████░░░░░ 80%                             │   │
│  │ Phase: QA Validation                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                │
│  │ AutoGen Studio Status    │  │ Real-time Agent Chat      │                │
│  │ ✓ Connected (8081)       │  │ [Streaming from AutoGen]  │                │
│  │ ✓ Latest Run: complete   │  │ "계산 완료: 8"           │                │
│  └──────────────────────────┘  └──────────────────────────┘                │
│                                                                             │
│  [AutogenStatusBadge] [AutogenCollabPanel] [AutogenResultsWidget]          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

### 새로운 아키텍처 (AG-ACE-BRIDGE)

| Phase | 컴포넌트 | 설명 |
|-------|----------|------|
| Phase 1 | spec_runner.py | AI 기반 Spec 생성 (복잡도 자동 평가) |
| Phase 2 | run.py | Planner → Coder → QA Reviewer → QA Fixer |
| Phase 3 | Git Worktree | 안전한 격리 빌드, --merge로 병합 |
| **Total** | - | **완전 자동화** |

### 사용된 Auto-Claude 기능

| 기능 | 설명 |
|------|------|
| **AI Spec 생성** | 복잡도 자동 평가, 정교한 Spec |
| **Planner Agent** | 구현 계획 수립, subtask 분해 |
| **Coder Agent** | 코드 작성 (subagent 병렬 처리) |
| **QA Reviewer** | 검증 및 피드백 |
| **QA Fixer** | 수정 루프 |
| **Git Worktree** | 안전한 격리 빌드 |
| **Graphiti Memory** | 크로스 세션 컨텍스트 |

---

## 핵심 코드

```python
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()

# 완전 자동화 실행
result = executor.execute_full_pipeline_sync(
    task_description="Calculator에 퍼센트 기능 추가",
    complexity="standard",  # simple, standard, complex
    auto_merge=False
)

# 결과 확인
if result["success"]:
    print(f"Spec: {result['spec_id']}")
    print(f"Review: python run.py --spec {result['spec_id']} --review")
    print(f"Merge:  python run.py --spec {result['spec_id']} --merge")
```

---

## Next Steps

이 예시를 기반으로:

1. **복잡도 조절**: `complexity="complex"`로 더 정교한 Spec 생성
2. **자동 병합**: `auto_merge=True`로 완료 후 자동 병합
3. **AutoGen Studio 연동**: 에이전트 팀 설계 → 자동 실행
4. **모니터링**: Auto-Claude UI에서 실시간 진행 상황 확인

---

*이 문서는 25_ACE 시스템의 실제 워크플로우를 보여줍니다.*
*자세한 아키텍처는 [ARCHITECTURE.md](ARCHITECTURE.md)를 참조하세요.*