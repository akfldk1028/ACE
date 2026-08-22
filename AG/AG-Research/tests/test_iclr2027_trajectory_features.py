from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


class TrajectoryFeatureTests(unittest.TestCase):
    def test_builder_rejects_hardlinked_snapshot_before_read_or_output_mutation(
        self,
    ) -> None:
        from build_exp09_dataset import build_dataset
        from iclr2027.study_contract import StudyContract

        project = Path(__file__).parents[1]
        real_snapshot = (
            project
            / "results/exp09_cats/development_snapshot/snapshot_receipt.json"
        )
        with tempfile.TemporaryDirectory(prefix="ace-dataset-hardlink-") as temporary:
            root = Path(temporary)
            outside = root / "outside-snapshot.json"
            outside.write_bytes(real_snapshot.read_bytes())
            linked = root / "snapshot_receipt.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            output = root / "dataset-output"
            observed: list[Path] = []
            original_read_text = Path.read_text

            def observe_read(path: Path, *args, **kwargs) -> str:
                if path == linked:
                    observed.append(path)
                return original_read_text(path, *args, **kwargs)

            caught: ValueError | None = None
            with mock.patch.object(Path, "read_text", observe_read):
                try:
                    build_dataset(
                        snapshot=linked,
                        results=project
                        / "results/exp08_architecture/pilot_full_v12_clean_recovery",
                        split_manifest=project / "data/iclr2027/split_manifest.json",
                        projection_identity=project
                        / "data/iclr2027/projection_identity.private.json",
                        epsilon=0.02,
                        output=output,
                        method_lock=StudyContract.primary(),
                    )
                except ValueError as error:
                    caught = error
            if (
                observed
                or output.exists()
                or caught is None
                or "link count" not in str(caught)
            ):
                self.fail(
                    "dataset snapshot hardlink must fail before read/output mutation; "
                    f"observed={observed!r}, output_exists={output.exists()}, "
                    f"error={caught!r}"
                )

    def test_builder_rejects_hardlinked_projection_before_read_or_output_mutation(
        self,
    ) -> None:
        from build_exp09_dataset import build_dataset
        from iclr2027.study_contract import StudyContract

        project = Path(__file__).parents[1]
        real_identity = project / "data/iclr2027/projection_identity.private.json"
        with tempfile.TemporaryDirectory(prefix="ace-projection-hardlink-") as temporary:
            root = Path(temporary)
            outside = root / "outside-projection.json"
            outside.write_bytes(real_identity.read_bytes())
            linked = root / "projection_identity.private.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            output = root / "dataset-output"
            observed: list[Path] = []
            original_read_text = Path.read_text

            def observe_read(path: Path, *args, **kwargs) -> str:
                if path == linked:
                    observed.append(path)
                return original_read_text(path, *args, **kwargs)

            caught: ValueError | None = None
            with mock.patch.object(Path, "read_text", observe_read):
                try:
                    build_dataset(
                        snapshot=project
                        / "results/exp09_cats/development_snapshot/snapshot_receipt.json",
                        results=project
                        / "results/exp08_architecture/pilot_full_v12_clean_recovery",
                        split_manifest=project / "data/iclr2027/split_manifest.json",
                        projection_identity=linked,
                        epsilon=0.02,
                        output=output,
                        method_lock=StudyContract.primary(),
                    )
                except ValueError as error:
                    caught = error
            if (
                observed
                or output.exists()
                or caught is None
                or "link count" not in str(caught)
            ):
                self.fail(
                    "dataset projection hardlink must fail before read/output mutation; "
                    f"observed={observed!r}, output_exists={output.exists()}, "
                    f"error={caught!r}"
                )

    def setUp(self) -> None:
        from iclr2027.trajectory_features import fit_text_distance

        self.transformer = fit_text_distance(
            (
                "site geometry evidence",
                "law parking program evidence",
            )
        )

    @staticmethod
    def _prefix_fixture() -> dict[str, object]:
        return {
            "trajectory_id": f"trajectory:{'a' * 64}",
            "pattern": "rr2",
            "pattern_category": "A",
            "agent_count": 2,
            "prefix_turn_index": 2,
            "turns": [
                {
                    "index": 1,
                    "source": "site_agent",
                    "content": "Site geometry evidence is present.",
                    "tokens_in": 8,
                    "tokens_out": 5,
                },
                {
                    "index": 2,
                    "source": "law_agent",
                    "content": "Law and parking evidence remain checked.",
                    "tokens_in": 9,
                    "tokens_out": 6,
                },
                {
                    "index": 3,
                    "source": "program_agent",
                    "content": "Future content must not leak.",
                    "tokens_in": 10,
                    "tokens_out": 7,
                },
            ],
            "parsed": [
                {
                    "parse_complete": True,
                    "state": {
                        "blocking_issue_codes": [],
                        "checked_domains": ["site", "geometry"],
                        "confidence": 0.6,
                        "evidence_ids": [
                            "evidence:site_agent",
                            "evidence:geometry_agent",
                        ],
                        "missing_evidence_codes": [
                            "law.required_evidence_missing"
                        ],
                        "recommended_decision": "CONTINUE",
                    },
                },
                {
                    "parse_complete": True,
                    "state": {
                        "blocking_issue_codes": [],
                        "checked_domains": ["site", "geometry", "law", "parking"],
                        "confidence": 0.8,
                        "evidence_ids": [
                            "evidence:site_agent",
                            "evidence:geometry_agent",
                            "evidence:law_graph_agent",
                            "evidence:parking_agent",
                        ],
                        "missing_evidence_codes": [],
                        "recommended_decision": "STOP_ACCEPT",
                    },
                },
                {
                    "parse_complete": True,
                    "state": {
                        "blocking_issue_codes": ["program.capacity_failed"],
                        "checked_domains": ["program"],
                        "confidence": 0.99,
                        "evidence_ids": ["evidence:program_agent"],
                        "missing_evidence_codes": [],
                        "recommended_decision": "STOP_REJECT",
                    },
                },
            ],
            "scores": [
                {"quality": 0.2},
                {"quality": 0.4},
                {"quality": 1.0},
            ],
            "condition": "native",
            "mutation_family": "private-family",
            "pnu": "1165011100200390001",
            "gold": {"expected_decision": "STOP_ACCEPT"},
            "final_turn_count": 3,
            "final_tokens": 45,
        }

    def test_five_sites_follow_exact_preregistered_hash_rank_mapping(self) -> None:
        from iclr2027.trajectory_features import assign_site_groups

        dev_case_index = tuple(
            SimpleNamespace(site_ref=f"site:{index:064x}")
            for index in range(5)
            for _ in range(6)
        )
        assignments = assign_site_groups(dev_case_index, seed=20260819)
        self.assertEqual(
            {assignment.site_ref: assignment.partition for assignment in assignments},
            {
                f"site:{0:064x}": "development_gate",
                f"site:{1:064x}": "train",
                f"site:{2:064x}": "development_gate",
                f"site:{3:064x}": "calibration",
                f"site:{4:064x}": "train",
            },
        )
        self.assertEqual(
            Counter(assignment.partition for assignment in assignments),
            {"train": 2, "calibration": 1, "development_gate": 2},
        )
        by_site: defaultdict[str, set[str]] = defaultdict(set)
        for row in assignments:
            by_site[row.site_ref].add(row.partition)
        self.assertTrue(all(len(partitions) == 1 for partitions in by_site.values()))

    def test_builder_rejects_any_test_bundle_argument_before_method_lock(self) -> None:
        from build_exp09_dataset import build_dataset

        with self.assertRaisesRegex(PermissionError, "held-out access is locked"):
            build_dataset(
                case_paths=[Path("data/iclr2027/cases/test.native.public.jsonl")],
                method_lock=None,
            )

    def test_runtime_prefix_is_invariant_to_future_and_private_changes(self) -> None:
        from iclr2027.io import canonical_json
        from iclr2027.trajectory_features import runtime_features

        fixture = self._prefix_fixture()
        changed = deepcopy(fixture)
        changed["turns"][2]["content"] = "Completely changed future text."
        changed["turns"][2]["tokens_out"] = 99999
        changed["parsed"][2]["state"]["confidence"] = 0.01
        changed["scores"] = [{"quality": 1.0}] * 3
        changed["condition"] = "challenged"
        changed["mutation_family"] = "different-private-family"
        changed["pnu"] = "1168011800104670003"
        changed["gold"] = {"expected_decision": "STOP_REJECT"}
        changed["final_turn_count"] = 999
        changed["final_tokens"] = 999999

        left = runtime_features(fixture, fitted=self.transformer)
        right = runtime_features(changed, fitted=self.transformer)
        self.assertEqual(canonical_json(left), canonical_json(right))

    def test_runtime_schema_excludes_forbidden_fields(self) -> None:
        from iclr2027.trajectory_features import PrefixRuntimeFeature

        forbidden = {
            "quality_t",
            "future_max_quality",
            "beneficial_future",
            "condition",
            "mutation_family",
            "pnu",
            "gold",
            "final_turn_count",
            "final_tokens",
        }
        self.assertFalse(forbidden & set(PrefixRuntimeFeature.field_names()))

    def test_runtime_schema_is_exact_and_normalizes_against_registered_budget(self) -> None:
        from iclr2027.trajectory_features import (
            CATEGORICAL_FEATURES,
            NUMERIC_FEATURES,
            PrefixRuntimeFeature,
            runtime_features,
        )

        feature = runtime_features(self._prefix_fixture(), fitted=self.transformer)
        self.assertEqual(
            PrefixRuntimeFeature.field_names(),
            ("row_id", "trajectory_id", *NUMERIC_FEATURES, *CATEGORICAL_FEATURES),
        )
        self.assertEqual(feature.turn_index, 2)
        self.assertEqual(feature.normalized_turn, 0.2)

    def test_transforming_nontrain_text_does_not_change_fitted_vocabulary(self) -> None:
        from iclr2027.trajectory_features import runtime_features

        before = self.transformer.vocabulary_sha256
        fixture = self._prefix_fixture()
        fixture["turns"][1]["content"] = "calibration_only_token"
        runtime_features(fixture, fitted=self.transformer)
        self.assertEqual(self.transformer.vocabulary_sha256, before)
        self.assertNotIn("calibration_only_token", self.transformer.vocabulary)

    def test_private_labels_use_only_strictly_beneficial_future_quality(self) -> None:
        from iclr2027.trajectory_features import (
            PrivatePrefixLabel,
            private_prefix_labels,
        )

        labels = private_prefix_labels(
            f"trajectory:{'b' * 64}",
            (0.10, 0.12, 0.121, 0.50),
            epsilon=0.02,
        )
        self.assertEqual(
            [label.beneficial_future for label in labels],
            [True, True, True, False],
        )
        self.assertEqual(labels[0].future_max_quality, 0.50)
        self.assertEqual(labels[-1].future_max_quality, 0.50)
        self.assertEqual(
            PrivatePrefixLabel.field_names(),
            ("row_id", "quality_t", "future_max_quality", "beneficial_future"),
        )

    def test_development_builder_writes_separated_bound_artifacts(self) -> None:
        from build_exp09_dataset import build_dataset
        from iclr2027.artifact_receipts import verify_artifact_receipt
        from iclr2027.study_contract import StudyContract
        from iclr2027.trajectory_features import MODEL_FEATURES, PrefixRuntimeFeature

        root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "dataset"
            result = build_dataset(
                snapshot=root
                / "results"
                / "exp09_cats"
                / "development_snapshot"
                / "snapshot_receipt.json",
                results=root
                / "results"
                / "exp08_architecture"
                / "pilot_full_v12_clean_recovery",
                split_manifest=root / "data" / "iclr2027" / "split_manifest.json",
                projection_identity=root
                / "data"
                / "iclr2027"
                / "projection_identity.private.json",
                epsilon=0.02,
                output=output,
                method_lock=StudyContract.primary(),
            )

            runtime_path = output / "runtime" / "runtime_features.jsonl"
            labels_path = output / "private" / "private_labels.jsonl"
            assignments_path = output / "private" / "group_assignments.json"
            manifest_path = output / "feature_manifest.json"
            runtime = [
                json.loads(line)
                for line in runtime_path.read_text(encoding="utf-8").splitlines()
            ]
            labels = [
                json.loads(line)
                for line in labels_path.read_text(encoding="utf-8").splitlines()
            ]
            assignments = json.loads(assignments_path.read_text(encoding="utf-8"))[
                "assignments"
            ]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(len(assignments), 450)
            self.assertEqual(len({row["trajectory_id"] for row in assignments}), 450)
            self.assertEqual(
                Counter(row["partition"] for row in assignments),
                {"train": 180, "calibration": 90, "development_gate": 180},
            )
            self.assertEqual(
                [row["row_id"] for row in runtime],
                [row["row_id"] for row in labels],
            )
            self.assertEqual(set(runtime[0]), set(PrefixRuntimeFeature.field_names()))
            self.assertEqual(
                set(labels[0]),
                {
                    "row_id",
                    "quality_t",
                    "future_max_quality",
                    "beneficial_future",
                },
            )
            self.assertFalse(set(assignments[0]) & set(MODEL_FEATURES))
            self.assertFalse(
                {
                    "quality_t",
                    "future_max_quality",
                    "beneficial_future",
                    "partition",
                    "condition",
                    "mutation_family",
                    "final_turn_count",
                    "final_tokens",
                }
                & set(runtime[0])
            )
            self.assertEqual(result.trajectory_count, 450)
            self.assertEqual(result.prefix_count, len(runtime))
            self.assertEqual(manifest["transformer"]["fit_partition"], "train")
            self.assertEqual(manifest["transformer"]["fit_site_count"], 2)
            self.assertEqual(manifest["transformer"]["fit_trajectory_count"], 180)
            self.assertEqual(
                manifest["access_policy"],
                {
                    "allowed_split": "dev",
                    "held_out_bundle_reads": 0,
                    "resolved_bundle_keys": ["dev.challenged", "dev.native"],
                },
            )
            verify_artifact_receipt(manifest["artifact_receipt"], root=output)
            for relative_path, entry in manifest["artifacts"].items():
                artifact = output / relative_path
                self.assertEqual(
                    hashlib.sha256(artifact.read_bytes()).hexdigest(), entry["sha256"]
                )


if __name__ == "__main__":
    unittest.main()
