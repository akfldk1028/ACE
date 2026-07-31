"""
Gemini Live API Client — standalone, zero-dependency wrapper.

Drop this folder into any project for bidirectional voice streaming with:
- Audio in/out (16kHz PCM → 24kHz PCM)
- Text input/output + transcript
- Function calling (register tools, handle calls, send responses)
- Stream lifecycle signals (audio_stream_end, activity hints)

Usage:
    from liveapi import LiveClient

    client = LiveClient(api_key="...", model="gemini-live-2.5-flash-preview")
    client.register_tool("search", "Search docs", my_handler, params_schema)
    await client.start(on_audio=..., on_text=..., voice="Aoede")
    await client.send_audio(pcm_bytes)
    await client.send_text("hello")
    await client.stop()

Requires: google-genai>=1.0
"""

import asyncio
import base64
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class LiveClient:
    """Bidirectional streaming client for Gemini Live API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-live-2.5-flash-preview",
        audio_sample_rate: int = 16000,
    ):
        self.api_key = api_key
        self.model = model
        self.audio_sample_rate = audio_sample_rate

        self._session = None
        self.active = False
        self._audio_q: asyncio.Queue = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []

        # Function calling
        self._tool_decls: list[dict] = []
        self._tool_handlers: dict[str, Callable] = {}

    # ── Tool registration ────────────────────────────

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable,
        parameters: Optional[dict] = None,
    ):
        """Register a function-calling tool.

        Args:
            name: Function name exposed to the model.
            description: What the function does (for the LLM).
            handler: Async callable — receives kwargs, returns dict.
            parameters: JSON Schema for the function parameters.
        """
        decl = {"name": name, "description": description}
        if parameters:
            decl["parameters"] = parameters
        self._tool_decls.append(decl)
        self._tool_handlers[name] = handler

    # ── Session lifecycle ────────────────────────────

    async def start(
        self,
        on_audio: Optional[Callable] = None,
        on_text: Optional[Callable] = None,
        on_tool_call: Optional[Callable] = None,
        voice: str = "Aoede",
        system_instruction: str = "",
    ):
        """Open a Live API session.

        Args:
            on_audio: async callback(bytes) — raw 24kHz PCM chunks from model.
            on_text: async callback(dict) — {"type": "transcript"|"text", "text": str}.
            on_tool_call: async callback(dict) — {"name": str, "args": dict, "result": dict}.
            voice: Gemini voice preset name.
            system_instruction: System prompt for the conversation.
        """
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        config = {
            "response_modalities": ["AUDIO", "TEXT"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": voice}
                }
            },
            "input_audio_transcription": {},
            "output_audio_transcription": {},
        }
        if system_instruction:
            config["system_instruction"] = system_instruction
        if self._tool_decls:
            config["tools"] = [{"function_declarations": self._tool_decls}]

        async with client.aio.live.connect(
            model=self.model, config=config
        ) as session:
            self._session = session
            self.active = True
            logger.info("Live API connected: %s", self.model)

            self._tasks = [
                asyncio.create_task(
                    self._pump_audio(session, types)
                ),
                asyncio.create_task(
                    self._pump_responses(session, types, on_audio, on_text, on_tool_call)
                ),
            ]

            try:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            finally:
                self.active = False
                self._session = None

    async def stop(self):
        """Gracefully end the session."""
        self.active = False
        for t in self._tasks:
            if not t.done():
                t.cancel()
        self._tasks.clear()
        self._session = None
        logger.info("Live API session stopped")

    # ── Sending ──────────────────────────────────────

    async def send_audio(self, data: bytes):
        """Queue raw PCM audio bytes for streaming to the model."""
        if self.active:
            await self._audio_q.put(data)

    async def send_audio_base64(self, b64: str):
        """Queue base64-encoded audio for streaming."""
        try:
            await self.send_audio(base64.b64decode(b64))
        except (ValueError, base64.binascii.Error):
            logger.error("Invalid base64 audio data")

    async def send_text(self, text: str):
        """Send a text message to the model."""
        if not self._session or not self.active:
            return
        await self._session.send_client_content(
            turns={"parts": [{"text": text}]},
            turn_complete=True,
        )

    async def signal_audio_end(self):
        """Signal that the user stopped speaking."""
        if self._session and self.active:
            await self._session.send_realtime_input(audio_stream_end=True)

    async def signal_activity(self, started: bool):
        """VAD hint: user started/stopped being active."""
        if not self._session or not self.active:
            return
        try:
            if started:
                await self._session.send_realtime_input(activity_start=True)
            else:
                await self._session.send_realtime_input(activity_end=True)
        except Exception:
            pass  # not all models support this

    # ── Internal pumps ───────────────────────────────

    async def _pump_audio(self, session, types):
        """Continuously send queued audio to the model."""
        while self.active:
            try:
                data = await asyncio.wait_for(self._audio_q.get(), timeout=0.1)
                if data:
                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=data,
                            mime_type=f"audio/pcm;rate={self.audio_sample_rate}",
                        )
                    )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Audio send error: %s", e)
                break

    async def _pump_responses(self, session, types, on_audio, on_text, on_tool_call):
        """Receive and dispatch model responses."""
        try:
            async for response in session.receive():
                if not self.active:
                    break

                # ─ server_content ─
                sc = getattr(response, "server_content", None)
                if sc:
                    # Input transcript (user speech → text)
                    it = getattr(sc, "input_transcription", None)
                    if it and it.text and on_text:
                        await on_text({"type": "input_transcript", "text": it.text})

                    # Output transcript (model speech → text)
                    ot = getattr(sc, "output_transcription", None)
                    if ot and ot.text and on_text:
                        await on_text({"type": "output_transcript", "text": ot.text})

                    # Interruption
                    if getattr(sc, "interrupted", False):
                        # Flush audio queue
                        while not self._audio_q.empty():
                            try:
                                self._audio_q.get_nowait()
                            except asyncio.QueueEmpty:
                                break

                    # Model turn (audio + text parts)
                    mt = getattr(sc, "model_turn", None)
                    if mt:
                        for part in mt.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                if on_audio:
                                    await on_audio(part.inline_data.data)
                            if hasattr(part, "text") and part.text:
                                if on_text:
                                    await on_text({"type": "text", "text": part.text})

                # ─ tool_call ─
                tc = getattr(response, "tool_call", None)
                if tc:
                    responses = []
                    for fc in tc.function_calls:
                        handler = self._tool_handlers.get(fc.name)
                        args = dict(fc.args) if fc.args else {}
                        if handler:
                            try:
                                result = await handler(**args) if args else await handler()
                            except Exception as e:
                                logger.error("Tool %s error: %s", fc.name, e)
                                result = {"error": str(e)}
                        else:
                            result = {"error": f"Unknown tool: {fc.name}"}

                        responses.append(
                            types.FunctionResponse(
                                id=fc.id, name=fc.name, response=result
                            )
                        )
                        if on_tool_call:
                            await on_tool_call({
                                "name": fc.name,
                                "args": args,
                                "result": result,
                            })

                    await session.send_tool_response(function_responses=responses)

                # ─ setup_complete ─
                if getattr(response, "setup_complete", None):
                    logger.info("Live API setup complete")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Response pump error: %s", e, exc_info=True)
