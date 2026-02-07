# AG-CLI Base Collaborative Agent
# 대화 기능이 포함된 에이전트 베이스 클래스
"""
CollaborativeAgent는 다른 에이전트와 대화하고 협업할 수 있는 에이전트입니다.

주요 기능:
1. 다른 에이전트에게 메시지 전송 (say, ask)
2. 메시지 수신 대기 (listen)
3. SharedMemory 연동 (정보 공유, 락)
4. Claude CLI 실행 (실제 코드 작성)

사용법:
    agent = CollaborativeAgent(
        name="frontend_agent",
        folder="frontend",
        expertise="React/TypeScript",
        bus_url="ws://localhost:8100",
        memory_url="http://localhost:8101"
    )
    await agent.connect()
    await agent.say("작업 시작합니다!", to="orchestrator")
    response = await agent.ask("API 스펙 알려줘", to="backend_agent")
    await agent.work("Button 컴포넌트 만들어줘")
"""
import asyncio
import json
import logging
import subprocess
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys

# HTTP 클라이언트
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("[WARN] 'httpx' library not installed. Install with: pip install httpx")

# WebSocket 클라이언트
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[WARN] 'websockets' library not installed. Install with: pip install websockets")

# .env 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DialogueEvent:
    """대화 이벤트"""
    timestamp: str
    from_agent: str
    to_agent: str
    message: str
    event_type: str = "dialogue"
    metadata: Optional[dict] = None


class MessageBusClient:
    """Message Bus 클라이언트"""

    def __init__(self, url: str = "ws://127.0.0.1:8100"):
        self.url = url
        self.agent_name: Optional[str] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.receive_queue: asyncio.Queue = asyncio.Queue()
        self._receive_task: Optional[asyncio.Task] = None

    async def connect(self, agent_name: str):
        """Message Bus에 연결"""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets library not available")
            return False

        self.agent_name = agent_name
        try:
            self.ws = await websockets.connect(f"{self.url}/ws/{agent_name}")
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info(f"Connected to Message Bus as {agent_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Message Bus: {e}")
            return False

    async def disconnect(self):
        """연결 해제"""
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws:
            await self.ws.close()

    async def send(self, to_agent: str, message: str, metadata: dict = None):
        """메시지 전송"""
        if not self.ws:
            logger.error("Not connected to Message Bus")
            return

        data = {
            "to": to_agent,
            "message": message,
            "metadata": metadata or {}
        }
        await self.ws.send(json.dumps(data))

    async def receive(self, timeout: float = None) -> Optional[DialogueEvent]:
        """메시지 수신"""
        try:
            if timeout:
                data = await asyncio.wait_for(self.receive_queue.get(), timeout)
            else:
                data = await self.receive_queue.get()
            return DialogueEvent(**data)
        except asyncio.TimeoutError:
            return None

    async def _receive_loop(self):
        """메시지 수신 루프"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self.receive_queue.put(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Message Bus connection closed")


class SharedMemoryClient:
    """SharedMemory 클라이언트"""

    def __init__(self, url: str = "http://127.0.0.1:8101"):
        self.url = url
        self.agent_name: Optional[str] = None

    def set_agent(self, agent_name: str):
        """에이전트 이름 설정"""
        self.agent_name = agent_name

    async def store_decision(self, category: str, decision: Any) -> dict:
        """결정 저장"""
        if not HTTPX_AVAILABLE:
            logger.error("httpx library not available")
            return {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/decision",
                json={
                    "category": category,
                    "decision": decision,
                    "agent": self.agent_name or "unknown"
                }
            )
            return response.json()

    async def get_decision(self, category: str) -> Optional[Any]:
        """결정 조회"""
        if not HTTPX_AVAILABLE:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/decision/{category}")
            if response.status_code == 200:
                return response.json()
            return None

    async def get_api_spec(self) -> List[dict]:
        """API 스펙 조회"""
        if not HTTPX_AVAILABLE:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/api-spec")
            return response.json() if response.status_code == 200 else []

    async def get_schema(self) -> Dict[str, dict]:
        """DB 스키마 조회"""
        if not HTTPX_AVAILABLE:
            return {}

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/schema")
            return response.json() if response.status_code == 200 else {}

    async def publish_event(self, event_type: str, data: dict) -> dict:
        """이벤트 발행"""
        if not HTTPX_AVAILABLE:
            return {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/event",
                json={
                    "event_type": event_type,
                    "data": data,
                    "source": self.agent_name or "unknown"
                }
            )
            return response.json()

    async def acquire_lock(self, file_path: str, timeout: int = 300) -> bool:
        """파일 락 획득"""
        if not HTTPX_AVAILABLE:
            return False

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/lock/acquire",
                json={
                    "file_path": file_path,
                    "agent": self.agent_name or "unknown",
                    "timeout_seconds": timeout
                }
            )
            return response.status_code == 200

    async def release_lock(self, file_path: str) -> bool:
        """파일 락 해제"""
        if not HTTPX_AVAILABLE:
            return False

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/lock/release",
                json={
                    "file_path": file_path,
                    "agent": self.agent_name or "unknown"
                }
            )
            return response.status_code == 200


class CollaborativeAgent:
    """대화 기능이 포함된 협업 에이전트"""

    def __init__(
        self,
        name: str,
        folder: str,
        expertise: str,
        project_root: Optional[str] = None,
        bus_url: str = "ws://127.0.0.1:8100",
        memory_url: str = "http://127.0.0.1:8101"
    ):
        """
        Args:
            name: 에이전트 이름 (frontend_agent, backend_agent 등)
            folder: 담당 폴더 (frontend, backend, db 등)
            expertise: 전문 분야 (React/TypeScript, FastAPI/Python 등)
            project_root: 프로젝트 루트 경로
            bus_url: Message Bus URL
            memory_url: SharedMemory URL
        """
        self.name = name
        self.folder = folder
        self.expertise = expertise

        # 프로젝트 경로
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).parent.parent.parent / "project"
        self.work_dir = self.project_root / folder
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 클라이언트
        self.bus = MessageBusClient(bus_url)
        self.memory = SharedMemoryClient(memory_url)

        # 상태
        self.connected = False

    async def connect(self):
        """Message Bus와 SharedMemory에 연결"""
        self.memory.set_agent(self.name)

        if await self.bus.connect(self.name):
            self.connected = True
            logger.info(f"{self.name} connected")
            return True
        return False

    async def disconnect(self):
        """연결 해제"""
        await self.bus.disconnect()
        self.connected = False

    # === 대화 기능 ===

    async def say(self, message: str, to: str = "orchestrator"):
        """다른 에이전트에게 말하기

        Args:
            message: 전달할 메시지
            to: 대상 에이전트 (기본: orchestrator)
        """
        if not self.connected:
            logger.warning(f"{self.name} not connected")
            return

        await self.bus.send(to, message)
        logger.info(f"{self.name} → {to}: {message[:50]}...")

    async def ask(self, question: str, to: str, timeout: float = 60.0) -> Optional[str]:
        """다른 에이전트에게 질문하고 답변 대기

        Args:
            question: 질문
            to: 대상 에이전트
            timeout: 대기 시간 (초)

        Returns:
            답변 메시지 또는 None
        """
        await self.say(question, to)

        response = await self.bus.receive(timeout)
        if response:
            logger.info(f"{self.name} ← {response.from_agent}: {response.message[:50]}...")
            return response.message
        return None

    async def listen(self, timeout: float = None) -> Optional[DialogueEvent]:
        """메시지 수신 대기

        Args:
            timeout: 대기 시간 (초, None이면 무한 대기)

        Returns:
            수신된 대화 이벤트
        """
        return await self.bus.receive(timeout)

    async def broadcast(self, message: str):
        """모든 에이전트에게 브로드캐스트

        Args:
            message: 브로드캐스트할 메시지
        """
        await self.say(message, to="*all*")

    # === SharedMemory 연동 ===

    async def share(self, category: str, data: Any):
        """SharedMemory에 정보 공유

        Args:
            category: 카테고리 (api_spec, schema, types 등)
            data: 공유할 데이터
        """
        await self.memory.store_decision(category, data)
        logger.info(f"{self.name} shared {category}")

    async def fetch(self, category: str) -> Optional[Any]:
        """SharedMemory에서 정보 조회

        Args:
            category: 카테고리

        Returns:
            저장된 데이터
        """
        return await self.memory.get_decision(category)

    async def get_api_spec(self) -> List[dict]:
        """API 스펙 조회"""
        return await self.memory.get_api_spec()

    async def get_schema(self) -> Dict[str, dict]:
        """DB 스키마 조회"""
        return await self.memory.get_schema()

    async def publish_event(self, event_type: str, data: dict = None):
        """이벤트 발행

        Args:
            event_type: 이벤트 유형 (task_completed, error 등)
            data: 이벤트 데이터
        """
        await self.memory.publish_event(event_type, data or {})

    # === 파일 락 ===

    async def lock_file(self, file_path: str) -> bool:
        """파일 락 획득

        Args:
            file_path: 락을 걸 파일 경로 (work_dir 기준 상대경로)

        Returns:
            성공 여부
        """
        full_path = str(self.work_dir / file_path)
        return await self.memory.acquire_lock(full_path)

    async def unlock_file(self, file_path: str) -> bool:
        """파일 락 해제

        Args:
            file_path: 락을 해제할 파일 경로

        Returns:
            성공 여부
        """
        full_path = str(self.work_dir / file_path)
        return await self.memory.release_lock(full_path)

    # === Claude CLI 실행 ===

    async def work(self, task: str, context: dict = None) -> dict:
        """Claude CLI로 실제 작업 수행

        Args:
            task: 수행할 작업 설명
            context: 추가 컨텍스트 (API 스펙, 스키마 등)

        Returns:
            작업 결과
        """
        # 1. 작업 시작 알림
        await self.say(f"작업 시작: {task[:50]}...")

        # 2. Claude CLI 실행
        result = await self._execute_claude_cli(task, context)

        # 3. 결과에 따라 알림
        if result.get("success"):
            await self.say(f"작업 완료! {result.get('summary', '')}")
            await self.publish_event("task_completed", {
                "task": task[:100],
                "result": result.get("summary", "")
            })
        else:
            await self.say(f"작업 실패: {result.get('error', 'Unknown error')}")
            await self.publish_event("task_failed", {
                "task": task[:100],
                "error": result.get("error", "")
            })

        return result

    async def _execute_claude_cli(self, task: str, context: dict = None) -> dict:
        """Claude CLI subprocess 실행

        Args:
            task: 작업 설명
            context: 추가 컨텍스트

        Returns:
            실행 결과
        """
        # 시스템 프롬프트 구성
        system_prompt = f"""You are a {self.expertise} expert.

WORKSPACE RULES:
1. You can ONLY modify files in the current directory ({self.folder}/)
2. Do NOT modify files outside this folder
3. Follow best practices for {self.expertise}

CODING STANDARDS:
- Write clean, readable code
- Include proper type annotations
- Add comments for complex logic
- Handle errors gracefully
"""

        if context:
            system_prompt += f"\n\nCONTEXT:\n{json.dumps(context, indent=2)}"

        # Claude CLI 명령 구성
        cmd = [
            "claude", "-p", task,
            "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash",
            "--output-format", "json",
            "--append-system-prompt", system_prompt
        ]

        try:
            logger.info(f"Executing Claude CLI in {self.work_dir}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.work_dir),
                timeout=300,  # 5분 타임아웃
                env={**os.environ}
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Claude CLI error: {error_msg[:200]}")
                return {
                    "success": False,
                    "error": error_msg[:500],
                    "return_code": result.returncode
                }

            # JSON 파싱
            try:
                output = json.loads(result.stdout)
                return {
                    "success": True,
                    "result": output.get("result", ""),
                    "summary": output.get("result", "")[:200],
                    "session_id": output.get("session_id"),
                    "usage": output.get("usage", {})
                }
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트로 반환
                return {
                    "success": True,
                    "result": result.stdout[:2000],
                    "summary": result.stdout[:200]
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "타임아웃: 5분 초과"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Claude CLI가 설치되지 않았습니다. npm install -g @anthropic-ai/claude-code"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # === 협업 패턴 ===

    async def collaborate_on_task(self, task: str, dependencies: List[str] = None) -> dict:
        """의존성을 고려한 협업 작업

        Args:
            task: 수행할 작업
            dependencies: 필요한 정보 목록 (api_spec, schema 등)

        Returns:
            작업 결과
        """
        context = {}

        # 의존성 정보 수집
        if dependencies:
            for dep in dependencies:
                if dep == "api_spec":
                    context["api_spec"] = await self.get_api_spec()
                elif dep == "schema":
                    context["schema"] = await self.get_schema()
                else:
                    data = await self.fetch(dep)
                    if data:
                        context[dep] = data

        # 작업 수행
        return await self.work(task, context if context else None)


# === A2A 통합 ===

def create_a2a_agent(collaborative_agent: CollaborativeAgent):
    """CollaborativeAgent를 A2A 에이전트로 래핑

    Args:
        collaborative_agent: CollaborativeAgent 인스턴스

    Returns:
        Google ADK Agent
    """
    try:
        from google.adk.agents import Agent
        from google.adk.tools import FunctionTool
        from google.adk.models.lite_llm import LiteLlm
    except ImportError:
        logger.error("google-adk not installed")
        return None

    # 도구 함수들
    def execute_task(task: str, context: str = None) -> dict:
        """작업 수행"""
        ctx = json.loads(context) if context else None
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            collaborative_agent.work(task, ctx)
        )

    def ask_agent(question: str, to_agent: str) -> str:
        """다른 에이전트에게 질문"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            collaborative_agent.ask(question, to_agent)
        )

    def get_shared_info(category: str) -> dict:
        """SharedMemory에서 정보 조회"""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            collaborative_agent.fetch(category)
        )
        return result or {}

    def share_info(category: str, data: str) -> dict:
        """SharedMemory에 정보 공유"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            collaborative_agent.share(category, json.loads(data))
        )

    # A2A 에이전트 생성
    agent = Agent(
        model=LiteLlm(model="openai/gpt-4o-mini"),
        name=collaborative_agent.name,
        description=f"{collaborative_agent.expertise} 전문가. "
                    f"{collaborative_agent.folder}/ 폴더의 코드를 작성합니다.",
        instruction=f"""당신은 {collaborative_agent.expertise} 전문 에이전트입니다.

담당 폴더: {collaborative_agent.folder}/
전문 분야: {collaborative_agent.expertise}

주요 기능:
1. execute_task - Claude CLI로 코드 작성
2. ask_agent - 다른 에이전트에게 질문
3. get_shared_info - SharedMemory에서 정보 조회
4. share_info - SharedMemory에 정보 공유

협업 규칙:
- 다른 에이전트의 폴더는 수정하지 않습니다
- 필요한 정보는 SharedMemory를 통해 공유합니다
- 작업 완료 시 관련 에이전트에게 알립니다

한국어로 응답해주세요.""",
        tools=[
            FunctionTool(execute_task),
            FunctionTool(ask_agent),
            FunctionTool(get_shared_info),
            FunctionTool(share_info),
        ]
    )

    return agent


# === 테스트 ===

async def test_agent():
    """에이전트 테스트"""
    agent = CollaborativeAgent(
        name="test_agent",
        folder="test",
        expertise="Testing"
    )

    # 연결 (서버가 실행 중이어야 함)
    if await agent.connect():
        await agent.say("테스트 시작!")
        await asyncio.sleep(2)
        await agent.disconnect()
    else:
        print("서버에 연결할 수 없습니다. Message Bus를 먼저 실행하세요.")


if __name__ == "__main__":
    asyncio.run(test_agent())
