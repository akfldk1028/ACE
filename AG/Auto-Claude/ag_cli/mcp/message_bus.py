# AG-CLI Message Bus
# 에이전트 간 대화를 라우팅하고 UI에 실시간 표시
"""
Message Bus는 모든 에이전트 간 메시지가 통과하는 중앙 허브입니다.

주요 기능:
1. 에이전트 간 메시지 라우팅
2. 대화 로그 저장
3. WebSocket/Terminal로 실시간 브로드캐스트
4. 대화 이력 조회

사용법:
    # 서버 시작
    python message_bus.py

    # 에이전트에서 사용
    bus = MessageBusClient("ws://localhost:8100")
    await bus.connect("frontend_agent")
    await bus.send("backend_agent", "API 스펙 알려줘")
    response = await bus.receive()
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
import sys

# Rich 라이브러리 (터미널 UI용)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("[WARN] 'rich' library not installed. Install with: pip install rich")

# WebSocket 서버
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[WARN] 'websockets' library not installed. Install with: pip install websockets")

# FastAPI (REST API 엔드포인트)
try:
    from fastapi import FastAPI, WebSocket
    from fastapi.responses import HTMLResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DialogueEvent:
    """에이전트 간 대화 이벤트"""
    timestamp: str
    from_agent: str
    to_agent: str
    message: str
    event_type: str = "dialogue"  # dialogue, broadcast, system
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DialogueEvent":
        return cls(**data)


# 에이전트 아이콘 매핑
AGENT_ICONS = {
    "orchestrator": "🎯",
    "frontend": "🎨",
    "frontend_agent": "🎨",
    "backend": "🔧",
    "backend_agent": "🔧",
    "db": "💾",
    "db_agent": "💾",
    "test": "🧪",
    "test_agent": "🧪",
    "devops": "🚀",
    "devops_agent": "🚀",
    "system": "⚙️",
}


def get_agent_icon(agent_name: str) -> str:
    """에이전트 이름에 맞는 아이콘 반환"""
    return AGENT_ICONS.get(agent_name, "🤖")


class AgentMessageBus:
    """에이전트 간 메시지 라우팅 허브"""

    def __init__(self, log_path: Optional[str] = None):
        # 에이전트별 메시지 큐
        self.queues: Dict[str, asyncio.Queue] = {}
        # 연결된 에이전트 목록
        self.connected_agents: Set[str] = set()
        # WebSocket 연결 (UI용)
        self.ui_connections: Set[WebSocketServerProtocol] = set()
        # 대화 로그
        self.log: List[DialogueEvent] = []
        # 로그 저장 경로
        self.log_path = Path(log_path) if log_path else None
        # Rich console (터미널 UI)
        self.console = Console() if RICH_AVAILABLE else None
        # 실행 중 플래그
        self.running = False

    async def register_agent(self, agent_name: str):
        """에이전트 등록"""
        if agent_name not in self.queues:
            self.queues[agent_name] = asyncio.Queue()
            self.connected_agents.add(agent_name)
            logger.info(f"Agent registered: {agent_name}")
            await self._log_system(f"에이전트 등록: {agent_name}")

    async def unregister_agent(self, agent_name: str):
        """에이전트 등록 해제"""
        if agent_name in self.queues:
            del self.queues[agent_name]
            self.connected_agents.discard(agent_name)
            logger.info(f"Agent unregistered: {agent_name}")
            await self._log_system(f"에이전트 해제: {agent_name}")

    async def send(self, from_agent: str, to_agent: str, message: str, metadata: dict = None):
        """에이전트 간 메시지 전송"""
        event = DialogueEvent(
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            message=message,
            event_type="dialogue",
            metadata=metadata
        )

        # 1. 로그 저장
        self.log.append(event)
        if self.log_path:
            self._save_log()

        # 2. 터미널에 표시
        self._display_event(event)

        # 3. UI에 실시간 전송
        await self._broadcast_to_ui(event)

        # 4. 대상 에이전트에게 전달
        if to_agent in self.queues:
            await self.queues[to_agent].put(event)
        else:
            logger.warning(f"Target agent not found: {to_agent}")

    async def broadcast(self, from_agent: str, message: str, metadata: dict = None):
        """모든 에이전트에게 브로드캐스트"""
        event = DialogueEvent(
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent,
            to_agent="*all*",
            message=message,
            event_type="broadcast",
            metadata=metadata
        )

        self.log.append(event)
        self._display_event(event)
        await self._broadcast_to_ui(event)

        for agent_name in self.connected_agents:
            if agent_name != from_agent:
                await self.queues[agent_name].put(event)

    async def receive(self, agent_name: str, timeout: float = None) -> Optional[DialogueEvent]:
        """메시지 수신 (blocking)"""
        if agent_name not in self.queues:
            await self.register_agent(agent_name)

        try:
            if timeout:
                return await asyncio.wait_for(self.queues[agent_name].get(), timeout)
            else:
                return await self.queues[agent_name].get()
        except asyncio.TimeoutError:
            return None

    async def _log_system(self, message: str):
        """시스템 메시지 로깅"""
        event = DialogueEvent(
            timestamp=datetime.now().isoformat(),
            from_agent="system",
            to_agent="*log*",
            message=message,
            event_type="system"
        )
        self.log.append(event)
        self._display_event(event)
        await self._broadcast_to_ui(event)

    def _display_event(self, event: DialogueEvent):
        """터미널에 이벤트 표시"""
        if self.console and RICH_AVAILABLE:
            icon_from = get_agent_icon(event.from_agent)
            icon_to = get_agent_icon(event.to_agent)
            time_str = event.timestamp.split("T")[1].split(".")[0]

            if event.event_type == "system":
                self.console.print(f"[dim][{time_str}] ⚙️  {event.message}[/dim]")
            elif event.event_type == "broadcast":
                self.console.print(
                    f"[{time_str}] {icon_from} [bold cyan]{event.from_agent}[/bold cyan] → [bold magenta]*ALL*[/bold magenta]:\n"
                    f"    [italic]{event.message}[/italic]"
                )
            else:
                self.console.print(
                    f"[{time_str}] {icon_from} [bold cyan]{event.from_agent}[/bold cyan] → "
                    f"{icon_to} [bold green]{event.to_agent}[/bold green]:\n"
                    f"    {event.message}"
                )
        else:
            print(f"[{event.timestamp}] {event.from_agent} → {event.to_agent}: {event.message}")

    async def _broadcast_to_ui(self, event: DialogueEvent):
        """WebSocket으로 UI에 전송"""
        if not self.ui_connections:
            return

        message = json.dumps(event.to_dict())
        disconnected = set()

        for ws in self.ui_connections:
            try:
                await ws.send(message)
            except Exception:
                disconnected.add(ws)

        self.ui_connections -= disconnected

    def _save_log(self):
        """로그를 파일에 저장"""
        if self.log_path:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self.log], f, ensure_ascii=False, indent=2)

    def get_log(self, limit: int = 100) -> List[dict]:
        """로그 조회"""
        return [e.to_dict() for e in self.log[-limit:]]

    def get_conversation(self, agent1: str, agent2: str) -> List[dict]:
        """두 에이전트 간 대화 조회"""
        return [
            e.to_dict() for e in self.log
            if (e.from_agent == agent1 and e.to_agent == agent2) or
               (e.from_agent == agent2 and e.to_agent == agent1)
        ]


# === WebSocket 서버 ===

async def handle_websocket(websocket: WebSocketServerProtocol, bus: AgentMessageBus):
    """WebSocket 연결 처리"""
    try:
        # 첫 메시지로 에이전트 이름 수신
        init_msg = await websocket.recv()
        data = json.loads(init_msg)
        agent_name = data.get("agent_name", "unknown")

        await bus.register_agent(agent_name)
        logger.info(f"WebSocket connected: {agent_name}")

        # 양방향 통신
        async def receive_task():
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    await bus.send(
                        from_agent=agent_name,
                        to_agent=msg.get("to"),
                        message=msg.get("message"),
                        metadata=msg.get("metadata")
                    )
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {agent_name}")

        async def send_task():
            while True:
                event = await bus.receive(agent_name)
                if event:
                    await websocket.send(json.dumps(event.to_dict()))

        await asyncio.gather(receive_task(), send_task())

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket disconnected: {agent_name}")
        await bus.unregister_agent(agent_name)


async def start_websocket_server(bus: AgentMessageBus, host: str = "127.0.0.1", port: int = 8100):
    """WebSocket 서버 시작"""
    if not WEBSOCKETS_AVAILABLE:
        logger.error("websockets library not available")
        return

    async def handler(websocket):
        await handle_websocket(websocket, bus)

    logger.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # 영원히 실행


# === FastAPI REST API ===

def create_fastapi_app(bus: AgentMessageBus) -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(title="AG-CLI Message Bus")

    @app.get("/")
    async def root():
        return {
            "service": "AG-CLI Message Bus",
            "connected_agents": list(bus.connected_agents),
            "log_count": len(bus.log)
        }

    @app.get("/log")
    async def get_log(limit: int = 100):
        return bus.get_log(limit)

    @app.get("/conversation/{agent1}/{agent2}")
    async def get_conversation(agent1: str, agent2: str):
        return bus.get_conversation(agent1, agent2)

    @app.post("/send")
    async def send_message(from_agent: str, to_agent: str, message: str):
        await bus.send(from_agent, to_agent, message)
        return {"status": "sent"}

    @app.post("/broadcast")
    async def broadcast_message(from_agent: str, message: str):
        await bus.broadcast(from_agent, message)
        return {"status": "broadcast"}

    @app.websocket("/ws/{agent_name}")
    async def websocket_endpoint(websocket: WebSocket, agent_name: str):
        await websocket.accept()
        await bus.register_agent(agent_name)

        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                await bus.send(
                    from_agent=agent_name,
                    to_agent=msg.get("to"),
                    message=msg.get("message")
                )
        except Exception:
            await bus.unregister_agent(agent_name)

    @app.get("/viewer", response_class=HTMLResponse)
    async def viewer():
        """실시간 대화 뷰어 HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>AG-CLI Collaboration Viewer</title>
    <style>
        body { font-family: 'Consolas', monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }
        h1 { color: #569cd6; }
        #log { background: #252526; padding: 15px; border-radius: 5px; height: 80vh; overflow-y: auto; }
        .event { margin: 10px 0; padding: 10px; border-left: 3px solid #569cd6; }
        .event .time { color: #808080; font-size: 0.9em; }
        .event .from { color: #4ec9b0; font-weight: bold; }
        .event .to { color: #9cdcfe; font-weight: bold; }
        .event .message { margin-top: 5px; white-space: pre-wrap; }
        .event.system { border-left-color: #808080; opacity: 0.7; }
        .event.broadcast { border-left-color: #dcdcaa; }
        .status { position: fixed; top: 10px; right: 10px; background: #252526; padding: 10px; border-radius: 5px; }
        .status .online { color: #4ec9b0; }
    </style>
</head>
<body>
    <div class="status">
        <div>Agents: <span id="agents" class="online">-</span></div>
        <div>Messages: <span id="count">0</span></div>
    </div>
    <h1>AG-CLI Collaboration Viewer</h1>
    <div id="log"></div>
    <script>
        const icons = {
            orchestrator: "🎯", frontend: "🎨", frontend_agent: "🎨",
            backend: "🔧", backend_agent: "🔧", db: "💾", db_agent: "💾",
            test: "🧪", test_agent: "🧪", devops: "🚀", system: "⚙️"
        };
        const getIcon = (name) => icons[name] || "🤖";

        const log = document.getElementById("log");
        const agentsEl = document.getElementById("agents");
        const countEl = document.getElementById("count");
        let count = 0;

        const ws = new WebSocket(`ws://${location.host}/ws/viewer`);
        ws.onmessage = (e) => {
            const event = JSON.parse(e.data);
            const div = document.createElement("div");
            div.className = `event ${event.event_type}`;
            const time = event.timestamp.split("T")[1].split(".")[0];
            div.innerHTML = `
                <span class="time">[${time}]</span>
                ${getIcon(event.from_agent)} <span class="from">${event.from_agent}</span> →
                ${getIcon(event.to_agent)} <span class="to">${event.to_agent}</span>
                <div class="message">${event.message}</div>
            `;
            log.appendChild(div);
            log.scrollTop = log.scrollHeight;
            countEl.textContent = ++count;
        };

        // 주기적으로 에이전트 상태 갱신
        setInterval(async () => {
            const res = await fetch("/");
            const data = await res.json();
            agentsEl.textContent = data.connected_agents.join(", ") || "none";
        }, 5000);
    </script>
</body>
</html>
"""

    return app


# === 메인 ===

async def main():
    """Message Bus 서버 시작"""
    print("=" * 60)
    print("AG-CLI Message Bus")
    print("=" * 60)

    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    bus = AgentMessageBus(log_path=str(log_file))

    if FASTAPI_AVAILABLE:
        app = create_fastapi_app(bus)
        config = uvicorn.Config(app, host="127.0.0.1", port=8100, log_level="info")
        server = uvicorn.Server(config)

        print(f"REST API: http://127.0.0.1:8100")
        print(f"WebSocket: ws://127.0.0.1:8100/ws/{{agent_name}}")
        print(f"Viewer: http://127.0.0.1:8100/viewer")
        print(f"Log file: {log_file}")
        print("=" * 60)

        await server.serve()
    elif WEBSOCKETS_AVAILABLE:
        print(f"WebSocket: ws://127.0.0.1:8100")
        print(f"Log file: {log_file}")
        print("=" * 60)
        await start_websocket_server(bus)
    else:
        print("ERROR: Either 'websockets' or 'fastapi' library is required")
        print("Install with: pip install websockets fastapi uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
