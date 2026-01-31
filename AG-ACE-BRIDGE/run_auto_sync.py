"""
AutoGen Studio ↔ Auto-Claude 자동 연동 스크립트

실행 방법: python run_auto_sync.py

이 스크립트가 백그라운드에서 실행되면:
1. AutoGen Studio 패턴/워크플로우 폴더 감시
2. 변경 감지 시 SharedMemory에 이벤트 발행
3. Auto-Claude UI가 이벤트 수신하여 반영
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# AG-ACE-BRIDGE 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.watcher import PatternWatcher, PatternEvent
from src.memory.shared_memory_client import SharedMemoryClient


class AutoSyncBridge:
    """AutoGen Studio ↔ Auto-Claude 자동 동기화"""

    def __init__(self):
        self.memory_client = SharedMemoryClient(
            base_url="http://localhost:8101",
            source_name="auto-sync-bridge",
        )

        # AutoGen Studio 폴더 감시
        autogen_home = os.path.expanduser("~/.autogenstudio")
        self.watcher = PatternWatcher(
            watch_paths=[
                os.path.join(autogen_home, "patterns"),
                os.path.join(autogen_home, "workflows"),
                str(Path(__file__).parent / "patterns"),  # 로컬 patterns
            ],
            on_pattern_detected=self.on_pattern_detected,
        )

        self.running = False

    async def on_pattern_detected(self, event: PatternEvent):
        """패턴 감지 시 콜백"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [PATTERN DETECTED]")
        print(f"  Type: {event.event_type.value}")
        print(f"  Name: {event.pattern_name}")
        print(f"  File: {event.file_path}")

        # SharedMemory에 이벤트 발행
        try:
            await self.memory_client.publish_event(
                event_type=f"pattern_{event.event_type.value}",
                data={
                    "pattern_name": event.pattern_name,
                    "pattern_data": event.pattern_data,
                    "file_path": event.file_path,
                    "timestamp": event.timestamp.isoformat(),
                    "source": "autogen_studio",
                },
            )
            print(f"  [OK] SharedMemory event published")

            # Auto-Claude UI 알림용 특별 키 저장
            await self.memory_client.store(
                key="latest_autogen_pattern",
                data={
                    "pattern_name": event.pattern_name,
                    "event_type": event.event_type.value,
                    "timestamp": datetime.now().isoformat(),
                    "pattern_data": event.pattern_data,
                },
            )
            print(f"  [OK] Auto-Claude notification saved")

        except Exception as e:
            print(f"  [ERROR] SharedMemory connection failed: {e}")
            print(f"     Check if SharedMemory server(8101) is running")

    async def start(self):
        """동기화 시작"""
        print("=" * 60)
        print("[AUTO-SYNC] AutoGen Studio <-> Auto-Claude Started")
        print("=" * 60)
        print()
        print("Watching folders:")
        for path in self.watcher.watch_paths:
            exists = "[OK]" if os.path.exists(path) else "[X]"
            print(f"  {exists} {path}")
        print()
        print("Waiting for changes... (Ctrl+C to stop)")
        print("-" * 60)

        self.running = True

        # 기존 패턴 스캔
        existing = await self.watcher.scan_existing()
        if existing:
            print(f"\n[SCAN] Found {len(existing)} existing patterns:")
            for e in existing[:5]:  # 처음 5개만 표시
                print(f"  - {e.pattern_name}")
            if len(existing) > 5:
                print(f"  ... and {len(existing) - 5} more")
            print()

        # Watcher 시작
        await self.watcher.start()

        # 메인 루프
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self):
        """동기화 종료"""
        self.running = False
        await self.watcher.stop()
        await self.memory_client.close()
        print("\n[STOPPED] Auto-sync bridge terminated")


async def main():
    bridge = AutoSyncBridge()

    try:
        await bridge.start()
    except KeyboardInterrupt:
        print("\n중단됨...")
    finally:
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
