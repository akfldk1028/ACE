from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib
import inspect
import json
import math
from collections.abc import Mapping
import unittest


NONCE_A = "a" * 64
NONCE_B = "b" * 64
ONTOLOGY_HASH = "c" * 64
AUDIT_HASH = "d" * 64
SEED_A = "e" * 64
SEED_B = "f" * 64


def _module():
    try:
        return importlib.import_module("iclr2027.capability_binding")
    except ModuleNotFoundError as error:
        raise AssertionError("capability binding is not implemented") from error


def _profiles(*, first_advantage: float = 0.25, zero_cost: bool = False):
    contract = _module()
    cost = -0.0 if zero_cost else 1.0
    return (
        contract.CapabilityProfile((("geometry.angle", first_advantage),), cost),
        contract.CapabilityProfile((("law.use", -0.5),), cost),
        contract.CapabilityProfile((("parking.supply", 0.75),), cost),
        contract.CapabilityProfile((("program.area", 1.25),), cost),
    )


def _catalog(*, nonce: str = NONCE_A, first_advantage: float = 0.25):
    contract = _module()
    return contract.build_controller_catalog(
        _profiles(first_advantage=first_advantage),
        nonce,
        ONTOLOGY_HASH,
        AUDIT_HASH,
    )


def _packet(action: str, digit: str):
    contract = _module()
    digest = digit * 64
    return contract.CapabilityPacketManifest(
        action=action,
        prompt_sha256=digest,
        tool_manifest_sha256=digest,
        permission_manifest_sha256=digest,
        evidence_scope_sha256=digest,
        budget_contract_sha256=digest,
        output_schema_sha256=digest,
        model_runtime_sha256=digest,
        container_sha256=digest,
    )


def _packets():
    return (
        _packet("ASK_GEOMETRY", "1"),
        _packet("ASK_LAW", "2"),
        _packet("ASK_PARKING", "3"),
        _packet("ASK_PROGRAM", "4"),
    )


def _catalog_and_plan(*, seed: str = SEED_A):
    contract = _module()
    catalog = _catalog()
    plan = contract.build_crossover_plan(catalog, _packets(), seed)
    return catalog, plan


def _assignment_map(binding) -> dict[str, object]:
    return {slot_id: packet for slot_id, packet in binding.assignments}


def _rehash_plan_payload(payload: dict[str, object]) -> None:
    content = {key: value for key, value in payload.items() if key != "plan_id"}
    encoded = json.dumps(
        content,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload["plan_id"] = "plan:" + hashlib.sha256(encoded).hexdigest()


class CapabilityBindingTests(unittest.TestCase):
    def test_profiles_are_frozen_sorted_unique_finite_and_signed_zero_canonical(self) -> None:
        contract = _module()
        unordered = contract.CapabilityProfile(
            (("law.use", -0.0), ("geometry.angle", -2.5)),
            -0.0,
        )
        self.assertEqual(
            unordered.obligation_advantages,
            (("geometry.angle", -2.5), ("law.use", 0.0)),
        )
        self.assertIsInstance(unordered.obligation_advantages, tuple)
        self.assertTrue(
            all(isinstance(pair, tuple) for pair in unordered.obligation_advantages)
        )
        self.assertEqual(math.copysign(1.0, unordered.incremental_cost), 1.0)
        self.assertEqual(
            math.copysign(1.0, unordered.obligation_advantages[1][1]), 1.0
        )
        with self.assertRaises(FrozenInstanceError):
            unordered.incremental_cost = 2.0
        with self.assertRaises(ValueError):
            contract.CapabilityProfile(
                (("law.use", 1.0), ("law.use", 2.0)), 0.0
            )
        for invalid in (math.nan, math.inf, -math.inf, True):
            with self.subTest(advantage=invalid), self.assertRaises(
                (TypeError, ValueError)
            ):
                contract.CapabilityProfile((("law.use", invalid),), 0.0)
        for invalid in (math.nan, math.inf, -math.inf, -0.01, True):
            with self.subTest(cost=invalid), self.assertRaises((TypeError, ValueError)):
                contract.CapabilityProfile((("law.use", 1.0),), invalid)

    def test_catalog_ids_are_salted_content_addressed_and_hand_derived(self) -> None:
        contract = _module()
        profiles = _profiles(first_advantage=-0.0, zero_cost=True)
        catalog = contract.build_controller_catalog(
            profiles, NONCE_A, ONTOLOGY_HASH, AUDIT_HASH
        )
        first = catalog.slots[0]
        profile_json = (
            '{"catalog_nonce":"'
            + NONCE_A
            + '","profile":{"incremental_cost":0.0,'
            '"obligation_advantages":[["geometry.angle",0.0]]}}'
        )
        slot_json = (
            '{"catalog_nonce":"' + NONCE_A + '","slot_index":0}'
        )
        self.assertEqual(
            first.profile.profile_id,
            "profile:"
            + hashlib.sha256(profile_json.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            first.slot_id,
            "slot:" + hashlib.sha256(slot_json.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(math.copysign(1.0, first.profile.incremental_cost), 1.0)
        self.assertEqual(
            math.copysign(1.0, first.profile.obligation_advantages[0][1]), 1.0
        )

        changed_content = _catalog(nonce=NONCE_A, first_advantage=0.5)
        changed_nonce = _catalog(nonce=NONCE_B)
        self.assertEqual(
            tuple(slot.slot_id for slot in catalog.slots),
            tuple(slot.slot_id for slot in changed_content.slots),
        )
        self.assertNotEqual(
            catalog.slots[0].profile.profile_id,
            changed_content.slots[0].profile.profile_id,
        )
        self.assertTrue(
            all(
                left.profile.profile_id != right.profile.profile_id
                for left, right in zip(catalog.slots, changed_nonce.slots, strict=True)
            )
        )
        self.assertTrue(
            all(
                left.slot_id != right.slot_id
                for left, right in zip(catalog.slots, changed_nonce.slots, strict=True)
            )
        )

    def test_catalog_builder_has_no_execution_input_and_rejects_semantic_ids(self) -> None:
        contract = _module()
        self.assertEqual(
            tuple(inspect.signature(contract.build_controller_catalog).parameters),
            (
                "profiles_in_canonical_order",
                "catalog_nonce",
                "obligation_catalog_sha256",
                "capability_audit_sha256",
            ),
        )
        with self.assertRaises(TypeError):
            contract.build_controller_catalog(
                _profiles(),
                NONCE_A,
                ONTOLOGY_HASH,
                AUDIT_HASH,
                action="ASK_LAW",
            )
        with self.assertRaises(TypeError):
            contract.CapabilityProfile(
                (("law.use", 1.0),), 1.0, profile_id="profile:law"
            )
        with self.assertRaises(ValueError):
            contract.OpaqueActionSlot("ASK_LAW", _profiles()[0])

        catalog = _catalog()
        forged_slot = contract.OpaqueActionSlot(
            "slot:" + "0" * 64,
            catalog.slots[0].profile,
        )
        with self.assertRaises(ValueError):
            contract.ControllerCapabilityCatalog(
                NONCE_A,
                ONTOLOGY_HASH,
                AUDIT_HASH,
                (forged_slot, *catalog.slots[1:]),
            )

    def test_catalog_schema_order_hashes_and_nonce_audit_fail_closed(self) -> None:
        contract = _module()
        catalog = _catalog()
        self.assertIsInstance(catalog.slots, tuple)
        self.assertEqual(len(catalog.slots), 4)
        self.assertEqual(
            set(catalog.to_dict()),
            {
                "catalog_nonce",
                "obligation_catalog_sha256",
                "capability_audit_sha256",
                "slots",
            },
        )
        self.assertEqual(
            set(catalog.to_dict()["slots"][0]), {"slot_id", "profile"}
        )
        self.assertEqual(
            set(catalog.to_dict()["slots"][0]["profile"]),
            {"profile_id", "obligation_advantages", "incremental_cost"},
        )
        for malformed in ("A" * 64, "a" * 63, "g" * 64, "sha256:" + "a" * 64):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                contract.build_controller_catalog(
                    _profiles(), malformed, ONTOLOGY_HASH, AUDIT_HASH
                )
        with self.assertRaises(ValueError):
            contract.build_controller_catalog(
                tuple(reversed(_profiles())), NONCE_A, ONTOLOGY_HASH, AUDIT_HASH
            )
        duplicate_profiles = (_profiles()[0], _profiles()[0], *_profiles()[2:])
        with self.assertRaises(ValueError):
            contract.build_controller_catalog(
                duplicate_profiles, NONCE_A, ONTOLOGY_HASH, AUDIT_HASH
            )
        contract.assert_unique_catalog_nonces((_catalog(nonce=NONCE_A), _catalog(nonce=NONCE_B)))
        with self.assertRaises(ValueError):
            contract.assert_unique_catalog_nonces((_catalog(), _catalog()))

    def test_controller_bytes_expose_only_opaque_numeric_catalog(self) -> None:
        contract = _module()
        catalog = _catalog()
        payload = contract.controller_catalog_bytes(catalog)
        self.assertIsInstance(payload, bytes)
        self.assertEqual(payload, catalog.canonical_json().encode("utf-8"))
        decoded = payload.decode("utf-8")
        self.assertIn("geometry.angle", decoded)
        document = json.loads(decoded)
        observed_keys: set[str] = set()
        observed_values: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    observed_keys.add(key)
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)
            elif isinstance(value, str):
                observed_values.add(value)

        collect(document)
        for forbidden_key in (
            "action",
            "packet",
            "prompt",
            "tool",
            "permission",
            "evidence_scope",
            "budget",
            "output_schema",
            "model_runtime",
            "container",
            "evaluator",
            "gold",
            "mutation",
            "seed",
        ):
            with self.subTest(forbidden_key=forbidden_key):
                self.assertNotIn(forbidden_key, observed_keys)
        for forbidden_value in (
            "ASK_LAW",
            "ASK_PARKING",
            "ASK_PROGRAM",
            "ASK_GEOMETRY",
        ):
            with self.subTest(forbidden_value=forbidden_value):
                self.assertNotIn(forbidden_value, observed_values)

    def test_controller_byte_api_rejects_all_evaluator_types_shapes_and_subclasses(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        packet = _packets()[0]

        class CatalogSubclass(contract.ControllerCapabilityCatalog):
            pass

        subclass = CatalogSubclass(
            catalog.catalog_nonce,
            catalog.obligation_catalog_sha256,
            catalog.capability_audit_sha256,
            catalog.slots,
        )
        for rejected in (
            packet,
            plan.arms[0],
            plan,
            catalog.to_dict(),
            subclass,
        ):
            with self.subTest(rejected=type(rejected).__name__), self.assertRaises(
                TypeError
            ):
                contract.controller_catalog_bytes(rejected)

    def test_packet_manifest_is_complete_frozen_hashed_and_ask_only(self) -> None:
        contract = _module()
        packet = _packet("ASK_LAW", "1")
        expected_manifest_json = (
            '{"action":"ASK_LAW","budget_contract_sha256":"'
            + "1" * 64
            + '","container_sha256":"'
            + "1" * 64
            + '","evidence_scope_sha256":"'
            + "1" * 64
            + '","model_runtime_sha256":"'
            + "1" * 64
            + '","output_schema_sha256":"'
            + "1" * 64
            + '","permission_manifest_sha256":"'
            + "1" * 64
            + '","prompt_sha256":"'
            + "1" * 64
            + '","tool_manifest_sha256":"'
            + "1" * 64
            + '"}'
        )
        self.assertEqual(
            packet.packet_id,
            "packet:"
            + hashlib.sha256(expected_manifest_json.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            set(packet.to_dict()),
            {
                "packet_id",
                "action",
                "prompt_sha256",
                "tool_manifest_sha256",
                "permission_manifest_sha256",
                "evidence_scope_sha256",
                "budget_contract_sha256",
                "output_schema_sha256",
                "model_runtime_sha256",
                "container_sha256",
            },
        )
        with self.assertRaises(FrozenInstanceError):
            packet.action = "ASK_PROGRAM"
        for invalid_action in ("STOP", "SOLO_SYNTHESIS", "ASK_GENERALIST", "ask_law"):
            with self.subTest(action=invalid_action), self.assertRaises(ValueError):
                _packet(invalid_action, "1")
        with self.assertRaises(ValueError):
            contract.CapabilityPacketManifest(
                action="ASK_LAW",
                prompt_sha256="A" * 64,
                tool_manifest_sha256="1" * 64,
                permission_manifest_sha256="1" * 64,
                evidence_scope_sha256="1" * 64,
                budget_contract_sha256="1" * 64,
                output_schema_sha256="1" * 64,
                model_runtime_sha256="1" * 64,
                container_sha256="1" * 64,
            )

    def test_each_binding_is_a_four_way_bijection_with_associated_packets(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        expected_slots = {slot.slot_id for slot in catalog.slots}
        expected_packets = {packet.packet_id for packet in _packets()}
        expected_actions = {
            "ASK_GEOMETRY",
            "ASK_LAW",
            "ASK_PARKING",
            "ASK_PROGRAM",
        }
        for arm in plan.arms:
            self.assertIsInstance(arm.assignments, tuple)
            self.assertTrue(all(isinstance(item, tuple) for item in arm.assignments))
            self.assertEqual(arm.catalog_sha256, catalog.sha256())
            self.assertEqual({slot for slot, _ in arm.assignments}, expected_slots)
            self.assertEqual(
                {packet.packet_id for _, packet in arm.assignments}, expected_packets
            )
            self.assertEqual(
                {packet.action for _, packet in arm.assignments}, expected_actions
            )
        with self.assertRaises(FrozenInstanceError):
            plan.arms[0].assignments = ()

        assignments = plan.arms[0].assignments
        with self.assertRaises(ValueError):
            contract.ExecutionCapabilityBinding(
                catalog.sha256(),
                (assignments[0], assignments[0], assignments[2], assignments[3]),
            )
        with self.assertRaises(ValueError):
            contract.ExecutionCapabilityBinding(
                catalog.sha256(),
                (
                    assignments[0],
                    (assignments[1][0], assignments[0][1]),
                    assignments[2],
                    assignments[3],
                ),
            )

    def test_four_arms_are_a_complete_latin_crossover_with_full_derangements(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        packets = _packets()
        aligned = {
            slot.slot_id: packet.packet_id
            for slot, packet in zip(catalog.slots, packets, strict=True)
        }
        arm_maps = [
            {slot: packet.packet_id for slot, packet in arm.assignments}
            for arm in plan.arms
        ]
        self.assertEqual(len(plan.arms), 4)
        self.assertEqual(sum(arm == aligned for arm in arm_maps), 1)
        for arm in arm_maps:
            if arm != aligned:
                self.assertTrue(
                    all(arm[slot_id] != packet_id for slot_id, packet_id in aligned.items())
                )
        for slot in catalog.slots:
            self.assertEqual(
                {arm[slot.slot_id] for arm in arm_maps},
                {packet.packet_id for packet in packets},
            )
        self.assertEqual(len({arm.sha256() for arm in plan.arms}), 4)

        repeated = contract.build_crossover_plan(catalog, packets, SEED_A)
        self.assertEqual(repeated, plan)
        other_seed = contract.build_crossover_plan(catalog, packets, SEED_B)
        self.assertEqual(
            {arm.sha256() for arm in other_seed.arms},
            {arm.sha256() for arm in plan.arms},
        )

    def test_aligned_arm_uses_evaluator_packet_order_without_semantic_inference(self) -> None:
        contract = _module()
        catalog = _catalog()
        deliberately_misaligned = tuple(reversed(_packets()))
        plan = contract.build_crossover_plan(catalog, deliberately_misaligned, SEED_A)
        expected = {
            slot.slot_id: packet.packet_id
            for slot, packet in zip(catalog.slots, deliberately_misaligned, strict=True)
        }
        observed = [
            {slot: packet.packet_id for slot, packet in arm.assignments}
            for arm in plan.arms
        ]
        self.assertEqual(sum(arm == expected for arm in observed), 1)

    def test_relabel_changes_only_opaque_surface_names_and_hash_bindings(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        new_catalog, new_plan = contract.relabel_crossover(catalog, plan, NONCE_B)
        contract.validate_crossover_plan(new_catalog, new_plan)
        self.assertNotEqual(new_catalog.sha256(), catalog.sha256())
        self.assertTrue(
            all(
                old.slot_id != new.slot_id
                for old, new in zip(catalog.slots, new_catalog.slots, strict=True)
            )
        )
        self.assertEqual(
            tuple(slot.profile.obligation_advantages for slot in new_catalog.slots),
            tuple(slot.profile.obligation_advantages for slot in catalog.slots),
        )
        self.assertEqual(
            tuple(slot.profile.incremental_cost for slot in new_catalog.slots),
            tuple(slot.profile.incremental_cost for slot in catalog.slots),
        )
        rename = {
            old.slot_id: new.slot_id
            for old, new in zip(catalog.slots, new_catalog.slots, strict=True)
        }
        for old_arm, new_arm in zip(plan.arms, new_plan.arms, strict=True):
            old_pairs = {
                rename[slot_id]: (packet.packet_id, packet.action)
                for slot_id, packet in old_arm.assignments
            }
            new_pairs = {
                slot_id: (packet.packet_id, packet.action)
                for slot_id, packet in new_arm.assignments
            }
            self.assertEqual(new_pairs, old_pairs)
            self.assertEqual(new_arm.catalog_sha256, new_catalog.sha256())
        self.assertEqual(new_plan.crossover_seed_sha256, plan.crossover_seed_sha256)
        self.assertEqual(new_plan.aligned_arm_index, plan.aligned_arm_index)
        self.assertEqual(
            tuple(reference[2] for reference in new_plan.aligned_reference),
            tuple(reference[2] for reference in plan.aligned_reference),
        )
        self.assertTrue(
            all(
                old[0] != new[0] and old[1] != new[1]
                for old, new in zip(
                    plan.aligned_reference,
                    new_plan.aligned_reference,
                    strict=True,
                )
            )
        )

    def test_incomplete_duplicate_and_stale_evaluator_contracts_fail_closed(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        packets = _packets()
        with self.assertRaises(ValueError):
            contract.build_crossover_plan(catalog, packets[:3], SEED_A)
        with self.assertRaises(ValueError):
            contract.build_crossover_plan(
                catalog, (packets[0], packets[0], packets[2], packets[3]), SEED_A
            )
        duplicate_action = _packet("ASK_GEOMETRY", "5")
        with self.assertRaises(ValueError):
            contract.build_crossover_plan(
                catalog,
                (packets[0], duplicate_action, packets[2], packets[3]),
                SEED_A,
            )
        with self.assertRaises(ValueError):
            replace(plan, catalog_sha256="0" * 64)
        with self.assertRaises(ValueError):
            replace(plan, arms=(plan.arms[0],) * 4)
        with self.assertRaises(ValueError):
            contract.relabel_crossover(
                _catalog(nonce=NONCE_B), plan, "9" * 64
            )

    def test_complete_but_noncyclic_latin_plan_is_rejected(self) -> None:
        contract = _module()
        catalog, valid_plan = _catalog_and_plan()
        packets = _packets()
        permutations = (
            (0, 1, 2, 3),
            (1, 0, 3, 2),
            (2, 3, 0, 1),
            (3, 2, 1, 0),
        )
        arms = tuple(
            contract.ExecutionCapabilityBinding(
                catalog.sha256(),
                tuple(
                    (slot.slot_id, packets[packet_index])
                    for slot, packet_index in zip(
                        catalog.slots, permutation, strict=True
                    )
                ),
            )
            for permutation in permutations
        )
        payload = valid_plan.to_dict()
        payload["arms"] = [arm.to_dict() for arm in arms]
        _rehash_plan_payload(payload)
        with self.assertRaisesRegex(ValueError, "seed"):
            contract.CapabilityCrossoverPlan.from_dict(payload)

    def test_exact_evaluator_schemas_and_plan_identity_are_bound(self) -> None:
        catalog, plan = _catalog_and_plan()
        binding_dict = plan.arms[0].to_dict()
        self.assertEqual(set(binding_dict), {"catalog_sha256", "assignments"})
        self.assertEqual(
            set(binding_dict["assignments"][0]), {"slot_id", "packet"}
        )
        self.assertEqual(
            set(plan.to_dict()),
            {
                "plan_id",
                "catalog_sha256",
                "obligation_catalog_sha256",
                "capability_audit_sha256",
                "crossover_seed_sha256",
                "aligned_reference",
                "aligned_arm_index",
                "arms",
            },
        )
        self.assertTrue(plan.plan_id.startswith("plan:"))
        self.assertEqual(len(plan.plan_id), len("plan:") + 64)
        self.assertEqual(plan.catalog_sha256, catalog.sha256())

    def test_catalog_aware_validation_rejects_real_hash_with_foreign_slots(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        payload = json.loads(plan.canonical_json())
        foreign_slot_ids = tuple(
            f"slot:{digit * 64}" for digit in ("5", "6", "7", "8")
        )
        rename = {
            slot.slot_id: foreign
            for slot, foreign in zip(catalog.slots, foreign_slot_ids, strict=True)
        }
        for reference in payload["aligned_reference"]:
            reference["slot_id"] = rename[reference["slot_id"]]
        for arm in payload["arms"]:
            for assignment in arm["assignments"]:
                assignment["slot_id"] = rename[assignment["slot_id"]]
            arm["assignments"].sort(key=lambda assignment: assignment["slot_id"])
        _rehash_plan_payload(payload)
        foreign_plan = contract.CapabilityCrossoverPlan.from_dict(payload)
        self.assertEqual(foreign_plan.catalog_sha256, catalog.sha256())
        with self.assertRaisesRegex(ValueError, "catalog slot"):
            contract.validate_crossover_plan(catalog, foreign_plan)

    def test_persisted_artifacts_authenticate_aligned_arm_without_builder_inputs(self) -> None:
        contract = _module()
        built_catalog, built_plan = _catalog_and_plan()
        catalog_payload = json.loads(built_catalog.canonical_json())
        plan_payload = json.loads(built_plan.canonical_json())
        del built_catalog, built_plan

        catalog = contract.ControllerCapabilityCatalog.from_dict(catalog_payload)
        plan = contract.CapabilityCrossoverPlan.from_dict(plan_payload)
        contract.validate_crossover_plan(catalog, plan)

        reference = {
            slot_id: packet_id
            for slot_id, _profile_id, packet_id in plan.aligned_reference
        }
        arm_maps = [
            {slot_id: packet.packet_id for slot_id, packet in arm.assignments}
            for arm in plan.arms
        ]
        self.assertEqual(arm_maps[plan.aligned_arm_index], reference)
        for index, arm in enumerate(arm_maps):
            if index != plan.aligned_arm_index:
                self.assertTrue(
                    all(arm[slot_id] != packet_id for slot_id, packet_id in reference.items())
                )

    def test_seed_inconsistent_persisted_arm_reorder_is_rejected(self) -> None:
        contract = _module()
        _catalog_value, plan = _catalog_and_plan()
        payload = json.loads(plan.canonical_json())
        payload["arms"] = payload["arms"][1:] + payload["arms"][:1]
        payload["aligned_arm_index"] = (payload["aligned_arm_index"] - 1) % 4
        _rehash_plan_payload(payload)
        with self.assertRaisesRegex(ValueError, "seed"):
            contract.CapabilityCrossoverPlan.from_dict(payload)

    def test_public_obligation_ids_with_controller_vocabulary_are_preserved(self) -> None:
        contract = _module()
        obligation_ids = (
            "BUDGET/TEST_TIME",
            "action_area",
            "tool_clearance",
            "zoning.container_mutation",
        )
        profiles = tuple(
            sorted(
                (
                    contract.CapabilityProfile(((obligation_id, 1.0),), 1.0)
                    for obligation_id in obligation_ids
                ),
                key=lambda profile: profile.canonical_json(),
            )
        )
        catalog = contract.build_controller_catalog(
            profiles, NONCE_A, ONTOLOGY_HASH, AUDIT_HASH
        )
        decoded = contract.controller_catalog_bytes(catalog).decode("utf-8")
        for obligation_id in obligation_ids:
            self.assertIn(obligation_id, decoded)
        for action in ("ASK_LAW", "ASK_PARKING", "ASK_PROGRAM", "ASK_GEOMETRY"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                contract.CapabilityProfile(((action, 1.0),), 1.0)

    def test_all_exact_hash_and_prefixed_id_grammars_reject_whitespace(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        packet = _packets()[0]
        for label, operation in (
            (
                "catalog nonce",
                lambda: contract.build_controller_catalog(
                    _profiles(), f" {NONCE_A}", ONTOLOGY_HASH, AUDIT_HASH
                ),
            ),
            (
                "ontology hash",
                lambda: contract.build_controller_catalog(
                    _profiles(), NONCE_A, f"{ONTOLOGY_HASH} ", AUDIT_HASH
                ),
            ),
            (
                "audit hash",
                lambda: contract.build_controller_catalog(
                    _profiles(), NONCE_A, ONTOLOGY_HASH, f" {AUDIT_HASH}"
                ),
            ),
            (
                "manifest hash",
                lambda: contract.CapabilityPacketManifest(
                    action="ASK_LAW",
                    prompt_sha256=f"{'1' * 64} ",
                    tool_manifest_sha256="1" * 64,
                    permission_manifest_sha256="1" * 64,
                    evidence_scope_sha256="1" * 64,
                    budget_contract_sha256="1" * 64,
                    output_schema_sha256="1" * 64,
                    model_runtime_sha256="1" * 64,
                    container_sha256="1" * 64,
                ),
            ),
            (
                "slot id",
                lambda: contract.OpaqueActionSlot(
                    f" {catalog.slots[0].slot_id}", catalog.slots[0].profile
                ),
            ),
            (
                "binding catalog hash",
                lambda: contract.ExecutionCapabilityBinding(
                    f"{catalog.sha256()} ", plan.arms[0].assignments
                ),
            ),
            (
                "plan id",
                lambda: replace(plan, plan_id=f" {plan.plan_id}"),
            ),
            (
                "crossover seed",
                lambda: replace(
                    plan, crossover_seed_sha256=f"{plan.crossover_seed_sha256} "
                ),
            ),
        ):
            with self.subTest(label=label), self.assertRaises(ValueError):
                operation()

        packet_payload = packet.to_dict()
        packet_payload["packet_id"] = f"{packet.packet_id} "
        with self.assertRaises(ValueError):
            contract.CapabilityPacketManifest.from_dict(packet_payload)
        catalog_payload = catalog.to_dict()
        catalog_payload["slots"][0]["profile"]["profile_id"] += " "
        with self.assertRaises(ValueError):
            contract.ControllerCapabilityCatalog.from_dict(catalog_payload)

    def test_every_public_record_exactly_round_trips_from_persisted_dicts(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()
        packet = _packets()[0]
        unbound_profile = _profiles()[0]
        records = (
            (
                contract.CapabilityProfile,
                unbound_profile,
                lambda payload: contract.CapabilityProfile.from_dict(payload),
            ),
            (
                contract.OpaqueActionSlot,
                catalog.slots[0],
                lambda payload: contract.OpaqueActionSlot.from_dict(
                    payload,
                    catalog_nonce=catalog.catalog_nonce,
                    slot_index=0,
                ),
            ),
            (
                contract.ControllerCapabilityCatalog,
                catalog,
                contract.ControllerCapabilityCatalog.from_dict,
            ),
            (
                contract.CapabilityPacketManifest,
                packet,
                contract.CapabilityPacketManifest.from_dict,
            ),
            (
                contract.ExecutionCapabilityBinding,
                plan.arms[0],
                contract.ExecutionCapabilityBinding.from_dict,
            ),
            (
                contract.CapabilityCrossoverPlan,
                plan,
                contract.CapabilityCrossoverPlan.from_dict,
            ),
        )
        for record_type, record, loader in records:
            with self.subTest(record=record_type.__name__):
                persisted = json.loads(record.canonical_json())
                rebuilt = loader(persisted)
                self.assertEqual(rebuilt, record)
                self.assertEqual(rebuilt.canonical_json(), record.canonical_json())
                self.assertEqual(rebuilt.sha256(), record.sha256())

    def test_standalone_slot_from_dict_requires_exact_index_and_rejects_stale_id(self) -> None:
        contract = _module()
        catalog = _catalog()
        valid_payload = json.loads(catalog.slots[0].canonical_json())
        stale_payload = json.loads(catalog.slots[0].canonical_json())
        stale_payload["slot_id"] = "slot:" + "0" * 64

        with self.assertRaisesRegex(ValueError, "stale slot_id"):
            contract.OpaqueActionSlot.from_dict(
                stale_payload,
                catalog_nonce=catalog.catalog_nonce,
                slot_index=0,
            )
        with self.assertRaises(TypeError):
            contract.OpaqueActionSlot.from_dict(
                valid_payload,
                catalog_nonce=catalog.catalog_nonce,
            )
        for invalid_index in (True, 0.0, "0"):
            with self.subTest(invalid_index=invalid_index), self.assertRaises(TypeError):
                contract.OpaqueActionSlot.from_dict(
                    valid_payload,
                    catalog_nonce=catalog.catalog_nonce,
                    slot_index=invalid_index,
                )
        for invalid_index in (-1, 4):
            with self.subTest(invalid_index=invalid_index), self.assertRaises(ValueError):
                contract.OpaqueActionSlot.from_dict(
                    valid_payload,
                    catalog_nonce=catalog.catalog_nonce,
                    slot_index=invalid_index,
                )

    def test_from_dict_rejects_extra_missing_wrong_native_and_stale_nested_values(self) -> None:
        contract = _module()
        catalog, plan = _catalog_and_plan()

        extra_catalog = json.loads(catalog.canonical_json())
        extra_catalog["evaluator"] = "forbidden"
        with self.assertRaises(ValueError):
            contract.ControllerCapabilityCatalog.from_dict(extra_catalog)

        nested_extra = json.loads(catalog.canonical_json())
        nested_extra["slots"][0]["profile"]["unexpected"] = 1
        with self.assertRaises(ValueError):
            contract.ControllerCapabilityCatalog.from_dict(nested_extra)

        missing_plan = json.loads(plan.canonical_json())
        del missing_plan["aligned_reference"]
        with self.assertRaises(ValueError):
            contract.CapabilityCrossoverPlan.from_dict(missing_plan)

        bool_index = json.loads(plan.canonical_json())
        bool_index["aligned_arm_index"] = True
        _rehash_plan_payload(bool_index)
        with self.assertRaises(TypeError):
            contract.CapabilityCrossoverPlan.from_dict(bool_index)

        stale_profile = json.loads(catalog.canonical_json())
        stale_profile["slots"][0]["profile"]["profile_id"] = (
            "profile:" + "0" * 64
        )
        with self.assertRaises(ValueError):
            contract.ControllerCapabilityCatalog.from_dict(stale_profile)

        stale_packet = json.loads(plan.canonical_json())
        stale_packet["arms"][0]["assignments"][0]["packet"]["packet_id"] = (
            "packet:" + "0" * 64
        )
        with self.assertRaises(ValueError):
            contract.CapabilityCrossoverPlan.from_dict(stale_packet)

        stale_plan = json.loads(plan.canonical_json())
        stale_plan["plan_id"] = "plan:" + "0" * 64
        with self.assertRaises(ValueError):
            contract.CapabilityCrossoverPlan.from_dict(stale_plan)

    def test_no_family_to_action_mapping_is_exported_or_present_as_a_table(self) -> None:
        contract = _module()
        family_names = {"law", "parking", "program", "geometry", "site/evidence"}
        for name, value in vars(contract).items():
            with self.subTest(name=name):
                self.assertNotIn("family_to_action", name.casefold())
                if isinstance(value, Mapping):
                    keys = {str(key).casefold() for key in value}
                    values = {str(item) for item in value.values()}
                    self.assertFalse(
                        bool(keys & family_names)
                        and any(item.startswith("ASK_") for item in values)
                    )


if __name__ == "__main__":
    unittest.main()
