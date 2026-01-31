"""
AutoGen Studio Session Watcher

AutoGen Studio의 세션 완료를 감지하고 SharedMemory MCP 서버로 전송.
이를 통해 Auto-Claude UI에서 AutoGen Studio 결과를 자동으로 볼 수 있음.

Architecture:
    AutoGen Studio (8081) -> Watcher (polling) -> MCP Server (8102) -> SharedMemory (8101) -> Auto-Claude UI
"""

import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, Set
import json


class AutoGenSessionWatcher:
    """AutoGen Studio 세션 모니터링 및 SharedMemory 동기화"""

    def __init__(
        self,
        autogen_url: str = "http://localhost:8081",
        mcp_url: str = "http://localhost:8102",
        poll_interval: float = 2.0,
        user_id: str = "guestuser@gmail.com",
    ):
        self.autogen_url = autogen_url
        self.mcp_url = mcp_url
        self.poll_interval = poll_interval
        self.user_id = user_id
        self.seen_runs: Set[str] = set()  # session_id:run_id
        self.http_client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        return self.http_client

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()

    async def get_sessions(self) -> list:
        """AutoGen Studio에서 세션 목록 조회"""
        client = await self.get_client()
        try:
            response = await client.get(
                f"{self.autogen_url}/api/sessions/",
                params={"user_id": self.user_id}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", []) if isinstance(data, dict) else data
        except Exception as e:
            print(f"[ERROR] Failed to get sessions: {e}")
        return []

    async def get_session_runs(self, session_id: int) -> dict:
        """특정 세션의 실행(runs) 조회"""
        client = await self.get_client()
        try:
            response = await client.get(
                f"{self.autogen_url}/api/sessions/{session_id}/runs/",
                params={"user_id": self.user_id}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}) if isinstance(data, dict) else {}
        except Exception as e:
            print(f"[ERROR] Failed to get runs for session {session_id}: {e}")
        return {}

    async def sync_to_mcp(self, session: dict, run_data: dict) -> bool:
        """MCP 서버로 세션 결과 동기화"""
        client = await self.get_client()

        # 결과 파싱
        run_id = run_data.get("id", "unknown")
        status = run_data.get("status", "unknown")
        task_content = ""
        result_content = ""
        agents_used = set()

        # 태스크 추출
        task = run_data.get("task", {})
        task_msgs = task.get("content", [])
        for msg in task_msgs:
            if msg.get("source") == "user":
                task_content = msg.get("content", "")
                break

        # 결과 메시지 추출
        team_result = run_data.get("team_result", {})
        task_result = team_result.get("task_result", {})
        messages = task_result.get("messages", [])

        for msg in messages:
            source = msg.get("source", "")
            if source and source != "user":
                agents_used.add(source)
                # 마지막 에이전트 메시지를 결과로 사용
                content = msg.get("content", "")
                # content가 리스트인 경우 첫 번째 텍스트 추출
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content = item.get("text", "")
                            break
                        elif isinstance(item, str):
                            content = item
                            break
                    else:
                        content = str(content)
                if content and isinstance(content, str) and not content.startswith("{"):
                    result_content = content

        if not result_content:
            return False

        # 결과 정리 (500자 제한)
        if len(result_content) > 500:
            result_content = result_content[:500] + "..."

        payload = {
            "name": "sync_workflow_result",
            "arguments": {
                "workflow_name": f"session_{session.get('id', 'unknown')}",
                "task": task_content or "Unknown task",
                "result": result_content,
                "agents_used": list(agents_used) if agents_used else ["unknown"],
                "status": status,
            },
        }

        try:
            response = await client.post(
                f"{self.mcp_url}/tools/call",
                json=payload,
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
        except Exception as e:
            print(f"[ERROR] Failed to sync to MCP: {e}")
        return False

    async def check_for_updates(self):
        """새로운 세션 또는 실행 업데이트 확인"""
        sessions = await self.get_sessions()

        # 최근 5개 세션만 체크 (성능 최적화)
        for session in sessions[:5]:
            session_id = session.get("id")
            if not session_id:
                continue

            runs_data = await self.get_session_runs(session_id)
            runs = runs_data.get("runs", [])

            for run in runs:
                run_id = run.get("id")
                status = run.get("status", "")
                run_key = f"{session_id}:{run_id}"

                # 새로운 완료된 실행만 처리
                if run_key not in self.seen_runs and status == "complete":
                    # 태스크 내용 추출
                    task = run.get("task", {})
                    task_msgs = task.get("content", [])
                    task_text = ""
                    for msg in task_msgs:
                        if msg.get("source") == "user":
                            task_text = msg.get("content", "")[:50]
                            break

                    print(f"[NEW RUN] Session {session_id}, Run {run_id}: {task_text}...")

                    success = await self.sync_to_mcp(session, run)
                    if success:
                        print(f"[SYNCED] Session {session_id} -> SharedMemory")
                    else:
                        print(f"[FAILED] Could not sync session {session_id}")

                    self.seen_runs.add(run_key)

    async def run(self):
        """메인 감시 루프"""
        print(f"[START] AutoGen Session Watcher")
        print(f"  AutoGen Studio: {self.autogen_url}")
        print(f"  MCP Server: {self.mcp_url}")
        print(f"  User ID: {self.user_id}")
        print(f"  Poll interval: {self.poll_interval}s")
        print()

        # 초기 실행: 기존 세션들을 seen으로 마킹 (중복 방지)
        print("[INIT] Loading existing sessions...")
        sessions = await self.get_sessions()
        for session in sessions[:10]:
            session_id = session.get("id")
            if session_id:
                runs_data = await self.get_session_runs(session_id)
                runs = runs_data.get("runs", [])
                for run in runs:
                    run_id = run.get("id")
                    if run_id:
                        self.seen_runs.add(f"{session_id}:{run_id}")
        print(f"[INIT] Loaded {len(self.seen_runs)} existing runs")
        print()
        print("[WATCHING] Waiting for new AutoGen Studio sessions...")
        print()

        try:
            while True:
                await self.check_for_updates()
                await asyncio.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n[STOP] Watcher stopped")
        finally:
            await self.close()


async def main():
    watcher = AutoGenSessionWatcher(
        autogen_url="http://localhost:8081",
        mcp_url="http://localhost:8102",
        poll_interval=2.0,
    )
    await watcher.run()


if __name__ == "__main__":
    asyncio.run(main())
