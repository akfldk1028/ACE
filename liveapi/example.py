"""
Example: standalone voice chat with Gemini Live API.

Run:
    pip install google-genai
    GEMINI_API_KEY=your_key python -m liveapi.example

Demonstrates:
- Text-only mode (no mic, just type)
- Function calling (weather tool)
- Transcript output
"""

import asyncio
import os
import sys

# Allow running as `python -m liveapi.example`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from liveapi import LiveClient


async def main():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Set GEMINI_API_KEY environment variable")
        return

    client = LiveClient(api_key=api_key)

    # Register a sample tool
    async def get_weather(city: str = "Seoul") -> dict:
        """Fake weather tool for demo."""
        return {"city": city, "temp": "18°C", "condition": "맑음"}

    client.register_tool(
        name="get_weather",
        description="Get current weather for a city",
        handler=get_weather,
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
        },
    )

    # Callbacks
    async def on_audio(data: bytes):
        print(f"[AUDIO] {len(data)} bytes")

    async def on_text(event: dict):
        t = event.get("type", "")
        text = event.get("text", "")
        if t == "input_transcript":
            print(f"[YOU] {text}")
        elif t == "output_transcript":
            print(f"[GEMINI] {text}")
        else:
            print(f"[{t}] {text}")

    async def on_tool(event: dict):
        print(f"[TOOL] {event['name']}({event.get('args', {})}) → {event.get('result', {})}")

    # Start session in background
    session_task = asyncio.create_task(
        client.start(
            on_audio=on_audio,
            on_text=on_text,
            on_tool_call=on_tool,
            voice="Aoede",
            system_instruction="You are a helpful Korean assistant. 한국어로 대답하세요.",
        )
    )

    # Wait for connection
    await asyncio.sleep(1)

    # Text input loop
    print("\n=== Gemini Live API Text Chat ===")
    print("Type a message and press Enter. Type 'quit' to exit.\n")

    while client.active:
        try:
            text = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("> ")
            )
        except (EOFError, KeyboardInterrupt):
            break

        if text.strip().lower() in ("quit", "exit", "q"):
            break

        if text.strip():
            await client.send_text(text.strip())

    await client.stop()
    print("\nSession ended.")


if __name__ == "__main__":
    asyncio.run(main())
