from __future__ import annotations

from collections import defaultdict
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


EXPECTED_POLICIES = (
    "natural",
    "max_cap",
    "keyword",
    "lexical_du",
    "semantic_patience",
    "logistic",
    "uncalibrated_histgb",
    "state_conformal",
    "cats",
    "cats_no_guard",
    "oracle_peak",
)


class PolicyReplaySecureReadTests(unittest.TestCase):
    def test_canonical_json_reader_rejects_hardlink_before_outside_inode_read(
        self,
    ) -> None:
        replay = _module()
        with tempfile.TemporaryDirectory(prefix="ace-replay-hardlink-") as temporary:
            root = Path(temporary)
            outside = root / "outside.json"
            outside_bytes = b'{"sentinel":"outside-hardlink-bytes"}\n'
            outside.write_bytes(outside_bytes)
            linked = root / "declared.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            observed: list[tuple[Path, bytes]] = []
            original_read_bytes = Path.read_bytes

            def observe_read(path: Path) -> bytes:
                artifact = original_read_bytes(path)
                if path == linked:
                    observed.append((path, artifact))
                return artifact

            caught: ValueError | None = None
            with mock.patch.object(Path, "read_bytes", observe_read):
                try:
                    replay._read_canonical_json(  # noqa: SLF001
                        linked, label="hardlinked replay input"
                    )
                except ValueError as error:
                    caught = error
            if observed or caught is None or "link count" not in str(caught):
                self.fail(
                    "replay hardlink must fail before its outside inode is read; "
                    f"observed={observed!r}, error={caught!r}"
                )

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = PROJECT_ROOT / "results/exp09_cats/development_snapshot/snapshot_receipt.json"
DATASET = PROJECT_ROOT / "results/exp09_cats/dataset"
MODELS = PROJECT_ROOT / "results/exp09_cats/models"

EXPECTED_IMPLEMENTATION_CLOSURE = {
    "config.py",
    "iclr2027/__init__.py",
    "iclr2027/architecture_metrics.py",
    "iclr2027/artifact_receipts.py",
    "iclr2027/audit.py",
    "iclr2027/cats.py",
    "iclr2027/exp08.py",
    "iclr2027/io.py",
    "iclr2027/pilot_gate.py",
    "iclr2027/policy_replay.py",
    "iclr2027/prompts.py",
    "iclr2027/protocol.py",
    "iclr2027/review_state.py",
    "iclr2027/run_manifest.py",
    "iclr2027/schema.py",
    "iclr2027/study_contract.py",
    "iclr2027/trajectory_features.py",
    "iclr2027/trajectory_ingest.py",
    "iclr2027/usage_ledger.py",
    "iclr2027/validators.py",
    "replay_exp09_policies.py",
}


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_gate(path: Path, gate: dict[str, object]) -> None:
    payload = {key: value for key, value in gate.items() if key != "receipt_sha256"}
    gate["receipt_sha256"] = _sha256_json(payload)
    path.write_bytes((_canonical_json(gate) + "\n").encode("utf-8"))


def _write_rows_and_rebind_gate(
    root: Path,
    rows: list[dict[str, object]],
    gate: dict[str, object],
) -> None:
    rows_bytes = "".join(f"{_canonical_json(row)}\n" for row in rows).encode(
        "utf-8"
    )
    (root / "replay_rows.jsonl").write_bytes(rows_bytes)
    gate["replay_rows_sha256"] = hashlib.sha256(rows_bytes).hexdigest()
    _write_gate(root / "development_gate.json", gate)


def _module():
    try:
        return importlib.import_module("iclr2027.policy_replay")
    except ModuleNotFoundError as error:
        raise AssertionError("Task 6 policy replay module is not implemented") from error


def _safe_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "blocking_issue_count": 0,
        "geometry_evidence_present": True,
        "law_evidence_present": True,
        "missing_evidence_count": 0,
        "parking_evidence_present": True,
        "parse_complete": True,
        "program_evidence_present": True,
        "recommended_decision": "STOP_ACCEPT",
        "site_evidence_present": True,
        "tfidf_distance_prev": 0.10,
    }
    state.update(overrides)
    return state


def _prefix(
    turn_index: int,
    *,
    content: str = "stable evidence summary",
    state: dict[str, object] | None = None,
    histgb: float = 0.1,
    logistic: float = 0.1,
):
    replay = _module()
    return replay.RuntimePrefix(
        trajectory_id="trajectory:" + "a" * 64,
        turn_index=turn_index,
        pattern="rr3",
        content=content,
        turn_tokens=10,
        cumulative_visible_tokens=turn_index * 10,
        message_hash=str(turn_index) * 64,
        runtime_state=state or _safe_state(),
        histgb_p_improve=histgb,
        logistic_p_improve=logistic,
    )


def _trajectory(contents: tuple[str, ...] = ("first", "TERMINATE", "third")):
    replay = _module()
    cumulative = 0
    prefixes = []
    for index, (content, tokens) in enumerate(zip(contents, (100, 200, 300)), start=1):
        cumulative += tokens
        prefixes.append(
            replay.RuntimePrefix(
                trajectory_id="trajectory:" + "a" * 64,
                turn_index=index,
                pattern="rr3",
                content=content,
                turn_tokens=tokens,
                cumulative_visible_tokens=cumulative,
                message_hash=str(index) * 64,
                runtime_state=_safe_state(),
                histgb_p_improve=0.1,
                logistic_p_improve=0.1,
            )
        )
    return replay.RuntimeTrajectory(
        trajectory_id="trajectory:" + "a" * 64,
        group_id="group:" + "b" * 64,
        site_ref="site:" + "c" * 64,
        case_id="case:" + "d" * 64,
        condition="native",
        mutation_family="",
        repeat=0,
        pattern="rr3",
        prefixes=tuple(prefixes),
    )


class PolicyContractTests(unittest.TestCase):
    def test_policy_registry_is_exact_and_ordered(self) -> None:
        replay = _module()
        self.assertEqual(tuple(replay.POLICY_REGISTRY), EXPECTED_POLICIES)

    def test_frozen_policy_parameters_are_exact_and_distinct(self) -> None:
        replay = _module()
        parameters = replay.POLICY_PARAMETERS
        self.assertEqual(parameters["max_cap"], {"max_agent_turns": 3})
        self.assertEqual(
            parameters["lexical_du"],
            {
                "cost_proxy": {
                    "actual_usage": (
                        "prompt_tokens + completion_tokens when their sum is positive"
                    ),
                    "fallback": "len(text) / 4",
                },
                "delta_utility": "delta_quality - lambda_cost * cost",
                "epsilon": 0.0,
                "lambda_cost": 0.1,
                "min_turns": 2,
                "patience": 2,
                "quality_proxy": {
                    "empty_text": 0.0,
                    "formula": "min(word_count, 500) / 50 * unique_word_ratio",
                    "tokenization": "lowercase regex \\w+",
                    "unique_word_ratio": "unique_word_count / word_count",
                },
            },
        )
        self.assertEqual(
            parameters["semantic_patience"],
            {"cosine_similarity_gte": 0.85, "patience": 2},
        )
        for name in ("logistic", "uncalibrated_histgb"):
            self.assertEqual(parameters[name]["p_improve_lt"], 0.5)
            self.assertEqual(parameters[name]["patience"], 2)
            self.assertFalse(parameters[name]["hard_guard"])
        self.assertEqual(parameters["logistic"]["variant"], "cats-logistic")
        self.assertEqual(
            parameters["uncalibrated_histgb"]["variant"], "cats-primary"
        )
        self.assertEqual(
            parameters["state_conformal"]["calibration_unit"],
            "positive_calibration_row",
        )
        self.assertEqual(
            parameters["cats"]["calibration_unit"],
            "maximum_positive_nonconformity_per_calibration_trajectory",
        )
        self.assertTrue(parameters["cats"]["hard_guard"])
        self.assertTrue(parameters["state_conformal"]["hard_guard"])
        self.assertFalse(parameters["cats_no_guard"]["hard_guard"])
        self.assertEqual(
            parameters["oracle_peak"]["selection"],
            "earliest_maximum_quality_prefix",
        )

    def test_keyword_signals_are_the_reviewed_protocol_mapping(self) -> None:
        replay = _module()
        from iclr2027.protocol import PILOT_TERMINAL_SIGNALS

        self.assertEqual(replay.KEYWORD_SIGNALS, PILOT_TERMINAL_SIGNALS)

    def test_only_oracle_observe_accepts_future_quality(self) -> None:
        replay = _module()
        prefix = _prefix(1)
        for name, factory in replay.POLICY_REGISTRY.items():
            if name == "oracle_peak":
                decision = factory().observe(prefix, future_quality=(0.4, 0.7))
                self.assertFalse(decision.stop)
            else:
                with self.assertRaises(TypeError, msg=name):
                    factory().observe(prefix, future_quality=(0.4, 0.7))

    def test_runtime_prefix_rejects_private_or_future_fields(self) -> None:
        for forbidden in (
            "beneficial_future",
            "condition",
            "final_tokens",
            "final_turn_count",
            "future_max_quality",
            "future_quality",
            "mutation_family",
            "oracle_quality",
            "quality_t",
            "raw_pnu",
        ):
            with self.subTest(forbidden=forbidden), self.assertRaises(ValueError):
                _prefix(1, state={**_safe_state(), forbidden: 1})

    def test_fixed_baselines_stop_at_the_frozen_boundaries(self) -> None:
        replay = _module()
        max_cap = replay.POLICY_REGISTRY["max_cap"]()
        self.assertFalse(max_cap.observe(_prefix(2)).stop)
        self.assertTrue(max_cap.observe(_prefix(3)).stop)

        keyword = replay.POLICY_REGISTRY["keyword"]()
        self.assertFalse(keyword.observe(_prefix(1, content="please TERMINATE soon")).stop)
        self.assertTrue(keyword.observe(_prefix(2, content="summary\nTERMINATE")).stop)

        lexical = replay.POLICY_REGISTRY["lexical_du"]()
        self.assertFalse(lexical.observe(_prefix(1, content="same words")).stop)
        self.assertFalse(lexical.observe(_prefix(2, content="same words")).stop)
        self.assertTrue(lexical.observe(_prefix(3, content="same words")).stop)

        semantic = replay.POLICY_REGISTRY["semantic_patience"]()
        self.assertFalse(semantic.observe(_prefix(1)).stop)
        self.assertFalse(
            semantic.observe(
                _prefix(2, state=_safe_state(tfidf_distance_prev=0.15))
            ).stop
        )
        self.assertTrue(
            semantic.observe(
                _prefix(3, state=_safe_state(tfidf_distance_prev=0.10))
            ).stop
        )

    def test_lexical_delta_utility_matches_exp05_with_usage_and_fallback(self) -> None:
        from exp05_adaptive_termination.adaptive_condition import (
            AdaptiveTerminationState,
        )

        replay = _module()
        legacy = AdaptiveTerminationState(
            lambda_cost=0.1,
            epsilon=0.0,
            min_turns=2,
            patience=2,
        )
        current = replay.POLICY_REGISTRY["lexical_du"]()
        turns = (
            ("a", SimpleNamespace(prompt_tokens=1, completion_tokens=0), True),
            ("a b c d e f g h i j", None, False),
            (
                "a b c d e f g h i j",
                SimpleNamespace(prompt_tokens=0, completion_tokens=0),
                True,
            ),
        )
        cumulative = 0
        legacy_stops: list[bool] = []
        current_stops: list[bool] = []
        for turn_index, (content, usage, usage_available) in enumerate(turns, start=1):
            legacy_stops.append(legacy.update("assistant", content, usage=usage))
            turn_tokens = (
                int(usage.prompt_tokens) + int(usage.completion_tokens)
                if usage is not None
                else 0
            )
            cumulative += turn_tokens
            prefix = replay.RuntimePrefix(
                trajectory_id="trajectory:" + "a" * 64,
                turn_index=turn_index,
                pattern="rr3",
                content=content,
                turn_tokens=turn_tokens,
                cumulative_visible_tokens=cumulative,
                message_hash=str(turn_index) * 64,
                runtime_state=_safe_state(),
                histgb_p_improve=0.1,
                logistic_p_improve=0.1,
                turn_tokens_from_usage=usage_available,
            )
            current_stops.append(current.observe(prefix).stop)

        self.assertEqual(legacy.stats["costs"], [1.0, 4.75, 4.75])
        self.assertEqual(current_stops, legacy_stops)
        self.assertEqual(current_stops, [False, False, True])

    def test_learned_thresholds_use_their_own_reviewed_probabilities(self) -> None:
        replay = _module()
        logistic = replay.POLICY_REGISTRY["logistic"]()
        histgb = replay.POLICY_REGISTRY["uncalibrated_histgb"]()
        for turn in (1, 2):
            logistic_decision = logistic.observe(
                _prefix(turn, histgb=0.9, logistic=0.49)
            )
            histgb_decision = histgb.observe(
                _prefix(turn, histgb=0.9, logistic=0.49)
            )
        self.assertTrue(logistic_decision.stop)
        self.assertFalse(histgb_decision.stop)

    def test_cats_no_guard_is_the_only_hard_guard_ablation(self) -> None:
        replay = _module()
        unsafe = _safe_state(parse_complete=False)
        cats = replay.POLICY_REGISTRY["cats"](q_alpha=0.5)
        no_guard = replay.POLICY_REGISTRY["cats_no_guard"](q_alpha=0.5)
        state_conformal = replay.POLICY_REGISTRY["state_conformal"](q_alpha=0.5)
        for turn in (1, 2):
            cats_decision = cats.observe(_prefix(turn, state=unsafe, histgb=0.1))
            no_guard_decision = no_guard.observe(
                _prefix(turn, state=unsafe, histgb=0.1)
            )
            state_decision = state_conformal.observe(
                _prefix(turn, state=unsafe, histgb=0.1)
            )
        self.assertFalse(cats_decision.stop)
        self.assertTrue(no_guard_decision.stop)
        self.assertFalse(state_decision.stop)


class CalibrationAndStatisticsTests(unittest.TestCase):
    def test_state_conformal_uses_only_positive_calibration_rows(self) -> None:
        replay = _module()
        predictions = (
            {"row_id": "c1", "partition": "calibration", "p_improve": 0.9},
            {"row_id": "c2", "partition": "calibration", "p_improve": 0.7},
            {"row_id": "c3", "partition": "calibration", "p_improve": 0.1},
            {"row_id": "d1", "partition": "development_gate", "p_improve": 0.0},
        )
        labels = {
            "c1": {"beneficial_future": True},
            "c2": {"beneficial_future": True},
            "c3": {"beneficial_future": False},
            "d1": {"beneficial_future": True},
        }
        first = replay.derive_state_conformal(predictions, labels, alpha=0.5)
        labels["d1"] = {"beneficial_future": False}
        second = replay.derive_state_conformal(predictions, labels, alpha=0.5)
        self.assertEqual(first, second)
        self.assertEqual(first.score_count, 2)
        self.assertAlmostEqual(first.q_alpha, 0.3)
        self.assertEqual(first.source_partition, "calibration")

    def test_site_cluster_bootstrap_never_resamples_individual_rows(self) -> None:
        replay = _module()
        rows = (
            {"site_ref": "site:a", "quality_delta": 0.0, "case_id": "a1"},
            {"site_ref": "site:a", "quality_delta": 0.0, "case_id": "a2"},
            {"site_ref": "site:b", "quality_delta": 10.0, "case_id": "b1"},
            {"site_ref": "site:b", "quality_delta": 10.0, "case_id": "b2"},
        )
        result = replay.site_cluster_bootstrap(rows, draws=10_000, seed=20260819)
        self.assertEqual(result["resampling_unit"], "site_ref")
        self.assertTrue(result["nested_clusters_kept_together"])
        self.assertEqual(result["site_count"], 2)
        self.assertEqual(result["distinct_draw_statistics"], [0.0, 5.0, 10.0])


class ReplayBoundaryTests(unittest.TestCase):
    def test_replay_truncates_exact_source_prefix_then_joins_private_outcomes(self) -> None:
        replay = _module()
        trajectory = _trajectory()
        labels = replay.EvaluationLabels(
            qualities=(0.40, 0.41, 0.50),
            beneficial_future=(True, True, False),
        )
        outcome = replay.replay(
            trajectory,
            replay.POLICY_REGISTRY["keyword"](),
            evaluation_labels=labels,
        )
        self.assertEqual(outcome.stop_turn, 2)
        self.assertEqual(outcome.message_hashes, ("1" * 64, "2" * 64))
        self.assertEqual(outcome.visible_agent_tokens, 300)
        self.assertEqual(outcome.natural_visible_agent_tokens, 600)
        self.assertAlmostEqual(outcome.visible_agent_token_reduction, 0.5)
        self.assertAlmostEqual(outcome.stopped_quality, 0.41)
        self.assertAlmostEqual(outcome.full_quality, 0.50)
        self.assertAlmostEqual(outcome.oracle_quality, 0.50)
        self.assertTrue(outcome.unsafe_stop)
        self.assertTrue(outcome.premature_stop)
        self.assertEqual(outcome.overshoot_turns, 0)
        self.assertAlmostEqual(outcome.oracle_regret, 0.09)

    def test_unsafe_uses_frozen_labels_and_premature_uses_earliest_peak(self) -> None:
        replay = _module()
        trajectory = _trajectory()
        labels = replay.EvaluationLabels(
            qualities=(0.40, 0.50, 0.52),
            beneficial_future=(True, False, False),
        )
        outcome = replay.replay(
            trajectory,
            replay.POLICY_REGISTRY["keyword"](),
            evaluation_labels=labels,
        )
        self.assertFalse(outcome.unsafe_stop)
        self.assertTrue(outcome.premature_stop)
        self.assertAlmostEqual(outcome.oracle_regret, 0.02)

    def test_oracle_selects_earliest_maximum_quality_prefix(self) -> None:
        replay = _module()
        trajectory = _trajectory(("first", "second", "third"))
        labels = replay.EvaluationLabels(
            qualities=(0.80, 0.80, 0.70),
            beneficial_future=(False, False, False),
        )
        outcome = replay.replay(
            trajectory,
            replay.POLICY_REGISTRY["oracle_peak"](),
            evaluation_labels=labels,
        )
        self.assertEqual(outcome.stop_turn, 1)
        self.assertEqual(outcome.oracle_regret, 0.0)
        self.assertEqual(outcome.overshoot_turns, 0)

    def test_partition_guard_rejects_before_loader_is_called(self) -> None:
        replay = _module()
        called = False

        def loader() -> None:
            nonlocal called
            called = True

        with self.assertRaises(PermissionError):
            replay.authorize_partition("train", pre_read_hook=loader)
        self.assertFalse(called)

    def test_input_path_guard_rejects_symlink_before_read(self) -> None:
        replay = _module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "link.json"
            try:
                link.symlink_to(target)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            with self.assertRaises(ValueError):
                replay.safe_input_file(link, label="synthetic input")


class DevelopmentReplayIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        replay = _module()
        cls._temporary = tempfile.TemporaryDirectory()
        cls.first = Path(cls._temporary.name) / "first"
        cls.second = Path(cls._temporary.name) / "second"
        replay.run_development_replay(
            snapshot=SNAPSHOT,
            dataset=DATASET,
            models=MODELS,
            partition="development_gate",
            output=cls.first,
        )
        replay.run_development_replay(
            snapshot=SNAPSHOT,
            dataset=DATASET,
            models=MODELS,
            partition="development_gate",
            output=cls.second,
        )
        cls.rows_bytes = (cls.first / "replay_rows.jsonl").read_bytes()
        cls.gate_bytes = (cls.first / "development_gate.json").read_bytes()
        cls.rows = [json.loads(line) for line in cls.rows_bytes.splitlines()]
        cls.gate = json.loads(cls.gate_bytes)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_exact_1980_row_closure_and_paired_source_identity(self) -> None:
        self.assertEqual(len(self.rows), 1_980)
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in self.rows:
            grouped[str(row["trajectory_id"])].append(row)
        self.assertEqual(len(grouped), 180)
        for trajectory_rows in grouped.values():
            self.assertEqual(
                tuple(row["policy"] for row in trajectory_rows), EXPECTED_POLICIES
            )
            identities = {
                (
                    row["site_ref"],
                    row["case_id"],
                    row["condition"],
                    row["mutation_family"],
                    row["repeat"],
                    row["pattern"],
                    row["natural_turns"],
                    row["natural_visible_agent_tokens"],
                )
                for row in trajectory_rows
            }
            self.assertEqual(len(identities), 1)

    def test_every_replay_prefix_matches_source_hash_and_usage_prefix(self) -> None:
        from iclr2027.trajectory_features import trajectory_id_from_resume_key
        snapshot = _module()._load_snapshot(SNAPSHOT).snapshot  # noqa: SLF001
        transactions = {
            trajectory_id_from_resume_key(str(transaction["resume_identity_sha256"])): (
                transaction
            )
            for transaction in snapshot.transactions
        }
        usage_path = DATASET / "usage/usage_events.jsonl"
        usage_rows = [
            json.loads(line) for line in usage_path.read_text(encoding="utf-8").splitlines()
        ]
        cumulative_tokens = {
            (str(event["trajectory_id"]), int(event["turn_index"])): int(
                event["cumulative_visible_agent_tokens"]
            )
            for event in usage_rows
            if event["event_kind"] == "agent_inference"
        }
        for row in self.rows:
            with self.subTest(row=(row["trajectory_id"], row["policy"])):
                trajectory_id = str(row["trajectory_id"])
                transaction = transactions[trajectory_id]
                resume_identity = str(transaction["resume_identity_sha256"])
                agent_turns = [
                    turn
                    for turn in transaction["raw"]["result"]["turns"]
                    if str(turn["source"]).lower() != "user"
                ]
                stop_turn = int(row["stop_turn"])
                expected_hashes = list(snapshot.message_hashes[resume_identity][:stop_turn])
                source_turn_index = int(agent_turns[stop_turn - 1]["index"])
                self.assertEqual(row["message_hashes"], expected_hashes)
                self.assertEqual(
                    row["visible_agent_tokens"],
                    cumulative_tokens[(trajectory_id, source_turn_index)],
                )

    def test_gate_binds_calibration_derivation_statistics_and_claim_limits(self) -> None:
        self.assertEqual(
            self.gate["schema_version"], "ace.iclr2027.development_gate.v1"
        )
        self.assertEqual(self.gate["row_census"]["replay_rows"], 1_980)
        self.assertEqual(self.gate["row_census"]["trajectories"], 180)
        self.assertEqual(self.gate["row_census"]["policies"], 11)
        self.assertEqual(self.gate["bootstrap"]["draws"], 10_000)
        self.assertEqual(self.gate["bootstrap"]["site_count"], 2)
        self.assertEqual(self.gate["bootstrap"]["resampling_unit"], "site_ref")
        self.assertEqual(
            tuple(item["policy"] for item in self.gate["policy_statistics"]),
            EXPECTED_POLICIES,
        )
        for item in self.gate["policy_statistics"]:
            self.assertTrue(
                {
                    "natural_quality",
                    "natural_visible_agent_tokens",
                    "hard_guard_admissible_rate",
                }.issubset(item)
            )
        self.assertEqual(
            self.gate["state_conformal_derivation"]["source_partition"],
            "calibration",
        )
        self.assertIn(
            "adapted_after_development_outcomes",
            self.gate["state_conformal_derivation"],
        )
        self.assertFalse(
            self.gate["state_conformal_derivation"][
                "adapted_after_development_outcomes"
            ]
        )
        self.assertEqual(
            set(self.gate["state_conformal_derivation"]["source_bindings"]),
            {
                "group_assignments_sha256",
                "primary_predictions_sha256",
                "private_labels_sha256",
            },
        )
        self.assertFalse(self.gate["usage_claims"]["invoice_grade_cost"])
        self.assertFalse(self.gate["usage_claims"]["total_compute"])
        self.assertTrue(self.gate["usage_claims"]["visible_agent_tokens"])
        self.assertEqual(self.gate["access_audit"]["held_out_bundle_reads"], 0)

    def test_gate_binds_exact_implementation_closure_and_lexical_collision(self) -> None:
        self.assertEqual(
            set(self.gate["replay_implementation"]),
            EXPECTED_IMPLEMENTATION_CLOSURE,
        )
        contrast = self.gate["policy_contrasts"]["lexical_du_vs_max_cap"]
        self.assertTrue(contrast["algorithmically_distinct"])
        self.assertTrue(contrast["empirically_identical_to_max_cap"])
        self.assertEqual(contrast["matching_stop_turns"], 180)
        self.assertEqual(contrast["trajectory_count"], 180)
        grouped: dict[str, dict[str, int]] = defaultdict(dict)
        for row in self.rows:
            if row["policy"] in {"lexical_du", "max_cap"}:
                grouped[str(row["trajectory_id"])][str(row["policy"])] = int(
                    row["stop_turn"]
                )
        collision_vector = [
            [
                trajectory_id,
                values["lexical_du"],
                values["max_cap"],
                values["lexical_du"] == values["max_cap"],
            ]
            for trajectory_id, values in sorted(grouped.items())
        ]
        self.assertTrue(all(item[3] for item in collision_vector))
        self.assertEqual(
            contrast["collision_vector_sha256"], _sha256_json(collision_vector)
        )

    def test_gate_persists_every_check_and_failure(self) -> None:
        self.assertEqual(
            set(self.gate["checks"]),
            {
                "cats_empirical_trajectory_coverage_present",
                "cats_mean_quality_delta_bootstrap_lower_gt_negative_0p03",
                "cats_median_visible_agent_token_reduction_gte_0p15",
                "cats_observed_unsafe_stops_eq_0",
            },
        )
        failed = sorted(
            name for name, check in self.gate["checks"].items() if not check["passed"]
        )
        self.assertEqual(self.gate["failures"], failed)
        self.assertEqual(self.gate["passed"], not failed)

    def test_verifier_rejects_bare_self_authentication_and_accepts_trust_modes(
        self,
    ) -> None:
        replay = _module()
        with self.assertRaises(ValueError):
            replay.verify_replay_outputs(self.first)
        replay.verify_replay_outputs(
            self.first,
            snapshot=SNAPSHOT,
            dataset=DATASET,
            models=MODELS,
        )
        gate_digest = hashlib.sha256(self.gate_bytes).hexdigest()
        replay.verify_replay_outputs(
            self.first,
            expected_gate_file_sha256=gate_digest,
        )
        with self.assertRaises(ValueError):
            replay.verify_replay_outputs(
                self.first,
                expected_gate_file_sha256="0" * 64,
            )

    def test_source_recomputation_rejects_adversarial_rehashed_gate(self) -> None:
        replay = _module()
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "tampered"
            copied.mkdir()
            (copied / "replay_rows.jsonl").write_bytes(self.rows_bytes)
            gate = copy.deepcopy(self.gate)
            gate["passed"] = True
            gate["failures"] = []
            gate["checks"]["cats_observed_unsafe_stops_eq_0"]["observed"] = 0
            gate["checks"]["cats_observed_unsafe_stops_eq_0"]["passed"] = True
            gate["bootstrap"]["lower_95"] = 0.25
            gate["policy_statistics"][8]["unsafe_stops"] = 0
            gate["source_hashes"][next(iter(gate["source_hashes"]))] = "1" * 64
            gate["replay_implementation"]["iclr2027/io.py"] = "2" * 64
            _write_gate(copied / "development_gate.json", gate)
            with self.assertRaises(ValueError):
                replay.verify_replay_outputs(
                    copied,
                    snapshot=SNAPSHOT,
                    dataset=DATASET,
                    models=MODELS,
                )

    def test_source_recomputation_rejects_rehashed_helper_binding(self) -> None:
        replay = _module()
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "tampered"
            copied.mkdir()
            (copied / "replay_rows.jsonl").write_bytes(self.rows_bytes)
            gate = copy.deepcopy(self.gate)
            gate["replay_implementation"]["iclr2027/io.py"] = "3" * 64
            _write_gate(copied / "development_gate.json", gate)
            with self.assertRaises(ValueError):
                replay.verify_replay_outputs(
                    copied,
                    snapshot=SNAPSHOT,
                    dataset=DATASET,
                    models=MODELS,
                )

    def test_source_recomputation_rejects_same_length_wrong_hash_and_tokens(
        self,
    ) -> None:
        replay = _module()
        for mutation in ("hash", "tokens"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                copied = Path(temporary) / "tampered"
                copied.mkdir()
                rows = copy.deepcopy(self.rows)
                gate = copy.deepcopy(self.gate)
                if mutation == "hash":
                    original = str(rows[0]["message_hashes"][0])
                    rows[0]["message_hashes"][0] = (
                        ("0" if original[0] != "0" else "1") + original[1:]
                    )
                else:
                    original = int(rows[0]["visible_agent_tokens"])
                    replacement = original + 1 if len(str(original + 1)) == len(str(original)) else original - 1
                    rows[0]["visible_agent_tokens"] = replacement
                _write_rows_and_rebind_gate(copied, rows, gate)
                with self.assertRaises(ValueError):
                    replay.verify_replay_outputs(
                        copied,
                        snapshot=SNAPSHOT,
                        dataset=DATASET,
                        models=MODELS,
                    )

    def test_output_receipt_and_row_tampering_fail_closed(self) -> None:
        replay = _module()
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "tampered"
            copied.mkdir()
            (copied / "replay_rows.jsonl").write_bytes(self.rows_bytes + b"{}\n")
            (copied / "development_gate.json").write_bytes(self.gate_bytes)
            with self.assertRaises(ValueError):
                replay.verify_replay_outputs(
                    copied,
                    snapshot=SNAPSHOT,
                    dataset=DATASET,
                    models=MODELS,
                )
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "tampered"
            copied.mkdir()
            (copied / "replay_rows.jsonl").write_bytes(self.rows_bytes)
            gate = dict(self.gate)
            gate["passed"] = not gate["passed"]
            (copied / "development_gate.json").write_text(
                json.dumps(gate), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                replay.verify_replay_outputs(
                    copied,
                    snapshot=SNAPSHOT,
                    dataset=DATASET,
                    models=MODELS,
                )

    def test_two_independent_output_directories_are_byte_identical(self) -> None:
        self.assertEqual(
            self.rows_bytes, (self.second / "replay_rows.jsonl").read_bytes()
        )
        self.assertEqual(
            self.gate_bytes, (self.second / "development_gate.json").read_bytes()
        )


if __name__ == "__main__":
    unittest.main()
