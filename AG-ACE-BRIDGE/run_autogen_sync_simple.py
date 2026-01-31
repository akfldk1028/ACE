"""
AutoGen Studio -> SharedMemory 직접 동기화 (단순화 버전)

MCP Server 없이 직접 SharedMemory(8101)에 저장.
Auto-Claude UI에서 autogen_* 키로 결과 조회 가능.

Usage:
    python run_autogen_sync_simple.py
"""

import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, Set


class AutoGenToSharedMemory:
    """AutoGen Studio 결과를 SharedMemory에 직접 저장"""

    def __init__(
        self,
        autogen_url: str = "http://localhost:8081",
        shared_memory_url: str = "http://localhost:8101",
        poll_interval: float = 2.0,
        user_id: str = "guestuser@gmail.com",
    ):
        self.autogen_url = autogen_url
        self.shared_memory_url = shared_memory_url
        self.poll_interval = poll_interval
        self.user_id = user_id
        self.seen_runs: Set[str] = set()
        self.http_client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        return self.http_client

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()

    # =========================================================================
    # SharedMemory Direct API (MCP 없이 직접 호출)
    # =========================================================================

    async def store_to_shared_memory(self, key: str, data: Dict[str, Any]) -> bool:
        """SharedMemory에 직접 저장"""
        client = await self.get_client()
        payload = {
            "category": key,
            "decision": data,
            "agent": "autogen-studio",
        }
        try:
            response = await client.post(
                f"{self.shared_memory_url}/decision",
                json=payload,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] SharedMemory store failed: {e}", flush=True)
            return False

    async def publish_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """SharedMemory에 이벤트 발행"""
        client = await self.get_client()
        payload = {
            "event_type": event_type,
            "data": data,
            "source": "autogen-studio",
        }
        try:
            response = await client.post(
                f"{self.shared_memory_url}/event",
                json=payload,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Event publish failed: {e}", flush=True)
            return False

    # =========================================================================
    # AutoGen Studio API
    # =========================================================================

    async def get_sessions(self) -> list:
        client = await self.get_client()
        try:
            response = await client.get(
                f"{self.autogen_url}/api/sessions/",
                params={"user_id": self.user_id}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            print(f"[ERROR] Get sessions failed: {e}", flush=True)
        return []

    async def get_session_runs(self, session_id: int) -> dict:
        client = await self.get_client()
        try:
            response = await client.get(
                f"{self.autogen_url}/api/sessions/{session_id}/runs/",
                params={"user_id": self.user_id}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
        except Exception as e:
            print(f"[ERROR] Get runs failed: {e}", flush=True)
        return {}

    # =========================================================================
    # Sync Logic
    # =========================================================================

    async def sync_run_to_shared_memory(self, session: dict, run_data: dict) -> bool:
        """실행 결과를 SharedMemory에 저장"""

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
                content = msg.get("content", "")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content = item.get("text", "")
                            break
                        elif isinstance(item, str):
                            content = item
                            break
                if content and isinstance(content, str) and not content.startswith("{"):
                    result_content = content

        if not result_content:
            return False

        # 500자 제한
        if len(result_content) > 500:
            result_content = result_content[:500] + "..."

        # 데이터 구성
        workflow_data = {
            "workflow_name": f"session_{session.get('id', 'unknown')}",
            "task": task_content or "Unknown task",
            "result": result_content,
            "agents_used": list(agents_used) if agents_used else ["unknown"],
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "source": "autogen-studio",
        }

        # SharedMemory에 저장 (2개 키)
        session_key = f"autogen_session_{session.get('id')}"
        await self.store_to_shared_memory(session_key, workflow_data)
        await self.store_to_shared_memory("autogen_latest", workflow_data)

        # 이벤트 발행
        await self.publish_event("autogen_workflow_completed", workflow_data)

        return True

    async def check_for_updates(self):
        """새 실행 확인"""
        sessions = await self.get_sessions()

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

                if run_key not in self.seen_runs and status == "complete":
                    task = run.get("task", {})
                    task_msgs = task.get("content", [])
                    task_text = ""
                    for msg in task_msgs:
                        if msg.get("source") == "user":
                            task_text = msg.get("content", "")[:50]
                            break

                    print(f"[NEW] Session {session_id}: {task_text}...", flush=True)

                    success = await self.sync_run_to_shared_memory(session, run)
                    if success:
                        print(f"[OK] -> SharedMemory (autogen_session_{session_id})", flush=True)

                    self.seen_runs.add(run_key)

    async def run(self):
        """메인 루프"""
        print("=" * 50, flush=True)
        print("AutoGen Studio -> SharedMemory (Direct)", flush=True)
        print("=" * 50, flush=True)
        print(f"AutoGen: {self.autogen_url}", flush=True)
        print(f"SharedMemory: {self.shared_memory_url}", flush=True)
        print(flush=True)

        # 기존 세션 로드
        print("[INIT] Loading existing sessions...", flush=True)
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
        print(f"[INIT] Loaded {len(self.seen_runs)} runs", flush=True)
        print(flush=True)
        print("[WATCHING] Waiting for new AutoGen sessions...", flush=True)
        print(flush=True)

        try:
            while True:
                await self.check_for_updates()
                await asyncio.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n[STOP]", flush=True)
        finally:
            await self.close()


async def main():
    sync = AutoGenToSharedMemory()
    await sync.run()


if __name__ == "__main__":
    asyncio.run(main())
