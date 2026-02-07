"""
Workflow Executor (Enhanced)
=============================

AutoGen -> Auto-Claude 완전 자동화 파이프라인.

두 가지 모드:
1. AI 모드 (기본): spec_runner.py 사용 - AI가 Spec 생성
2. 템플릿 모드: autogen_to_spec.py 사용 - 빠른 템플릿 생성

사용법:
    executor = WorkflowExecutor()

    # AI 모드 (Auto-Claude의 모든 기능 활용)
    result = await executor.execute_full_pipeline(
        task_description="계산기 앱 만들어줘",
        complexity="standard"  # simple, standard, complex
    )

    # 템플릿 모드 (빠르지만 간단)
    result = await executor.execute(
        task_description="계산기 앱 만들어줘",
        workflow_name="calculator_app"
    )
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List, Literal

from .autogen_to_spec import AutogenToSpec
from .auto_claude_runner import AutoClaudeRunner

# Input validation constants
MAX_TASK_DESCRIPTION_LENGTH = 10000
SAFE_TEXT_REGEX = re.compile(r'^[\x20-\x7E\u00A0-\uFFFF\n\r\t]*$')
SPEC_ID_REGEX = re.compile(r'^\d{3}(?:-[a-z0-9-]+)?$')


def validate_task_description(description: str) -> str:
    """Validate and sanitize task description to prevent injection."""
    if not description or not description.strip():
        raise ValueError("Task description cannot be empty")
    if len(description) > MAX_TASK_DESCRIPTION_LENGTH:
        raise ValueError(f"Task description exceeds maximum length of {MAX_TASK_DESCRIPTION_LENGTH}")
    if not SAFE_TEXT_REGEX.match(description):
        raise ValueError("Task description contains invalid characters")
    return description.strip()


def validate_spec_id(spec_id: str) -> str:
    """Validate spec ID format (e.g., '001-feature-name')."""
    if not spec_id:
        raise ValueError("Spec ID cannot be empty")
    if not SPEC_ID_REGEX.match(spec_id):
        raise ValueError(f"Invalid spec ID format: {spec_id}. Expected format: '001-feature-name'")
    return spec_id


class WorkflowExecutor:
    """AutoGen -> Auto-Claude 완전 자동화 파이프라인."""

    def __init__(
        self,
        auto_claude_path: Optional[str] = None,
        project_path: Optional[str] = None
    ):
        """
        Args:
            auto_claude_path: Auto-Claude 프로젝트 경로 (None이면 config에서 로드)
            project_path: 타겟 프로젝트 경로 (None이면 Auto-Claude 자체)
        """
        if auto_claude_path is None:
            from src.utils.config import get_settings
            _backend = get_settings().auto_claude_path  # e.g. .../Auto-Claude/apps/backend
            auto_claude_path = str(Path(_backend).parent.parent)  # -> .../Auto-Claude
        self.auto_claude_path = Path(auto_claude_path)
        self.project_path = Path(project_path) if project_path else self.auto_claude_path
        self.backend_path = self.auto_claude_path / "apps" / "backend"

        # 컴포넌트 초기화
        self.converter = AutogenToSpec(
            auto_claude_path=str(self.auto_claude_path),
            project_path=str(self.project_path)
        )
        self.runner = AutoClaudeRunner(
            auto_claude_path=str(self.auto_claude_path),
            project_path=str(self.project_path)
        )

        # Python 실행 경로
        self.python_path = self._find_python()

        # 실행 기록
        self.execution_history: List[Dict[str, Any]] = []

    def _find_python(self) -> str:
        """Python 실행 경로 찾기."""
        venv_python = self.backend_path / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return "python"

    # ========================================
    # AI 모드: spec_runner.py + run.py
    # ========================================

    def execute_full_pipeline_sync(
        self,
        task_description: str,
        complexity: Literal["simple", "standard", "complex"] = "standard",
        auto_merge: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
        timeout: int = 7200  # 2시간
    ) -> Dict[str, Any]:
        """
        전체 AI 파이프라인 실행 (spec_runner.py + run.py).

        이 방식이 Auto-Claude의 모든 기능을 활용:
        - AI 기반 Spec 생성
        - Planner -> Coder -> QA Reviewer -> QA Fixer 파이프라인
        - Git Worktree 격리
        - Graphiti Memory

        Args:
            task_description: 태스크 설명 (예: "계산기 앱 만들어줘")
            complexity: 복잡도 (simple, standard, complex)
            auto_merge: 완료 후 자동 병합 여부
            on_output: 출력 콜백 함수
            timeout: 타임아웃 (초)

        Returns:
            실행 결과 딕셔너리
        """
        # Validate inputs before any subprocess execution
        task_description = validate_task_description(task_description)

        start_time = datetime.now()
        result = {
            "success": False,
            "mode": "full_pipeline",
            "task_description": task_description,
            "complexity": complexity,
            "start_time": start_time.isoformat(),
            "phases": []
        }

        def log(message: str):
            if on_output:
                on_output(message)
            else:
                try:
                    print(f"[FullPipeline] {message}")
                except UnicodeEncodeError:
                    # Windows cp949 can't handle some Unicode chars (box-drawing etc.)
                    enc = getattr(sys.stdout, "encoding", "ascii") or "ascii"
                    safe = message.encode(enc, errors="replace").decode(enc, errors="replace")
                    print(f"[FullPipeline] {safe}")

        try:
            # ========================================
            # Phase 1: spec_runner.py (AI Spec 생성)
            # ========================================
            log("=" * 60)
            log("Phase 1: AI Spec Creation (spec_runner.py)")
            log("=" * 60)
            log(f"Task: {task_description}")
            log(f"Complexity: {complexity}")

            spec_runner_path = self.backend_path / "runners" / "spec_runner.py"

            cmd = [
                self.python_path,
                str(spec_runner_path),
                "--task", task_description,
                "--complexity", complexity,
                "--auto-approve",
                "--no-build",
            ]

            log(f"Command: {' '.join(cmd)}")

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                bufsize=1
            )

            spec_output = []
            spec_id = None

            try:
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    spec_output.append(line)
                    log(f"[spec_runner] {line}")

                    # Spec ID 추출 (예: "Created spec: 001-feature-name")
                    if "Created spec:" in line or "Spec created:" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            spec_id = parts[-1].strip().split("-")[0]

                process.wait(timeout=timeout // 2)  # Spec 생성에 절반 시간
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
                result["error"] = f"Spec creation timeout ({timeout // 2}s)"
                result["phases"].append({
                    "phase": "spec_creation",
                    "success": False,
                    "error": result["error"],
                })
                return result
            finally:
                if process.stdout:
                    process.stdout.close()

            if process.returncode != 0:
                result["phases"].append({
                    "phase": "spec_creation",
                    "success": False,
                    "error": "spec_runner.py failed",
                    "return_code": process.returncode
                })
                result["error"] = "Spec creation failed"
                return result

            # Spec ID 찾기 (출력에서 못 찾았으면 최신 spec 사용)
            if not spec_id:
                specs = self.runner.get_specs()
                if specs:
                    spec_id = specs[-1]["number"]

            if not spec_id:
                result["error"] = "Could not find created spec"
                return result

            result["spec_id"] = spec_id
            result["phases"].append({
                "phase": "spec_creation",
                "success": True,
                "spec_id": spec_id
            })

            log(f"\nSpec created: {spec_id}")

            # ========================================
            # Phase 2: run.py (빌드 실행)
            # ========================================
            log("")
            log("=" * 60)
            log("Phase 2: Build Execution (run.py)")
            log("=" * 60)
            log(f"Spec ID: {spec_id}")

            run_result = self.runner.run_spec_sync(
                spec_id=spec_id,
                on_output=on_output,
                timeout=timeout // 2
            )

            result["run_result"] = run_result
            result["phases"].append({
                "phase": "build_execution",
                "success": run_result.get("success", False),
                "duration_seconds": run_result.get("duration_seconds"),
                "return_code": run_result.get("return_code")
            })

            if not run_result.get("success"):
                result["error"] = run_result.get("error", "Build failed")
                return result

            # ========================================
            # Phase 3: 완료 처리 (선택적 merge)
            # ========================================
            if auto_merge:
                log("")
                log("=" * 60)
                log("Phase 3: Auto Merge")
                log("=" * 60)

                merge_result = self._merge_spec(spec_id, on_output)
                result["phases"].append({
                    "phase": "merge",
                    "success": merge_result.get("success", False)
                })
                result["merged"] = merge_result.get("success", False)
            else:
                log("")
                log("=" * 60)
                log("Phase 3: Ready for Review")
                log("=" * 60)
                log(f"Review with: python run.py --spec {spec_id} --review")
                log(f"Merge with:  python run.py --spec {spec_id} --merge")
                result["phases"].append({
                    "phase": "ready_for_review",
                    "success": True
                })

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            result["phases"].append({
                "phase": "error",
                "success": False,
                "error": str(e)
            })

        # 완료 시간
        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()

        self.execution_history.append(result)
        return result

    async def execute_full_pipeline(
        self,
        task_description: str,
        complexity: Literal["simple", "standard", "complex"] = "standard",
        auto_merge: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
        timeout: int = 7200
    ) -> Dict[str, Any]:
        """전체 AI 파이프라인 비동기 실행."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute_full_pipeline_sync(
                task_description, complexity, auto_merge, on_output, timeout
            )
        )

    def _merge_spec(
        self,
        spec_id: str,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Spec 병합 (run.py --merge)."""
        spec_id = validate_spec_id(spec_id)
        cmd = [
            self.python_path,
            str(self.backend_path / "run.py"),
            "--spec", spec_id,
            "--merge"
        ]

        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env
            )

            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                if on_output:
                    on_output(f"[merge] {line.rstrip()}")

            process.wait(timeout=300)

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # 템플릿 모드: autogen_to_spec.py + run.py
    # ========================================

    def execute_sync(
        self,
        task_description: str,
        workflow_name: Optional[str] = None,
        autogen_workflow: Optional[Dict[str, Any]] = None,
        goals: Optional[list] = None,
        on_output: Optional[Callable[[str], None]] = None,
        timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        템플릿 기반 실행 (빠르지만 AI 없음).

        Args:
            task_description: 태스크 설명
            workflow_name: 워크플로우 이름 (선택)
            autogen_workflow: AutoGen 워크플로우 JSON (선택)
            goals: 목표 목록 (선택)
            on_output: 출력 콜백 함수
            timeout: 타임아웃 (초)

        Returns:
            실행 결과 딕셔너리
        """
        start_time = datetime.now()
        result = {
            "success": False,
            "mode": "template",
            "task_description": task_description,
            "workflow_name": workflow_name,
            "start_time": start_time.isoformat(),
            "phases": []
        }

        def log(message: str):
            if on_output:
                on_output(message)
            else:
                print(f"[TemplateMode] {message}")

        try:
            # Phase 1: Spec 변환 (템플릿)
            log("=" * 60)
            log("Phase 1: Template Spec Creation")
            log("=" * 60)

            spec_path = self.converter.convert(
                task_description=task_description,
                workflow_name=workflow_name,
                autogen_workflow=autogen_workflow,
                goals=goals
            )

            spec_folder_name = spec_path.name
            spec_number = spec_folder_name.split("-", 1)[0]

            result["spec_path"] = str(spec_path)
            result["spec_id"] = spec_number
            result["phases"].append({
                "phase": "convert",
                "success": True,
                "spec_path": str(spec_path)
            })

            log(f"Spec created: {spec_path}")

            # Phase 2: Auto-Claude 실행
            log("")
            log("=" * 60)
            log("Phase 2: Auto-Claude Execution")
            log("=" * 60)

            run_result = self.runner.run_spec_sync(
                spec_id=spec_number,
                on_output=on_output,
                timeout=timeout
            )

            result["run_result"] = run_result
            result["phases"].append({
                "phase": "execute",
                "success": run_result.get("success", False),
                "duration_seconds": run_result.get("duration_seconds"),
                "return_code": run_result.get("return_code")
            })

            result["success"] = run_result.get("success", False)

        except Exception as e:
            result["error"] = str(e)
            result["phases"].append({
                "phase": "error",
                "success": False,
                "error": str(e)
            })

        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()

        self.execution_history.append(result)
        return result

    async def execute(
        self,
        task_description: str,
        workflow_name: Optional[str] = None,
        autogen_workflow: Optional[Dict[str, Any]] = None,
        goals: Optional[list] = None,
        on_output: Optional[Callable[[str], None]] = None,
        timeout: int = 3600
    ) -> Dict[str, Any]:
        """템플릿 기반 비동기 실행."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute_sync(
                task_description, workflow_name, autogen_workflow,
                goals, on_output, timeout
            )
        )

    # ========================================
    # 유틸리티 메서드
    # ========================================

    def get_status(self, spec_id: str) -> Dict[str, Any]:
        """Spec 실행 상태 확인."""
        return self.runner.check_spec_status(spec_id)

    def list_specs(self) -> List[Dict[str, Any]]:
        """사용 가능한 Spec 목록."""
        return self.runner.get_specs()

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """실행 기록 반환."""
        return self.execution_history

    def save_execution_history(self, path: Optional[str] = None) -> str:
        """실행 기록 저장."""
        if not path:
            path = str(self.project_path / ".auto-claude" / "execution_history.json")

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.execution_history, f, ensure_ascii=False, indent=2)

        return path

    def review_spec(self, spec_id: str) -> Dict[str, Any]:
        """Spec 리뷰 (run.py --review)."""
        cmd = [
            self.python_path,
            str(self.backend_path / "run.py"),
            "--spec", spec_id,
            "--review"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 테스트
    executor = WorkflowExecutor()

    print("=== Spec List ===")
    specs = executor.list_specs()
    for spec in specs:
        print(f"  {spec['number']}: {spec['name']}")

    print("\n=== Usage ===")
    print("Full Pipeline (AI mode):")
    print("  result = executor.execute_full_pipeline_sync('Create a calculator app')")
    print("\nTemplate Mode (fast):")
    print("  result = executor.execute_sync('Create a calculator app')")
