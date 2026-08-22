from __future__ import annotations

import copy
import unittest


_IDENTITY_FIELDS = (
    "schema_version",
    "input_mode",
    "split",
    "patterns",
    "repeats",
    "model",
    "code_commit",
    "case_count",
    "expected_case_count",
    "planned_run_count",
    "stage_case_counts",
    "decision_case_counts",
    "input_hashes",
    "identity_commitment",
    "registry_core_sha256",
    "split_manifest_sha256",
    "plan_sha256",
)


def _api():
    try:
        from iclr2027.run_manifest import (
            RUN_MANIFEST_SCHEMA,
            run_manifest_identity,
            validate_run_manifest,
        )
    except (ImportError, ModuleNotFoundError) as exc:
        raise AssertionError(f"run manifest validator is missing: {exc}") from exc
    return RUN_MANIFEST_SCHEMA, run_manifest_identity, validate_run_manifest


def _input_hashes(count: int) -> dict[str, str]:
    digests = [f"{index:064x}" for index in range(1, count + 1)]
    return {f"input:{digest}": digest for digest in digests}


def _planned_manifest() -> dict:
    return {
        "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
        "input_mode": "frozen_private_binding",
        "split": "dev",
        "patterns": ["rr3", "sel3", "swm3", "refl3", "debate3"],
        "repeats": 1,
        "model": "fixture-model",
        "code_commit": "fixture-commit",
        "case_count": 7,
        "expected_case_count": 30,
        "planned_run_count": 35,
        "stage_case_counts": {
            "execution": 3,
            "selection": 1,
            "materialization": 1,
            "preflight": 1,
            "candidate_floor_context": 1,
        },
        "decision_case_counts": {
            "STOP_ACCEPT": 2,
            "STOP_REJECT": 4,
            "CONTINUE": 1,
        },
        "input_hashes": _input_hashes(6),
        "identity_commitment": "a" * 64,
        "registry_core_sha256": "b" * 64,
        "split_manifest_sha256": "c" * 64,
        "plan_sha256": "d" * 64,
        "executed": False,
    }


def _executed_manifest() -> dict:
    manifest = _planned_manifest()
    manifest.update(
        {
            "executed": True,
            "execution": {
                "completed_runs": 35,
                "skipped_runs": 0,
                "error_runs": 0,
                "parsed_states": 70,
                "successful_parses": 70,
            },
            "estimated_cost_per_run_usd": 0.25,
            "estimated_total_cost_usd": 8.75,
            "estimated_completion_date": "2026-09-01",
        }
    )
    return manifest


class RunManifestV2Tests(unittest.TestCase):
    def test_actual_seven_case_planned_manifest_is_valid(self) -> None:
        schema, _identity, validate = _api()
        manifest = _planned_manifest()

        validated = validate(manifest)

        self.assertEqual(schema, "ace.iclr2027.exp08_run_manifest.v2")
        self.assertEqual(validated, manifest)
        self.assertIsNot(validated, manifest)
        self.assertIsNot(validated["stage_case_counts"], manifest["stage_case_counts"])

    def test_extra_private_payload_is_rejected_recursively(self) -> None:
        _schema, _identity, validate = _api()
        manifest = _planned_manifest()
        manifest["diagnostics"] = {
            "private_packet": {"pnu": "1" * 19},
        }

        with self.assertRaises(ValueError):
            validate(manifest)

    def test_executed_manifest_has_exact_metadata_schema(self) -> None:
        _schema, _identity, validate = _api()

        validated = validate(_executed_manifest())

        self.assertTrue(validated["executed"])
        self.assertEqual(validated["execution"]["completed_runs"], 35)

        invalid = _executed_manifest()
        invalid["execution"]["unexpected"] = 0
        with self.assertRaises(ValueError):
            validate(invalid)

        missing = _executed_manifest()
        missing.pop("estimated_completion_date")
        with self.assertRaises(ValueError):
            validate(missing)

        planned_with_execution = _planned_manifest()
        planned_with_execution["execution"] = _executed_manifest()["execution"]
        with self.assertRaises(ValueError):
            validate(planned_with_execution)

    def test_stable_identity_projection_is_exact_and_state_independent(self) -> None:
        _schema, identity, _validate = _api()
        planned = _planned_manifest()
        executed = _executed_manifest()

        planned_identity = identity(planned)
        executed_identity = identity(executed)

        self.assertEqual(tuple(planned_identity), _IDENTITY_FIELDS)
        self.assertEqual(planned_identity, executed_identity)
        self.assertNotIn("executed", planned_identity)
        self.assertIsNot(planned_identity["patterns"], planned["patterns"])

    def test_top_level_schema_and_native_scalar_types_fail_closed(self) -> None:
        _schema, _identity, validate = _api()
        mutations = (
            ("schema_version", "ace.iclr2027.exp08_run_manifest.v1"),
            ("input_mode", "other"),
            ("input_mode", []),
            ("split", "train"),
            ("split", []),
            ("patterns", ("rr3",)),
            ("repeats", True),
            ("repeats", 1.0),
            ("model", " "),
            ("code_commit", ""),
            ("case_count", True),
            ("expected_case_count", 7.0),
            ("planned_run_count", False),
            ("executed", 0),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                manifest = _planned_manifest()
                manifest[field] = value
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_sha256_fields_do_not_treat_digest_substrings_as_private_ids(self) -> None:
        _schema, _identity, validate = _api()
        manifest = _planned_manifest()
        digest = "a" + "1" * 19 + "b" * 44
        manifest["identity_commitment"] = digest
        manifest["registry_core_sha256"] = digest
        manifest["split_manifest_sha256"] = digest
        manifest["plan_sha256"] = digest
        manifest["input_hashes"] = {
            f"input:{digest}": digest,
            **{
                key: value
                for key, value in _input_hashes(6).items()
                if value != f"{1:064x}"
            },
        }

        self.assertEqual(validate(manifest), manifest)

    def test_patterns_are_nonempty_unique_and_known(self) -> None:
        _schema, _identity, validate = _api()
        patterns = (
            [],
            ["rr3", "rr3"],
            ["rr3", "not-a-pattern"],
            ["rr3", 3],
        )
        for value in patterns:
            with self.subTest(patterns=value):
                manifest = _planned_manifest()
                manifest["patterns"] = value
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_count_composition_is_exact(self) -> None:
        _schema, _identity, validate = _api()
        mutations = (
            ("repeats", 0),
            ("case_count", 0),
            ("expected_case_count", 6),
            ("planned_run_count", 34),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                manifest = _planned_manifest()
                manifest[field] = value
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_stage_and_decision_censuses_are_exact(self) -> None:
        _schema, _identity, validate = _api()
        mutations = []
        unknown_stage = _planned_manifest()
        unknown_stage["stage_case_counts"] = {"other": 7}
        mutations.append(unknown_stage)
        boolean_stage = _planned_manifest()
        boolean_stage["stage_case_counts"]["execution"] = True
        mutations.append(boolean_stage)
        zero_stage = _planned_manifest()
        zero_stage["stage_case_counts"]["execution"] = 0
        mutations.append(zero_stage)
        wrong_stage_sum = _planned_manifest()
        wrong_stage_sum["stage_case_counts"]["execution"] = 2
        mutations.append(wrong_stage_sum)
        unknown_decision = _planned_manifest()
        unknown_decision["decision_case_counts"] = {"MAYBE": 7}
        mutations.append(unknown_decision)
        boolean_decision = _planned_manifest()
        boolean_decision["decision_case_counts"]["STOP_ACCEPT"] = False
        mutations.append(boolean_decision)
        zero_decision = _planned_manifest()
        zero_decision["decision_case_counts"]["STOP_ACCEPT"] = 0
        mutations.append(zero_decision)
        wrong_decision_sum = _planned_manifest()
        wrong_decision_sum["decision_case_counts"]["STOP_REJECT"] = 3
        mutations.append(wrong_decision_sum)

        for index, manifest in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_neutral_input_hashes_have_mode_bound_cardinality_and_content(self) -> None:
        _schema, _identity, validate = _api()
        invalid_values = (
            _input_hashes(2),
            {"dev.native:public": "a" * 64},
            {"input:" + "a" * 64: "b" * 64},
            {"input:" + "A" * 64: "A" * 64},
        )
        for value in invalid_values:
            with self.subTest(value=value):
                manifest = _planned_manifest()
                manifest["input_hashes"] = value
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_public_fixture_uses_two_hashes_and_no_private_commitments(self) -> None:
        _schema, _identity, validate = _api()
        manifest = _planned_manifest()
        manifest.update(
            {
                "input_mode": "public_fixture",
                "input_hashes": _input_hashes(2),
                "identity_commitment": None,
                "registry_core_sha256": None,
                "split_manifest_sha256": None,
                "decision_case_counts": {},
            }
        )

        self.assertEqual(validate(manifest), manifest)

        manifest["identity_commitment"] = "a" * 64
        with self.assertRaises(ValueError):
            validate(manifest)

    def test_frozen_commitments_and_plan_hash_are_lowercase_sha256(self) -> None:
        _schema, _identity, validate = _api()
        fields = (
            "identity_commitment",
            "registry_core_sha256",
            "split_manifest_sha256",
            "plan_sha256",
        )
        for field in fields:
            for value in (None, "a" * 63, "A" * 64, 1):
                with self.subTest(field=field, value=value):
                    manifest = _planned_manifest()
                    manifest[field] = value
                    with self.assertRaises(ValueError):
                        validate(manifest)

    def test_executed_count_and_cost_invariants_fail_closed(self) -> None:
        _schema, _identity, validate = _api()
        mutations = []
        bool_count = _executed_manifest()
        bool_count["execution"]["completed_runs"] = True
        mutations.append(bool_count)
        wrong_total = _executed_manifest()
        wrong_total["execution"]["skipped_runs"] = 1
        mutations.append(wrong_total)
        too_many_errors = _executed_manifest()
        too_many_errors["execution"]["error_runs"] = 36
        mutations.append(too_many_errors)
        too_many_parses = _executed_manifest()
        too_many_parses["execution"]["successful_parses"] = 71
        mutations.append(too_many_parses)
        negative_cost = _executed_manifest()
        negative_cost["estimated_cost_per_run_usd"] = -0.01
        mutations.append(negative_cost)
        bool_cost = _executed_manifest()
        bool_cost["estimated_total_cost_usd"] = True
        mutations.append(bool_cost)
        mismatched_cost = _executed_manifest()
        mismatched_cost["estimated_total_cost_usd"] = 9.0
        mutations.append(mismatched_cost)
        bad_date = _executed_manifest()
        bad_date["estimated_completion_date"] = "2026/09/01"
        mutations.append(bad_date)

        for index, manifest in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_recursive_privacy_audit_rejects_forbidden_tokens_and_paths(self) -> None:
        _schema, _identity, validate = _api()
        forbidden_values = (
            "unknown-model",
            "condition-model",
            "private-model",
            "gold-model",
            "secret-model",
            "internal-model",
            "C:/models/checkpoint",
            "1" * 19,
        )
        for value in forbidden_values:
            with self.subTest(value=value):
                manifest = _planned_manifest()
                manifest["model"] = value
                with self.assertRaises(ValueError):
                    validate(manifest)

    def test_identity_projection_does_not_alias_or_preserve_extra_keys(self) -> None:
        _schema, identity, _validate = _api()
        manifest = _planned_manifest()
        projected = identity(manifest)

        projected["patterns"].append("solo")
        projected["stage_case_counts"]["execution"] = 99

        self.assertEqual(len(manifest["patterns"]), 5)
        self.assertEqual(manifest["stage_case_counts"]["execution"], 3)

        extra = copy.deepcopy(manifest)
        extra["unexpected"] = "safe-looking"
        with self.assertRaises(ValueError):
            identity(extra)


if __name__ == "__main__":
    unittest.main()
