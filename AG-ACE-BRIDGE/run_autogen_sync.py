"""
AutoGen Studio <-> SharedMemory Sync Runner

이 스크립트는 두 가지를 실행합니다:
1. SharedMemory MCP Server (8102) - AutoGen Studio 결과를 SharedMemory에 저장
2. AutoGen Session Watcher - AutoGen Studio 세션 완료를 감지하고 MCP 서버로 전송

사용법:
    python run_autogen_sync.py

Architecture:
    AutoGen Studio (8081)
           |
           | (Session Watcher가 polling)
           v
    MCP Server (8102)
           |
           | (SharedMemory API 호출)
           v
    SharedMemory (8101)
           |
           | (Auto-Claude UI가 polling/subscribe)
           v
    Auto-Claude UI
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp.shared_memory_mcp_server import run_http_server
from src.watcher.autogen_session_watcher import AutoGenSessionWatcher


async def run_session_watcher():
    """세션 워처 실행"""
    watcher = AutoGenSessionWatcher(
        autogen_url="http://localhost:8081",
        mcp_url="http://localhost:8102",
        poll_interval=2.0,
    )
    await watcher.run()


async def main():
    print("=" * 60)
    print("AutoGen Studio <-> SharedMemory Sync")
    print("=" * 60)
    print()
    print("Components:")
    print("  [1] MCP Server (8102) - Receives results, stores to SharedMemory")
    print("  [2] Session Watcher   - Monitors AutoGen Studio, sends to MCP")
    print()
    print("Flow:")
    print("  AutoGen Studio (8081)")
    print("         |")
    print("         v")
    print("  Session Watcher (polling)")
    print("         |")
    print("         v")
    print("  MCP Server (8102)")
    print("         |")
    print("         v")
    print("  SharedMemory (8101)")
    print("         |")
    print("         v")
    print("  Auto-Claude UI")
    print()
    print("=" * 60)
    print()

    # 두 서비스를 병렬 실행
    await asyncio.gather(
        run_http_server(port=8102),
        run_session_watcher(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
