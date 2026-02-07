"""
Auto-Claude Runner
==================

Auto-Claude run.py 호출 래퍼.

사용법:
    runner = AutoClaudeRunner()
    result = await runner.run_spec("001-calculator-app")
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable
import threading
import queue


class AutoClaudeRunner:
    """Auto-Claude run.py 호출 래퍼."""

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
            _backend = get_settings().auto_claude_path
            auto_claude_path = str(Path(_backend).parent.parent)
        self.auto_claude_path = Path(auto_claude_path)
        self.project_path = Path(project_path) if project_path else self.auto_claude_path
        self.backend_path = self.auto_claude_path / "apps" / "backend"
        self.run_py = self.backend_path / "run.py"

        # Python 실행 경로
        self.python_path = self._find_python()

    def _find_python(self) -> str:
        """Python 실행 경로 찾기."""
        # Auto-Claude venv 확인
        venv_python = self.backend_path / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)

        # 시스템 Python
        return sys.executable

    def get_specs(self) -> list:
        """사용 가능한 Spec 목록 반환."""
        specs_dir = self.project_path / ".auto-claude" / "specs"
        specs = []

        if not specs_dir.exists():
            return specs

        for folder in sorted(specs_dir.iterdir()):
            if folder.is_dir():
                spec_file = folder / "spec.md"
                if spec_file.exists():
                    parts = folder.name.split("-", 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        specs.append({
                            "number": parts[0],
                            "name": parts[1],
                            "folder": folder.name,
                            "path": str(folder)
                        })

        return specs

    def run_spec_sync(
        self,
        spec_id: str,
        on_output: Optional[Callable[[str], None]] = None,
        timeout: int = 3600  # 1시간
    ) -> Dict[str, Any]:
        """
        Spec 동기 실행.

        Args:
            spec_id: Spec 번호 또는 폴더 이름 (예: "001" 또는 "001-calculator")
            on_output: 출력 콜백 함수
            timeout: 타임아웃 (초)

        Returns:
            실행 결과 딕셔너리
        """
        start_time = datetime.now()

        # 명령어 구성
        cmd = [
            self.python_path,
            str(self.run_py),
            "--spec", spec_id
        ]

        try:
            print(f"[AutoClaudeRunner] Run: {' '.join(cmd)}")
            print(f"[AutoClaudeRunner] CWD: {self.project_path}")
        except UnicodeEncodeError:
            print("[AutoClaudeRunner] Run: (encoding error in command)")
            print(f"[AutoClaudeRunner] CWD: {self.project_path}")

        try:
            # 환경 변수 설정
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            # 프로세스 실행 (stdin=PIPE로 interactive prompt 자동 응답)
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_path),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                bufsize=1
            )

            # Auto-confirm any "Press Enter" prompts by feeding newlines
            try:
                process.stdin.write("\n" * 5)
                process.stdin.flush()
                process.stdin.close()
            except (OSError, BrokenPipeError):
                # stdin may already be closed or process may have exited
                pass

            output_lines = []

            try:
                # 실시간 출력 읽기
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    output_lines.append(line)

                    if on_output:
                        on_output(line)
                    else:
                        try:
                            print(f"[Auto-Claude] {line}")
                        except UnicodeEncodeError:
                            enc = getattr(sys.stdout, "encoding", "ascii") or "ascii"
                            safe = line.encode(enc, errors="replace").decode(enc, errors="replace")
                            print(f"[Auto-Claude] {safe}")

                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
                return {
                    "success": False,
                    "spec_id": spec_id,
                    "error": f"Timeout ({timeout}s)",
                    "duration_seconds": timeout
                }
            finally:
                if process.stdout:
                    process.stdout.close()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "success": process.returncode == 0,
                "spec_id": spec_id,
                "return_code": process.returncode,
                "output": "\n".join(output_lines),
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

            print(f"[AutoClaudeRunner] Done: {'OK' if result['success'] else 'FAIL'} ({duration:.1f}s)")
            return result

        except Exception as e:
            return {
                "success": False,
                "spec_id": spec_id,
                "error": str(e)
            }

    async def run_spec(
        self,
        spec_id: str,
        on_output: Optional[Callable[[str], None]] = None,
        timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        Spec 비동기 실행.

        Args:
            spec_id: Spec 번호 또는 폴더 이름
            on_output: 출력 콜백 함수
            timeout: 타임아웃 (초)

        Returns:
            실행 결과 딕셔너리
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.run_spec_sync(spec_id, on_output, timeout)
        )

    def check_spec_status(self, spec_id: str) -> Dict[str, Any]:
        """Spec 상태 확인."""
        specs = self.get_specs()

        for spec in specs:
            if spec["number"] == spec_id or spec["folder"] == spec_id:
                spec_path = Path(spec["path"])
                plan_file = spec_path / "implementation_plan.json"

                status = "pending"
                progress = {"completed": 0, "total": 0}

                if plan_file.exists():
                    try:
                        with open(plan_file, "r", encoding="utf-8") as f:
                            plan = json.load(f)

                        total = 0
                        completed = 0
                        for phase in plan.get("phases", []):
                            for chunk in phase.get("chunks", []):
                                total += 1
                                if chunk.get("status") == "completed":
                                    completed += 1

                        progress = {"completed": completed, "total": total}

                        if total > 0:
                            if completed == total:
                                status = "complete"
                            elif completed > 0:
                                status = "in_progress"

                    except Exception as e:
                        print(f"[AutoClaudeRunner] Plan 읽기 실패: {e}")

                return {
                    "found": True,
                    "spec": spec,
                    "status": status,
                    "progress": progress
                }

        return {"found": False, "spec_id": spec_id}


if __name__ == "__main__":
    # 테스트
    runner = AutoClaudeRunner()

    print("=== Spec 목록 ===")
    specs = runner.get_specs()
    for spec in specs:
        print(f"  {spec['number']}: {spec['name']}")

    if specs:
        print(f"\n=== 첫 번째 Spec 상태 ===")
        status = runner.check_spec_status(specs[0]["number"])
        print(json.dumps(status, indent=2, ensure_ascii=False))
