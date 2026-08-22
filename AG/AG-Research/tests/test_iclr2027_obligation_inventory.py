from __future__ import annotations

import ast
from contextlib import contextmanager
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import MappingProxyType
from typing import Any, Iterator
import unittest
from unittest.mock import patch

import audit_iclr2027_obligation_inventory as audit_cli
from iclr2027 import gate0_sources
from iclr2027 import obligation_inventory as obligation_inventory_module
from iclr2027.gate0_sources import (
    GATE0_TOP_SOURCES,
    Gate0RawSourcePaths,
    Gate0TopSourceSpec,
    validate_gate0_raw_source_paths,
)
from iclr2027.obligation_inventory import (
    Gate0Inventory,
    Gate0PublicationReceipt,
    Gate0Status,
    build_gate0_inventory,
    gate0_inventory_file_bytes,
    publish_gate0_inventory,
    verify_gate0_publication,
)
from iclr2027.secure_files import AuthenticatedTree as RealAuthenticatedTree


PATTERNS = ("rr3", "sel3", "swm3", "refl3", "debate3")
DATASET_FILES = (
    "private/group_assignments.json",
    "private/private_labels.jsonl",
    "runtime/runtime_features.jsonl",
)
DATASET_BINDINGS = (
    "projection_identity_commitment",
    "snapshot_receipt_sha256",
    "split_manifest_sha256",
    "study_contract_sha256",
    "transaction_set_sha256",
    "vocabulary_sha256",
)
INVENTORY_FIELDS = (
    "schema_version",
    "status",
    "acceptance_passed",
    "blockers",
    "access_audit",
    "source_files",
    "development_inventory",
    "branch_coverage",
    "split_readiness",
    "mechanism_readiness",
    "execution_readiness",
    "baseline_readiness",
    "historical_reference",
    "call_budget",
    "receipt_sha256",
)
PUBLICATION_FIELDS = (
    "schema_version",
    "inventory_relative_path",
    "inventory_file_sha256",
    "inventory_self_sha256",
    "source_files_sha256",
    "receipt_sha256",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _json_file(value: object) -> bytes:
    return _canonical(value) + b"\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: object) -> str:
    return _sha(_canonical(value))


def _rehash_record(payload: dict[str, Any]) -> None:
    payload["receipt_sha256"] = _sha_json(
        {key: value for key, value in payload.items() if key != "receipt_sha256"}
    )


_PUBLICATION_PHASES = (
    "write_inventory_temp",
    "write_receipt_temp",
    "replace_inventory",
    "replace_receipt",
    "verify_inventory",
    "verify_receipt",
)


def _make_directory_reparse(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError:
        if os.name != "nt":
            raise
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise OSError(result.stderr or result.stdout or "cannot create directory reparse")


def _remove_directory_reparse(link: Path) -> None:
    if link.is_symlink():
        link.unlink()
    else:
        os.rmdir(link)


def _directory_snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class _DirectorySwapAttack:
    def __init__(self, root: Path, output: Path, *, kind: str, phase: str) -> None:
        if kind not in {"output", "parent"}:
            raise ValueError("unsupported swap kind")
        self.output = output
        self.kind = kind
        self.phase = phase
        self.rename_attempt_count = 0
        self.rename_count = 0
        self.blocked_by_retained_handle = False
        if kind == "output":
            self.replaced_path = output
            self.authenticated_path = output.with_name(output.name + ".authenticated")
            self.outside_root = root / "outside-output"
            self.outside_directory = self.outside_root
        else:
            self.replaced_path = output.parent
            self.authenticated_path = output.parent.with_name(
                output.parent.name + ".authenticated"
            )
            self.outside_root = root / "outside-parent"
            self.outside_directory = self.outside_root / output.name
        self.outside_directory.mkdir(parents=True)
        (self.outside_directory / "sentinel.bin").write_bytes(b"outside-sentinel")
        self.outside_before = _directory_snapshot(self.outside_root)

    @property
    def authenticated_output(self) -> Path:
        if self.kind == "output":
            return self.authenticated_path
        return self.authenticated_path / self.output.name

    def hook(self, phase: str) -> None:
        if phase != self.phase or self.rename_attempt_count:
            return
        self.rename_attempt_count += 1
        try:
            os.replace(self.replaced_path, self.authenticated_path)
        except PermissionError:
            if os.name != "nt":
                raise
            self.blocked_by_retained_handle = True
            return
        _make_directory_reparse(self.replaced_path, self.outside_root)
        self.rename_count += 1

    def restore_namespace(self) -> None:
        if not self.rename_count:
            return
        _remove_directory_reparse(self.replaced_path)
        os.replace(self.authenticated_path, self.replaced_path)

    def assert_outside_untouched(self, case: unittest.TestCase) -> None:
        case.assertEqual(_directory_snapshot(self.outside_root), self.outside_before)
        residue = {
            name
            for tree in (self.secured_output(), self.outside_directory)
            if tree.exists()
            for name in _directory_snapshot(tree)
            if name.startswith(".") or name.endswith((".tmp", ".bak"))
        }
        case.assertEqual(residue, set())

    def secured_output(self) -> Path:
        return self.authenticated_output if self.rename_count else self.output


class _SyntheticGate0Sources:
    """Exact v1.5 metadata shapes; no transaction or dataset child is created."""

    def __init__(self, root: Path, *, development_nonce: str = "first") -> None:
        self.root = root
        self.model = "provider-model-v1"
        self.code_commit = "commitabc123"
        self.pilot_gate: dict[str, Any] = {"schema_version": "synthetic-pilot"}
        self.development: dict[str, Any] = {
            "schema_version": "synthetic-development",
            "nonce": development_nonce,
        }
        self.plan: list[dict[str, Any]] = []
        for case_index in range(30):
            case_id = f"case{case_index:02d}"
            public_case_sha256 = _sha(f"public-case-{case_index}".encode())
            prompt_sha256 = _sha(f"prompt-{case_index}".encode())
            for pattern in PATTERNS:
                for repeat in range(3):
                    row = {
                        "case_id": case_id,
                        "pattern": pattern,
                        "repeat": repeat,
                        "model": self.model,
                        "public_case_sha256": public_case_sha256,
                        "prompt_sha256": prompt_sha256,
                        "code_commit": self.code_commit,
                    }
                    row["resume_key"] = self.resume_key(row)
                    self.plan.append(row)
        input_digests = tuple(_sha(f"input-{index}".encode()) for index in range(6))
        self.manifest: dict[str, Any] = {
            "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
            "input_mode": "frozen_private_binding",
            "split": "dev",
            "patterns": list(PATTERNS),
            "repeats": 3,
            "model": self.model,
            "code_commit": self.code_commit,
            "case_count": 30,
            "expected_case_count": 30,
            "planned_run_count": 450,
            "stage_case_counts": {"execution": 30},
            "decision_case_counts": {"CONTINUE": 30},
            "input_hashes": {f"input:{digest}": digest for digest in input_digests},
            "identity_commitment": _sha(b"identity"),
            "registry_core_sha256": _sha(b"registry"),
            "split_manifest_sha256": _sha(b"split"),
            "plan_sha256": _sha(_json_file(self.plan)),
            "executed": False,
        }
        self.dataset_files = {
            name: _sha(f"declared-{index}".encode())
            for index, name in enumerate(DATASET_FILES)
        }
        self.dataset_bindings = {
            name: _sha(f"binding-{index}".encode())
            for index, name in enumerate(DATASET_BINDINGS)
        }
        self.row_census: dict[str, Any] = {
            "assignments": 450,
            "prefixes": 1524,
            "private_labels": 1524,
            "runtime_features": 1524,
            "sites": 5,
            "trajectories": 450,
        }
        self.artifact_receipt: dict[str, Any] = {}
        self.refresh_artifact_receipt()
        self.snapshot_receipt: dict[str, Any] = {}

    @staticmethod
    def resume_key(row: dict[str, Any]) -> str:
        return _sha_json(
            {
                "case_id": row["case_id"],
                "pattern": row["pattern"],
                "repeat": row["repeat"],
                "model": row["model"],
                "public_case_sha256": row["public_case_sha256"],
                "prompt_sha256": row["prompt_sha256"],
                "code_commit": row["code_commit"],
            }
        )

    def refresh_artifact_receipt(self) -> None:
        files = dict(sorted(self.dataset_files.items()))
        census = dict(sorted(self.row_census.items()))
        receipt: dict[str, Any] = {
            "bindings": dict(sorted(self.dataset_bindings.items())),
            "file_set_sha256": _sha_json(files),
            "files": files,
            "row_census": census,
            "row_census_sha256": _sha_json(census),
            "schema_version": "ace.iclr2027.cats_dataset_artifacts.v1",
        }
        receipt["artifact_sha256"] = _sha_json(receipt)
        self.artifact_receipt = receipt

    def refresh_snapshot_receipt(self, files: dict[str, str]) -> None:
        canonical_files = dict(sorted(files.items()))
        row_census = {
            "agent_messages": 1524,
            "completed_checkpoints": 450,
            "final_parse_complete_states": 450,
            "parse_complete_states": 1481,
            "parsed_states": 1524,
            "terminal_errors": 0,
            "transactions": 450,
        }
        bindings = {
            name: _sha(f"snapshot-binding-{name}".encode())
            for name in (
                "code_runtime_identity_sha256",
                "message_hashes_sha256",
                "run_plan_identity_sha256",
                "run_plan_sha256",
                "study_contract_sha256",
                "transaction_set_sha256",
            )
        }
        source_receipt: dict[str, Any] = {
            "bindings": bindings,
            "file_set_sha256": _sha_json(canonical_files),
            "files": canonical_files,
            "row_census": row_census,
            "row_census_sha256": _sha_json(row_census),
            "schema_version": "ace.iclr2027.development_snapshot_sources.v1",
        }
        source_receipt["artifact_sha256"] = _sha_json(source_receipt)
        snapshot = {
            "schema_version": "ace.iclr2027.development_snapshot_receipt.v1",
            "source_artifact_receipt": source_receipt,
        }
        snapshot["receipt_sha256"] = _sha_json(snapshot)
        self.snapshot_receipt = snapshot

    def materialize(
        self,
        *,
        sync_plan_sha256: bool = True,
        sync_artifact_receipt: bool = True,
        sync_snapshot_receipt: bool = True,
        transaction_names: tuple[str, ...] | None = None,
    ) -> tuple[tuple[Gate0TopSourceSpec, ...], Gate0RawSourcePaths]:
        if sync_artifact_receipt:
            self.refresh_artifact_receipt()
        plan_bytes = _json_file(self.plan)
        if sync_plan_sha256:
            self.manifest["plan_sha256"] = _sha(plan_bytes)
        manifest_bytes = _json_file(self.manifest)
        pilot_gate_bytes = _json_file(self.pilot_gate)
        dataset_bytes = _json_file({"artifact_receipt": self.artifact_receipt})
        development_bytes = _json_file(self.development)
        if transaction_names is None:
            transaction_names = tuple(
                sorted(f"run_transactions/{row['resume_key']}.json" for row in self.plan)
            )
        snapshot_files = {
            "pilot_gate.json": _sha(pilot_gate_bytes),
            "run_manifest.json": _sha(manifest_bytes),
            "run_plan.json": _sha(plan_bytes),
            **{name: _sha(name.encode()) for name in transaction_names},
        }
        if sync_snapshot_receipt:
            self.refresh_snapshot_receipt(snapshot_files)
        snapshot_bytes = _json_file(self.snapshot_receipt)
        payloads = (snapshot_bytes, pilot_gate_bytes, dataset_bytes, development_bytes)
        specs = tuple(
            Gate0TopSourceSpec(
                template.logical_name,
                template.relative_path,
                _sha(payload),
                template.declared_members,
            )
            for template, payload in zip(GATE0_TOP_SOURCES, payloads, strict=True)
        )
        for spec, payload in zip(specs, payloads, strict=True):
            path = self.root / spec.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        pilot_root = self.root / Path(specs[1].relative_path).parent
        (pilot_root / "run_manifest.json").write_bytes(manifest_bytes)
        (pilot_root / "run_plan.json").write_bytes(plan_bytes)
        return specs, Gate0RawSourcePaths(*(spec.relative_path for spec in specs))


@contextmanager
def _patched_sources(
    fixture: _SyntheticGate0Sources,
    **materialize_kwargs: Any,
) -> Iterator[Gate0RawSourcePaths]:
    specs, raw = fixture.materialize(**materialize_kwargs)
    with patch.object(gate0_sources, "GATE0_TOP_SOURCES", specs), patch(
        "iclr2027.obligation_inventory._SOURCE_ROOT", fixture.root
    ):
        yield raw


def _build(
    fixture: _SyntheticGate0Sources,
    **materialize_kwargs: Any,
) -> Gate0Inventory:
    with _patched_sources(fixture, **materialize_kwargs) as raw:
        return build_gate0_inventory(sources=raw)


class Gate0SourceContractTests(unittest.TestCase):
    def test_minimal_trust_contract_is_exact_immutable_and_import_isolated(self) -> None:
        self.assertEqual(
            tuple(spec.logical_name for spec in GATE0_TOP_SOURCES),
            ("snapshot_receipt", "pilot_gate", "dataset_manifest", "development_gate"),
        )
        self.assertEqual(len({spec.logical_name for spec in GATE0_TOP_SOURCES}), 4)
        self.assertEqual(GATE0_TOP_SOURCES[2].declared_members, DATASET_FILES)
        with self.assertRaises(TypeError):
            GATE0_TOP_SOURCES[0] = GATE0_TOP_SOURCES[0]  # type: ignore[index]
        with self.assertRaises((AttributeError, TypeError)):
            GATE0_TOP_SOURCES[0].sha256 = "0" * 64  # type: ignore[misc]
        isolated_spec = Gate0TopSourceSpec("x", "x.json", "0" * 64, ())
        with self.assertRaises(AttributeError):
            getattr(isolated_spec, "__dict__")
        imports = ast.parse(
            (Path(__file__).parents[1] / "iclr2027/gate0_sources.py").read_text(
                encoding="utf-8"
            )
        )
        imported_roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(imports)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(imports)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertLessEqual(
            imported_roots,
            {"__future__", "dataclasses", "pathlib", "typing", "re"},
        )
        code = (
            "import sys; import iclr2027.obligation_inventory; "
            "bad=('iclr2027.method_lock','iclr2027.policy_replay',"
            "'iclr2027.run_manifest','iclr2027.cats','iclr2027.trajectory_ingest'); "
            "raise SystemExit(1 if any(x in sys.modules for x in bad) else 0)"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=Path(__file__).parents[1],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_raw_lexical_rejection_occurs_before_path_or_io(self) -> None:
        canonical = tuple(spec.relative_path for spec in GATE0_TOP_SOURCES)

        class ForeignPathLike:
            def __fspath__(self) -> str:
                return canonical[0]

        bad_values: tuple[object, ...] = (
            Path(canonical[0]),
            ForeignPathLike(),
            canonical[0].encode(),
            "./" + canonical[0],
            "../" + canonical[0],
            canonical[0].replace("/", "\\"),
            canonical[0].replace("/", "//", 1),
            canonical[0] + "/",
            "C:/" + canonical[0],
            "\\\\server\\share\\x",
            "results/unauthorized_partition/selector.json",
        )
        for bad in bad_values:
            with self.subTest(bad=bad), patch(
                "iclr2027.gate0_sources.Path",
                side_effect=AssertionError("Path constructed before lexical rejection"),
            ):
                with self.assertRaises((TypeError, ValueError)):
                    validate_gate0_raw_source_paths(
                        Gate0RawSourcePaths(
                            bad,  # type: ignore[arg-type]
                            canonical[1],
                            canonical[2],
                            canonical[3],
                        )
                    )

    def test_valid_raw_paths_construct_only_private_validated_paths(self) -> None:
        raw = Gate0RawSourcePaths(*(spec.relative_path for spec in GATE0_TOP_SOURCES))
        validated = validate_gate0_raw_source_paths(raw)
        self.assertTrue(
            all(
                isinstance(getattr(validated, spec.logical_name), Path)
                for spec in GATE0_TOP_SOURCES
            )
        )


class Gate0AuthenticatedCensusTests(unittest.TestCase):
    def test_real_shape_planned_manifest_and_450_row_list_recompute_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            inventory = _build(fixture)
        full = inventory.development_inventory["full_frozen_development"]
        self.assertEqual(
            full,
            {
                "site_count": 5,
                "case_count": 30,
                "receipt_declared_historical_runs": 450,
                "historical_patterns": PATTERNS,
                "repeats_per_case_pattern": 3,
                "receipt_declared_prefix_count": 1524,
            },
        )
        self.assertEqual(inventory.status.value, "data_collection_required")
        self.assertFalse(inventory.acceptance_passed)

    def test_executed_manifest_conditional_shape_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            fixture.manifest.update(
                {
                    "executed": True,
                    "execution": {
                        "completed_runs": 450,
                        "skipped_runs": 0,
                        "error_runs": 0,
                        "parsed_states": 450,
                        "successful_parses": 450,
                    },
                    "estimated_cost_per_run_usd": 0.1,
                    "estimated_total_cost_usd": 45.0,
                    "estimated_completion_date": "2026-08-20",
                }
            )
            inventory = _build(fixture)
        self.assertEqual(
            inventory.development_inventory["full_frozen_development"][
                "receipt_declared_historical_runs"
            ],
            450,
        )

    def test_manifest_conditional_keys_native_types_privacy_and_arithmetic_fail_closed(self) -> None:
        mutations = {
            "planned_extra_execution": lambda f: f.manifest.__setitem__(
                "execution",
                {
                    "completed_runs": 450,
                    "skipped_runs": 0,
                    "error_runs": 0,
                    "parsed_states": 0,
                    "successful_parses": 0,
                },
            ),
            "bool_repeats": lambda f: f.manifest.__setitem__("repeats", True),
            "wrong_arithmetic": lambda f: f.manifest.__setitem__("planned_run_count", 449),
            "private_path_text": lambda f: f.manifest.__setitem__("model", "private/model"),
            "bad_commitment": lambda f: f.manifest.__setitem__("identity_commitment", "A" * 64),
            "extra_key": lambda f: f.manifest.__setitem__("unexpected", 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                fixture = _SyntheticGate0Sources(Path(temp))
                mutate(fixture)
                with self.assertRaises(ValueError):
                    _build(fixture)

    def test_manifest_plan_commitment_is_format_checked_not_given_an_invented_formula(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            fixture.manifest["plan_sha256"] = "f" * 64
            inventory = _build(fixture, sync_plan_sha256=False)
            self.assertEqual(inventory.status.value, "data_collection_required")
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            fixture.manifest["plan_sha256"] = "F" * 64
            with self.assertRaises(ValueError):
                _build(fixture, sync_plan_sha256=False)

    def test_expected_case_count_is_only_a_positive_upper_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            fixture.manifest["expected_case_count"] = 31
            inventory = _build(fixture)
        self.assertEqual(
            inventory.development_inventory["full_frozen_development"]["case_count"],
            30,
        )

    def test_manifest_pattern_order_is_exact_and_same_set_reorder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            inventory = _build(fixture)
            self.assertEqual(
                inventory.development_inventory["full_frozen_development"][
                    "historical_patterns"
                ],
                PATTERNS,
            )
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            fixture.manifest["patterns"] = list(reversed(PATTERNS))
            with self.assertRaisesRegex(ValueError, "manifest patterns"):
                _build(fixture)

    def test_resume_identity_model_code_and_cartesian_cells_are_recomputed(self) -> None:
        mutations = {}

        def bad_resume(fixture: _SyntheticGate0Sources) -> None:
            fixture.plan[0]["resume_key"] = "0" * 64

        def bad_model(fixture: _SyntheticGate0Sources) -> None:
            fixture.plan[0]["model"] = "other-model"
            fixture.plan[0]["resume_key"] = fixture.resume_key(fixture.plan[0])

        def duplicate_cell(fixture: _SyntheticGate0Sources) -> None:
            fixture.plan[-1] = dict(fixture.plan[0])

        mutations.update(
            bad_resume=bad_resume,
            model_mismatch=bad_model,
            duplicate_cartesian_cell=duplicate_cell,
        )
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                fixture = _SyntheticGate0Sources(Path(temp))
                mutate(fixture)
                with self.assertRaises(ValueError):
                    _build(fixture)

    def test_case_digest_bijection_and_prompt_stability_are_enforced(self) -> None:
        def changed_case_digest(fixture: _SyntheticGate0Sources) -> None:
            fixture.plan[1]["public_case_sha256"] = _sha(b"changed")
            fixture.plan[1]["resume_key"] = fixture.resume_key(fixture.plan[1])

        def aliased_case_digest(fixture: _SyntheticGate0Sources) -> None:
            first_digest = fixture.plan[0]["public_case_sha256"]
            for row in fixture.plan:
                if row["case_id"] == "case01":
                    row["public_case_sha256"] = first_digest
                    row["resume_key"] = fixture.resume_key(row)

        def changed_prompt(fixture: _SyntheticGate0Sources) -> None:
            fixture.plan[2]["prompt_sha256"] = _sha(b"changed-prompt")
            fixture.plan[2]["resume_key"] = fixture.resume_key(fixture.plan[2])

        for label, mutate in {
            "changed_case_digest": changed_case_digest,
            "aliased_case_digest": aliased_case_digest,
            "changed_repeat_prompt": changed_prompt,
        }.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                fixture = _SyntheticGate0Sources(Path(temp))
                mutate(fixture)
                with self.assertRaises(ValueError):
                    _build(fixture)

    def test_snapshot_parent_bindings_and_transaction_name_set_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            names = tuple(
                sorted(f"run_transactions/{row['resume_key']}.json" for row in fixture.plan)
            )
            wrong_names = (*names[:-1], "run_transactions/" + "f" * 64 + ".json")
            with self.assertRaises(ValueError):
                _build(fixture, transaction_names=wrong_names)

    def test_snapshot_outer_and_source_artifact_self_bindings_fail_closed(self) -> None:
        def missing_outer(fixture: _SyntheticGate0Sources) -> None:
            fixture.snapshot_receipt.pop("receipt_sha256")

        def bad_outer(fixture: _SyntheticGate0Sources) -> None:
            fixture.snapshot_receipt["receipt_sha256"] = "0" * 64

        def bad_file_set(fixture: _SyntheticGate0Sources) -> None:
            fixture.snapshot_receipt["source_artifact_receipt"][
                "file_set_sha256"
            ] = "0" * 64
            _rehash_record(fixture.snapshot_receipt)

        def bad_row_census(fixture: _SyntheticGate0Sources) -> None:
            fixture.snapshot_receipt["source_artifact_receipt"][
                "row_census_sha256"
            ] = "0" * 64
            _rehash_record(fixture.snapshot_receipt)

        def bad_artifact(fixture: _SyntheticGate0Sources) -> None:
            fixture.snapshot_receipt["source_artifact_receipt"][
                "artifact_sha256"
            ] = "0" * 64
            _rehash_record(fixture.snapshot_receipt)

        for label, mutate in {
            "missing_outer_receipt": missing_outer,
            "bad_outer_receipt": bad_outer,
            "bad_source_file_set": bad_file_set,
            "bad_source_row_census": bad_row_census,
            "bad_source_artifact": bad_artifact,
        }.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                fixture = _SyntheticGate0Sources(Path(temp))
                fixture.materialize()
                mutate(fixture)
                with self.assertRaises(ValueError):
                    _build(fixture, sync_snapshot_receipt=False)

    def test_artifact_receipt_nested_maps_and_three_hash_layers_are_strict(self) -> None:
        def bad_files(fixture: _SyntheticGate0Sources) -> None:
            fixture.artifact_receipt["files"]["extra.json"] = "e" * 64

        def bad_bindings(fixture: _SyntheticGate0Sources) -> None:
            fixture.artifact_receipt["bindings"].pop("vocabulary_sha256")

        def bad_file_hash(fixture: _SyntheticGate0Sources) -> None:
            fixture.artifact_receipt["file_set_sha256"] = "0" * 64

        def bad_census_hash(fixture: _SyntheticGate0Sources) -> None:
            fixture.artifact_receipt["row_census_sha256"] = "0" * 64

        def bad_artifact_hash(fixture: _SyntheticGate0Sources) -> None:
            fixture.artifact_receipt["artifact_sha256"] = "0" * 64

        for label, mutate in {
            "files": bad_files,
            "bindings": bad_bindings,
            "file_set_hash": bad_file_hash,
            "row_census_hash": bad_census_hash,
            "artifact_hash": bad_artifact_hash,
        }.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                fixture = _SyntheticGate0Sources(Path(temp))
                mutate(fixture)
                with self.assertRaises(ValueError):
                    _build(fixture, sync_artifact_receipt=False)

    def test_row_census_native_types_values_and_cross_counts_fail_closed(self) -> None:
        mutations = {
            "bool_prefixes": lambda f: f.row_census.__setitem__("prefixes", True),
            "wrong_trajectories": lambda f: f.row_census.__setitem__("trajectories", 449),
            "extra_key": lambda f: f.row_census.__setitem__("extra", 1),
            "wrong_sites": lambda f: f.row_census.__setitem__("sites", 6),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                fixture = _SyntheticGate0Sources(Path(temp))
                mutate(fixture)
                with self.assertRaises(ValueError):
                    _build(fixture)

    def test_only_six_authenticated_metadata_files_are_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            observed: list[Path] = []

            def observed_tree(root: str | Path, *, label: str) -> RealAuthenticatedTree:
                return RealAuthenticatedTree(
                    root,
                    label=label,
                    read_observer=observed.append,
                )

            with _patched_sources(fixture) as raw, patch(
                "iclr2027.obligation_inventory.AuthenticatedTree",
                side_effect=observed_tree,
            ):
                inventory = build_gate0_inventory(sources=raw)
        self.assertEqual(len(observed), 6)
        observed_text = tuple(path.as_posix() for path in observed)
        self.assertTrue(any(text.endswith("run_manifest.json") for text in observed_text))
        self.assertTrue(any(text.endswith("run_plan.json") for text in observed_text))
        self.assertFalse(any("run_transactions/" in text for text in observed_text))
        self.assertFalse(any(text.endswith(DATASET_FILES) for text in observed_text))
        self.assertEqual(inventory.access_audit["transaction_body_reads"], 0)
        self.assertEqual(inventory.access_audit["private_group_assignment_reads"], 0)
        self.assertEqual(inventory.access_audit["private_label_reads"], 0)
        self.assertEqual(inventory.access_audit["runtime_feature_reads"], 0)

    def test_row_identifiers_model_commit_and_nonaggregate_hashes_are_not_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = _SyntheticGate0Sources(Path(temp))
            forbidden = {
                fixture.plan[0]["case_id"],
                fixture.plan[0]["resume_key"],
                fixture.plan[0]["public_case_sha256"],
                fixture.plan[0]["prompt_sha256"],
                fixture.model,
                fixture.code_commit,
            }
            inventory = _build(fixture)
        serialized = gate0_inventory_file_bytes(inventory).decode("utf-8")
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, serialized)


class Gate0ScientificBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = _SyntheticGate0Sources(Path(self.temporary.name))
        self.inventory = _build(self.fixture)

    def test_branch_coverage_is_exact_zero_and_never_maps_historical_names(self) -> None:
        self.assertEqual(
            self.inventory.branch_coverage,
            {
                "required_actions": (
                    "STOP",
                    "SOLO_SYNTHESIS",
                    "ASK_LAW",
                    "ASK_PARKING",
                    "ASK_PROGRAM",
                    "ASK_GEOMETRY",
                ),
                "direct_terminal_cells": {
                    "STOP": 0,
                    "SOLO_SYNTHESIS": 0,
                    "ASK_LAW": 0,
                    "ASK_PARKING": 0,
                    "ASK_PROGRAM": 0,
                    "ASK_GEOMETRY": 0,
                },
                "identical_post_action_synthesis": False,
                "transition_stitching_permitted": False,
                "historical_topologies_are_oacs_actions": False,
            },
        )

    def test_safe_projection_is_absent_and_split_gaps_use_only_site_case_units(self) -> None:
        preserved = self.inventory.development_inventory["preserved_development_gate"]
        self.assertEqual(preserved["state"], "safe_projection_not_declared_in_v1")
        self.assertIsNone(preserved["site_count"])
        split = self.inventory.split_readiness
        self.assertEqual(split["available_sites"], 5)
        self.assertEqual(split["available_cases"], 30)
        self.assertEqual(split["site_gap"], 3)
        self.assertEqual(split["minimum_primary_unit_gap"], 34)
        self.assertIsNone(split["verified_eligible_primary_units"])
        self.assertIsNone(split["verified_primary_unit_gap"])
        self.assertFalse(self.inventory.development_inventory["prefixes_are_independent"])
        self.assertFalse(
            self.inventory.development_inventory["repeated_trajectories_are_independent"]
        )

    def test_future_mechanism_evidence_and_reserved_positive_status_are_rejected(self) -> None:
        mechanism = self.inventory.mechanism_readiness
        self.assertEqual(mechanism["status"], "not_measured")
        self.assertFalse(mechanism["residual_label_receipt_available"])
        self.assertFalse(mechanism["blind_label_metrics_available"])
        self.assertFalse(mechanism["capability_audit_outcome_receipt_available"])
        payload = self.inventory.to_dict()
        payload["status"] = "collection_prerequisites_met"
        payload["acceptance_passed"] = True
        payload["blockers"] = []
        payload["future_projection_path"] = "unsupported"
        _rehash_record(payload)
        with self.assertRaises(ValueError):
            Gate0Inventory.from_dict(payload)

    def test_call_budgets_are_derived_and_baselines_remain_separate(self) -> None:
        budget = self.inventory.call_budget
        self.assertEqual(budget["factored_terminal_records_for_64_units"], 16 * 64)
        self.assertEqual(budget["factored_base_calls_for_64_units"], 27 * 64)
        self.assertEqual(budget["factorial_terminal_records_for_64_units"], 144 * 64)
        self.assertEqual(budget["factorial_base_calls_for_64_units"], 216 * 64)
        self.assertEqual(budget["gate0_model_calls"], 0)
        self.assertEqual(budget["current_authorized_calls"], 0)
        self.assertFalse(self.inventory.execution_readiness["reuse_1728_eligible"])
        self.assertEqual(
            set(self.inventory.baseline_readiness),
            {
                "cost_aware_routing",
                "rirs",
                "vmao",
                "verimap",
                "equal_information_raw_router",
                "separated_router_stopper",
                "all_specialists",
                "solo",
            },
        )
        self.assertEqual(set(self.inventory.baseline_readiness.values()), {"specification_missing"})
        self.assertEqual(
            self.inventory.historical_reference,
            {"fixed_topologies": "historical_reference_only"},
        )


class Gate0ImmutableSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = _SyntheticGate0Sources(Path(self.temporary.name))
        self.inventory = _build(self.fixture)

    def test_records_have_exact_fields_and_recursively_immutable_values(self) -> None:
        self.assertEqual(tuple(field.name for field in dataclasses.fields(Gate0Inventory)), INVENTORY_FIELDS)
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(Gate0PublicationReceipt)),
            PUBLICATION_FIELDS,
        )
        self.assertIsInstance(self.inventory.source_files, MappingProxyType)
        self.assertIsInstance(self.inventory.development_inventory, MappingProxyType)
        self.assertIsInstance(
            self.inventory.development_inventory["full_frozen_development"],
            MappingProxyType,
        )
        self.assertIsInstance(self.inventory.blockers, tuple)
        with self.assertRaises(TypeError):
            self.inventory.source_files["snapshot_receipt"] = "0" * 64  # type: ignore[index]
        with self.assertRaises(TypeError):
            self.inventory.development_inventory["full_frozen_development"]["site_count"] = 6  # type: ignore[index]
        payload = self.inventory.to_dict()
        round_trip = Gate0Inventory.from_dict(payload)
        payload["source_files"]["snapshot_receipt"] = "0" * 64
        self.assertNotEqual(round_trip.source_files["snapshot_receipt"], "0" * 64)

    def test_from_dict_recomputes_all_derived_fields_not_only_self_hash(self) -> None:
        payload = self.inventory.to_dict()
        payload["development_inventory"]["full_frozen_development"]["site_count"] = 6
        payload["split_readiness"]["available_sites"] = 6
        payload["split_readiness"]["site_gap"] = 2
        _rehash_record(payload)
        with self.assertRaises(ValueError):
            Gate0Inventory.from_dict(payload)

    def test_direct_constructor_requires_exact_status_enum(self) -> None:
        self.assertIs(type(self.inventory.status), Gate0Status)
        with self.assertRaises(TypeError):
            dataclasses.replace(
                self.inventory,
                status=Gate0Status.DATA_COLLECTION_REQUIRED.value,
            )

    def test_exact_nested_keys_native_types_blocker_order_and_hashes_are_required(self) -> None:
        mutations = {
            "extra_source": lambda p: p["source_files"].__setitem__("claim_availability", "0" * 64),
            "bool_counter": lambda p: p["access_audit"].__setitem__("model_calls", False),
            "reordered_blockers": lambda p: p.__setitem__("blockers", list(reversed(p["blockers"]))),
            "extra_nested": lambda p: p["split_readiness"].__setitem__("extra", 0),
            "wrong_budget_total": lambda p: p["call_budget"].__setitem__("factorial_base_calls_for_64_units", 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = self.inventory.to_dict()
                mutate(payload)
                _rehash_record(payload)
                with self.assertRaises(ValueError):
                    Gate0Inventory.from_dict(payload)


class Gate0PublicationTests(unittest.TestCase):
    def _inventory(self, root: Path, nonce: str) -> Gate0Inventory:
        return _build(_SyntheticGate0Sources(root, development_nonce=nonce))

    def test_publication_ast_has_no_path_based_post_preflight_mutation(self) -> None:
        source = ast.parse(
            (Path(__file__).parents[1] / "iclr2027/obligation_inventory.py").read_text(
                encoding="utf-8"
            )
        )
        forbidden_methods = {"rename", "touch", "unlink", "write_bytes", "write_text"}
        for node in ast.walk(source):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr in forbidden_methods and not (
                isinstance(node.func.value, ast.Name) and node.func.value.id == "os"
            ):
                self.fail(f"path-based publication mutation: {ast.unparse(node.func)}")
            if node.func.attr == "replace" and not (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id in {"directory", "os", "self"}
            ):
                self.fail(f"path-based publication replacement: {ast.unparse(node.func)}")
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                keyword_names = {keyword.arg for keyword in node.keywords}
                if node.func.attr == "replace":
                    self.assertGreaterEqual(
                        keyword_names, {"src_dir_fd", "dst_dir_fd"}
                    )
                if node.func.attr == "unlink":
                    self.assertIn("dir_fd", keyword_names)

    def test_posix_capability_check_uses_rename_membership_not_replace(self) -> None:
        dir_fd_support = {os.mkdir, os.open, os.rename, os.stat, os.unlink}
        dir_fd_support.discard(os.replace)
        self.assertTrue(
            obligation_inventory_module._posix_publication_capabilities_available(
                dir_fd_support=dir_fd_support,
                fd_support={os.listdir},
                follow_symlinks_support={os.stat},
            )
        )

    def test_publication_round_trip_and_internal_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = self._inventory(root / "source", "first")
            output = root / "out"
            receipt_path = publish_gate0_inventory(inventory, output_dir=output)
            inventory_path = output / "stage0_inventory.json"
            expected = _sha(receipt_path.read_bytes())
            self.assertEqual(
                verify_gate0_publication(
                    inventory_path,
                    receipt_path,
                    expected_receipt_file_sha256=expected,
                ).to_dict(),
                inventory.to_dict(),
            )
            receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_payload["source_files_sha256"] = "0" * 64
            _rehash_record(receipt_payload)
            receipt_path.write_bytes(_json_file(receipt_payload))
            with self.assertRaises(ValueError):
                verify_gate0_publication(
                    inventory_path,
                    receipt_path,
                    expected_receipt_file_sha256=_sha(receipt_path.read_bytes()),
                )

    def test_cli_rejects_post_return_namespace_swap_with_prepublication_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "results").mkdir()
            expected_inventory = self._inventory(root / "source-expected", "expected")
            forged_inventory = self._inventory(root / "source-forged", "forged")

            def publish_then_swap(
                inventory: Gate0Inventory, *, output_dir: Path
            ) -> Path:
                receipt_path = publish_gate0_inventory(inventory, output_dir=output_dir)
                authenticated = output_dir.with_name(output_dir.name + ".authenticated")
                os.replace(output_dir, authenticated)
                publish_gate0_inventory(forged_inventory, output_dir=output_dir)
                return receipt_path

            with patch.object(audit_cli, "__file__", str(root / "audit.py")), patch.object(
                audit_cli,
                "build_gate0_inventory",
                return_value=expected_inventory,
            ), patch.object(
                audit_cli,
                "publish_gate0_inventory",
                side_effect=publish_then_swap,
            ):
                with self.assertRaisesRegex(ValueError, "receipt file hash mismatch"):
                    audit_cli.main(["--mode", "source"])

    def test_stale_prior_pair_is_rejected_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            first = self._inventory(root / "source-first", "first")
            stale = self._inventory(root / "source-stale", "stale")
            replacement = self._inventory(root / "source-replacement", "replacement")
            receipt_path = publish_gate0_inventory(first, output_dir=output)
            inventory_path = output / "stage0_inventory.json"
            inventory_path.write_bytes(gate0_inventory_file_bytes(stale))
            stale_pair = (inventory_path.read_bytes(), receipt_path.read_bytes())

            with self.assertRaises(ValueError):
                publish_gate0_inventory(replacement, output_dir=output)

            self.assertEqual(
                (inventory_path.read_bytes(), receipt_path.read_bytes()), stale_pair
            )
            self.assertFalse(
                any(name.startswith(".") for name in os.listdir(output))
            )

    def test_temporary_leaf_move_or_replacement_leaves_no_residue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            inventory = self._inventory(root / "source", "first")
            moved = output / "attacker-moved-temporary.bin"
            attack_succeeded = False

            def move_inventory_temporary(phase: str) -> None:
                nonlocal attack_succeeded
                if phase != "replace_inventory":
                    return
                candidates = tuple(output.glob(".stage0_inventory.json.*.tmp"))
                self.assertEqual(len(candidates), 1)
                try:
                    os.replace(candidates[0], moved)
                except PermissionError:
                    return
                candidates[0].write_bytes(b"attacker replacement")
                attack_succeeded = True

            with patch(
                "iclr2027.obligation_inventory._publication_phase_hook",
                side_effect=move_inventory_temporary,
            ):
                if os.name == "nt":
                    try:
                        publish_gate0_inventory(inventory, output_dir=output)
                    except (OSError, ValueError):
                        pass
                else:
                    with self.assertRaises((OSError, ValueError)):
                        publish_gate0_inventory(inventory, output_dir=output)

            if not attack_succeeded:
                self.assertTrue((output / "stage0_inventory.json").exists())
                return
            self.assertFalse(moved.exists())
            self.assertFalse((output / "stage0_inventory.json").exists())
            self.assertFalse((output / "stage0_inventory.receipt.json").exists())
            self.assertFalse(
                any(
                    name.startswith(".") or name.endswith((".tmp", ".bak"))
                    for name in os.listdir(output)
                )
            )

    def test_no_prior_pair_rollback_quarantines_either_transient_delete_failure(self) -> None:
        for failed_name in (
            "stage0_inventory.receipt.json",
            "stage0_inventory.json",
        ):
            with self.subTest(failed_name=failed_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "out"
                inventory = self._inventory(root / "source", "first")
                original_delete = obligation_inventory_module._PublicationDirectory._delete_relative
                failed = False

                def fail_one_delete(
                    directory: object, name: str, *, detached: bool
                ) -> None:
                    nonlocal failed
                    if name == failed_name and not failed:
                        failed = True
                        raise OSError(f"synthetic delete failure: {failed_name}")
                    original_delete(
                        directory,  # type: ignore[arg-type]
                        name,
                        detached=detached,
                    )

                def fail_verification(phase: str) -> None:
                    if phase == "verify_inventory":
                        raise OSError("synthetic post-commit verification failure")

                with patch(
                    "iclr2027.obligation_inventory._publication_phase_hook",
                    side_effect=fail_verification,
                ), patch.object(
                    obligation_inventory_module._PublicationDirectory,
                    "_delete_relative",
                    new=fail_one_delete,
                ):
                    with self.assertRaisesRegex(
                        OSError, "synthetic post-commit verification failure"
                    ):
                        publish_gate0_inventory(inventory, output_dir=output)

                self.assertTrue(failed)
                self.assertFalse((output / "stage0_inventory.json").exists())
                self.assertFalse(
                    (output / "stage0_inventory.receipt.json").exists()
                )
                self.assertEqual(os.listdir(output), [])

    def test_second_step_rollback_failure_quarantines_mixed_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            first = self._inventory(root / "source-first", "first")
            second = self._inventory(root / "source-second", "second")
            publish_gate0_inventory(first, output_dir=output)
            original_replace = obligation_inventory_module._PublicationDirectory.replace

            def fail_restore_receipt(
                directory: object,
                temporary: object,
                final_name: str,
                *,
                phase: str | None,
                detached: bool = False,
            ) -> None:
                if detached and final_name == "stage0_inventory.receipt.json":
                    raise OSError("synthetic second-step rollback failure")
                original_replace(
                    directory,  # type: ignore[arg-type]
                    temporary,  # type: ignore[arg-type]
                    final_name,
                    phase=phase,
                    detached=detached,
                )

            def fail_verification(phase: str) -> None:
                if phase == "verify_inventory":
                    raise OSError("synthetic post-commit verification failure")

            with patch(
                "iclr2027.obligation_inventory._publication_phase_hook",
                side_effect=fail_verification,
            ), patch.object(
                obligation_inventory_module._PublicationDirectory,
                "replace",
                new=fail_restore_receipt,
            ):
                with self.assertRaisesRegex(
                    OSError, "synthetic post-commit verification failure"
                ) as caught:
                    publish_gate0_inventory(second, output_dir=output)

            self.assertIsNotNone(caught.exception.__cause__)
            self.assertIn(
                "synthetic second-step rollback failure",
                str(caught.exception.__cause__),
            )

            self.assertFalse((output / "stage0_inventory.json").exists())
            self.assertFalse((output / "stage0_inventory.receipt.json").exists())
            self.assertFalse(
                any(
                    name.startswith(".") or name.endswith((".tmp", ".bak"))
                    for name in os.listdir(output)
                )
            )

    def test_newline_fixed_sibling_and_hardlink_attacks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = self._inventory(root / "source", "first")
            output = root / "out"
            receipt_path = publish_gate0_inventory(inventory, output_dir=output)
            inventory_path = output / "stage0_inventory.json"
            expected = _sha(receipt_path.read_bytes())
            inventory_path.write_bytes(inventory_path.read_bytes().rstrip(b"\n"))
            with self.assertRaises(ValueError):
                verify_gate0_publication(
                    inventory_path,
                    receipt_path,
                    expected_receipt_file_sha256=expected,
                )
            inventory_path.unlink()
            receipt_path.unlink()
            publish_gate0_inventory(inventory, output_dir=output)
            wrong_name = output / "redirected_inventory.json"
            wrong_name.write_bytes(inventory_path.read_bytes())
            with self.assertRaises(ValueError):
                verify_gate0_publication(
                    wrong_name,
                    receipt_path,
                    expected_receipt_file_sha256=_sha(receipt_path.read_bytes()),
                )
            hardlink = output / "inventory-hardlink.json"
            try:
                os.link(inventory_path, hardlink)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            with self.assertRaises(ValueError):
                verify_gate0_publication(
                    inventory_path,
                    receipt_path,
                    expected_receipt_file_sha256=_sha(receipt_path.read_bytes()),
                )

    def test_receipt_is_replaced_last(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = self._inventory(root / "source", "first")
            output = root / "out"
            phases: list[str] = []
            with patch(
                "iclr2027.obligation_inventory._publication_phase_hook",
                side_effect=phases.append,
            ):
                publish_gate0_inventory(inventory, output_dir=output)
        self.assertEqual(
            [phase for phase in phases if phase.startswith("replace_")],
            ["replace_inventory", "replace_receipt"],
        )

    def test_caught_receipt_replace_failure_restores_verified_prior_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            first = self._inventory(root / "source-first", "first")
            second = self._inventory(root / "source-second", "second")
            receipt_path = publish_gate0_inventory(first, output_dir=output)
            inventory_path = output / "stage0_inventory.json"
            prior_inventory = inventory_path.read_bytes()
            prior_receipt = receipt_path.read_bytes()
            failed = False

            def fail_new_receipt_once(phase: str) -> None:
                nonlocal failed
                if phase == "replace_receipt" and not failed:
                    failed = True
                    raise OSError("synthetic receipt replacement failure")

            with patch(
                "iclr2027.obligation_inventory._publication_phase_hook",
                side_effect=fail_new_receipt_once,
            ):
                with self.assertRaises(OSError):
                    publish_gate0_inventory(second, output_dir=output)
            self.assertEqual(inventory_path.read_bytes(), prior_inventory)
            self.assertEqual(receipt_path.read_bytes(), prior_receipt)
            verify_gate0_publication(
                inventory_path,
                receipt_path,
                expected_receipt_file_sha256=_sha(prior_receipt),
            )

    def test_real_output_and_parent_swaps_fail_closed_at_every_publication_phase(self) -> None:
        for kind in ("output", "parent"):
            for phase in _PUBLICATION_PHASES:
                with self.subTest(kind=kind, phase=phase), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    inventory = self._inventory(root / "source", "first")
                    output = root / "publication" / "out"
                    output.mkdir(parents=True)
                    attack = _DirectorySwapAttack(root, output, kind=kind, phase=phase)
                    try:
                        with patch(
                            "iclr2027.obligation_inventory._publication_phase_hook",
                            side_effect=attack.hook,
                            create=True,
                        ):
                            caught: BaseException | None = None
                            try:
                                publish_gate0_inventory(inventory, output_dir=output)
                            except (OSError, ValueError) as error:
                                caught = error
                        self.assertEqual(attack.rename_attempt_count, 1)
                        if os.name == "nt" and attack.blocked_by_retained_handle:
                            self.assertIsNone(caught)
                            self.assertTrue(attack.blocked_by_retained_handle)
                            self.assertEqual(attack.rename_count, 0)
                        else:
                            self.assertIsNotNone(caught)
                            self.assertEqual(attack.rename_count, 1)
                            self.assertEqual(
                                _directory_snapshot(attack.authenticated_output), {}
                            )
                        attack.assert_outside_untouched(self)
                    finally:
                        attack.restore_namespace()

    def test_missing_output_creation_is_parent_handle_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = self._inventory(root / "source", "first")
            output = root / "publication" / "out"
            output.parent.mkdir()
            attack = _DirectorySwapAttack(
                root,
                output,
                kind="parent",
                phase="create_output_directory",
            )
            try:
                with patch(
                    "iclr2027.obligation_inventory._publication_phase_hook",
                    side_effect=attack.hook,
                ):
                    with self.assertRaises((OSError, ValueError)):
                        publish_gate0_inventory(inventory, output_dir=output)
                self.assertEqual(attack.rename_attempt_count, 1)
                self.assertEqual(attack.rename_count, 1)
                self.assertFalse((attack.authenticated_path / output.name).exists())
                attack.assert_outside_untouched(self)
            finally:
                attack.restore_namespace()

    def test_rollback_after_real_output_or_parent_swap_restores_through_handle(self) -> None:
        for kind in ("output", "parent"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "publication" / "out"
                output.parent.mkdir()
                first = self._inventory(root / "source-first", "first")
                second = self._inventory(root / "source-second", "second")
                receipt_path = publish_gate0_inventory(first, output_dir=output)
                inventory_path = output / "stage0_inventory.json"
                prior_inventory = inventory_path.read_bytes()
                prior_receipt = receipt_path.read_bytes()
                attack = _DirectorySwapAttack(root, output, kind=kind, phase="rollback")

                def fail_then_swap(phase: str) -> None:
                    if phase == "replace_receipt":
                        raise OSError("force rollback before receipt commit")
                    attack.hook(phase)

                try:
                    with patch(
                        "iclr2027.obligation_inventory._publication_phase_hook",
                        side_effect=fail_then_swap,
                        create=True,
                    ):
                        with self.assertRaisesRegex(
                            OSError, "force rollback before receipt commit"
                        ):
                            publish_gate0_inventory(second, output_dir=output)
                    self.assertEqual(attack.rename_attempt_count, 1)
                    if os.name == "nt" and attack.blocked_by_retained_handle:
                        self.assertTrue(attack.blocked_by_retained_handle)
                        self.assertEqual(attack.rename_count, 0)
                    else:
                        self.assertEqual(attack.rename_count, 1)
                    self.assertEqual(
                        (
                            (attack.secured_output() / "stage0_inventory.json").read_bytes(),
                            (
                                attack.secured_output()
                                / "stage0_inventory.receipt.json"
                            ).read_bytes(),
                        ),
                        (prior_inventory, prior_receipt),
                    )
                    attack.assert_outside_untouched(self)
                finally:
                    attack.restore_namespace()
                verify_gate0_publication(
                    inventory_path,
                    receipt_path,
                    expected_receipt_file_sha256=_sha(prior_receipt),
                )

    def test_authentication_error_publishes_nothing_and_preserves_prior_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = _SyntheticGate0Sources(root / "source")
            inventory = _build(fixture)
            output = root / "out"
            receipt_path = publish_gate0_inventory(inventory, output_dir=output)
            inventory_path = output / "stage0_inventory.json"
            prior = (inventory_path.read_bytes(), receipt_path.read_bytes())
            specs, raw = fixture.materialize()
            bad_specs = (
                Gate0TopSourceSpec(
                    specs[0].logical_name,
                    specs[0].relative_path,
                    "0" * 64,
                    specs[0].declared_members,
                ),
                *specs[1:],
            )
            with patch.object(gate0_sources, "GATE0_TOP_SOURCES", bad_specs), patch(
                "iclr2027.obligation_inventory._SOURCE_ROOT", fixture.root
            ):
                with self.assertRaises(ValueError):
                    build_gate0_inventory(sources=raw)
            self.assertEqual(
                (inventory_path.read_bytes(), receipt_path.read_bytes()),
                prior,
            )


if __name__ == "__main__":
    unittest.main()
