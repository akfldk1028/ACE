"""Independent contract tests for the public mutation census."""

from __future__ import annotations

import ast
import hashlib
import importlib
import itertools
import json
import unittest
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from types import ModuleType

from iclr2027.estimand_receipt_generator import generate_clean_benchmark
from iclr2027.estimand_receipts import ObservedArtifactV1, ObservedReceiptV1


EXPECTED_ATOMIC_FAULTS = tuple(
    sorted(
        (
            "execution_omit_geometry",
            "execution_omit_law",
            "execution_omit_parking",
            "execution_omit_program",
            "execution_omit_site_evidence",
            "target_rebind_same_site_same_assignment",
            "target_rebind_same_site_other_assignment",
            "target_rebind_other_site_same_assignment",
            "target_rebind_other_site_other_assignment",
            "terminal_stale_owner",
            "terminal_stale_value",
            "terminal_stale_owner_and_value",
            "scorer_drop_geometry",
            "scorer_duplicate_geometry_as_shadow",
            "scorer_shift_geometry_to_law",
            "scorer_replace_program_with_shadow",
            "protocol_stale_incompatible",
            "protocol_future_incompatible",
            "policy_menu_drift",
            "policy_information_snapshot_drift",
            "policy_cost_drift",
            "policy_decision_event_drift",
        ),
        key=lambda value: value.encode("utf-8"),
    )
)
EXPECTED_CONTROLS = tuple(
    sorted(
        (
            "protocol_registered_compatible",
            "scorer_add_zero_mass_shadow",
            "target_registered_within_stratum",
        ),
        key=lambda value: value.encode("utf-8"),
    )
)
FAMILY_ORDER = ("E", "B", "T", "S", "G", "P")
REPRESENTATIVES = {
    "E": "execution_omit_geometry",
    "B": "target_rebind_same_site_same_assignment",
    "T": "terminal_stale_owner",
    "S": "scorer_drop_geometry",
    "G": "protocol_stale_incompatible",
    "P": "policy_menu_drift",
}
FAMILY_BY_FAULT = {
    **{name: "E" for name in EXPECTED_ATOMIC_FAULTS if name.startswith("execution_")},
    **{name: "B" for name in EXPECTED_ATOMIC_FAULTS if name.startswith("target_")},
    **{name: "T" for name in EXPECTED_ATOMIC_FAULTS if name.startswith("terminal_")},
    **{name: "S" for name in EXPECTED_ATOMIC_FAULTS if name.startswith("scorer_")},
    **{name: "G" for name in EXPECTED_ATOMIC_FAULTS if name.startswith("protocol_")},
    **{name: "P" for name in EXPECTED_ATOMIC_FAULTS if name.startswith("policy_")},
}
STATUS_BY_FAMILIES = {
    "tau_itt": frozenset(("B", "T", "S", "G")),
    "tau_cb": frozenset(("E", "B", "T", "S", "G")),
    "psi_natural": frozenset(("B", "T", "S", "G", "P")),
}


def _fault_module() -> ModuleType:
    try:
        return importlib.import_module("iclr2027.estimand_receipt_faults")
    except ModuleNotFoundError as exc:
        raise AssertionError("estimand_receipt_faults must be implemented") from exc


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _unit_coordinates(unit_id: str) -> tuple[int, int]:
    prefix, site_text, target_text = unit_id.rsplit("-", 2)
    if prefix != "syn-target":
        raise AssertionError(unit_id)
    return int(site_text), int(target_text)


def _partner_coordinates(unit_id: str, mutation_name: str) -> tuple[int, int] | None:
    site, target = _unit_coordinates(unit_id)
    if mutation_name == "target_rebind_same_site_same_assignment":
        return site, target ^ 4
    if mutation_name == "target_rebind_same_site_other_assignment":
        return site, target ^ 1
    if mutation_name == "target_rebind_other_site_same_assignment":
        return site ^ 1, target
    if mutation_name == "target_rebind_other_site_other_assignment":
        return site ^ 1, target ^ 1
    if mutation_name == "target_registered_within_stratum":
        return site, target ^ 2
    return None


def _artifact_map() -> dict[tuple[int, int], ObservedArtifactV1]:
    return {
        _unit_coordinates(artifact.unit_id): artifact
        for artifact in generate_clean_benchmark().artifacts
    }


def _payload_digest_is_valid(artifact: ObservedArtifactV1) -> bool:
    value = artifact.to_dict()
    observed = value.pop("payload_sha256")
    return observed == _sha256_json(value)


class FaultRegistryAndOperatorTests(unittest.TestCase):
    def test_registry_is_the_exact_byte_sorted_public_contract(self) -> None:
        # Catches a missing, renamed, added, or source-ordered mutation/control.
        module = _fault_module()

        self.assertEqual(module.ATOMIC_FAULTS, EXPECTED_ATOMIC_FAULTS)
        self.assertEqual(module.INVARIANCE_CONTROLS, EXPECTED_CONTROLS)
        self.assertEqual(len(module.ATOMIC_FAULTS), 22)

    def test_every_atomic_operator_has_one_intended_semantic_delta_and_reseals(
        self,
    ) -> None:
        # Catches cross-family field corruption and stale payload digests.
        module = _fault_module()
        clean = generate_clean_benchmark()
        source = clean.artifacts[0]
        artifacts = _artifact_map()
        base = source.to_dict()
        expected_top_level = {
            **{
                name: {"executed_action_id"}
                for name in EXPECTED_ATOMIC_FAULTS
                if FAMILY_BY_FAULT[name] == "E"
            },
            **{
                name: {"target_binding_sha256"}
                for name in EXPECTED_ATOMIC_FAULTS
                if FAMILY_BY_FAULT[name] == "B"
            },
            "terminal_stale_owner": {"terminal_owner_id"},
            "terminal_stale_value": {"terminal_value_sha256"},
            "terminal_stale_owner_and_value": {
                "terminal_owner_id",
                "terminal_value_sha256",
            },
            **{
                name: {"scorer_weights"}
                for name in EXPECTED_ATOMIC_FAULTS
                if FAMILY_BY_FAULT[name] == "S"
            },
            **{
                name: {"protocol_version"}
                for name in EXPECTED_ATOMIC_FAULTS
                if FAMILY_BY_FAULT[name] == "G"
            },
            **{
                name: {"policy_record"}
                for name in EXPECTED_ATOMIC_FAULTS
                if FAMILY_BY_FAULT[name] == "P"
            },
        }
        for name in EXPECTED_ATOMIC_FAULTS:
            coordinates = _partner_coordinates(source.unit_id, name)
            partner = source if coordinates is None else artifacts[coordinates]
            with self.subTest(name=name):
                mutated = module.apply_fault(source, name, partner=partner)
                value = mutated.to_dict()
                changed = {key for key in base if base[key] != value[key]} - {
                    "payload_sha256"
                }
                self.assertEqual(changed, expected_top_level[name])
                self.assertNotEqual(value["payload_sha256"], base["payload_sha256"])
                self.assertTrue(_payload_digest_is_valid(mutated))
                self.assertEqual(
                    ObservedArtifactV1.from_dict(value).to_dict(),
                    value,
                )

    def test_execution_terminal_protocol_and_policy_values_are_exact(self) -> None:
        # Catches plausible-looking but unregistered semantic replacement values.
        module = _fault_module()
        source = generate_clean_benchmark().artifacts[0]
        for domain in ("geometry", "law", "parking", "program", "site_evidence"):
            with self.subTest(domain=domain):
                observed = module.apply_fault(
                    source, f"execution_omit_{domain}", partner=source
                )
                self.assertEqual(
                    observed.executed_action_id,
                    f"partial-action-omit-{domain}-v1",
                )
                self.assertEqual(observed.executed_members, source.executed_members)

        stale_value = _sha256_json(
            {
                "schema_version": "fault-terminal/v1",
                "unit_id": source.unit_id,
                "source_terminal_value_sha256": source.terminal_value_sha256,
            }
        )
        terminal_cases = {
            "terminal_stale_owner": (
                f"{source.terminal_owner_id}-stale",
                source.terminal_value_sha256,
            ),
            "terminal_stale_value": (source.terminal_owner_id, stale_value),
            "terminal_stale_owner_and_value": (
                f"{source.terminal_owner_id}-stale",
                stale_value,
            ),
        }
        for name, expected in terminal_cases.items():
            with self.subTest(name=name):
                observed = module.apply_fault(source, name, partner=source)
                self.assertEqual(
                    (observed.terminal_owner_id, observed.terminal_value_sha256),
                    expected,
                )

        protocols = {
            "protocol_stale_incompatible": "estimand-receipt-protocol-v0-stale",
            "protocol_future_incompatible": "estimand-receipt-protocol-v2-future",
        }
        for name, expected in protocols.items():
            with self.subTest(name=name):
                self.assertEqual(
                    module.apply_fault(source, name, partner=source).protocol_version,
                    expected,
                )

        policy_cases = {
            "policy_menu_drift": {
                "action_menu": [
                    "action-baseline-v1",
                    "action-receipt-v1",
                    "action-shadow-v1",
                ]
            },
            "policy_information_snapshot_drift": {
                "information_snapshot_sha256": _sha256_json(
                    {
                        "schema_version": "fault-policy-information-snapshot/v1",
                        "unit_id": source.unit_id,
                        "source_information_snapshot_sha256": source.policy_record.information_snapshot_sha256,
                    }
                )
            },
            "policy_cost_drift": {"realized_cost": 2.0},
            "policy_decision_event_drift": {
                "decision_event_sha256": _sha256_json(
                    {
                        "schema_version": "fault-policy-decision-event/v1",
                        "unit_id": source.unit_id,
                        "source_decision_event_sha256": source.policy_record.decision_event_sha256,
                    }
                )
            },
        }
        for name, expected_fields in policy_cases.items():
            with self.subTest(name=name):
                observed = module.apply_fault(source, name, partner=source)
                observed_policy = observed.policy_record.to_dict()
                for key, expected in expected_fields.items():
                    self.assertEqual(observed_policy[key], expected)
                changed = {
                    key
                    for key, clean_value in source.policy_record.to_dict().items()
                    if observed_policy[key] != clean_value
                }
                self.assertEqual(changed, set(expected_fields))

    def test_scorer_mutations_are_exact_unique_key_probability_maps(self) -> None:
        # Catches wrong masses, invalid duplicate keys, and shadow-key confusion.
        module = _fault_module()
        source = generate_clean_benchmark().artifacts[0]
        expected = {
            "scorer_drop_geometry": {
                "law": 0.25,
                "parking": 0.25,
                "program": 0.25,
                "site_evidence": 0.25,
            },
            "scorer_duplicate_geometry_as_shadow": {
                "geometry": 0.1,
                "geometry_shadow": 0.1,
                "law": 0.2,
                "parking": 0.2,
                "program": 0.2,
                "site_evidence": 0.2,
            },
            "scorer_shift_geometry_to_law": {
                "geometry": 0.3,
                "law": 0.1,
                "parking": 0.2,
                "program": 0.2,
                "site_evidence": 0.2,
            },
            "scorer_replace_program_with_shadow": {
                "geometry": 0.2,
                "law": 0.2,
                "parking": 0.2,
                "program_shadow": 0.2,
                "site_evidence": 0.2,
            },
        }
        for name, expected_map in expected.items():
            with self.subTest(name=name):
                observed = module.apply_fault(source, name, partner=source)
                observed_map = {row.key: row.weight for row in observed.scorer_weights}
                self.assertEqual(observed_map, expected_map)
                self.assertEqual(len(observed_map), len(observed.scorer_weights))
                self.assertAlmostEqual(sum(observed_map.values()), 1.0)

    def test_target_rebinding_uses_exact_nonregistered_xor_partners(self) -> None:
        # Catches off-by-one/site swaps and accidental use of the registered ^2 pair.
        module = _fault_module()
        clean = generate_clean_benchmark()
        artifacts = {
            _unit_coordinates(artifact.unit_id): artifact
            for artifact in clean.artifacts
        }
        commitment_by_id = {item.unit_id: item for item in clean.trust_root.commitments}
        for source in clean.artifacts:
            for name in EXPECTED_ATOMIC_FAULTS:
                coordinates = _partner_coordinates(source.unit_id, name)
                if coordinates is None:
                    continue
                with self.subTest(unit=source.unit_id, name=name):
                    partner = artifacts[coordinates]
                    observed = module.apply_fault(source, name, partner=partner)
                    self.assertEqual(
                        observed.target_binding_sha256,
                        partner.target_binding_sha256,
                    )
                    self.assertNotIn(
                        observed.target_binding_sha256,
                        commitment_by_id[source.unit_id].allowed_target_binding_sha256,
                    )
                    self.assertEqual(observed.unit_id, source.unit_id)
                    self.assertEqual(observed.site_id, source.site_id)

    def test_unknown_fault_and_wrong_types_are_rejected(self) -> None:
        # Catches silent fallbacks that could label an unchanged artifact as faulty.
        module = _fault_module()
        source = generate_clean_benchmark().artifacts[0]
        with self.assertRaises(ValueError):
            module.apply_fault(source, "not-registered", partner=source)
        with self.assertRaises(TypeError):
            module.apply_fault({}, EXPECTED_ATOMIC_FAULTS[0], partner=source)
        with self.assertRaises(TypeError):
            module.apply_fault(source, EXPECTED_ATOMIC_FAULTS[0], partner={})


class PublicCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _fault_module()
        cls.clean = generate_clean_benchmark()
        cls.census = cls.module.materialize_public_census(cls.clean)

    def test_public_census_has_exact_independently_derived_decomposition(self) -> None:
        # Catches omitted cases, one-order compounds, and count padding.
        expected_counts = {
            "clean": 64,
            "single": 64 * 22,
            "ordered_compound": 64 * 2 * 15,
            "invariance": 64 * 3,
        }
        self.assertEqual(self.census.counts, expected_counts)
        self.assertEqual(len(self.census.rows), sum(expected_counts.values()))
        self.assertEqual(len(self.census.artifacts), 3_584)
        self.assertEqual(len(self.census.oracle_records), 3_584)
        self.assertEqual(len({row.case_id for row in self.census.rows}), 3_584)

    def test_private_oracle_census_retains_every_required_case_without_public_blocks(
        self,
    ) -> None:
        # Catches case loss while permitting the public channel to anonymize order.
        records = self.census.oracle_records
        self.assertEqual(
            Counter(record.case_kind for record in records),
            {
                "clean": 64,
                "single": 1_408,
                "ordered_compound": 1_920,
                "invariance": 192,
            },
        )
        single_names = Counter(
            record.mutation_names for record in records if record.case_kind == "single"
        )
        self.assertEqual(single_names, {(name,): 64 for name in EXPECTED_ATOMIC_FAULTS})
        control_names = Counter(
            record.mutation_names
            for record in records
            if record.case_kind == "invariance"
        )
        self.assertEqual(control_names, {(name,): 64 for name in EXPECTED_CONTROLS})
        compound_orders = Counter(
            record.families
            for record in records
            if record.case_kind == "ordered_compound"
        )
        expected_orders = {}
        for left, right in itertools.combinations(FAMILY_ORDER, 2):
            expected_orders[(left, right)] = 64
            expected_orders[(right, left)] = 64
        self.assertEqual(compound_orders, expected_orders)

    def test_legacy_public_indices_do_not_reveal_fixed_private_decisions(self) -> None:
        # Catches restoration of the exact legacy 64-row oracle block channel.
        leaked_single = (
            "single",
            ("execution_omit_geometry",),
            ("E",),
            ("CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
        )
        leaked_compound = (
            "ordered_compound",
            (
                "execution_omit_geometry",
                "target_rebind_same_site_same_assignment",
            ),
            ("E", "B"),
            ("NOT_CERTIFIED", "NOT_CERTIFIED", "NOT_CERTIFIED"),
        )
        at_64 = self.census.rows[64].oracle
        at_1472 = self.census.rows[1_472].oracle
        self.assertNotEqual(
            (
                at_64.case_kind,
                at_64.mutation_names,
                at_64.families,
                at_64.expected_statuses,
            ),
            leaked_single,
        )
        self.assertNotEqual(
            (
                at_1472.case_kind,
                at_1472.mutation_names,
                at_1472.families,
                at_1472.expected_statuses,
            ),
            leaked_compound,
        )

    def test_public_ids_and_order_ignore_private_row_permutations(self) -> None:
        # Catches public order or duplicate ranks inherited from private labels/order.
        rows = self.census.rows
        permutations = (
            tuple(reversed(rows)),
            rows[::2] + rows[1::2],
            rows[1::3] + rows[2::3] + rows[::3],
        )
        expected = _canonical_bytes(self.census.public_to_dict())
        expected_ids = tuple(row.case_id for row in self.census.rows)
        for index, private_rows in enumerate(permutations):
            with self.subTest(permutation=index):
                rebuilt = self.module.PublicMutationCensusV1(
                    schema_version="public-mutation-census/v1",
                    trust_root=self.clean.trust_root,
                    rows=private_rows,
                )
                self.assertEqual(_canonical_bytes(rebuilt.public_to_dict()), expected)
                self.assertEqual(
                    tuple(row.case_id for row in rebuilt.rows), expected_ids
                )

    def test_anonymous_ids_are_exact_hash_rank_ids_and_public_rows_are_id_sorted(
        self,
    ) -> None:
        # Catches label-derived IDs, label-derived tie breaks, and positional joins.
        grouped_ids: dict[bytes, list[str]] = defaultdict(list)
        grouped_hashes: dict[bytes, set[str]] = defaultdict(set)
        for row in self.census.rows:
            artifact_bytes = _canonical_bytes(row.artifact.to_dict())
            grouped_ids[artifact_bytes].append(row.case_id)
            grouped_hashes[artifact_bytes].add(row.artifact_sha256)
        for artifact_bytes, observed_ids in grouped_ids.items():
            self.assertEqual(len(grouped_hashes[artifact_bytes]), 1)
            artifact_sha256 = next(iter(grouped_hashes[artifact_bytes]))
            expected_ids = {
                _sha256_json(
                    {
                        "schema_version": "public-case-id/v1",
                        "artifact_sha256": artifact_sha256,
                        "occurrence_rank": rank,
                    }
                )
                for rank in range(len(observed_ids))
            }
            self.assertEqual(set(observed_ids), expected_ids)

        public_rows = self.census.public_to_dict()["artifact_rows"]
        public_ids = tuple(row["case_id"] for row in public_rows)
        oracle_rows = self.census.oracle_to_dict()["oracle_records"]
        ordered_oracle_ids = tuple(row["case_id"] for row in oracle_rows)
        oracle_ids = set(ordered_oracle_ids)
        self.assertEqual(
            public_ids,
            tuple(sorted(public_ids, key=lambda value: value.encode("utf-8"))),
        )
        self.assertEqual(set(public_ids), oracle_ids)
        self.assertEqual(len(public_ids), len(oracle_ids))
        self.assertNotEqual(public_ids, ordered_oracle_ids)

    def test_byte_identical_artifacts_with_different_oracle_decisions_are_rejected(
        self,
    ) -> None:
        # Catches hidden-label tie breaking for a genuinely ambiguous public input.
        groups: dict[bytes, list[object]] = defaultdict(list)
        for row in self.census.rows:
            groups[_canonical_bytes(row.artifact.to_dict())].append(row)
        duplicate_group = next(group for group in groups.values() if len(group) > 1)
        source = duplicate_group[0]
        changed_statuses = (
            "CERTIFIED",
            "CERTIFIED",
            "CERTIFIED",
        )
        if source.oracle.expected_statuses == changed_statuses:
            changed_statuses = (
                "NOT_CERTIFIED",
                "NOT_CERTIFIED",
                "NOT_CERTIFIED",
            )
        ambiguous_oracle = replace(
            duplicate_group[1].oracle,
            expected_statuses=changed_statuses,
        )
        ambiguous_row = replace(
            duplicate_group[1],
            oracle=ambiguous_oracle,
        )
        rows = list(self.census.rows)
        rows[rows.index(duplicate_group[1])] = ambiguous_row
        with self.assertRaisesRegex(ValueError, "ambiguous census"):
            self.module.PublicMutationCensusV1(
                schema_version="public-mutation-census/v1",
                trust_root=self.clean.trust_root,
                rows=tuple(rows),
            )

    def test_every_row_is_locally_valid_and_fully_resealed(self) -> None:
        # Catches stale payload or census-level artifact digests.
        for row in self.census.rows:
            with self.subTest(case_id=row.case_id):
                value = row.artifact.to_dict()
                self.assertEqual(ObservedArtifactV1.from_dict(value).to_dict(), value)
                self.assertTrue(_payload_digest_is_valid(row.artifact))
                self.assertEqual(row.artifact_sha256, _sha256_json(value))

    def test_clean_artifacts_and_external_trust_root_bytes_are_unchanged(self) -> None:
        # Catches mutation of the trust anchor or replacement of clean rows.
        self.assertEqual(
            _canonical_bytes(self.census.trust_root.to_dict()),
            _canonical_bytes(self.clean.trust_root.to_dict()),
        )
        clean_by_unit = {
            row.artifact.unit_id: row
            for row in self.census.rows
            if row.oracle.case_kind == "clean"
        }
        self.assertEqual(len(clean_by_unit), 64)
        for source in self.clean.artifacts:
            row = clean_by_unit[source.unit_id]
            self.assertIs(row.artifact, source)
            self.assertEqual(row.artifact_sha256, _sha256_json(source.to_dict()))

    def test_oracle_channels_are_separate_stable_and_absent_from_evaluated_bytes(
        self,
    ) -> None:
        # Catches evaluator-visible gold labels and unstable oracle serialization.
        rerun = self.module.materialize_public_census(generate_clean_benchmark())
        self.assertEqual(self.census.to_dict(), rerun.to_dict())
        forbidden_keys = (
            b'"oracle"',
            b'"case_kind"',
            b'"mutation_names"',
            b'"families"',
            b'"partner_unit_ids"',
            b'"expected_statuses"',
        )
        for row in self.census.rows:
            evaluated = _canonical_bytes(row.artifact.to_dict())
            with self.subTest(case_id=row.case_id):
                public_row = row.public_to_dict()
                self.assertEqual(
                    set(public_row),
                    {"schema_version", "case_id", "artifact"},
                )
                self.assertEqual(public_row["schema_version"], "public-artifact-row/v1")
                self.assertEqual(public_row["case_id"], row.case_id)
                self.assertEqual(public_row["artifact"], row.artifact.to_dict())
                for key in forbidden_keys:
                    self.assertNotIn(key, evaluated)
                for label in row.oracle.mutation_names:
                    self.assertNotIn(label.encode("utf-8"), evaluated)
                for partner_id in row.oracle.partner_unit_ids:
                    self.assertNotIn(partner_id.encode("utf-8"), evaluated)
                self.assertNotIn(row.oracle.case_kind.encode("utf-8"), evaluated)
                for status in row.oracle.expected_statuses:
                    self.assertNotIn(status.encode("utf-8"), evaluated)

    def test_oracle_expected_statuses_are_independent_family_unions(self) -> None:
        # Catches all-estimand blocking where only E or P should be selective.
        estimands = ("tau_itt", "tau_cb", "psi_natural")
        for row in self.census.rows:
            families = frozenset(row.oracle.families)
            expected = tuple(
                "NOT_CERTIFIED"
                if families & STATUS_BY_FAMILIES[estimand]
                else "CERTIFIED"
                for estimand in estimands
            )
            with self.subTest(case_id=row.case_id):
                self.assertEqual(row.oracle.expected_statuses, expected)

    def test_partner_records_and_target_bindings_follow_exact_census_arithmetic(
        self,
    ) -> None:
        # Catches a correct operator fed the wrong census partner.
        artifact_by_coordinates = {
            _unit_coordinates(artifact.unit_id): artifact
            for artifact in self.clean.artifacts
        }
        for row in self.census.rows:
            names = row.oracle.mutation_names
            target_names = tuple(
                name
                for name in names
                if name.startswith("target_rebind_")
                or name == "target_registered_within_stratum"
            )
            if not target_names:
                self.assertEqual(row.oracle.partner_unit_ids, ())
                continue
            self.assertEqual(len(target_names), 1)
            expected_coordinates = _partner_coordinates(
                row.artifact.unit_id, target_names[0]
            )
            self.assertIsNotNone(expected_coordinates)
            expected_partner = artifact_by_coordinates[expected_coordinates]
            with self.subTest(case_id=row.case_id):
                self.assertEqual(
                    row.oracle.partner_unit_ids, (expected_partner.unit_id,)
                )
                self.assertEqual(
                    row.artifact.target_binding_sha256,
                    expected_partner.target_binding_sha256,
                )

    def test_commutative_compound_bytes_remain_two_distinct_cases(self) -> None:
        # Catches deduplication of the required order-sensitive case population.
        forward = next(
            row
            for row in self.census.rows
            if row.oracle.families == ("E", "B")
            and row.artifact.unit_id == self.clean.artifacts[0].unit_id
        )
        reverse = next(
            row
            for row in self.census.rows
            if row.oracle.families == ("B", "E")
            and row.artifact.unit_id == self.clean.artifacts[0].unit_id
        )
        self.assertNotEqual(forward.case_id, reverse.case_id)
        self.assertNotEqual(forward.oracle.to_dict(), reverse.oracle.to_dict())
        self.assertEqual(forward.artifact.to_dict(), reverse.artifact.to_dict())
        self.assertEqual(forward.artifact_sha256, reverse.artifact_sha256)

    def test_registered_invariances_certify_when_embedded_in_full_receipt(self) -> None:
        # Catches controls that are schema-valid but not registered equivalences.
        from iclr2027.estimand_receipts import evaluate_reportability

        trust_root_sha256 = _sha256_json(self.clean.trust_root.to_dict())
        unit_id = self.clean.artifacts[0].unit_id
        for control in EXPECTED_CONTROLS:
            mutation = next(
                row.artifact
                for row in self.census.rows
                if row.oracle.case_kind == "invariance"
                and row.oracle.mutation_names == (control,)
                and row.artifact.unit_id == unit_id
            )
            artifacts = (mutation, *self.clean.artifacts[1:])
            payload = {
                "schema_version": "observed-receipt/v1",
                "study_id": self.clean.study_id,
                "trust_root_sha256": trust_root_sha256,
                "artifacts": [item.to_dict() for item in artifacts],
            }
            receipt = ObservedReceiptV1.from_dict(
                {**payload, "payload_sha256": _sha256_json(payload)}
            )
            with self.subTest(control=control):
                self.assertEqual(
                    tuple(
                        decision.status
                        for decision in evaluate_reportability(
                            receipt, self.clean.trust_root
                        )
                    ),
                    ("CERTIFIED", "CERTIFIED", "CERTIFIED"),
                )

    def test_fault_module_has_no_verifier_or_oracle_import_capability(self) -> None:
        # Catches direct access to the decision code or future oracle labels.
        source_path = (
            Path(__file__).parents[1] / "iclr2027" / "estimand_receipt_faults.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        project_imports = tuple(
            name for name in imports if name.startswith("iclr2027.")
        )
        self.assertEqual(
            project_imports,
            (
                "iclr2027.estimand_receipt_generator",
                "iclr2027.io",
            ),
        )
        self.assertFalse(any("oracle" in name for name in imports))
        self.assertFalse(any("verifier" in name for name in imports))


if __name__ == "__main__":
    unittest.main()
