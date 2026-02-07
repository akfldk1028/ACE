# AG-CLI Claude CLI Tool
"""
Claude CLI 실행 도구

사용법:
    from tools.claude_cli import execute_claude_cli

    result = execute_claude_cli("React Button 컴포넌트 만들어줘")
"""
import os
import sys
import json
import subprocess
import threading
import uuid
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from utils.logging import log_line, set_current_task_id, generate_execution_summary, log_tool_use


def find_claude_cli() -> str:
    """Claude CLI 실행 파일 경로를 찾습니다.

    Returns:
        Claude CLI 경로
    """
    # 1. PATH에서 찾기
    claude_path = shutil.which("claude")
    if claude_path:
        return claude_path

    # 2. Windows npm 전역 설치 경로
    if sys.platform == "win32":
        npm_path = Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd"
        if npm_path.exists():
            return str(npm_path)

    # 3. 기본값
    return "claude"


# 모듈 로드 시 CLI 경로 캐시
CLAUDE_CLI_PATH = find_claude_cli()


def execute_claude_cli(task: str) -> dict:
    """Claude CLI를 실행하여 코드를 작성하거나 파일을 수정합니다.

    이 도구는 Claude Code CLI를 subprocess로 실행하여 실제 파일 작업을 수행합니다.
    작업은 지정된 폴더 내에서만 수행됩니다.
    **실시간 출력이 로그에 기록됩니다!**

    Args:
        task: 수행할 작업 설명 (예: "React Button 컴포넌트 만들어줘")

    Returns:
        Claude CLI 실행 결과를 담은 딕셔너리
    """
    work_dir = Path(config.WORK_FOLDER)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Task ID 생성 (로그 추적용)
    task_id = str(uuid.uuid4())[:8]
    set_current_task_id(task_id)

    # 로그 시작
    log_line(task_id, "=== Claude CLI Task Started ===", "START")
    log_line(task_id, f"Task: {task}", "INFO")
    log_line(task_id, f"Folder: {config.WORK_FOLDER}/", "INFO")
    log_line(task_id, f"Task ID: {task_id}", "INFO")

    # shared 폴더 생성 (없으면)
    shared_dir = Path(config.SHARED_FOLDER)
    shared_dir.mkdir(parents=True, exist_ok=True)

    # 시스템 프롬프트 구성
    system_prompt = f"""You are a {config.EXPERTISE} expert.
You can modify files in TWO folders:
1. {config.WORK_FOLDER}/ - Your main work folder
2. {config.SHARED_FOLDER}/ - Shared folder for cross-agent collaboration

Use the shared/ folder to:
- Share code, configs, or data with other agents
- Read files created by other agents
- Store common utilities or API specs

Do NOT modify files outside these two folders.
Write clean, well-documented code."""

    cmd = [
        CLAUDE_CLI_PATH,
        "-p", task,
        "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash",
        "--output-format", "stream-json",
        "--verbose",
        "--max-turns", str(config.MAX_TURNS),
        "--append-system-prompt", system_prompt
    ]

    log_line(task_id, f"Command: {CLAUDE_CLI_PATH}", "CMD")

    try:
        # Popen으로 실시간 스트리밍
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(work_dir),
            bufsize=1,
            encoding='utf-8',
            errors='replace',
        )

        stdout_lines = []
        stderr_lines = []

        # stdout 실시간 읽기 (별도 스레드)
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                if line:
                    stdout_lines.append(line)
                    stripped = line.strip()
                    if stripped:
                        try:
                            data = json.loads(stripped)
                            msg_type = data.get("type")

                            if msg_type == "system":
                                subtype = data.get("subtype", "")
                                if subtype == "init":
                                    session_id = data.get("session_id", "")[:8]
                                    log_line(task_id, f"[INIT] Session: {session_id}", "INFO")

                            elif msg_type == "assistant":
                                msg_obj = data.get("message", {})
                                content_arr = msg_obj.get("content", [])
                                for item in content_arr:
                                    if item.get("type") == "text":
                                        text = item.get("text", "")
                                        if text and len(text) < 150:
                                            log_line(task_id, f"[ASSISTANT] {text[:100]}", "OUT")
                                    elif item.get("type") == "tool_use":
                                        tool_name = item.get("name", "Unknown")
                                        tool_input = item.get("input", {})
                                        log_tool_use(task_id, tool_name, tool_input)

                            elif msg_type == "user":
                                tool_result = data.get("tool_use_result", {})
                                if tool_result:
                                    result_type = tool_result.get("type", "")
                                    file_path = tool_result.get("filePath", "")
                                    if result_type == "create":
                                        log_line(task_id, f"[CREATED] {file_path}", "RESULT")
                                    elif result_type == "edit":
                                        log_line(task_id, f"[EDITED] {file_path}", "RESULT")
                                    else:
                                        log_line(task_id, f"[RESULT] {result_type}: {file_path}", "RESULT")

                            elif msg_type == "result":
                                subtype = data.get("subtype", "")
                                duration = data.get("duration_ms", 0)
                                log_line(task_id, f"[DONE] Status: {subtype}, Duration: {duration}ms", "INFO")

                        except json.JSONDecodeError:
                            if len(stripped) < 200:
                                log_line(task_id, stripped[:100], "OUT")

        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                if line:
                    stderr_lines.append(line)
                    log_line(task_id, line.strip(), "ERR")

        # 스레드로 stdout/stderr 동시 읽기
        stdout_thread = threading.Thread(target=read_stdout)
        stderr_thread = threading.Thread(target=read_stderr)
        stdout_thread.start()
        stderr_thread.start()

        # 타임아웃 대기 (5분)
        try:
            process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            process.kill()
            log_line(task_id, "TIMEOUT - 작업이 5분을 초과했습니다", "ERROR")
            return {
                "success": False,
                "error": "Timeout - 작업이 5분을 초과했습니다",
                "task": task,
                "task_id": task_id,
                "folder": config.WORK_FOLDER,
                "logs_url": f"/logs/{task_id}"
            }

        stdout_thread.join()
        stderr_thread.join()

        stdout_output = ''.join(stdout_lines)
        stderr_output = ''.join(stderr_lines)

        if process.returncode != 0:
            log_line(task_id, f"Exit code: {process.returncode}", "ERROR")
            log_line(task_id, "=== Task Failed ===", "END")
            return {
                "success": False,
                "error": stderr_output,
                "task": task,
                "task_id": task_id,
                "folder": config.WORK_FOLDER,
                "logs_url": f"/logs/{task_id}"
            }

        # NDJSON 파싱 - 최종 결과 추출
        log_line(task_id, "=== Task Completed Successfully ===", "END")

        final_result = None
        all_text_parts = []
        tool_uses = []
        tool_results = []

        for line in stdout_lines:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
                msg_type = data.get("type")

                if msg_type == "message":
                    role = data.get("role", "")
                    if role == "assistant":
                        for item in data.get("content", []):
                            if item.get("type") == "text":
                                all_text_parts.append(item.get("text", ""))

                elif msg_type == "assistant":
                    msg_obj = data.get("message", {})
                    content_arr = msg_obj.get("content", [])
                    for item in content_arr:
                        if item.get("type") == "tool_use":
                            tool_uses.append({
                                "tool": item.get("name"),
                                "input": item.get("input")
                            })

                elif msg_type == "tool_result":
                    tool_results.append(data.get("output", ""))

                elif msg_type == "result":
                    final_result = {
                        "status": data.get("status"),
                        "duration_ms": data.get("duration_ms"),
                        "session_id": data.get("session_id")
                    }

            except json.JSONDecodeError:
                pass

        # 응답 구성
        combined_output = {
            "result": final_result,
            "assistant_response": "".join(all_text_parts),
            "tools_used": tool_uses,
            "tool_results": tool_results,
            "message_count": len(stdout_lines)
        }

        # 실행 로그 요약 생성
        execution_log_summary = generate_execution_summary(task_id, tool_uses)

        return {
            "success": True,
            "output": combined_output,
            "task": task,
            "task_id": task_id,
            "folder": config.WORK_FOLDER,
            "logs_url": f"/logs/{task_id}",
            "execution_summary": execution_log_summary
        }

    except FileNotFoundError:
        log_line(task_id, "Claude CLI를 찾을 수 없습니다!", "ERROR")
        return {
            "success": False,
            "error": "Claude CLI를 찾을 수 없습니다. Claude Code가 설치되어 있는지 확인하세요.",
            "task": task,
            "task_id": task_id,
            "folder": config.WORK_FOLDER
        }
