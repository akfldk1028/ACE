"""
SharedMemory MCP Server for AutoGen Studio

AutoGen Studio에서 SharedMemory(8101)에 접근할 수 있도록 하는 MCP 서버.
이를 통해 AutoGen Studio 실행 결과가 Auto-Claude UI에 자동 전달됨.

실행: python -m src.mcp.shared_memory_mcp_server
또는: npx를 통해 AutoGen Studio에 등록

Architecture:
    AutoGen Studio → MCP Server (이 파일) → SharedMemory(8101) → Auto-Claude UI
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx


# MCP Protocol Implementation
class MCPServer:
    """Minimal MCP Server implementation for STDIO transport"""

    def __init__(self):
        self.shared_memory_url = "http://localhost:8101"
        self.source_name = "autogen-studio"
        self.http_client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()

    # === Tool Implementations ===

    async def store_result(self, key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """AutoGen Studio 실행 결과를 SharedMemory에 저장"""
        client = await self.get_client()

        # SharedMemory API format: POST /decision
        # Request: {"category": str, "decision": Any, "agent": str}
        payload = {
            "category": f"autogen_{key}",
            "decision": {
                "data": data,
                "timestamp": datetime.now().isoformat(),
            },
            "agent": self.source_name,
        }

        try:
            response = await client.post(
                f"{self.shared_memory_url}/decision",  # Fixed: /decisions -> /decision
                json=payload,
            )
            response.raise_for_status()

            # Auto-Claude 알림 이벤트 발행
            await self.publish_event("autogen_result_stored", {
                "key": key,
                "source": self.source_name,
                "timestamp": payload["timestamp"],
            })

            return {"success": True, "key": f"autogen_{key}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def publish_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """SharedMemory에 이벤트 발행 (Auto-Claude가 구독)"""
        client = await self.get_client()

        # SharedMemory API format: POST /event
        # Request: {"event_type": str, "data": dict, "source": str}
        payload = {
            "event_type": event_type,
            "data": {
                **data,
                "timestamp": datetime.now().isoformat(),
            },
            "source": self.source_name,
        }

        try:
            response = await client.post(
                f"{self.shared_memory_url}/event",  # Fixed: /events -> /event
                json=payload,
            )
            response.raise_for_status()
            return {"success": True, "event_type": event_type}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def notify_auto_claude(self, message: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Auto-Claude UI에 직접 알림 전송"""
        notification = {
            "type": "autogen_notification",
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "source": self.source_name,
        }

        # 알림 저장
        result = await self.store_result("latest_notification", notification)

        # 이벤트 발행
        await self.publish_event("autogen_notification", notification)

        return result

    async def sync_workflow_result(
        self,
        workflow_name: str,
        task: str,
        result: str,
        agents_used: List[str],
        status: str = "completed",
    ) -> Dict[str, Any]:
        """AutoGen Studio 워크플로우 실행 결과를 동기화"""
        workflow_data = {
            "workflow_name": workflow_name,
            "task": task,
            "result": result,
            "agents_used": agents_used,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        # 워크플로우 결과 저장
        await self.store_result(f"workflow_{workflow_name}", workflow_data)

        # latest_workflow 업데이트 (Auto-Claude가 폴링)
        await self.store_result("latest_workflow", workflow_data)

        # 이벤트 발행
        await self.publish_event("autogen_workflow_completed", workflow_data)

        return {"success": True, "workflow": workflow_name, "status": status}

    # === MCP Protocol Handlers ===

    def get_tools(self) -> List[Dict[str, Any]]:
        """MCP 도구 목록 반환"""
        return [
            {
                "name": "store_result",
                "description": "AutoGen Studio 실행 결과를 SharedMemory에 저장하여 Auto-Claude와 공유",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "결과 식별 키"},
                        "data": {"type": "object", "description": "저장할 데이터"},
                    },
                    "required": ["key", "data"],
                },
            },
            {
                "name": "notify_auto_claude",
                "description": "Auto-Claude UI에 알림 메시지 전송",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "알림 메시지"},
                        "data": {"type": "object", "description": "추가 데이터 (선택)"},
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "sync_workflow_result",
                "description": "워크플로우 실행 결과를 Auto-Claude와 동기화",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {"type": "string", "description": "워크플로우 이름"},
                        "task": {"type": "string", "description": "실행한 태스크"},
                        "result": {"type": "string", "description": "실행 결과"},
                        "agents_used": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "사용된 에이전트 목록",
                        },
                        "status": {"type": "string", "description": "상태 (completed/failed)"},
                    },
                    "required": ["workflow_name", "task", "result", "agents_used"],
                },
            },
            {
                "name": "publish_event",
                "description": "SharedMemory에 커스텀 이벤트 발행",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string", "description": "이벤트 타입"},
                        "data": {"type": "object", "description": "이벤트 데이터"},
                    },
                    "required": ["event_type", "data"],
                },
            },
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """MCP 도구 호출"""
        if name == "store_result":
            return await self.store_result(arguments["key"], arguments["data"])
        elif name == "notify_auto_claude":
            return await self.notify_auto_claude(
                arguments["message"],
                arguments.get("data"),
            )
        elif name == "sync_workflow_result":
            return await self.sync_workflow_result(
                workflow_name=arguments["workflow_name"],
                task=arguments["task"],
                result=arguments["result"],
                agents_used=arguments["agents_used"],
                status=arguments.get("status", "completed"),
            )
        elif name == "publish_event":
            return await self.publish_event(
                arguments["event_type"],
                arguments["data"],
            )
        else:
            return {"error": f"Unknown tool: {name}"}

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 메시지 처리"""
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": "shared-memory-mcp",
                        "version": "1.0.0",
                    },
                },
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": self.get_tools()},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await self.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                },
            }

        elif method == "notifications/initialized":
            return None  # No response for notifications

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }


async def run_stdio_server():
    """STDIO 기반 MCP 서버 실행"""
    server = MCPServer()

    # Read from stdin, write to stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

    try:
        while True:
            # Read content-length header
            header = await reader.readline()
            if not header:
                break

            if header.startswith(b"Content-Length:"):
                content_length = int(header.decode().split(":")[1].strip())
                await reader.readline()  # Empty line

                # Read content
                content = await reader.read(content_length)
                message = json.loads(content.decode())

                # Handle message
                response = await server.handle_message(message)

                if response:
                    response_bytes = json.dumps(response).encode()
                    writer.write(f"Content-Length: {len(response_bytes)}\r\n\r\n".encode())
                    writer.write(response_bytes)
                    await writer.drain()

    finally:
        await server.close()


# === HTTP Server (Alternative) ===

async def run_http_server(host: str = "localhost", port: int = 8102):
    """HTTP 기반 MCP 서버 실행 (SSE 지원)"""
    from aiohttp import web

    server = MCPServer()

    async def handle_tools_list(request):
        return web.json_response({"tools": server.get_tools()})

    async def handle_tools_call(request):
        data = await request.json()
        result = await server.call_tool(data["name"], data.get("arguments", {}))
        return web.json_response(result)

    async def handle_health(request):
        return web.json_response({"status": "ok", "server": "shared-memory-mcp"})

    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_get("/tools", handle_tools_list)
    app.router.add_post("/tools/call", handle_tools_call)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)

    print(f"SharedMemory MCP Server running at http://{host}:{port}")
    print("Tools: store_result, notify_auto_claude, sync_workflow_result, publish_event")

    await site.start()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()
        await server.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SharedMemory MCP Server")
    parser.add_argument("--mode", choices=["stdio", "http"], default="http")
    parser.add_argument("--port", type=int, default=8102)
    args = parser.parse_args()

    if args.mode == "stdio":
        asyncio.run(run_stdio_server())
    else:
        asyncio.run(run_http_server(port=args.port))
