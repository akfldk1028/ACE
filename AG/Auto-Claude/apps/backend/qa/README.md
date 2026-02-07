# QA Module

품질 검증 모듈. QA Reviewer와 QA Fixer를 통한 자동 검증 및 수정 루프를 담당합니다.

## 구조

```
qa/
├── loop.py         # 메인 QA 루프 (QA Reviewer → QA Fixer)
├── qa_loop.py      # QA 루프 유틸리티
├── reviewer.py     # QA Reviewer 에이전트
├── fixer.py        # QA Fixer 에이전트
├── criteria.py     # 인수 조건 관리
├── report.py       # QA 리포트 생성
└── __init__.py
```

## QA 검증 플로우

```
┌──────────────────────────────────────────────────────┐
│                  QA VALIDATION LOOP                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [QA Reviewer] ──→ 테스트 실행 & 검증               │
│        │           (E2E 테스팅 via Electron MCP)    │
│        │                                             │
│        ├─→ APPROVED? ──→ 완료!                       │
│        │                                             │
│        └─→ REJECTED? ──→ [QA Fixer] ──→ 재검증 루프 │
│                              │                       │
│                              └──→ (최대 5회 반복)    │
│                                                      │
│  MAX_QA_ITERATIONS = 5                               │
│  반복 이슈 감지 시 Human Escalation                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## 핵심 컴포넌트

### reviewer.py - QA Reviewer

인수 조건을 기반으로 구현을 검증합니다.

```python
from qa.reviewer import run_qa_review

result = run_qa_review(
    spec_dir="/path/to/spec",
    project_dir="/path/to/project"
)
# result: "APPROVED" 또는 "REJECTED"
```

### fixer.py - QA Fixer

QA에서 발견된 이슈를 자동으로 수정합니다.

```python
from qa.fixer import run_qa_fix

result = run_qa_fix(
    spec_dir="/path/to/spec",
    project_dir="/path/to/project",
    fix_request="/path/to/QA_FIX_REQUEST.md"
)
```

### loop.py - QA 루프

Reviewer → Fixer 반복 루프를 관리합니다.

```python
from qa.loop import run_qa_loop

result = run_qa_loop(
    spec_dir="/path/to/spec",
    project_dir="/path/to/project",
    max_iterations=5
)
```

## E2E 테스팅 (Electron MCP)

QA 에이전트는 Electron MCP를 통해 실제 앱과 상호작용할 수 있습니다.

### 설정

```bash
# .env
ELECTRON_MCP_ENABLED=true
ELECTRON_DEBUG_PORT=9222
```

### 기능

- 스크린샷 캡처
- 버튼 클릭, 폼 입력
- 페이지 구조 검사
- 콘솔 로그 읽기

## 생성되는 파일

```
.auto-claude/specs/XXX-feature/
├── qa_report.md           # QA 검증 결과
├── QA_FIX_REQUEST.md      # 수정 필요 사항 (rejected 시)
└── implementation_plan.json  # qa_status 필드 업데이트
```

## 인수 조건 (Acceptance Criteria)

`criteria.py`에서 인수 조건을 관리합니다:

```python
from qa.criteria import get_acceptance_criteria

criteria = get_acceptance_criteria(spec_dir)
# spec.md에서 추출된 인수 조건 목록
```

## 사용법

### CLI에서 QA 실행

```bash
cd apps/backend

# QA 수동 실행
python run.py --spec 001 --qa

# QA 상태 확인
python run.py --spec 001 --qa-status
```

## 관련 파일

- `qa/loop.py`: 메인 QA 루프
- `qa/reviewer.py`: 검증 에이전트
- `qa/fixer.py`: 수정 에이전트
- `prompts/qa_reviewer.md`: Reviewer 프롬프트
- `prompts/qa_fixer.md`: Fixer 프롬프트
