"""Security and determinism contract for the fixed estimand-study runner."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_estimand_receipt_study as runner


class RunnerArgumentTests(unittest.TestCase):
    def test_parsed_windows_path_is_an_authorized_output_path(self) -> None:
        config = runner.parse_args(("--dry-run", "--output-dir", "new-output"))
        self.assertIsInstance(config.output_dir, Path)
        self.assertIs(runner._validate_run_configuration(config), config)

    def test_dry_mode_is_exact_and_rejects_overrides(self) -> None:
        config = runner.parse_args(("--dry-run", "--output-dir", "new-output"))
        self.assertEqual(config.mode, "dry")
        self.assertEqual(config.replications, 20)
        for forbidden in (
            ("--dry-run", "--replications", "20", "--output-dir", "new-output"),
            ("--dry-run", "--seed", "1", "--output-dir", "new-output"),
            ("--dry-run", "--unexpected", "--output-dir", "new-output"),
        ):
            with self.subTest(arguments=forbidden), self.assertRaises(SystemExit):
                runner.parse_args(forbidden)

    def test_registered_mode_requires_exact_confirmation_and_index(self) -> None:
        registered = (
            "--registered",
            "--execution-index",
            "1",
            "--confirm-registered-simulation",
            "--output-dir",
            "new-output",
        )
        with self.assertRaises(SystemExit):
            runner.parse_args(registered)
        for forbidden in (
            ("--registered", "--execution-index", "1", "--output-dir", "new-output"),
            (
                "--registered",
                "--execution-index",
                "3",
                "--output-dir",
                "new-output",
                "--confirm-registered-simulation",
            ),
            (
                "--registered",
                "--execution-index",
                "1",
                "--confirm-registered-simulation",
                "--replications",
                "2000",
                "--output-dir",
                "new-output",
            ),
            ("--dry-run", "--registered", "--output-dir", "new-output"),
        ):
            with self.subTest(arguments=forbidden), self.assertRaises(SystemExit):
                runner.main(forbidden)


class RunnerRegisteredPreflightTests(unittest.TestCase):
    _REGISTERED_PREFIX = (
        "--registered",
        "--execution-index",
        "1",
        "--confirm-registered-simulation",
        "--output-dir",
    )

    def _assert_registered_output_rejects_before_compute(
        self, output_dir: Path, message: str
    ) -> None:
        scenario = mock.Mock()
        scenario.scenario_id = "preflight-scenario"
        scenario.to_dict.return_value = {"scenario_id": scenario.scenario_id}
        profile = mock.Mock()
        profile.canonical_bytes = b"{}\n"
        with (
            mock.patch.object(runner, "require_no_network_capability"),
            mock.patch.object(runner, "registered_scenarios", return_value=(scenario,)),
            mock.patch.object(runner, "build_evaluator_profile", return_value=profile),
            mock.patch.object(runner, "simulate_batch") as simulated,
            mock.patch.object(runner, "finalize_metrics", return_value=()),
            mock.patch.object(runner, "validate_scientific_payload"),
            mock.patch.object(
                runner,
                "create_fresh_output_root",
                wraps=runner.create_fresh_output_root,
            ) as created,
        ):
            with self.assertRaisesRegex(ValueError, message):
                runner.main((*self._REGISTERED_PREFIX, str(output_dir)))
        self.assertEqual((simulated.call_count, created.call_count), (0, 0))

    def test_registered_existing_output_rejects_before_compute(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "existing"
            output_dir.mkdir()
            self._assert_registered_output_rejects_before_compute(
                output_dir, "existing"
            )

    def test_registered_protected_output_rejects_before_compute(self) -> None:
        output_dir = runner.REPOSITORY_ROOT / "data" / "forbidden-output"
        self._assert_registered_output_rejects_before_compute(output_dir, "protected")

    def test_registered_reparse_output_rejects_before_compute(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "reparse-output"
            original = runner._has_link_or_reparse_ancestor

            def is_reparse_ancestor(path: Path) -> bool:
                return Path(path) == output_dir or original(path)

            with mock.patch.object(
                runner, "_has_link_or_reparse_ancestor", side_effect=is_reparse_ancestor
            ):
                self._assert_registered_output_rejects_before_compute(
                    output_dir, "link or reparse"
                )


class RunnerBoundaryTests(unittest.TestCase):
    def test_output_directory_must_be_new_and_outside_protected_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "existing"
            existing.mkdir()
            with self.assertRaisesRegex(ValueError, "existing"):
                runner.validate_output_directory(existing)
        for protected in (
            runner.REPOSITORY_ROOT / "data" / "forbidden-output",
            runner.REPOSITORY_ROOT / "results" / "forbidden-output",
            runner.REPOSITORY_ROOT / "models" / "forbidden-output",
        ):
            with (
                self.subTest(protected=protected),
                self.assertRaisesRegex(ValueError, "protected"),
            ):
                runner.validate_output_directory(protected)

    def test_output_directory_rejects_link_or_reparse_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "output"
            with mock.patch.object(runner, "_is_link_or_reparse", return_value=True):
                with self.assertRaisesRegex(ValueError, "link"):
                    runner.validate_output_directory(candidate)

    def test_network_capability_fails_closed(self) -> None:
        normal = subprocess.run(
            [
                sys.executable,
                "-E",
                "-B",
                "-c",
                "import run_estimand_receipt_study as r; r.require_no_network_capability()",
            ],
            cwd=runner.REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(normal.returncode, 0, normal.stderr)
        with mock.patch.object(
            runner, "_network_capability_present", return_value=True
        ):
            with self.assertRaisesRegex(RuntimeError, "network"):
                runner.require_no_network_capability()

    def test_execution_seal_blocks_socket_before_scientific_compute(self) -> None:
        probe = (
            "import run_estimand_receipt_study as r, socket; "
            "r.install_execution_seal(); "
            "socket.socket()"
        )
        completed = subprocess.run(
            [sys.executable, "-E", "-B", "-c", probe],
            cwd=runner.REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("network capability", completed.stderr)

    def test_execution_seal_blocks_popen_before_spawn_in_isolated_process(self) -> None:
        probe = (
            "import run_estimand_receipt_study as r, subprocess, sys; "
            "r.install_execution_seal(); "
            "subprocess.Popen([sys.executable, '-c', 'raise SystemExit(99)'])"
        )
        completed = subprocess.run(
            [sys.executable, "-E", "-B", "-c", probe],
            cwd=runner.REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("network capability", completed.stderr)

    def test_post_seal_transport_import_is_blocked_before_network(self) -> None:
        probe = (
            "import run_estimand_receipt_study as r; "
            "r.install_execution_seal(); "
            "import http.client; "
            "http.client.HTTPConnection('example.invalid', 80).connect()"
        )
        completed = subprocess.run(
            [sys.executable, "-E", "-B", "-c", probe],
            cwd=runner.REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("network capability", completed.stderr)

    def test_real_symlink_parent_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            redirect = root / "redirect"
            try:
                os.symlink(target, redirect, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "link"):
                runner.create_fresh_output_root(redirect / "output")

    def test_injected_root_identity_race_is_rejected_and_safely_aborted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "output"
            root = runner.create_fresh_output_root(candidate)
            with mock.patch.object(root, "revalidate", side_effect=ValueError("race")):
                with self.assertRaisesRegex(ValueError, "race"):
                    root.write_new("design.json", b"{}\n")
            root.abort()
            self.assertFalse(candidate.exists())


class RunnerReceiptTests(unittest.TestCase):
    def test_receipt_binds_canonical_scientific_files_and_self_hash(self) -> None:
        payloads = {
            name: ("{}\n" if name != "metrics.jsonl" else "{}\n").encode("utf-8")
            for name in runner.SCIENTIFIC_FILENAMES
            if name != "receipt.json"
        }
        receipt = runner.build_receipt(
            mode="dry",
            replication_start=0,
            replication_end_exclusive=20,
            replication_count=20,
            source_hashes=runner._source_hashes(),
            evaluator_profile_bytes=b"{}",
            scenario_ids=("scenario-a",),
            scientific_payloads=payloads,
        )
        self.assertEqual(receipt["self_sha256"], runner.receipt_self_hash(receipt))
        self.assertEqual(
            receipt["scientific_files"]["design.json"],
            hashlib.sha256(b"{}\n").hexdigest(),
        )
        self.assertEqual(
            receipt["evaluator_profile_sha256"], hashlib.sha256(b"{}").hexdigest()
        )
        self.assertNotIn("timestamp", json.dumps(receipt, sort_keys=True))
        with self.assertRaisesRegex(ValueError, "source hashes"):
            runner.build_receipt(
                mode="dry",
                replication_start=0,
                replication_end_exclusive=20,
                replication_count=20,
                source_hashes={},
                evaluator_profile_bytes=b"{}",
                scenario_ids=("scenario-a",),
                scientific_payloads=payloads,
            )

    def test_source_manifest_is_exact_and_includes_io(self) -> None:
        self.assertIn("iclr2027/io.py", runner.REVIEWED_SOURCE_FILES)
        source_hashes = runner._source_hashes()
        payloads = {
            name: b"{}\n"
            for name in runner.SCIENTIFIC_FILENAMES
            if name != "receipt.json"
        }
        missing = dict(source_hashes)
        del missing["iclr2027/io.py"]
        extra = {**source_hashes, "unreviewed.py": "0" * 64}
        changed = dict(source_hashes)
        changed["iclr2027/io.py"] = "0" * 64
        for candidate in (missing, extra, changed):
            with (
                self.subTest(candidate=candidate),
                self.assertRaisesRegex(ValueError, "source hashes"),
            ):
                runner.build_receipt(
                    mode="dry",
                    replication_start=0,
                    replication_end_exclusive=20,
                    replication_count=20,
                    source_hashes=candidate,
                    evaluator_profile_bytes=b"{}",
                    scenario_ids=("scenario-a",),
                    scientific_payloads=payloads,
                )

    def test_replication_interval_is_exactly_bound(self) -> None:
        payloads = {
            name: b"{}\n"
            for name in runner.SCIENTIFIC_FILENAMES
            if name != "receipt.json"
        }
        for start, end, count in ((1, 21, 20), (0, 19, 20), (0, 20, 19)):
            with (
                self.subTest(start=start, end=end, count=count),
                self.assertRaisesRegex(ValueError, "replication"),
            ):
                runner.build_receipt(
                    mode="dry",
                    replication_start=start,
                    replication_end_exclusive=end,
                    replication_count=count,
                    source_hashes=runner._source_hashes(),
                    evaluator_profile_bytes=b"{}",
                    scenario_ids=("scenario-a",),
                    scientific_payloads=payloads,
                )

    def test_forged_registered_configuration_rejects_before_simulation(self) -> None:
        former_marker = getattr(runner, "_PARSED_AUTHORIZATION", object())
        forged = object.__new__(runner.RunConfiguration)
        object.__setattr__(forged, "mode", "registered")
        object.__setattr__(forged, "replication_start", 0)
        object.__setattr__(forged, "replication_end_exclusive", 2000)
        object.__setattr__(forged, "replication_count", 2000)
        object.__setattr__(forged, "output_dir", Path("forged-output"))
        object.__setattr__(forged, "execution_index", 1)
        object.__setattr__(forged, "_authorization", former_marker)
        payloads = {name: b"{}\n" for name in runner.SCIENTIFIC_FILENAMES}
        with (
            mock.patch.object(runner, "simulate_batch") as simulated,
            mock.patch.object(runner, "create_fresh_output_root") as created,
        ):
            for helper, arguments in (
                (runner.build_scientific_payloads, (forged,)),
                (runner._write_output, (forged, payloads)),
                (runner.execute, (forged,)),
            ):
                with (
                    self.subTest(helper=helper.__name__),
                    self.assertRaisesRegex(ValueError, "registered"),
                ):
                    helper(*arguments)
        self.assertEqual(simulated.call_count, 0)
        self.assertEqual(created.call_count, 0)
        self.assertFalse(hasattr(runner, "_PARSED_AUTHORIZATION"))

    def test_scientific_payload_rejects_timestamps_and_noncanonical_text(self) -> None:
        for key in (
            "createdAt",
            "timestamp",
            "hostname",
            "processId",
            "nonce",
            "tempLocation",
            "file_path",
        ):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "metadata"):
                runner.canonical_json_bytes({"nested": {key: "forbidden"}})
        with self.assertRaisesRegex(ValueError, "canonical"):
            runner.validate_scientific_payload("design.json", b"{}\r\n")
        with self.assertRaisesRegex(ValueError, "blank"):
            runner.validate_scientific_payload("metrics.jsonl", b"{}\n\n")


if __name__ == "__main__":
    unittest.main()
