from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

import iclr2027.method_lock as method_lock_module
from iclr2027.io import canonical_json, sha256_json
from iclr2027.method_lock import (
    METHOD_LOCK_SCHEMA,
    SYNTHETIC_SCOPE,
    build_method_lock,
    build_method_lock_from_sources,
    candidate_file_bytes,
    render_execution_memory_continuation,
    require_positive_method_lock,
    verify_method_lock_candidate,
)
from iclr2027.policy_replay import POLICY_PARAMETERS, POLICY_REGISTRY
from iclr2027.study_contract import StudyContract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parents[1]
SDD_ROOT = (
    WORKSPACE_ROOT
    / ".superpowers/sdd/2026-08-19-iclr2027-development-snapshot-cats-gate"
)
REAL_SOURCES = {
    "design_receipt": WORKSPACE_ROOT
    / "docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.receipt.json",
    "snapshot": PROJECT_ROOT
    / "results/exp09_cats/development_snapshot/snapshot_receipt.json",
    "pilot_gate": PROJECT_ROOT
    / "results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json",
    "dataset": PROJECT_ROOT / "results/exp09_cats/dataset/feature_manifest.json",
    "models": PROJECT_ROOT / "results/exp09_cats/models/model_registry.json",
    "replay": PROJECT_ROOT
    / "results/exp09_cats/replay/development/development_gate.json",
}
MEMORY_BASELINE = (
    SDD_ROOT / "baselines/task-7/ICLR_2027_EXECUTION_MEMORY_2026-08-19.md"
)
AUTHORITATIVE_MEMORY = PROJECT_ROOT / "ICLR_2027_EXECUTION_MEMORY_2026-08-19.md"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _synthetic_closure() -> dict[str, object]:
    variants = [
        {
            "alpha": 0.1,
            "epsilon": 0.02,
            "family": "histgb",
            "name": f"synthetic-{index}",
            "q_alpha": 0.1 * index,
            "semantic_sha256": _digest(f"semantic-{index}"),
        }
        for index in range(6)
    ]
    return {
        "scope": SYNTHETIC_SCOPE,
        "design_receipt": {
            "document": "synthetic-design.md",
            "document_bytes": 17,
            "document_sha256": _digest("design-document"),
            "effective_date": "2026-08-19",
            "receipt_file_sha256": _digest("design-receipt"),
            "schema_version": "ace.iclr2027.design_receipt.v1",
            "status": "approved_prospective_amendment",
            "timing_disclosure": "synthetic_logic_only",
        },
        "scientific_identity": {
            "code_runtime_identity": "synthetic-runtime-identity",
            "run_plan_sha256": _digest("run-plan"),
            "transaction_set_sha256": _digest("transactions"),
        },
        "study_contract": asdict(StudyContract.primary()),
        "source_files": {
            name: _digest(name)
            for name in (
                "dataset_manifest",
                "design_document",
                "design_receipt",
                "development_gate",
                "model_registry",
                "pilot_gate",
                "snapshot_receipt",
            )
        },
        "dependency_receipts": {
            "dataset_artifact_sha256": _digest("dataset-artifact"),
            "model_semantic_determinism_receipt_sha256": _digest(
                "model-determinism"
            ),
            "snapshot_source_artifact_sha256": _digest("snapshot-source"),
        },
        "dataset": {
            "artifact_files": 3,
            "prefix_partition_counts": {
                "calibration": 1,
                "development_gate": 2,
                "train": 3,
            },
            "row_census": {
                "assignments": 6,
                "prefixes": 6,
                "private_labels": 6,
                "runtime_features": 6,
                "sites": 5,
                "trajectories": 6,
            },
            "site_partition_counts": {
                "calibration": 1,
                "development_gate": 2,
                "train": 2,
            },
            "trajectory_partition_counts": {
                "calibration": 1,
                "development_gate": 2,
                "train": 3,
            },
            "vocabulary_sha256": _digest("vocabulary"),
            "vocabulary_size": 9,
        },
        "models": {
            "artifact_count": 24,
            "semantic_comparisons_passed": 48,
            "semantic_comparisons_total": 48,
            "variant_count": 6,
            "variants": variants,
        },
        "replay": {
            "bootstrap": {
                "draws": 10_000,
                "resampling_unit": "site_ref",
                "seed": 20260819,
                "site_count": 2,
            },
            "lexical_collision": {
                "algorithmically_distinct": True,
                "empirically_identical_to_max_cap": False,
                "matching_stop_turns": 0,
                "trajectory_count": 2,
            },
            "policy_parameters": dict(POLICY_PARAMETERS),
            "policy_registry": list(POLICY_REGISTRY),
            "receipt_sha256": _digest("replay-receipt"),
            "replay_rows_sha256": _digest("replay-rows"),
            "row_census": {
                "development_gate_sites": 2,
                "policies": 11,
                "replay_rows": 22,
                "trajectories": 2,
            },
            "state_conformal": {
                "adapted_after_development_outcomes": False,
                "q_alpha": 0.25,
                "source_partition": "calibration",
            },
        },
        "implementation_closure": {
            "synthetic_helper.py": _digest("synthetic-helper")
        },
        "execution_memory": {
            "baseline_sha256": _digest("synthetic-memory-baseline"),
            "continuation_schema": "ace.iclr2027.execution_memory_continuation.v1",
            "path": "synthetic-memory.md",
        },
        "usage_claims": {
            "invoice_grade_cost": False,
            "reasons": ["synthetic_usage_incomplete"],
            "total_compute": False,
            "visible_agent_token_boundary": "synthetic visible-agent boundary",
            "visible_agent_tokens": True,
        },
        "access_audit": {
            "held_out_bundle_reads": 0,
            "llm_calls": 0,
            "model_refits": 0,
            "transformer_refits": 0,
        },
    }


def _pilot_gate(passed: bool) -> dict[str, object]:
    return {
        "passed": passed,
        "checks": {
            "pilot_complete": True,
            "performance_threshold": passed,
        },
    }


def _development_gate(passed: bool) -> dict[str, object]:
    return {
        "passed": passed,
        "failures": [] if passed else ["development_metric"],
        "receipt_sha256": _digest(
            "synthetic-development-gate-positive"
            if passed
            else "synthetic-development-gate-negative"
        ),
        "checks": {
            "development_metric": {
                "observed": 1 if passed else 0,
                "operator": "==",
                "passed": passed,
                "threshold": 1,
            }
        },
    }


def _rehash(candidate: dict[str, object]) -> dict[str, object]:
    payload = {key: value for key, value in candidate.items() if key != "receipt_sha256"}
    candidate["receipt_sha256"] = sha256_json(payload)
    return candidate


def _write_candidate(root: Path, candidate: dict[str, object], name: str) -> Path:
    path = root / name / "method_lock_candidate.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(candidate_file_bytes(candidate))
    return path


def _write_unvalidated_candidate(
    root: Path, candidate: dict[str, object], name: str
) -> Path:
    path = root / name / "method_lock_candidate.json"
    path.parent.mkdir(parents=True)
    path.write_bytes((canonical_json(candidate) + "\n").encode("utf-8"))
    return path


def _isolated_development_sources(
    destination: Path,
    *,
    implementation_names: object,
) -> tuple[dict[str, Path], Path]:
    """Copy only the exact declared development closure; never discover a tree."""

    project = destination / "AG/AG-Research"
    sources = {
        "design_receipt": destination
        / "docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.receipt.json",
        "snapshot": project
        / "results/exp09_cats/development_snapshot/snapshot_receipt.json",
        "pilot_gate": project
        / "results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json",
        "dataset": project / "results/exp09_cats/dataset/feature_manifest.json",
        "models": project / "results/exp09_cats/models/model_registry.json",
        "replay": project
        / "results/exp09_cats/replay/development/development_gate.json",
    }

    def copy(source: Path, target: Path) -> bytes:
        artifact = source.read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(artifact)
        return artifact

    design_bytes = copy(REAL_SOURCES["design_receipt"], sources["design_receipt"])
    design = json.loads(design_bytes.decode("utf-8"))
    copy(
        REAL_SOURCES["design_receipt"].parent / design["document"],
        sources["design_receipt"].parent / design["document"],
    )
    snapshot_bytes = copy(REAL_SOURCES["snapshot"], sources["snapshot"])
    snapshot = json.loads(snapshot_bytes.decode("utf-8"))
    real_pilot = REAL_SOURCES["pilot_gate"].parent
    isolated_pilot = sources["pilot_gate"].parent
    for name in sorted(snapshot["source_artifact_receipt"]["files"]):
        copy(real_pilot / name, isolated_pilot / name)
    copy(real_pilot / "pilot_summary.json", isolated_pilot / "pilot_summary.json")

    dataset_bytes = copy(REAL_SOURCES["dataset"], sources["dataset"])
    dataset = json.loads(dataset_bytes.decode("utf-8"))
    real_dataset = REAL_SOURCES["dataset"].parent
    isolated_dataset = sources["dataset"].parent
    for name in sorted(dataset["artifact_receipt"]["files"]):
        copy(real_dataset / name, isolated_dataset / name)
    for name in ("usage/claim_availability.json", "usage/usage_events.jsonl"):
        copy(real_dataset / name, isolated_dataset / name)

    registry_bytes = copy(REAL_SOURCES["models"], sources["models"])
    registry = json.loads(registry_bytes.decode("utf-8"))
    real_models = REAL_SOURCES["models"].parent
    isolated_models = sources["models"].parent
    copy(real_models / "registry.json", isolated_models / "registry.json")
    copy(
        real_models / "semantic_determinism.json",
        isolated_models / "semantic_determinism.json",
    )
    for variant in registry["variants"]:
        for filename in (
            "classifier.joblib",
            "manifest.json",
            "predictions.jsonl",
            "transformer.joblib",
        ):
            relative = Path(variant["path"]) / filename
            copy(real_models / relative, isolated_models / relative)

    real_replay = REAL_SOURCES["replay"].parent
    isolated_replay = sources["replay"].parent
    copy(REAL_SOURCES["replay"], sources["replay"])
    copy(real_replay / "replay_rows.jsonl", isolated_replay / "replay_rows.jsonl")
    if not isinstance(implementation_names, Mapping):
        raise TypeError("implementation closure must be a mapping")
    for name in sorted(implementation_names):
        copy(PROJECT_ROOT / str(name), project / str(name))
    return sources, project


class MethodLockLogicTests(unittest.TestCase):
    def test_negative_pilot_gate_cannot_emit_positive_method_lock(self) -> None:
        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(False),
            development_gate=_development_gate(True),
        )
        self.assertFalse(candidate["held_out_access_allowed"])
        self.assertEqual(candidate["blockers"], ["pilot_gate_failed"])
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-negative-") as temporary:
            path = _write_candidate(Path(temporary), candidate, "negative")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(PermissionError):
                require_positive_method_lock(
                    path,
                    expected_candidate_file_sha256=digest,
                )

    def test_negative_development_gate_adds_exact_second_blocker(self) -> None:
        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(False),
            development_gate=_development_gate(False),
        )
        self.assertEqual(
            candidate["blockers"],
            ["development_gate_failed", "pilot_gate_failed"],
        )
        self.assertEqual(
            candidate["pilot_gate"]["failed_checks"], ["performance_threshold"]
        )
        self.assertEqual(
            candidate["development_gate"]["failed_checks"],
            ["development_metric"],
        )

    def test_complete_synthetic_positive_fixture_is_logical_only(self) -> None:
        from iclr2027.method_lock import validate_logical_method_lock

        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(True),
            development_gate=_development_gate(True),
        )
        self.assertFalse(candidate["held_out_access_allowed"])
        self.assertEqual(candidate["status"], "logical_positive")
        self.assertTrue(validate_logical_method_lock(candidate))
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-positive-") as temporary:
            path = _write_candidate(Path(temporary), candidate, "positive")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(PermissionError, "non-real|synthetic"):
                require_positive_method_lock(
                    path,
                    expected_candidate_file_sha256=digest,
                )

    def test_downstream_no_exception_shortcut_cannot_authorize_synthetic(self) -> None:
        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(True),
            development_gate=_development_gate(True),
        )
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-downstream-") as temporary:
            path = _write_candidate(Path(temporary), candidate, "positive")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()

            def downstream_guard() -> bool:
                require_positive_method_lock(
                    path,
                    expected_candidate_file_sha256=digest,
                )
                return True

            with self.assertRaises(PermissionError):
                downstream_guard()
        self.assertFalse(candidate["held_out_access_allowed"])

    def test_forged_true_flag_and_removed_blockers_fail_after_rehash(self) -> None:
        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(False),
            development_gate=_development_gate(False),
        )
        candidate["held_out_access_allowed"] = True
        candidate["blockers"] = []
        _rehash(candidate)
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-forged-") as temporary:
            path = _write_unvalidated_candidate(Path(temporary), candidate, "forged")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises((PermissionError, ValueError)):
                require_positive_method_lock(
                    path,
                    expected_candidate_file_sha256=digest,
                )

    def test_missing_design_receipt_fails_after_rehash(self) -> None:
        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(True),
            development_gate=_development_gate(True),
        )
        del candidate["design_receipt"]
        _rehash(candidate)
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-missing-") as temporary:
            path = _write_unvalidated_candidate(Path(temporary), candidate, "missing")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "candidate fields"):
                verify_method_lock_candidate(
                    path,
                    expected_candidate_file_sha256=digest,
                )

    def test_candidate_bytes_are_canonical_and_deterministic(self) -> None:
        candidate = build_method_lock(
            _synthetic_closure(),
            pilot_gate=_pilot_gate(False),
            development_gate=_development_gate(False),
        )
        first = candidate_file_bytes(candidate)
        second = candidate_file_bytes(deepcopy(candidate))
        self.assertEqual(first, second)
        self.assertEqual(first, (canonical_json(candidate) + "\n").encode("utf-8"))

    def test_source_api_has_only_declared_development_receipt_inputs(self) -> None:
        parameters = set(inspect.signature(build_method_lock_from_sources).parameters)
        self.assertEqual(
            parameters,
            {
                "dataset",
                "design_receipt",
                "models",
                "pilot_gate",
                "replay",
                "snapshot",
            },
        )


class MethodLockRealClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="ace-method-lock-real-")
        cls.root = Path(cls.temporary.name)
        cls.candidate = build_method_lock_from_sources(**REAL_SOURCES)
        cls.candidate_path = _write_candidate(cls.root, cls.candidate, "real")
        baseline = MEMORY_BASELINE.read_bytes()
        cls.memory_path = cls.root / "ICLR_2027_EXECUTION_MEMORY_2026-08-19.md"
        cls.memory_path.write_bytes(
            baseline + render_execution_memory_continuation(cls.candidate)
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def _attacked_path(self, label: str, mutate) -> Path:
        candidate = deepcopy(self.candidate)
        mutate(candidate)
        _rehash(candidate)
        path = self.root / label / "method_lock_candidate.json"
        path.parent.mkdir(parents=True)
        path.write_bytes((canonical_json(candidate) + "\n").encode("utf-8"))
        return path

    def test_real_source_verification_recomputes_complete_closure(self) -> None:
        verified = verify_method_lock_candidate(
            self.candidate_path,
            **REAL_SOURCES,
            execution_memory=AUTHORITATIVE_MEMORY,
        )
        self.assertEqual(verified["schema_version"], METHOD_LOCK_SCHEMA)
        self.assertEqual(
            verified["blockers"],
            ["development_gate_failed", "pilot_gate_failed"],
        )

    def test_real_source_reconstruction_never_reopens_authenticated_paths(
        self,
    ) -> None:
        original_read_bytes = Path.read_bytes
        original_read_text = Path.read_text
        design_root = REAL_SOURCES["design_receipt"].parent.absolute()

        def is_real_source(path: Path) -> bool:
            absolute = path.absolute()
            return absolute.is_relative_to(PROJECT_ROOT) or absolute.is_relative_to(
                design_root
            )

        def guarded_read_bytes(path: Path) -> bytes:
            if is_real_source(path):
                raise AssertionError(f"real source path was reopened: {path.name}")
            return original_read_bytes(path)

        def guarded_read_text(path: Path, *args, **kwargs) -> str:
            if is_real_source(path):
                raise AssertionError(f"real source path was reopened: {path.name}")
            return original_read_text(path, *args, **kwargs)

        with (
            mock.patch.object(Path, "read_bytes", guarded_read_bytes),
            mock.patch.object(Path, "read_text", guarded_read_text),
        ):
            rebuilt = build_method_lock_from_sources(**REAL_SOURCES)
        self.assertEqual(rebuilt["blockers"], self.candidate["blockers"])

    def test_replay_child_ignores_pythonpath_sitecustomize_poison(self) -> None:
        poison = self.root / "ambient-python-poison"
        poison.mkdir()
        marker = poison / "startup-hook-ran.txt"
        user_marker = poison / "user-hook-ran.txt"
        fake_package = poison / "iclr2027"
        fake_package.mkdir()
        (fake_package / "__init__.py").write_text(
            "ORIGIN = 'ambient-poison'\n", encoding="utf-8"
        )
        (poison / "sitecustomize.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n"
            "import iclr2027\n"
            "print('ambient-startup-poison')\n",
            encoding="utf-8",
        )
        (poison / "usercustomize.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(user_marker)!r}).write_text('executed', encoding='utf-8')\n",
            encoding="utf-8",
        )
        with mock.patch.dict(
            os.environ,
            {
                "PYTHONHOME": str(poison),
                "PYTHONPATH": str(poison),
                "PYTHONUSERBASE": str(poison),
            },
            clear=False,
        ):
            rebuilt = build_method_lock_from_sources(**REAL_SOURCES)
        self.assertFalse(marker.exists())
        self.assertFalse(user_marker.exists())
        self.assertEqual(
            rebuilt["blockers"], ["development_gate_failed", "pilot_gate_failed"]
        )

    def _run_managed_replay_child(
        self,
        *,
        label: str,
        lazy_import_poison: bool,
        mutate_during_replay: bool,
    ) -> tuple[dict[str, object], Path, dict[str, object]]:
        fixture_root = self.root / label
        project = fixture_root / "authenticated/project"
        package = project / "iclr2027"
        package.mkdir(parents=True)
        (project / "config.py").write_bytes((PROJECT_ROOT / "config.py").read_bytes())
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "io.py").write_text(
            "import json\n"
            "def canonical_json(value):\n"
            "    return json.dumps(value, sort_keys=True, separators=(',', ':'))\n",
            encoding="utf-8",
        )
        (project / "replay_lazy_probe.py").write_text(
            "SOURCE = 'authenticated-mirror'\n", encoding="utf-8"
        )
        mutation = (
            "    sys.path.insert(0, str(Path(__file__).parent / 'replay-mutation'))\n"
            if mutate_during_replay
            else ""
        )
        lazy_import = (
            "    import replay_lazy_probe\n"
            "    if replay_lazy_probe.SOURCE != 'authenticated-mirror':\n"
            "        raise RuntimeError('unauthenticated lazy import')\n"
            if lazy_import_poison
            else ""
        )
        (package / "policy_replay.py").write_text(
            "import sys\n"
            "from pathlib import Path\n"
            "def verify_replay_outputs(output, *, snapshot, dataset, models):\n"
            f"{lazy_import}"
            f"{mutation}"
            "    return {'passed': False}\n",
            encoding="utf-8",
        )

        poison_root = fixture_root / "AG/autogen_a2a_kit"
        poison_root.mkdir(parents=True)
        marker = poison_root / "lazy-poison-loaded.txt"
        (poison_root / "replay_lazy_probe.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('loaded', encoding='utf-8')\n"
            "SOURCE = 'unauthenticated-temp-path'\n",
            encoding="utf-8",
        )

        persisted_gate = project / "replay/development_gate.json"
        persisted_gate.parent.mkdir(parents=True)
        persisted_gate.write_bytes(b'{"passed":false}\n')
        snapshot = project / "snapshot/snapshot_receipt.json"
        dataset = project / "dataset/feature_manifest.json"
        models = project / "models/model_registry.json"
        for path in (snapshot, dataset, models):
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{}\n")
        dependency = fixture_root / "validated-dependency"
        dependency.mkdir()
        dependencies = [str(dependency), str(dependency) + os.sep + "."]
        if os.name == "nt":
            dependencies.append(str(dependency).swapcase())
        critical_modules = {
            "config": "config.py",
            "iclr2027": "iclr2027/__init__.py",
            "iclr2027.io": "iclr2027/io.py",
            "iclr2027.policy_replay": "iclr2027/policy_replay.py",
        }
        paths = method_lock_module._SourcePaths(
            design_receipt=project / "unused-design-receipt.json",
            design_document=project / "unused-design.md",
            snapshot=snapshot,
            pilot_gate=project / "unused-pilot-gate.json",
            dataset=dataset,
            models=models,
            replay=persisted_gate,
            project_root=project,
        )
        captured_attestation: dict[str, object] = {}
        original_decode = method_lock_module._decode_json_object

        def capture_attestation(artifact: bytes, *, label: str) -> dict[str, object]:
            value = original_decode(artifact, label=label)
            if label == "verified reconstruction":
                captured_attestation.update(value)
            return value

        with (
            mock.patch(
                "iclr2027.method_lock._critical_replay_module_paths",
                return_value=critical_modules,
            ),
            mock.patch(
                "iclr2027.method_lock._trusted_replay_dependency_paths",
                return_value=dependencies,
            ),
            mock.patch(
                "iclr2027.method_lock._decode_json_object",
                side_effect=capture_attestation,
            ),
        ):
            gate = method_lock_module._verify_replay_from_authenticated_snapshot(paths)
        return gate, marker, captured_attestation

    def test_replay_child_attests_config_and_removes_exact_temp_poison(self) -> None:
        error: ValueError | None = None
        gate: dict[str, object] | None = None
        marker: Path | None = None
        attestation: dict[str, object] = {}
        try:
            gate, marker, attestation = self._run_managed_replay_child(
                label="config-first-path-attestation",
                lazy_import_poison=True,
                mutate_during_replay=False,
            )
        except ValueError as caught:
            error = caught
            marker = (
                self.root
                / "config-first-path-attestation/AG/autogen_a2a_kit/"
                "lazy-poison-loaded.txt"
            )
        self.assertFalse(marker.exists())
        self.assertIsNone(error, str(error))
        self.assertEqual(gate, {"passed": False})
        self.assertEqual(
            attestation["import_sequence"],
            ["config", "iclr2027", "iclr2027.io", "iclr2027.policy_replay"],
        )
        expected_origins = {
            "config": self.root
            / "config-first-path-attestation/authenticated/project/config.py",
            "iclr2027": self.root
            / "config-first-path-attestation/authenticated/project/"
            "iclr2027/__init__.py",
            "iclr2027.io": self.root
            / "config-first-path-attestation/authenticated/project/iclr2027/io.py",
            "iclr2027.policy_replay": self.root
            / "config-first-path-attestation/authenticated/project/"
            "iclr2027/policy_replay.py",
        }
        self.assertEqual(
            attestation["module_origins"],
            {name: str(path.resolve()) for name, path in expected_origins.items()},
        )
        path_attestation = attestation["sys_path_attestation"]
        self.assertIsInstance(path_attestation, dict)
        allowed = path_attestation["allowed"]
        self.assertEqual(path_attestation["after_config_normalization"], allowed)
        self.assertEqual(path_attestation["before_replay"], allowed)
        self.assertEqual(path_attestation["after_replay"], allowed)

    def test_replay_child_rejects_local_sys_path_mutation_after_replay(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "authenticated replay sys.path changed after replay"
        ):
            self._run_managed_replay_child(
                label="replay-path-mutation",
                lazy_import_poison=False,
                mutate_during_replay=True,
            )

    def _assert_isolated_source_drift(
        self,
        *,
        label: str,
        relative: str,
        expected_error: str,
        drift_bytes: bytes = b"\ncontrolled-development-drift\n",
        assert_python_syntax: bool = False,
    ) -> None:
        fixture_sources, fixture_project = _isolated_development_sources(
            self.root / label,
            implementation_names=self.candidate["implementation_closure"],
        )
        target = fixture_project / relative
        mutated = target.read_bytes() + drift_bytes
        if assert_python_syntax:
            compile(mutated, str(target), "exec")
        target.write_bytes(mutated)
        with (
            mock.patch(
                "iclr2027.method_lock._expected_real_paths",
                return_value=fixture_sources,
            ),
            mock.patch(
                "iclr2027.method_lock._expected_implementation_root",
                return_value=fixture_project,
            ),
            self.assertRaisesRegex(ValueError, expected_error),
        ):
            verify_method_lock_candidate(
                self.candidate_path,
                **fixture_sources,
                execution_memory=AUTHORITATIVE_MEMORY,
            )

    def test_actual_design_document_drift_reaches_design_binding(self) -> None:
        fixture_sources, fixture_project = _isolated_development_sources(
            self.root / "actual-design-drift",
            implementation_names=self.candidate["implementation_closure"],
        )
        receipt = json.loads(fixture_sources["design_receipt"].read_text())
        document = fixture_sources["design_receipt"].parent / receipt["document"]
        document.write_bytes(document.read_bytes() + b"\ncontrolled-design-drift\n")
        with (
            mock.patch(
                "iclr2027.method_lock._expected_real_paths",
                return_value=fixture_sources,
            ),
            mock.patch(
                "iclr2027.method_lock._expected_implementation_root",
                return_value=fixture_project,
            ),
            self.assertRaisesRegex(ValueError, "design document SHA-256 mismatch"),
        ):
            verify_method_lock_candidate(
                self.candidate_path,
                **fixture_sources,
                execution_memory=AUTHORITATIVE_MEMORY,
            )

    def test_actual_model_artifact_drift_reaches_model_binding(self) -> None:
        self._assert_isolated_source_drift(
            label="actual-model-drift",
            relative="results/exp09_cats/models/cats-primary/classifier.joblib",
            expected_error="model artifact cats-primary/classifier.joblib SHA-256 mismatch",
        )

    def test_rehashed_pilot_gate_attack_fails_closed(self) -> None:
        def mutate(candidate: dict[str, object]) -> None:
            candidate["pilot_gate"]["passed"] = True
            candidate["pilot_gate"]["failed_checks"] = []

        path = self._attacked_path("pilot-gate-attack", mutate)
        with self.assertRaises(ValueError):
            verify_method_lock_candidate(
                path,
                **REAL_SOURCES,
                execution_memory=AUTHORITATIVE_MEMORY,
            )

    def test_rehashed_development_gate_attack_fails_closed(self) -> None:
        def mutate(candidate: dict[str, object]) -> None:
            candidate["development_gate"]["passed"] = True
            candidate["development_gate"]["failed_checks"] = []

        path = self._attacked_path("development-gate-attack", mutate)
        with self.assertRaises(ValueError):
            verify_method_lock_candidate(
                path,
                **REAL_SOURCES,
                execution_memory=AUTHORITATIVE_MEMORY,
            )

    def test_actual_replay_rows_drift_reaches_replay_binding(self) -> None:
        self._assert_isolated_source_drift(
            label="actual-replay-drift",
            relative="results/exp09_cats/replay/development/replay_rows.jsonl",
            expected_error="replay rows SHA-256 mismatch",
        )

    def test_actual_task6_helper_drift_reaches_source_reconstruction(self) -> None:
        self._assert_isolated_source_drift(
            label="actual-task6-helper-drift",
            relative="iclr2027/policy_replay.py",
            expected_error=(
                "authenticated Task 6 reconstruction failed: ValueError: "
                "development gate differs from source reconstruction"
            ),
            drift_bytes=b"\n# controlled-development-drift\n",
            assert_python_syntax=True,
        )

    def test_actual_method_helper_drift_reaches_implementation_closure(self) -> None:
        self._assert_isolated_source_drift(
            label="actual-method-helper-drift",
            relative="iclr2027/secure_files.py",
            expected_error="candidate implementation closure mismatch",
        )

    def test_stale_execution_memory_fails_closed(self) -> None:
        stale = self.root / "stale-memory.md"
        stale.write_bytes(MEMORY_BASELINE.read_bytes())
        with self.assertRaisesRegex(ValueError, "execution memory"):
            verify_method_lock_candidate(
                self.candidate_path,
                **REAL_SOURCES,
                execution_memory=stale,
            )

    def test_identical_alternate_execution_memory_is_not_authoritative(self) -> None:
        with self.assertRaisesRegex(ValueError, "authoritative execution memory"):
            verify_method_lock_candidate(
                self.candidate_path,
                **REAL_SOURCES,
                execution_memory=self.memory_path,
            )

    def test_digest_mode_requires_authoritative_execution_memory(self) -> None:
        digest = hashlib.sha256(self.candidate_path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "authoritative execution memory"):
            verify_method_lock_candidate(
                self.candidate_path,
                expected_candidate_file_sha256=digest,
            )
        with self.assertRaisesRegex(ValueError, "authoritative execution memory"):
            verify_method_lock_candidate(
                self.candidate_path,
                expected_candidate_file_sha256=digest,
                execution_memory=self.memory_path,
            )

    def test_digest_mode_rejects_missing_authoritative_memory(self) -> None:
        digest = hashlib.sha256(self.candidate_path.read_bytes()).hexdigest()
        missing = self.root / "missing-authoritative-memory.md"
        with (
            mock.patch(
                "iclr2027.method_lock._authoritative_memory_path",
                return_value=missing,
            ),
            self.assertRaisesRegex(ValueError, "authoritative|authenticated"),
        ):
            verify_method_lock_candidate(
                self.candidate_path,
                expected_candidate_file_sha256=digest,
                execution_memory=missing,
            )

    def test_digest_mode_rejects_stale_authoritative_memory(self) -> None:
        digest = hashlib.sha256(self.candidate_path.read_bytes()).hexdigest()
        stale = self.root / "stale-authoritative-memory.md"
        stale.write_bytes(MEMORY_BASELINE.read_bytes())
        with (
            mock.patch(
                "iclr2027.method_lock._authoritative_memory_path",
                return_value=stale,
            ),
            self.assertRaisesRegex(ValueError, "stale or mismatched"),
        ):
            verify_method_lock_candidate(
                self.candidate_path,
                expected_candidate_file_sha256=digest,
                execution_memory=stale,
            )

    def test_real_candidate_is_denied_after_independent_digest_validation(self) -> None:
        digest = hashlib.sha256(self.candidate_path.read_bytes()).hexdigest()
        with self.assertRaises(PermissionError):
            require_positive_method_lock(
                self.candidate_path,
                expected_candidate_file_sha256=digest,
                execution_memory=AUTHORITATIVE_MEMORY,
            )

    def test_real_candidate_binds_six_variants_twenty_four_artifacts_and_zero_reads(
        self,
    ) -> None:
        self.assertEqual(self.candidate["models"]["variant_count"], 6)
        self.assertEqual(self.candidate["models"]["artifact_count"], 24)
        self.assertEqual(self.candidate["access_audit"]["held_out_bundle_reads"], 0)
        self.assertFalse(self.candidate["held_out_access_allowed"])


class MethodLockPathSafetyTests(unittest.TestCase):
    def test_authenticated_hardlink_rejects_before_outside_bytes_are_read(self) -> None:
        from iclr2027.secure_files import AuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-method-lock-hardlink-") as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            outside = base / "outside-source.json"
            outside.write_bytes(b"outside-bytes-must-not-be-read")
            linked = source / "declared.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                if error.errno in {1, 13, 18, 45, 95} or getattr(
                    error, "winerror", None
                ) in {1, 5, 50, 1314}:
                    self.skipTest(f"hard links unsupported by test filesystem: {error}")
                raise
            self.assertGreater(os.stat(linked).st_nlink, 1)
            read_observer_calls: list[Path] = []
            with AuthenticatedTree(
                source,
                label="hardlink development source",
                read_observer=read_observer_calls.append,
            ) as tree:
                with self.assertRaisesRegex(ValueError, "link count|hardlink"):
                    tree.read_bytes("declared.json", label="hardlinked development file")
            self.assertEqual(read_observer_calls, [])

    def test_authenticated_file_swap_rejects_before_replacement_read(self) -> None:
        from iclr2027.secure_files import AuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-method-lock-file-swap-") as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            expected = source / "input.json"
            expected.write_bytes(b"trusted-development-bytes")
            replacement = base / "replacement.json"
            replacement.write_bytes(b"replacement-must-not-be-read")
            observed_reads: list[Path] = []

            with AuthenticatedTree(
                source,
                label="test development source",
                read_observer=observed_reads.append,
            ) as tree:
                expected.unlink()
                expected.symlink_to(replacement)
                with self.assertRaisesRegex(ValueError, "reparse|symlink"):
                    tree.read_bytes("input.json", label="swapped development file")

            self.assertEqual(observed_reads, [])

    def test_post_file_validation_replacement_cannot_change_handle_bytes(
        self,
    ) -> None:
        from iclr2027.secure_files import AuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-method-lock-post-file-") as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            expected = source / "input.json"
            original_bytes = b"authenticated-original-handle-bytes"
            expected.write_bytes(original_bytes)
            replacement = base / "replacement.json"
            replacement.write_bytes(b"replacement-bytes-must-not-be-returned")
            moved = source / "moved-original.json"
            state = {"blocked": False, "replaced": False}

            def replace_after_validation(_final: Path) -> None:
                try:
                    expected.replace(moved)
                    expected.symlink_to(replacement)
                    state["replaced"] = True
                except OSError:
                    state["blocked"] = True

            with AuthenticatedTree(
                source,
                label="post-validation file source",
                post_file_validation_hook=replace_after_validation,
            ) as tree:
                observed = tree.read_bytes(
                    "input.json", label="post-validation file"
                )
            self.assertEqual(observed, original_bytes)
            self.assertTrue(state["blocked"] if os.name == "nt" else state["replaced"])

    def test_post_directory_validation_replacement_stays_on_retained_handle(
        self,
    ) -> None:
        from iclr2027.secure_files import AuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-method-lock-post-dir-") as temporary:
            base = Path(temporary)
            source = base / "source"
            component = source / "declared"
            component.mkdir(parents=True)
            original_bytes = b"authenticated-directory-handle-bytes"
            (component / "input.json").write_bytes(original_bytes)
            target = base / "replacement-tree"
            target.mkdir()
            (target / "input.json").write_bytes(b"replacement-tree-bytes")
            moved = source / "moved-declared"
            state = {"blocked": False, "replaced": False}
            observed_reads: list[Path] = []

            def replace_component_after_validation(final: Path) -> None:
                if final.name != "declared":
                    return
                try:
                    component.replace(moved)
                    component.symlink_to(target, target_is_directory=True)
                    state["replaced"] = True
                except OSError:
                    state["blocked"] = True

            with AuthenticatedTree(
                source,
                label="post-validation directory source",
                read_observer=observed_reads.append,
                directory_validation_hook=replace_component_after_validation,
            ) as tree:
                if os.name == "nt":
                    observed = tree.read_bytes(
                        "declared/input.json", label="post-validation directory file"
                    )
                    self.assertEqual(observed, original_bytes)
                else:
                    with self.assertRaisesRegex(ValueError, "outside the frozen tree"):
                        tree.read_bytes(
                            "declared/input.json",
                            label="post-validation directory file",
                        )
            self.assertTrue(state["blocked"] if os.name == "nt" else state["replaced"])
            if state["replaced"]:
                self.assertEqual(observed_reads, [])

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_authenticated_enumeration_rejects_static_junction_before_names(
        self,
    ) -> None:
        from iclr2027.secure_files import AuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-list-static-junction-") as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            outside = base / "outside"
            outside.mkdir()
            outside_name = "outside-name-must-not-be-observed.json"
            (outside / outside_name).write_bytes(b"outside")
            junction = source / "linked"
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                created.returncode,
                0,
                msg=f"junction creation failed: {created.stdout}{created.stderr}",
            )
            observed: list[tuple[Path, str]] = []
            if "name_observer" not in inspect.signature(AuthenticatedTree).parameters:
                self.fail("authenticated directory name observer is missing")
            try:
                with AuthenticatedTree(
                    source,
                    label="Windows static junction enumeration",
                    name_observer=lambda directory, name: observed.append(
                        (directory, name)
                    ),
                ) as tree:
                    list_directory = getattr(tree, "list_directory", None)
                    if list_directory is None:
                        self.fail("authenticated directory enumeration is missing")
                    with self.assertRaisesRegex(ValueError, "symlink|reparse"):
                        list_directory(None, label="Windows source directory")
            finally:
                if junction.exists():
                    junction.rmdir()
            self.assertEqual(observed, [])

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_authenticated_enumeration_locks_validated_windows_directory(
        self,
    ) -> None:
        from iclr2027.secure_files import AuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-list-junction-swap-") as temporary:
            base = Path(temporary)
            source = base / "source"
            component = source / "declared"
            component.mkdir(parents=True)
            inside_name = "inside-original.json"
            (component / inside_name).write_bytes(b"inside")
            outside = base / "outside"
            outside.mkdir()
            outside_name = "outside-name-must-not-be-observed.json"
            (outside / outside_name).write_bytes(b"outside")
            moved = source / "moved-declared"
            state = {"attempted": False, "blocked": False, "replaced": False}
            observed: list[tuple[Path, str]] = []

            def replace_with_junction(final: Path) -> None:
                if final.name != "declared" or state["attempted"]:
                    return
                state["attempted"] = True
                try:
                    component.replace(moved)
                    created = subprocess.run(
                        ["cmd", "/c", "mklink", "/J", str(component), str(outside)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if created.returncode != 0:
                        moved.replace(component)
                        raise OSError(
                            "junction creation failed: "
                            f"{created.stdout}{created.stderr}"
                        )
                    state["replaced"] = True
                except OSError:
                    state["blocked"] = True

            if "name_observer" not in inspect.signature(AuthenticatedTree).parameters:
                self.fail("authenticated directory name observer is missing")
            try:
                with AuthenticatedTree(
                    source,
                    label="Windows directory swap enumeration",
                    name_observer=lambda directory, name: observed.append(
                        (directory, name)
                    ),
                    directory_validation_hook=replace_with_junction,
                ) as tree:
                    entries = tree.list_directory(
                        "declared", label="Windows declared directory"
                    )
            finally:
                if state["replaced"] and os.path.lexists(component):
                    component.rmdir()
                if state["replaced"] and moved.exists() and not component.exists():
                    moved.replace(component)
            self.assertTrue(state["attempted"])
            self.assertTrue(state["blocked"])
            self.assertFalse(state["replaced"])
            self.assertEqual([entry.name for entry in entries], [inside_name])
            self.assertNotIn(outside_name, [name for _directory, name in observed])

    def test_design_receipt_symlink_is_rejected_before_target_parse(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-link-") as temporary:
            root = Path(temporary)
            target = root / "invalid-target.json"
            target.write_bytes(b"not-json-and-must-not-be-parsed")
            link = root / REAL_SOURCES["design_receipt"].name
            link.symlink_to(target)
            sources = dict(REAL_SOURCES)
            sources["design_receipt"] = link
            with self.assertRaisesRegex(ValueError, "symlink|reparse|frozen source path"):
                build_method_lock_from_sources(**sources)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_design_receipt_junction_is_rejected_before_target_parse(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-method-lock-junction-") as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            (target / REAL_SOURCES["design_receipt"].name).write_bytes(
                b"not-json-and-must-not-be-parsed"
            )
            junction = root / "junction"
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                created.returncode,
                0,
                msg=f"junction creation failed: {created.stdout}{created.stderr}",
            )
            try:
                attributes = getattr(junction.lstat(), "st_file_attributes", 0)
                self.assertTrue(
                    attributes
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                )
                sources = dict(REAL_SOURCES)
                sources["design_receipt"] = (
                    junction / REAL_SOURCES["design_receipt"].name
                )
                with self.assertRaisesRegex(
                    ValueError, "symlink|reparse|frozen source path"
                ):
                    build_method_lock_from_sources(**sources)
            finally:
                if junction.exists():
                    junction.rmdir()


if __name__ == "__main__":
    unittest.main()
