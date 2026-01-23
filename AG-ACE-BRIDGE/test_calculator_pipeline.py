"""
Calculator App - Auto-Claude Pipeline Test

Auto-Claude 에이전트를 사용해서 Calculator 앱을 자동 생성합니다.
Pipeline: Planner → Coder → QA Reviewer → (QA Fixer if needed)
"""

import asyncio
from pathlib import Path

from src.agents.auto_claude import (
    AutoClaudePlanner,
    AutoClaudeCoder,
    AutoClaudeQAReviewer,
    AutoClaudeQAFixer,
    get_oauth_token,
    CLAUDE_SDK_AVAILABLE,
)


PROJECT_DIR = Path("D:/Data/25_ACE/Calculator")
PROJECT_SPEC = """
# Calculator App 프로젝트

## 목표
Python tkinter를 사용한 GUI 계산기 애플리케이션

## 기능 요구사항
1. 사칙연산 (덧셈, 뺄셈, 곱셈, 나눗셈)
2. GUI 인터페이스 (tkinter)
3. 숫자 버튼 (0-9)
4. 연산자 버튼 (+, -, *, /)
5. Clear/All Clear 버튼
6. 소수점 지원
7. = 버튼으로 결과 계산
8. 키보드 입력 지원

## 파일 구조
Calculator/
├── main.py          # 메인 실행 파일
├── calculator.py    # 계산 로직
├── gui.py           # tkinter GUI
├── tests/
│   └── test_calculator.py  # 단위 테스트
└── README.md        # 사용법

## 기술 스택
- Python 3.13
- tkinter (내장)
- pytest (테스트)
"""


async def run_pipeline():
    """Calculator 앱 생성 파이프라인 실행"""

    print("=" * 60)
    print("Calculator App - Auto-Claude Pipeline")
    print("=" * 60)

    # 사전 체크
    print("\n[0] Prerequisites Check")
    print(f"    Claude SDK available: {CLAUDE_SDK_AVAILABLE}")
    print(f"    OAuth token available: {get_oauth_token() is not None}")
    print(f"    Project directory: {PROJECT_DIR}")

    if not CLAUDE_SDK_AVAILABLE:
        print("\n[ERROR] Claude SDK not available!")
        print("Install: pip install claude-agent-sdk")
        return

    if not get_oauth_token():
        print("\n[ERROR] OAuth token not found!")
        print("Run 'claude' and '/login' to authenticate")
        return

    # 에이전트 초기화
    print("\n[1] Initializing Agents...")
    planner = AutoClaudePlanner()
    coder = AutoClaudeCoder()
    qa_reviewer = AutoClaudeQAReviewer()
    qa_fixer = AutoClaudeQAFixer()

    await planner.initialize()
    await coder.initialize()
    await qa_reviewer.initialize()
    await qa_fixer.initialize()
    print("    All agents initialized!")

    context = {"spec": PROJECT_SPEC}

    # Stage 1: Planning
    print("\n" + "=" * 60)
    print("[2] STAGE: PLANNER")
    print("=" * 60)

    plan_result = await planner.execute(
        task_description="Calculator 앱 구현 계획 수립",
        context={"requirements": PROJECT_SPEC},
        project_dir=PROJECT_DIR,
    )

    print(f"\n    Status: {plan_result.get('status')}")
    print(f"    Next action: {plan_result.get('next_action')}")

    if plan_result.get("status") == "failed":
        print(f"    Error: {plan_result.get('error')}")
        return

    context["plan"] = plan_result.get("plan", "")

    # Stage 2: Coding
    print("\n" + "=" * 60)
    print("[3] STAGE: CODER")
    print("=" * 60)

    code_result = await coder.execute(
        task_description="Calculator 앱 구현",
        context=context,
        project_dir=PROJECT_DIR,
    )

    print(f"\n    Status: {code_result.get('status')}")
    print(f"    Code generated: {code_result.get('code_generated')}")

    if code_result.get("status") == "failed":
        print(f"    Error: {code_result.get('error')}")
        return

    # Stage 3: QA Review
    print("\n" + "=" * 60)
    print("[4] STAGE: QA REVIEWER")
    print("=" * 60)

    qa_result = await qa_reviewer.execute(
        task_description="Calculator 앱 코드 리뷰",
        context={
            "requirements": PROJECT_SPEC,
            "acceptance_criteria": [
                "사칙연산이 정상 작동",
                "GUI가 표시됨",
                "테스트 통과",
            ],
        },
        project_dir=PROJECT_DIR,
    )

    print(f"\n    Status: {qa_result.get('status')}")
    print(f"    Review passed: {qa_result.get('review_passed')}")

    # Stage 4: QA Fix (if needed)
    if not qa_result.get("review_passed"):
        print("\n" + "=" * 60)
        print("[5] STAGE: QA FIXER")
        print("=" * 60)

        fix_result = await qa_fixer.execute(
            task_description="Calculator 앱 이슈 수정",
            context={
                "issues_found": qa_result.get("issues_found", []),
                "review_report": qa_result.get("review_report", ""),
            },
            project_dir=PROJECT_DIR,
        )

        print(f"\n    Status: {fix_result.get('status')}")
        print(f"    Fixes applied: {fix_result.get('fixes_applied')}")

    # Cleanup
    await planner.shutdown()
    await coder.shutdown()
    await qa_reviewer.shutdown()
    await qa_fixer.shutdown()

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print(f"\nProject created at: {PROJECT_DIR}")
    print("Run: python D:/Data/25_ACE/Calculator/main.py")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
