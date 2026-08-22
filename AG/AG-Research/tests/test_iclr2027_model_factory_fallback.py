from __future__ import annotations

import asyncio
import importlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from autogen_core.models import CreateResult, RequestUsage, UserMessage
from AG_Cohub import model_factory as model_factory_module
from AG_Cohub.sdk import client as sdk_client_module
from experiment_utils import ClaudeCLIChatCompletionClient


class _BrokenStderr:
    def write(self, _: str) -> int:
        raise OSError(22, "Invalid argument")

    def flush(self) -> None:
        raise OSError(22, "Invalid argument")


class ClaudeSubprocessFallbackTests(unittest.TestCase):
    def test_model_factory_reload_survives_broken_stderr(self) -> None:
        with patch("sys.stderr", _BrokenStderr()):
            reloaded = importlib.reload(model_factory_module)

        self.assertTrue(hasattr(reloaded, "ClaudeCLIChatCompletionClient"))

    def test_sdk_success_survives_broken_stderr(self) -> None:
        async def empty_sdk_query(**_: object):
            if False:
                yield None

        sdk = sdk_client_module.ClaudeSDK(
            model="claude-haiku-4-5-20251001"
        )
        fake_sys = SimpleNamespace(stderr=_BrokenStderr())

        with (
            patch.object(sdk_client_module, "SDK_AVAILABLE", True),
            patch.object(
                sdk_client_module,
                "claude_sdk_query",
                new=empty_sdk_query,
            ),
            patch.object(sdk_client_module, "sys", fake_sys),
            patch.object(sdk, "_build_options", return_value=object()),
        ):
            result = asyncio.run(sdk.query(prompt="diagnostic isolation"))

        self.assertTrue(result.success)
        self.assertEqual(result.error, None)

    def test_sdk_failure_survives_broken_stderr(self) -> None:
        async def failing_sdk_query(**_: object):
            raise RuntimeError("sdk transport failure")
            if False:
                yield None

        sdk = sdk_client_module.ClaudeSDK(
            model="claude-haiku-4-5-20251001"
        )
        fake_sys = SimpleNamespace(stderr=_BrokenStderr())

        with (
            patch.object(sdk_client_module, "SDK_AVAILABLE", True),
            patch.object(
                sdk_client_module,
                "claude_sdk_query",
                new=failing_sdk_query,
            ),
            patch.object(sdk_client_module, "sys", fake_sys),
            patch.object(sdk, "_build_options", return_value=object()),
        ):
            result = asyncio.run(sdk.query(prompt="diagnostic isolation"))

        self.assertFalse(result.success)
        self.assertEqual(result.error, "sdk transport failure")

    def test_sdk_failure_falls_back_when_stderr_is_broken(self) -> None:
        client = ClaudeCLIChatCompletionClient(
            model="claude-haiku-4-5-20251001"
        )
        client._sdk = SimpleNamespace(
            query=AsyncMock(
                return_value=sdk_client_module.SDKResult(
                    success=False,
                    error="sdk unavailable",
                )
            )
        )
        fallback_result = CreateResult(
            finish_reason="stop",
            content="fallback",
            usage=RequestUsage(prompt_tokens=1, completion_tokens=1),
            cached=False,
        )

        with (
            patch.object(
                client,
                "_create_via_subprocess",
                new=AsyncMock(return_value=fallback_result),
            ) as fallback,
            patch("sys.stderr", _BrokenStderr()),
        ):
            result = asyncio.run(
                client._create_via_sdk("prompt", ["system policy"])
            )

        fallback.assert_awaited_once()
        self.assertEqual(result.content, "fallback")

    def test_tool_transport_uses_clear_english_protocol_and_parses_handoff(self) -> None:
        client = ClaudeCLIChatCompletionClient(model="claude-haiku-4-5-20251001")
        client._use_sdk = False
        transport_result = CreateResult(
            finish_reason="stop",
            content="[TOOL_CALL: transfer_to_compliance_agent]",
            usage=RequestUsage(prompt_tokens=1, completion_tokens=1),
            cached=False,
        )
        tool = {
            "name": "transfer_to_compliance_agent",
            "description": "Transfer evidence review to compliance_agent",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

        with patch.object(
            client,
            "_create_via_subprocess",
            new=AsyncMock(return_value=transport_result),
        ) as transport:
            result = asyncio.run(
                client.create(
                    [UserMessage(content="handoff now", source="user")],
                    tools=[tool],
                )
            )

        system_prompt = "\n".join(transport.await_args.args[1])
        self.assertIn("Available tools", system_prompt)
        self.assertIn("output only this exact form", system_prompt)
        self.assertIn(
            "[TOOL_CALL: transfer_to_compliance_agent]", system_prompt
        )
        self.assertEqual(result.finish_reason, "function_calls")
        self.assertEqual(result.content[0].name, "transfer_to_compliance_agent")

    def test_long_prompt_uses_stdin_instead_of_windows_command_argument(self) -> None:
        client = ClaudeCLIChatCompletionClient(model="claude-haiku-4-5-20251001")
        prompt = "x" * 28_000
        response = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "result": "ok",
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                }
            ),
            stderr="",
        )

        with patch(
            "AG_Cohub.model_factory.subprocess.run",
            return_value=response,
        ) as run:
            result = asyncio.run(
                client._create_via_subprocess(prompt, ["system policy"], {})
            )

        command = run.call_args.args[0]
        self.assertNotIn(prompt, command)
        self.assertEqual(run.call_args.kwargs["input"], prompt)
        self.assertEqual(result.content, "ok")

    def test_subprocess_success_survives_broken_stderr(self) -> None:
        client = ClaudeCLIChatCompletionClient(
            model="claude-haiku-4-5-20251001"
        )
        response = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "result": "ok",
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                }
            ),
            stderr="",
        )

        with (
            patch(
                "AG_Cohub.model_factory.subprocess.run",
                return_value=response,
            ),
            patch("sys.stderr", _BrokenStderr()),
        ):
            result = asyncio.run(
                client._create_via_subprocess("prompt", [], {})
            )

        self.assertEqual(result.content, "ok")
        self.assertEqual(result.usage.prompt_tokens, 10)
        self.assertEqual(result.usage.completion_tokens, 2)

    def test_public_create_preserves_overlimit_prompt_for_every_transport_choice(self) -> None:
        middle = "MIDDLE_SENTINEL_MUST_SURVIVE"
        tail = "TAIL_CONTRACT_MUST_SURVIVE"
        prompt = "a" * 15_000 + middle + "b" * 16_000 + tail
        response = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "result": "ok",
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                }
            ),
            stderr="",
        )
        sdk_result = CreateResult(
            finish_reason="stop",
            content="sdk",
            usage=RequestUsage(prompt_tokens=1, completion_tokens=1),
            cached=False,
        )

        for sdk_selected in (False, True):
            with self.subTest(sdk_selected=sdk_selected):
                client = ClaudeCLIChatCompletionClient(
                    model="claude-haiku-4-5-20251001"
                )
                client._use_sdk = sdk_selected
                with (
                    patch(
                        "AG_Cohub.model_factory.subprocess.run",
                        return_value=response,
                    ) as run,
                    patch.object(
                        client,
                        "_create_via_sdk",
                        new=AsyncMock(return_value=sdk_result),
                    ) as sdk,
                ):
                    result = asyncio.run(
                        client.create(
                            [UserMessage(content=prompt, source="user")]
                        )
                    )

                sdk.assert_not_awaited()
                transported = run.call_args.kwargs["input"]
                self.assertEqual(transported, prompt)
                self.assertIn(middle, transported)
                self.assertTrue(transported.endswith(tail))
                self.assertEqual(result.content, "ok")


if __name__ == "__main__":
    unittest.main()
