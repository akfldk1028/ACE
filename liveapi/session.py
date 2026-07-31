"""
High-level voice session manager.

Wraps LiveClient with WebSocket-friendly callbacks and base64 audio encoding.
Use this when integrating with a web frontend via WebSocket or SSE.
"""

import asyncio
import base64
import logging
from typing import Callable, Optional

from .client import LiveClient

logger = logging.getLogger(__name__)


class VoiceSession:
    """Manages a continuous voice conversation with WebSocket-friendly I/O."""

    def __init__(self, api_key: str, model: str = "gemini-live-2.5-flash-preview"):
        self.client = LiveClient(api_key=api_key, model=model)
        self._task: Optional[asyncio.Task] = None

    async def start(
        self,
        send_event: Callable,
        voice: str = "Aoede",
        system_instruction: str = "",
        tools: Optional[list[tuple]] = None,
    ):
        """Start a voice session.

        Args:
            send_event: Async callable(dict) to push events to the frontend.
                Events:
                - {"type": "audio", "data": "<base64>"}
                - {"type": "input_transcript", "text": "..."}
                - {"type": "output_transcript", "text": "..."}
                - {"type": "text", "text": "..."}
                - {"type": "tool_call", "name": "...", "args": {...}, "result": {...}}
            voice: Gemini voice preset.
            system_instruction: System prompt.
            tools: List of (name, description, handler, parameters) tuples.
        """
        if tools:
            for name, desc, handler, params in tools:
                self.client.register_tool(name, desc, handler, params)

        async def on_audio(audio_bytes: bytes):
            await send_event({
                "type": "audio",
                "data": base64.b64encode(audio_bytes).decode("ascii"),
            })

        async def on_text(event: dict):
            await send_event(event)

        async def on_tool_call(event: dict):
            await send_event({"type": "tool_call", **event})

        self._task = asyncio.create_task(
            self.client.start(
                on_audio=on_audio,
                on_text=on_text,
                on_tool_call=on_tool_call,
                voice=voice,
                system_instruction=system_instruction,
            )
        )
        logger.info("Voice session started (voice=%s)", voice)

    async def push_audio(self, audio_bytes: bytes):
        """Send raw PCM audio from the user's microphone."""
        await self.client.send_audio(audio_bytes)

    async def push_audio_base64(self, b64: str):
        """Send base64-encoded PCM audio from a WebSocket message."""
        await self.client.send_audio_base64(b64)

    async def push_text(self, text: str):
        """Send a text message from the user."""
        await self.client.send_text(text)

    async def user_stopped_speaking(self):
        """Signal end of user audio stream."""
        await self.client.signal_audio_end()

    async def stop(self):
        """End the session and clean up."""
        await self.client.stop()
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
        logger.info("Voice session stopped")

    @property
    def is_active(self) -> bool:
        return self.client.active
