from __future__ import annotations

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.agents.maas_geometry_agent.oauth_batch_resume import (
    OauthBatchResumeError,
    run_codex_batch,
    run_codex_versioned_batch,
    run_codex_repair,
    validate_batch_bundle,
)


C53_BUNDLE = (
    Path(__file__).resolve().parents[2]
    / ".superpowers"
    / "sdd"
    / "2026-08-05-llm-authored-diverse-legal-mass"
    / "tmp-v31-c53-b01"
)


class MaasOauthBatchResumeTests(SimpleTestCase):
    def test_c53_bundle_binds_one_shared_twenty_count_and_artifact_hashes(self):
        evidence = validate_batch_bundle(C53_BUNDLE)

        self.assertEqual(evidence["target_count"], 20)
        self.assertEqual(evidence["author_batch_count"], 20)
        self.assertEqual(evidence["parser_expected_count"], 20)
        self.assertEqual(evidence["eligible_count"], 20)
        self.assertEqual(evidence["distinct_eligible_path_count"], 20)
        self.assertTrue(evidence["hard_pass"])
        self.assertEqual(
            set(evidence["artifact_sha256"]),
            {
                "eligible-path-scan.json",
                "exact-oauth-request.json",
                "provider-output-schema.json",
                "provider-prompt.txt",
            },
        )

    def test_bundle_rejects_count_drift_before_provider_execution(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory)
            for name in (
                "eligible-path-scan.json",
                "exact-oauth-request.json",
                "provider-output-schema.json",
                "provider-prompt.txt",
                "provider-attempt-result.json",
            ):
                (copied / name).write_bytes((C53_BUNDLE / name).read_bytes())
            request_path = copied / "exact-oauth-request.json"
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["parser_expected_count"] = 19
            request_path.write_text(
                json.dumps(request, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                OauthBatchResumeError,
                "shared batch count mismatch",
            ):
                validate_batch_bundle(copied)

    def test_codex_console_capture_is_decoded_as_utf8(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory)
            for artifact in C53_BUNDLE.iterdir():
                if artifact.is_file() and artifact.name in {
                    "eligible-path-scan.json",
                    "exact-oauth-request.json",
                    "provider-output-schema.json",
                    "provider-prompt.txt",
                    "provider-attempt-result.json",
                }:
                    (copied / artifact.name).write_bytes(artifact.read_bytes())

            def fake_run(command, **kwargs):
                self.assertEqual(kwargs["encoding"], "utf-8")
                self.assertEqual(kwargs["errors"], "replace")
                output_index = command.index("--output-last-message") + 1
                Path(command[output_index]).write_text(
                    json.dumps({"programs": []}),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="한글 진단",
                    stderr="",
                )

            with patch("subprocess.run", side_effect=fake_run):
                response_path, completed = run_codex_batch(
                    copied,
                    workspace_dir=Path(__file__).resolve().parents[2],
                    response_name="utf8-response.json",
                )

            self.assertTrue(response_path.is_file())
            self.assertEqual(completed.stdout, "한글 진단")

    def test_repair_resumes_explicit_session_with_versioned_artifacts(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory)
            for artifact in C53_BUNDLE.iterdir():
                if artifact.is_file() and artifact.name in {
                    "eligible-path-scan.json",
                    "exact-oauth-request.json",
                    "provider-output-schema.json",
                    "provider-prompt.txt",
                    "provider-attempt-result.json",
                }:
                    (copied / artifact.name).write_bytes(artifact.read_bytes())
            (copied / "provider-output-schema-v3.json").write_text(
                json.dumps({"type": "object"}),
                encoding="utf-8",
            )
            (copied / "provider-repair-prompt-v3.txt").write_text(
                "Use only production parameter names.",
                encoding="utf-8",
            )

            def fake_run(command, **kwargs):
                resume_index = command.index("resume")
                self.assertEqual(command[resume_index + 1], "session-53")
                self.assertIn("provider-output-schema-v3.json", " ".join(command))
                output_index = command.index("--output-last-message") + 1
                Path(command[output_index]).write_text(
                    json.dumps({"programs": []}),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0, "복구", "")

            with patch("subprocess.run", side_effect=fake_run):
                response_path, _ = run_codex_repair(
                    copied,
                    workspace_dir=Path(__file__).resolve().parents[2],
                    session_id="session-53",
                    schema_name="provider-output-schema-v3.json",
                    prompt_name="provider-repair-prompt-v3.txt",
                    response_name="provider-response-v3.json",
                )

            self.assertEqual(response_path.name, "provider-response-v3.json")
            self.assertTrue(response_path.is_file())

    def test_versioned_batch_starts_without_accumulated_resume_context(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory)
            for artifact in C53_BUNDLE.iterdir():
                if artifact.is_file() and artifact.name in {
                    "eligible-path-scan.json",
                    "exact-oauth-request.json",
                    "provider-output-schema.json",
                    "provider-prompt.txt",
                    "provider-attempt-result.json",
                }:
                    (copied / artifact.name).write_bytes(artifact.read_bytes())
            (copied / "schema-v5.json").write_text(
                json.dumps({"type": "object"}), encoding="utf-8"
            )
            (copied / "prompt-v5.txt").write_text("fresh", encoding="utf-8")

            def fake_run(command, **kwargs):
                self.assertNotIn("resume", command)
                config_index = command.index("-c")
                self.assertEqual(
                    command[config_index + 1],
                    'model_reasoning_effort="low"',
                )
                output_index = command.index("--output-last-message") + 1
                Path(command[output_index]).write_text(
                    json.dumps({"programs": []}), encoding="utf-8"
                )
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("subprocess.run", side_effect=fake_run):
                response_path, _ = run_codex_versioned_batch(
                    copied,
                    workspace_dir=Path(__file__).resolve().parents[2],
                    schema_name="schema-v5.json",
                    prompt_name="prompt-v5.txt",
                    response_name="response-v5.json",
                    reasoning_effort="low",
                )

            self.assertTrue(response_path.is_file())
