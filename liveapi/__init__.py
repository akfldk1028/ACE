"""
liveapi — Standalone Gemini Live API wrapper.

Drop this folder into any Python project. Requires: google-genai>=1.0

Quick start:
    from liveapi import LiveClient

    client = LiveClient(api_key="YOUR_KEY")
    await client.start(on_audio=my_audio_cb, on_text=my_text_cb)
"""

from .client import LiveClient

__all__ = ["LiveClient"]
__version__ = "1.0.0"
