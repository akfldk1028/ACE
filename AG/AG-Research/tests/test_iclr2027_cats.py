from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from iclr2027.artifact_receipts import canonical_artifact_receipt
from iclr2027.cats import (
    CATSStopPolicy,
    FrozenVariantSpec,
    assemble_frozen_dataset,
    ensure_finite_probabilities,
    finite_sample_quantile,
    load_frozen_dataset,
    compare_semantic_training_runs,
    train_frozen_variant,
    trajectory_nonconformity,
    write_verified_frozen_variants,
)
from iclr2027.io import sha256_json, write_json_atomic, write_jsonl_atomic
from iclr2027.study_contract import StudyContract


NUMERIC_FEATURES = (
    "turn_index",
    "normalized_turn",
    "agent_count",
    "speaker_count",
    "turn_tokens",
    "cumulative_tokens",
    "token_delta_1",
    "token_delta_2",
    "word_count",
    "unique_ratio",
    "repeated_ngram_ratio",
    "tfidf_distance_prev",
    "tfidf_distance_prefix",
    "reported_confidence",
    "checked_domain_count",
    "evidence_count",
    "blocking_issue_count",
    "missing_evidence_count",
)
CATEGORICAL_FEATURES = (
    "pattern",
    "pattern_category",
    "source",
    "recommended_decision",
    "parse_complete",
    "site_evidence_present",
    "geometry_evidence_present",
    "law_evidence_present",
    "parking_evidence_present",
    "program_evidence_present",
)
MODEL_FEATURES = (*NUMERIC_FEATURES, *CATEGORICAL_FEATURES)
RUNTIME_SCHEMA = ("row_id", "trajectory_id", *MODEL_FEATURES)
PRIVATE_SCHEMA = (
    "row_id",
    "quality_t",
    "future_max_quality",
    "beneficial_future",
)
ASSIGNMENT_SCHEMA = (
    "trajectory_id",
    "group_id",
    "partition",
    "site_ref",
    "case_id",
    "condition",
    "mutation_family",
    "repeat",
    "final_turn_count",
    "final_tokens",
)


def _runtime_row(
    row_id: str,
    trajectory_id: str,
    *,
    pattern: str,
    turn_tokens: int,
) -> dict[str, object]:
    return {
        "row_id": row_id,
        "trajectory_id": trajectory_id,
        "turn_index": 1,
        "normalized_turn": 0.1,
        "agent_count": 3,
        "speaker_count": 1,
        "turn_tokens": turn_tokens,
        "cumulative_tokens": turn_tokens,
        "token_delta_1": 0,
        "token_delta_2": 0,
        "word_count": 10,
        "unique_ratio": 0.8,
        "repeated_ngram_ratio": 0.1,
        "tfidf_distance_prev": 0.2,
        "tfidf_distance_prefix": 0.3,
        "reported_confidence": 0.7,
        "checked_domain_count": 5,
        "evidence_count": 5,
        "blocking_issue_count": 0,
        "missing_evidence_count": 0,
        "pattern": pattern,
        "pattern_category": "coordination",
        "source": "site_agent",
        "recommended_decision": "STOP_ACCEPT",
        "parse_complete": True,
        "site_evidence_present": True,
        "geometry_evidence_present": True,
        "law_evidence_present": True,
        "parking_evidence_present": True,
        "program_evidence_present": True,
    }


def _label_row(
    row_id: str,
    *,
    quality_t: float,
    future_max_quality: float,
) -> dict[str, object]:
    return {
        "row_id": row_id,
        "quality_t": quality_t,
        "future_max_quality": future_max_quality,
        "beneficial_future": future_max_quality - quality_t > 0.02,
    }


def _assignment(
    trajectory_id: str,
    *,
    group_id: str,
    site_ref: str,
    partition: str,
) -> dict[str, object]:
    return {
        "trajectory_id": trajectory_id,
        "group_id": group_id,
        "partition": partition,
        "site_ref": site_ref,
        "case_id": f"case-{trajectory_id}",
        "condition": "native",
        "mutation_family": "none",
        "repeat": 1,
        "final_turn_count": 1,
        "final_tokens": 100,
    }


def _frozen_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trajectories = (
        ("trajectory:train-a", "train", "group:train-a", "site:train-a", "rr3", 10),
        ("trajectory:train-b", "train", "group:train-b", "site:train-b", "sel3", 30),
        (
            "trajectory:calibration",
            "calibration",
            "group:calibration",
            "site:calibration",
            "calibration-only",
            100_000,
        ),
        (
            "trajectory:gate-a",
            "development_gate",
            "group:gate-a",
            "site:gate-a",
            "gate-only",
            200_000,
        ),
        (
            "trajectory:gate-b",
            "development_gate",
            "group:gate-b",
            "site:gate-b",
            "gate-only",
            300_000,
        ),
    )
    runtime: list[dict[str, object]] = []
    labels: list[dict[str, object]] = []
    assignments: list[dict[str, object]] = []
    qualities = (
        (0.50, 0.50),
        (0.40, 0.50),
        (0.20, 0.40),
        (0.70, 0.70),
        (0.60, 0.75),
    )
    for index, (trajectory, partition, group, site, pattern, tokens) in enumerate(
        trajectories
    ):
        row_id = f"row:{index}"
        runtime.append(
            _runtime_row(
                row_id,
                trajectory,
                pattern=pattern,
                turn_tokens=tokens,
            )
        )
        quality_t, future_max = qualities[index]
        labels.append(
            _label_row(
                row_id,
                quality_t=quality_t,
                future_max_quality=future_max,
            )
        )
        assignments.append(
            _assignment(
                trajectory,
                group_id=group,
                site_ref=site,
                partition=partition,
            )
        )
    return pd.DataFrame(runtime), pd.DataFrame(labels), pd.DataFrame(assignments)


def _write_dataset_fixture(root: Path) -> None:
    runtime, labels, assignments = _frozen_tables()
    runtime_path = root / "runtime" / "runtime_features.jsonl"
    labels_path = root / "private" / "private_labels.jsonl"
    assignments_path = root / "private" / "group_assignments.json"
    write_jsonl_atomic(runtime_path, runtime.to_dict(orient="records"))
    write_jsonl_atomic(labels_path, labels.to_dict(orient="records"))
    write_json_atomic(
        assignments_path,
        {
            "schema_version": "ace.iclr2027.cats_group_assignments.v1",
            "assignments": assignments.to_dict(orient="records"),
        },
    )
    bindings = {
        "projection_identity_commitment": "1" * 64,
        "snapshot_receipt_sha256": "2" * 64,
        "split_manifest_sha256": "3" * 64,
        "study_contract_sha256": sha256_json(asdict(StudyContract.primary())),
        "transaction_set_sha256": "4" * 64,
        "vocabulary_sha256": "5" * 64,
    }
    receipt = canonical_artifact_receipt(
        schema_version="ace.iclr2027.cats_dataset_artifacts.v1",
        files={
            "runtime/runtime_features.jsonl": runtime_path,
            "private/private_labels.jsonl": labels_path,
            "private/group_assignments.json": assignments_path,
        },
        row_census={
            "assignments": 5,
            "prefixes": 5,
            "private_labels": 5,
            "runtime_features": 5,
            "sites": 5,
            "trajectories": 5,
        },
        bindings=bindings,
    )
    artifacts = {
        relative_path: {
            "record_count": 5,
            "schema_version": schema,
            "sha256": receipt["files"][relative_path],
        }
        for relative_path, schema in (
            (
                "runtime/runtime_features.jsonl",
                "ace.iclr2027.cats_prefix_runtime_feature.v1",
            ),
            (
                "private/private_labels.jsonl",
                "ace.iclr2027.cats_private_prefix_label.v1",
            ),
            (
                "private/group_assignments.json",
                "ace.iclr2027.cats_group_assignments.v1",
            ),
        )
    }
    write_json_atomic(
        root / "feature_manifest.json",
        {
            "schema_version": "ace.iclr2027.cats_dataset_manifest.v1",
            "access_policy": {
                "allowed_split": "dev",
                "held_out_bundle_reads": 0,
                "resolved_bundle_keys": ["dev.challenged", "dev.native"],
            },
            "artifact_receipt": receipt,
            "artifacts": artifacts,
            "runtime_schema": list(RUNTIME_SCHEMA),
            "private_label_schema": list(PRIVATE_SCHEMA),
            "assignment_schema": list(ASSIGNMENT_SCHEMA),
            "numeric_features": list(NUMERIC_FEATURES),
            "categorical_features": list(CATEGORICAL_FEATURES),
            "model_features": list(MODEL_FEATURES),
            "epsilon": 0.02,
            "study_contract_sha256": bindings["study_contract_sha256"],
            "snapshot_receipt_sha256": bindings["snapshot_receipt_sha256"],
            "split_manifest_sha256": bindings["split_manifest_sha256"],
            "transaction_set_sha256": bindings["transaction_set_sha256"],
            "projection_identity_commitment": bindings[
                "projection_identity_commitment"
            ],
        },
    )


class CATSConformalTests(unittest.TestCase):
    def test_finite_sample_quantile_uses_corrected_rank(self) -> None:
        self.assertEqual(
            finite_sample_quantile(np.array([0.1, 0.2, 0.4]), alpha=0.25),
            0.4,
        )
        self.assertEqual(
            finite_sample_quantile(np.array([0.1, 0.2]), alpha=0.10),
            math.inf,
        )

    def test_trajectory_score_is_maximum_over_positive_prefixes(self) -> None:
        rows = pd.DataFrame(
            {"beneficial_future": [0, 1, 1], "p_improve": [0.2, 0.8, 0.4]}
        )
        self.assertEqual(trajectory_nonconformity(rows), 0.6)

    def test_trajectory_without_positive_prefix_has_zero_score(self) -> None:
        rows = pd.DataFrame(
            {"beneficial_future": [0, 0], "p_improve": [0.2, 0.8]}
        )
        self.assertEqual(trajectory_nonconformity(rows), 0.0)

    def test_empty_or_nonfinite_calibration_scores_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "calibration scores must not be empty"):
            finite_sample_quantile(np.array([]), alpha=0.10)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            trajectory_nonconformity(
                pd.DataFrame(
                    {"beneficial_future": [1], "p_improve": [float("nan")]}
                )
            )


class CATSStopPolicyTests(unittest.TestCase):
    @staticmethod
    def always_no_gain(_state: dict[str, object]) -> float:
        return 0.0

    def setUp(self) -> None:
        self.safe_prefix = {
            "parse_complete": True,
            "recommended_decision": "STOP_ACCEPT",
            "blocking_issue_count": 0,
            "missing_evidence_count": 0,
            "site_evidence_present": True,
            "geometry_evidence_present": True,
            "law_evidence_present": True,
            "parking_evidence_present": True,
            "program_evidence_present": True,
        }
        self.unsafe_prefix = {**self.safe_prefix, "program_evidence_present": False}

    def test_patience_and_hard_guard_both_required(self) -> None:
        policy = CATSStopPolicy(
            model=self.always_no_gain,
            q_alpha=0.2,
            patience=2,
        )
        self.assertFalse(policy.observe(self.safe_prefix).stop)
        self.assertTrue(policy.observe(self.safe_prefix).stop)
        policy.reset()
        self.assertFalse(policy.observe(self.unsafe_prefix).stop)
        self.assertFalse(policy.observe(self.unsafe_prefix).stop)

    def test_unsafe_prefix_resets_patience_streak(self) -> None:
        policy = CATSStopPolicy(
            model=self.always_no_gain,
            q_alpha=0.2,
            patience=2,
        )
        self.assertFalse(policy.observe(self.safe_prefix).stop)
        self.assertFalse(policy.observe(self.unsafe_prefix).stop)
        self.assertFalse(policy.observe(self.safe_prefix).stop)

    def test_pandas_runtime_boolean_scalars_pass_the_same_hard_guard(self) -> None:
        policy = CATSStopPolicy(
            model=self.always_no_gain,
            q_alpha=0.2,
            patience=2,
        )
        runtime_state = pd.DataFrame([self.safe_prefix]).iloc[0]
        self.assertFalse(policy.observe(runtime_state).stop)
        self.assertTrue(policy.observe(runtime_state).stop)

    def test_malformed_parse_complete_value_fails_the_hard_guard(self) -> None:
        policy = CATSStopPolicy(
            model=self.always_no_gain,
            q_alpha=0.2,
            patience=2,
        )
        malformed = {**self.safe_prefix, "parse_complete": "true"}
        self.assertFalse(policy.observe(malformed).stop)
        self.assertFalse(policy.observe(malformed).stop)


class CATSFrozenDataTests(unittest.TestCase):
    def test_real_preprocessor_and_both_models_fit_train_only(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        frozen = assemble_frozen_dataset(runtime, labels, assignments)
        for family in ("histgb", "logistic"):
            with self.subTest(family=family):
                result = train_frozen_variant(
                    frozen,
                    FrozenVariantSpec(
                        name=f"test-{family}",
                        family=family,
                        epsilon=0.02,
                        alpha=0.10,
                    ),
                )
                numeric = result.fitted.transformer.named_transformers_["numeric"]
                categorical = result.fitted.transformer.named_transformers_[
                    "categorical"
                ]
                self.assertEqual(float(numeric.named_steps["imputer"].statistics_[4]), 20.0)
                self.assertEqual(
                    set(categorical.categories_[0]),
                    {"rr3", "sel3"},
                )
                self.assertNotIn("calibration-only", categorical.categories_[0])
                self.assertNotIn("gate-only", categorical.categories_[0])
                self.assertEqual(len(result.predictions), 5)
                self.assertTrue(np.isfinite(result.predictions["p_improve"]).all())

    def test_one_class_training_labels_fail_closed(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        labels.loc[labels["row_id"] == "row:1", "future_max_quality"] = 0.40
        labels.loc[labels["row_id"] == "row:1", "beneficial_future"] = False
        frozen = assemble_frozen_dataset(runtime, labels, assignments)
        with self.assertRaisesRegex(ValueError, "training labels contain one class"):
            train_frozen_variant(
                frozen,
                FrozenVariantSpec(
                    name="one-class",
                    family="histgb",
                    epsilon=0.02,
                    alpha=0.10,
                ),
            )

    def test_missing_and_duplicate_row_ids_fail_closed(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        with self.assertRaisesRegex(ValueError, "duplicate runtime row_id"):
            assemble_frozen_dataset(
                pd.concat([runtime, runtime.iloc[[0]]], ignore_index=True),
                labels,
                assignments,
            )
        with self.assertRaisesRegex(ValueError, "runtime/private row_id mismatch"):
            assemble_frozen_dataset(runtime, labels.iloc[:-1], assignments)

    def test_empty_calibration_trajectory_fails_closed(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        keep = runtime["trajectory_id"] != "trajectory:calibration"
        with self.assertRaisesRegex(ValueError, "empty calibration trajectories"):
            assemble_frozen_dataset(
                runtime.loc[keep].reset_index(drop=True),
                labels.loc[keep].reset_index(drop=True),
                assignments,
            )

    def test_group_overlap_across_partitions_fails_closed(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        changed = assignments.copy()
        changed.loc[
            changed["trajectory_id"] == "trajectory:calibration", "group_id"
        ] = "group:train-a"
        with self.assertRaisesRegex(ValueError, "group overlap"):
            assemble_frozen_dataset(runtime, labels, changed)

    def test_nonfinite_or_out_of_range_probabilities_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-finite model predictions"):
            ensure_finite_probabilities(np.array([0.2, float("nan")]), expected=2)
        with self.assertRaisesRegex(ValueError, "outside.*zero-one"):
            ensure_finite_probabilities(np.array([0.2, 1.1]), expected=2)

    def test_receipt_mismatch_fails_before_loading_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write_dataset_fixture(root)
            loaded = load_frozen_dataset(root)
            self.assertEqual(len(loaded.runtime), 5)
            runtime_path = root / "runtime" / "runtime_features.jsonl"
            runtime_path.write_bytes(runtime_path.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                load_frozen_dataset(root)

    def test_hardlinked_manifest_rejects_before_outside_bytes_reach_parser(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-manifest-hardlink-") as temporary:
            base = Path(temporary)
            dataset = base / "dataset"
            dataset.mkdir()
            outside = base / "outside-manifest.json"
            outside.write_bytes(b"outside-manifest-bytes-must-not-be-parsed")
            manifest = dataset / "feature_manifest.json"
            try:
                os.link(outside, manifest)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            observed_reads: list[Path] = []
            observed_parses: list[object] = []
            original_read_text = Path.read_text
            original_loads = json.loads

            def observe_read(path: Path, *args, **kwargs) -> str:
                if path == manifest:
                    observed_reads.append(path)
                return original_read_text(path, *args, **kwargs)

            def observe_parse(value: object, *args, **kwargs):
                observed_parses.append(value)
                return original_loads(value, *args, **kwargs)

            caught: ValueError | None = None
            with (
                patch.object(Path, "read_text", observe_read),
                patch("iclr2027.cats.json.loads", side_effect=observe_parse),
            ):
                try:
                    load_frozen_dataset(dataset)
                except ValueError as error:
                    caught = error
            if (
                observed_reads
                or observed_parses
                or caught is None
                or "link count" not in str(caught)
            ):
                self.fail(
                    "manifest hardlink must reject before observer/parser; "
                    f"reads={observed_reads!r}, parses={observed_parses!r}, "
                    f"error={caught!r}"
                )

    def test_receipt_artifact_bytes_are_parsed_without_post_verify_reopen(
        self,
    ) -> None:
        import iclr2027.cats as cats_module

        with tempfile.TemporaryDirectory(prefix="ace-cats-artifact-reopen-") as temporary:
            base = Path(temporary)
            dataset = base / "dataset"
            _write_dataset_fixture(dataset)
            runtime = dataset / "runtime" / "runtime_features.jsonl"
            outside = base / "outside-runtime.jsonl"
            outside.write_bytes(b"outside-runtime-bytes-must-not-be-parsed\n")
            observed_reads: list[Path] = []
            original_read_text = Path.read_text
            original_verify = cats_module.verify_artifact_receipt_bytes
            swapped = False
            swap_blocked = False

            def swap_after_verification(*args, **kwargs) -> None:
                nonlocal swap_blocked, swapped
                original_verify(*args, **kwargs)
                try:
                    runtime.unlink()
                    os.link(outside, runtime)
                    swapped = True
                except OSError:
                    swap_blocked = True

            def observe_read(path: Path, *args, **kwargs) -> str:
                if path == runtime:
                    observed_reads.append(path)
                return original_read_text(path, *args, **kwargs)

            loaded = None
            caught: ValueError | None = None
            with (
                patch.object(Path, "read_text", observe_read),
                patch(
                    "iclr2027.cats.verify_artifact_receipt_bytes",
                    side_effect=swap_after_verification,
                ),
            ):
                try:
                    loaded = load_frozen_dataset(dataset)
                except ValueError as error:
                    caught = error
            if observed_reads or caught is not None or loaded is None:
                self.fail(
                    "receipt-bound artifact bytes must not be reopened after verify; "
                    f"swapped={swapped}, swap_blocked={swap_blocked}, "
                    f"reads={observed_reads!r}, error={caught!r}"
                )
            if os.name == "nt":
                self.assertTrue(swap_blocked)
                self.assertFalse(swapped)
            else:
                self.assertTrue(swapped)
                self.assertFalse(swap_blocked)
            self.assertEqual(len(loaded.runtime), 5)

    def test_symlinked_dataset_root_is_rejected_before_invalid_manifest_parse(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-root-link-") as temporary:
            temporary_root = Path(temporary)
            sentinel_target = temporary_root / "sentinel-target"
            sentinel_target.mkdir()
            (sentinel_target / "feature_manifest.json").write_bytes(
                b"invalid-sentinel-manifest"
            )
            dataset_link = temporary_root / "dataset-link"
            dataset_link.symlink_to(sentinel_target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlinked dataset roots"):
                load_frozen_dataset(dataset_link)

    def test_symlinked_manifest_is_rejected_before_invalid_target_parse(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-manifest-link-") as temporary:
            temporary_root = Path(temporary)
            dataset_root = temporary_root / "dataset"
            dataset_root.mkdir()
            sentinel_target = temporary_root / "invalid-sentinel.json"
            sentinel_target.write_bytes(b"invalid-sentinel-manifest")
            (dataset_root / "feature_manifest.json").symlink_to(sentinel_target)
            with self.assertRaisesRegex(ValueError, "symlinked dataset manifests"):
                load_frozen_dataset(dataset_root)

    def test_private_identity_is_recovered_only_through_runtime_row_ids(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        self.assertEqual(tuple(labels.columns), PRIVATE_SCHEMA)
        frozen = assemble_frozen_dataset(runtime, labels, assignments)
        self.assertEqual(
            frozen.partition_by_row.loc["row:0", "trajectory_id"],
            "trajectory:train-a",
        )
        self.assertNotIn("trajectory_id", frozen.labels.columns)

    def test_frozen_point_estimator_parameters_are_exact(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        frozen = assemble_frozen_dataset(runtime, labels, assignments)
        primary = train_frozen_variant(
            frozen,
            FrozenVariantSpec(
                name="primary",
                family="histgb",
                epsilon=0.02,
                alpha=0.10,
            ),
        )
        self.assertEqual(
            {
                "max_iter": primary.fitted.classifier.max_iter,
                "learning_rate": primary.fitted.classifier.learning_rate,
                "max_leaf_nodes": primary.fitted.classifier.max_leaf_nodes,
                "l2_regularization": primary.fitted.classifier.l2_regularization,
                "random_state": primary.fitted.classifier.random_state,
            },
            {
                "max_iter": 200,
                "learning_rate": 0.05,
                "max_leaf_nodes": 15,
                "l2_regularization": 1.0,
                "random_state": 20260819,
            },
        )

    def test_logistic_estimator_parameters_are_exact(self) -> None:
        runtime, labels, assignments = _frozen_tables()
        frozen = assemble_frozen_dataset(runtime, labels, assignments)
        logistic = train_frozen_variant(
            frozen,
            FrozenVariantSpec(
                name="logistic",
                family="logistic",
                epsilon=0.02,
                alpha=0.10,
            ),
        )
        self.assertEqual(logistic.fitted.classifier.max_iter, 2000)
        self.assertEqual(logistic.fitted.classifier.class_weight, "balanced")
        self.assertEqual(logistic.fitted.classifier.random_state, 20260819)


class CATSPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(prefix="ace-cats-publication-")
        cls.root = Path(cls._temporary.name)
        cls.dataset = cls.root / "dataset"
        cls.output = cls.root / "models"
        _write_dataset_fixture(cls.dataset)
        cls.registry = write_verified_frozen_variants(cls.dataset, cls.output)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_task7_registry_filename_and_compatibility_alias_are_atomic(self) -> None:
        primary = self.output / "model_registry.json"
        compatibility = self.output / "registry.json"
        self.assertTrue(primary.is_file())
        self.assertTrue(compatibility.is_file())
        self.assertEqual(primary.read_bytes(), compatibility.read_bytes())
        self.assertFalse(
            any(
                path.name.endswith(".tmp")
                for path in self.output.rglob("*")
                if path.is_file()
            )
        )
        self.assertEqual(self.registry["variant_count"], 6)

    def test_cli_publication_persists_bound_six_variant_determinism_receipt(self) -> None:
        receipt_path = self.output / "semantic_determinism.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        registry = json.loads(
            (self.output / "model_registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            receipt["schema_version"],
            "ace.iclr2027.cats_semantic_determinism.v1",
        )
        self.assertEqual(receipt["variant_count"], 6)
        self.assertEqual(receipt["source_receipts"], registry["source_receipts"])
        self.assertEqual(
            hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            registry["semantic_determinism"]["sha256"],
        )
        self.assertEqual(
            registry["semantic_determinism"]["receipt_sha256"],
            receipt["receipt_sha256"],
        )
        for comparison in receipt["variants"]:
            self.assertEqual(
                comparison["matching"],
                {
                    "alpha": True,
                    "canonical_predictions": True,
                    "classifier_parameters": True,
                    "epsilon": True,
                    "feature_order": True,
                    "q_alpha": True,
                    "semantic_manifest": True,
                    "source_receipts": True,
                },
            )
        self.assertFalse(receipt["raw_joblib_equality_required"])

    def test_semantic_comparator_rejects_prediction_mismatch(self) -> None:
        left = self.root / "comparison-left"
        right = self.root / "comparison-right"
        shutil.copytree(self.output, left)
        shutil.copytree(self.output, right)
        prediction_path = right / "cats-primary" / "predictions.jsonl"
        prediction_path.write_bytes(prediction_path.read_bytes() + b"{}\n")
        with self.assertRaisesRegex(ValueError, "prediction artifact hash mismatch"):
            compare_semantic_training_runs(left, right)

    def test_semantic_run_rejects_classifier_artifact_tamper(self) -> None:
        left = self.root / "classifier-left"
        right = self.root / "classifier-right"
        shutil.copytree(self.output, left)
        shutil.copytree(self.output, right)
        classifier_path = right / "cats-primary" / "classifier.joblib"
        classifier_path.write_bytes(classifier_path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "classifier artifact hash mismatch"):
            compare_semantic_training_runs(left, right)

    def test_semantic_run_rejects_transformer_artifact_tamper(self) -> None:
        left = self.root / "transformer-left"
        right = self.root / "transformer-right"
        shutil.copytree(self.output, left)
        shutil.copytree(self.output, right)
        transformer_path = right / "cats-primary" / "transformer.joblib"
        transformer_path.write_bytes(transformer_path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "transformer artifact hash mismatch"):
            compare_semantic_training_runs(left, right)

    def test_semantic_run_requires_regular_byte_identical_registry_alias(self) -> None:
        left = self.root / "alias-left"
        right = self.root / "alias-right"
        shutil.copytree(self.output, left)
        shutil.copytree(self.output, right)
        (right / "registry.json").unlink()
        with self.assertRaisesRegex(ValueError, "registry compatibility alias"):
            compare_semantic_training_runs(left, right)

    def test_comparator_rejects_internally_consistent_q_alpha_mismatch(self) -> None:
        left = self.root / "semantic-left"
        right = self.root / "semantic-right"
        shutil.copytree(self.output, left)
        shutil.copytree(self.output, right)
        manifest_path = right / "cats-primary" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["semantic"]["q_alpha"] = 0.123456789
        manifest["semantic_sha256"] = sha256_json(manifest["semantic"])
        write_json_atomic(manifest_path, manifest)
        registry_path = right / "model_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        primary = next(
            variant for variant in registry["variants"] if variant["name"] == "cats-primary"
        )
        primary["q_alpha"] = 0.123456789
        primary["semantic_sha256"] = manifest["semantic_sha256"]
        primary["manifest_sha256"] = hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest()
        write_json_atomic(registry_path, registry)
        write_json_atomic(right / "registry.json", registry)
        with self.assertRaisesRegex(
            ValueError,
            "semantic determinism mismatch.*q_alpha",
        ):
            compare_semantic_training_runs(left, right)


class CATSAtomicPublicationTests(unittest.TestCase):
    @staticmethod
    def _tree_snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
        directories = tuple(
            sorted(
                str(path.relative_to(root)).replace("\\", "/")
                for path in root.rglob("*")
                if path.is_dir()
            )
        )
        files = {
            str(path.relative_to(root)).replace("\\", "/"): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }
        return directories, files

    @staticmethod
    def _nontraversing_tree_snapshot(root: Path) -> tuple[str, tuple[dict[str, object], ...]]:
        records: list[dict[str, object]] = []
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

        def walk(directory: Path, relative_parent: Path) -> None:
            with os.scandir(directory) as entries:
                for entry in sorted(entries, key=lambda item: item.name):
                    path = Path(entry.path)
                    relative = relative_parent / entry.name
                    item_stat = entry.stat(follow_symlinks=False)
                    attributes = getattr(item_stat, "st_file_attributes", 0)
                    is_reparse = bool(attributes & reparse_flag)
                    is_junction = bool(
                        hasattr(path, "is_junction") and path.is_junction()
                    )
                    record: dict[str, object] = {
                        "path": relative.as_posix(),
                        "attributes": attributes,
                        "mode": item_stat.st_mode,
                        "size": item_stat.st_size,
                        "is_symlink": path.is_symlink(),
                        "is_junction": is_junction,
                        "is_reparse": is_reparse,
                    }
                    if is_reparse or path.is_symlink() or is_junction:
                        try:
                            record["target"] = os.readlink(path)
                        except OSError:
                            record["target"] = "<unreadable>"
                    elif entry.is_dir(follow_symlinks=False):
                        record["kind"] = "directory"
                        walk(path, relative)
                    elif entry.is_file(follow_symlinks=False):
                        record["kind"] = "file"
                        record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                    else:
                        record["kind"] = "other"
                    records.append(record)

        walk(root, Path())
        frozen_records = tuple(records)
        return sha256_json(frozen_records), frozen_records

    @staticmethod
    def _publication_rename_events(
        output: Path,
        events: list[str],
    ) -> object:
        real_replace = os.replace

        def tracking_replace(source: object, destination: object) -> None:
            source_path = Path(source)
            destination_path = Path(destination)
            if source_path == output or destination_path == output:
                events.append(f"{source_path.name}->{destination_path.name}")
            real_replace(source_path, destination_path)

        return tracking_replace

    @staticmethod
    def _injected_verification_failure() -> None:
        raise RuntimeError("injected verification failure")

    def test_verification_failure_preserves_preexisting_publication_byte_for_byte(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-existing-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            _write_dataset_fixture(dataset)
            (output / "nested").mkdir(parents=True)
            (output / "sentinel.bin").write_bytes(b"original-publication")
            (output / "nested" / "state.json").write_bytes(b'{"version":1}\n')
            before = self._tree_snapshot(output)
            with self.assertRaisesRegex(RuntimeError, "injected verification failure"):
                write_verified_frozen_variants(
                    dataset,
                    output,
                    verification_hook=self._injected_verification_failure,
                )
            self.assertEqual(self._tree_snapshot(output), before)
            self.assertFalse(
                any(path.name.startswith(".publication.") for path in root.iterdir())
            )

    def test_interior_file_symlink_is_rejected_before_publication_rename(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-file-link-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            target = root / "outside-sentinel.bin"
            _write_dataset_fixture(dataset)
            output.mkdir()
            (output / "sentinel.bin").write_bytes(b"original-publication")
            target.write_bytes(b"must-not-be-read")
            interior_link = output / "interior-link.bin"
            interior_link.symlink_to(target)
            attributes = getattr(
                interior_link.lstat(),
                "st_file_attributes",
                0,
            )
            self.assertTrue(interior_link.is_symlink())
            self.assertTrue(
                attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            )
            before = self._nontraversing_tree_snapshot(output)
            rename_events: list[str] = []
            tracking_replace = self._publication_rename_events(output, rename_events)
            with patch("iclr2027.cats.os.replace", side_effect=tracking_replace):
                with self.assertRaisesRegex(ValueError, "reparse point"):
                    write_verified_frozen_variants(dataset, output)
            self.assertEqual(self._nontraversing_tree_snapshot(output), before)
            self.assertEqual(rename_events, [])
            self.assertFalse(
                any(path.name.startswith(".publication.") for path in root.iterdir())
            )

    def test_interior_hardlink_is_rejected_before_hash_read_or_publication_rename(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-hardlink-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            outside = root / "outside-sentinel.bin"
            _write_dataset_fixture(dataset)
            output.mkdir()
            (output / "sentinel.bin").write_bytes(b"original-publication")
            outside.write_bytes(b"outside-hardlink-bytes-must-not-be-hashed")
            linked = output / "interior-hardlink.bin"
            try:
                os.link(outside, linked)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            before = self._nontraversing_tree_snapshot(output)
            observed_reads: list[Path] = []
            rename_events: list[str] = []
            original_open = Path.open

            def observe_open(path: Path, *args, **kwargs):
                if path == linked:
                    observed_reads.append(path)
                return original_open(path, *args, **kwargs)

            tracking_replace = self._publication_rename_events(output, rename_events)
            caught: ValueError | None = None
            with (
                patch.object(Path, "open", observe_open),
                patch("iclr2027.cats.os.replace", side_effect=tracking_replace),
            ):
                try:
                    write_verified_frozen_variants(dataset, output)
                except ValueError as error:
                    caught = error
            after = self._nontraversing_tree_snapshot(output)
            residue = [
                path.name
                for path in root.iterdir()
                if path.name.startswith(".publication.")
            ]
            if (
                observed_reads
                or rename_events
                or before != after
                or residue
                or caught is None
                or "link count" not in str(caught)
            ):
                self.fail(
                    "authoritative hardlink must fail before read or publication mutation; "
                    f"observed_reads={observed_reads!r}, "
                    f"rename_events={rename_events!r}, tree_unchanged={before == after}, "
                    f"residue={residue!r}, error={caught!r}"
                )

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_interior_directory_junction_is_rejected_before_publication_rename(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-junction-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            target = root / "outside-directory"
            _write_dataset_fixture(dataset)
            output.mkdir()
            (output / "sentinel.bin").write_bytes(b"original-publication")
            target.mkdir()
            (target / "must-not-be-read.bin").write_bytes(b"junction-target")
            junction = output / "interior-junction"
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
                self.assertTrue(
                    hasattr(junction, "is_junction") and junction.is_junction()
                )
                before = self._nontraversing_tree_snapshot(output)
                rename_events: list[str] = []
                tracking_replace = self._publication_rename_events(output, rename_events)
                with patch("iclr2027.cats.os.replace", side_effect=tracking_replace):
                    with self.assertRaisesRegex(ValueError, "reparse point"):
                        write_verified_frozen_variants(dataset, output)
                self.assertEqual(self._nontraversing_tree_snapshot(output), before)
                self.assertEqual(rename_events, [])
                self.assertFalse(
                    any(path.name.startswith(".publication.") for path in root.iterdir())
                )
            finally:
                if junction.exists():
                    junction.rmdir()

    def test_post_validation_child_junction_never_exposes_outside_names(
        self,
    ) -> None:
        import iclr2027.cats as cats_module
        from iclr2027.secure_files import AuthenticatedTree as RealAuthenticatedTree

        with tempfile.TemporaryDirectory(prefix="ace-cats-child-swap-") as temporary:
            root = Path(temporary)
            output = root / "publication"
            child = output / "nested"
            child.mkdir(parents=True)
            (child / "inside-original.bin").write_bytes(b"inside original")
            (output / "sentinel.bin").write_bytes(b"original publication")
            outside = root / "outside-directory"
            outside.mkdir()
            outside_name = "outside-name-must-not-be-observed.bin"
            (outside / outside_name).write_bytes(b"outside bytes")
            candidate = root / ".publication.candidate-test"
            candidate.mkdir()
            (candidate / "candidate.bin").write_bytes(b"candidate")
            moved = output / "moved-nested"
            observed_names: list[str] = []
            rename_events: list[str] = []
            state = {
                "attempted": False,
                "blocked": False,
                "replaced": False,
                "child_validations": 0,
            }

            def replace_child_with_link() -> None:
                if state["attempted"]:
                    return
                state["attempted"] = True
                try:
                    child.replace(moved)
                    if os.name == "nt":
                        created = subprocess.run(
                            ["cmd", "/c", "mklink", "/J", str(child), str(outside)],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        if created.returncode != 0:
                            moved.replace(child)
                            raise OSError(
                                f"junction creation failed: "
                                f"{created.stdout}{created.stderr}"
                            )
                    else:
                        child.symlink_to(outside, target_is_directory=True)
                    state["replaced"] = True
                except OSError:
                    state["blocked"] = True

            real_scandir = os.scandir

            def observe_scandir(directory):
                if isinstance(directory, int):
                    return real_scandir(directory)
                if Path(directory) != child:
                    return real_scandir(directory)
                replace_child_with_link()
                with real_scandir(directory) as entries:
                    materialized = tuple(entries)
                observed_names.extend(entry.name for entry in materialized)

                @contextmanager
                def retained_entries():
                    yield iter(materialized)

                return retained_entries()

            supports_name_observer = (
                "name_observer"
                in inspect.signature(RealAuthenticatedTree).parameters
            )

            def secure_directory_hook(final: Path) -> None:
                if final.name == "nested":
                    replace_child_with_link()

            def observed_tree(*args, **kwargs):
                kwargs["directory_validation_hook"] = secure_directory_hook
                if supports_name_observer:
                    kwargs["name_observer"] = (
                        lambda _directory, name: observed_names.append(name)
                    )
                return RealAuthenticatedTree(*args, **kwargs)

            tracking_replace = self._publication_rename_events(output, rename_events)
            caught: ValueError | None = None
            try:
                with (
                    patch("iclr2027.cats.os.scandir", side_effect=observe_scandir),
                    patch(
                        "iclr2027.cats.AuthenticatedTree",
                        side_effect=observed_tree,
                    ),
                    patch("iclr2027.cats.os.replace", side_effect=tracking_replace),
                ):
                    try:
                        cats_module._publish_candidate_directory(candidate, output)
                    except ValueError as error:
                        caught = error
            finally:
                if state["replaced"] and os.path.lexists(child):
                    if os.name == "nt":
                        child.rmdir()
                    else:
                        child.unlink()
                if state["replaced"] and moved.exists() and not child.exists():
                    moved.replace(child)

            outside_observed = outside_name in observed_names
            replacement_result_valid = (
                state["replaced"]
                and caught is not None
                and not rename_events
            ) or (
                state["blocked"]
                and caught is None
                and len(rename_events) == 2
            )
            if (
                not supports_name_observer
                or not state["attempted"]
                or outside_observed
                or not replacement_result_valid
            ):
                self.fail(
                    "post-validation child swap must keep enumeration handle-bound; "
                    f"state={state!r}, observed_names={observed_names!r}, "
                    f"rename_events={rename_events!r}, error={caught!r}"
                )

    def test_verification_failure_leaves_no_absent_output_or_staging_residue(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-absent-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            _write_dataset_fixture(dataset)
            with self.assertRaisesRegex(RuntimeError, "injected verification failure"):
                write_verified_frozen_variants(
                    dataset,
                    output,
                    verification_hook=self._injected_verification_failure,
                )
            self.assertFalse(output.exists())
            self.assertFalse(
                any(path.name.startswith(".publication.") for path in root.iterdir())
            )

    def test_double_rename_failure_uses_copy_fallback_to_restore_original_tree(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-copy-restore-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            _write_dataset_fixture(dataset)
            (output / "nested").mkdir(parents=True)
            (output / "sentinel.bin").write_bytes(b"original-publication")
            (output / "nested" / "state.json").write_bytes(b'{"version":1}\n')
            before = self._tree_snapshot(output)
            real_replace = os.replace
            events: list[str] = []

            def injected_replace(source: object, destination: object) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                if source_path == output and destination_path.name.startswith(
                    ".publication.backup-"
                ):
                    events.append("output_to_backup")
                    real_replace(source_path, destination_path)
                    return
                if (
                    source_path.name.startswith(".publication.candidate-")
                    and destination_path == output
                ):
                    events.append("candidate_to_output_failed")
                    raise OSError("injected candidate publication failure")
                if (
                    source_path.name.startswith(".publication.backup-")
                    and destination_path == output
                ):
                    events.append("backup_restore_rename_failed")
                    raise OSError("injected backup restore rename failure")
                real_replace(source_path, destination_path)

            with patch("iclr2027.cats.os.replace", side_effect=injected_replace):
                with self.assertRaisesRegex(
                    OSError,
                    "injected candidate publication failure",
                ):
                    write_verified_frozen_variants(dataset, output)
            self.assertEqual(
                events,
                [
                    "output_to_backup",
                    "candidate_to_output_failed",
                    "backup_restore_rename_failed",
                ],
            )
            self.assertEqual(self._tree_snapshot(output), before)
            self.assertFalse(
                any(path.name.startswith(".publication.") for path in root.iterdir())
            )

    def test_post_rename_digest_mismatch_restores_original_publication(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-digest-race-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            _write_dataset_fixture(dataset)
            (output / "nested").mkdir(parents=True)
            (output / "sentinel.bin").write_bytes(b"original-publication")
            (output / "nested" / "state.json").write_bytes(b'{"version":1}\n')
            before = self._tree_snapshot(output)
            rename_events: list[str] = []
            tracking_replace = self._publication_rename_events(output, rename_events)
            with (
                patch(
                    "iclr2027.cats._directory_tree_digest",
                    side_effect=["preflight-digest", "different-backup-digest"],
                ),
                patch("iclr2027.cats.os.replace", side_effect=tracking_replace),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "changed between preflight and backup validation",
                ):
                    write_verified_frozen_variants(dataset, output)
            self.assertEqual(len(rename_events), 2)
            self.assertTrue(rename_events[0].startswith("publication->.publication.backup-"))
            self.assertTrue(rename_events[1].startswith(".publication.backup-"))
            self.assertTrue(rename_events[1].endswith("->publication"))
            self.assertEqual(self._tree_snapshot(output), before)
            self.assertFalse(
                any(path.name.startswith(".publication.") for path in root.iterdir())
            )

    def test_partial_post_commit_cleanup_failure_preserves_new_publication(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-cats-atomic-cleanup-") as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            output = root / "publication"
            _write_dataset_fixture(dataset)
            (output / "old").mkdir(parents=True)
            (output / "old" / "first.bin").write_bytes(b"old-first")
            (output / "old" / "second.bin").write_bytes(b"old-second")
            real_rmtree = shutil.rmtree
            cleanup_events: list[str] = []

            def partial_cleanup(path: object, *args: object, **kwargs: object) -> None:
                cleanup_path = Path(path)
                if cleanup_path.name.startswith(".publication.cleanup-"):
                    cleanup_events.append("partial_cleanup_failed")
                    first_file = next(
                        child for child in cleanup_path.rglob("*") if child.is_file()
                    )
                    first_file.unlink()
                    raise OSError("injected partial cleanup failure")
                real_rmtree(cleanup_path, *args, **kwargs)

            with patch("iclr2027.cats.shutil.rmtree", side_effect=partial_cleanup):
                with self.assertWarnsRegex(
                    RuntimeWarning,
                    "post-commit backup cleanup failed",
                ):
                    registry = write_verified_frozen_variants(dataset, output)
            self.assertEqual(registry["variant_count"], 6)
            self.assertEqual(compare_semantic_training_runs(output, output)["variant_count"], 6)
            self.assertFalse((output / "old").exists())
            cleanup_residue = tuple(
                path
                for path in root.iterdir()
                if path.name.startswith(".publication.cleanup-")
            )
            self.assertEqual(len(cleanup_residue), 1)
            self.assertEqual(cleanup_events, ["partial_cleanup_failed"])
            self.assertEqual(
                len([path for path in cleanup_residue[0].rglob("*") if path.is_file()]),
                1,
            )
            real_rmtree(cleanup_residue[0])


if __name__ == "__main__":
    unittest.main()
