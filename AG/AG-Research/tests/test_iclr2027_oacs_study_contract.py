from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
import hashlib
import inspect
import json
from typing import get_type_hints
import unittest

from iclr2027.capability_binding import (
    CapabilityPacketManifest,
    CapabilityProfile,
    build_controller_catalog,
    build_crossover_plan,
)
from iclr2027.obligation_oracle import (
    BaselinePreOutcomeReadinessAuthority,
    MandatoryBaselineRoster,
    MandatoryBaselineRosterEntry,
)
import iclr2027.oacs_study_contract as oacs_study_contract
from iclr2027.oacs_study_contract import (
    OacsStudyContractV1,
    ParityFieldV1,
    StudyContractError,
    TreatmentSpecV1,
    study_contract_bytes,
    validate_study_contract,
)


def _hash(character: str) -> str:
    return character * 64


class _CustomMapping(Mapping[str, object]):
    def __init__(self, values: dict[str, object]) -> None:
        self._values = values

    def __getitem__(self, key: str) -> object:
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


class _CustomSequence(Sequence[object]):
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def __getitem__(self, index: int) -> object:
        return self._values[index]

    def __len__(self) -> int:
        return len(self._values)


def _catalog_and_plan():
    profiles = (
        CapabilityProfile((("geometry.angle", 0.25),), 1.0),
        CapabilityProfile((("law.use", -0.5),), 1.0),
        CapabilityProfile((("parking.supply", 0.75),), 1.0),
        CapabilityProfile((("program.area", 1.25),), 1.0),
    )
    catalog = build_controller_catalog(profiles, _hash("a"), _hash("b"), _hash("c"))
    packets = tuple(
        CapabilityPacketManifest(
            action=action,
            prompt_sha256=_hash(digit),
            tool_manifest_sha256=_hash(digit),
            permission_manifest_sha256=_hash(digit),
            evidence_scope_sha256=_hash(digit),
            budget_contract_sha256=_hash(digit),
            output_schema_sha256=_hash(digit),
            model_runtime_sha256=_hash(digit),
            container_sha256=_hash(digit),
        )
        for action, digit in (
            ("ASK_GEOMETRY", "1"),
            ("ASK_LAW", "2"),
            ("ASK_PARKING", "3"),
            ("ASK_PROGRAM", "4"),
        )
    )
    return catalog, build_crossover_plan(catalog, packets, _hash("d"))


def _baseline_roster_and_readiness():
    baseline_ids = (
        "agentprune",
        "agora",
        "always_all_specialists",
        "automix",
        "bicsrouter",
        "conformal_thinking",
        "cost_aware_protocol_routing",
        "difficulty_confidence",
        "fixed_topology",
        "gptswarm",
        "graphplanner",
        "masrouter",
        "matched_compute_self_agent_scaling",
        "random_admissible_action",
        "rirs_talk_to_right_specialists",
        "routellm",
        "self_resource_allocation",
        "separated_router_stopper",
        "solo",
        "verimap",
        "vmao",
        "zooter_adaptation",
    )
    internal = {
        "always_all_specialists",
        "difficulty_confidence",
        "fixed_topology",
        "random_admissible_action",
        "separated_router_stopper",
        "solo",
    }
    entries, readiness = [], []
    for baseline_id in baseline_ids:
        official = (
            None
            if baseline_id in internal
            else hashlib.sha256((baseline_id + ":official").encode("utf-8")).hexdigest()
        )
        version = hashlib.sha256((baseline_id + ":version").encode("utf-8")).hexdigest()
        entries.append(
            MandatoryBaselineRosterEntry.create(
                baseline_id=baseline_id,
                official_source_spec_sha256=official,
                version_sha256=version,
            )
        )
        readiness.append(
            BaselinePreOutcomeReadinessAuthority.create(
                baseline_id=baseline_id,
                version_sha256=version,
                status="unsupported_missing_dependency",
                reason_code="dependency_unavailable",
                official_source_spec_sha256=official,
                executed_method_id=None,
                adapter_code_sha256=None,
                dependency_environment_lock_sha256=_hash("c"),
                parity_projection_sha256=None,
                synthetic_faithfulness_test_receipt_sha256=None,
                reviewer_decision_sha256=_hash("d"),
                pre_outcome_amendment_sha256=None,
            )
        )
    return MandatoryBaselineRoster.create(entries=tuple(entries)), tuple(readiness)


class OacsStudyContractTests(unittest.TestCase):
    def test_public_annotation_surfaces_resolve_at_runtime(self) -> None:
        surfaces = [
            obj
            for name, obj in vars(oacs_study_contract).items()
            if inspect.isfunction(obj) and not name.startswith("_")
        ]
        for cls in vars(oacs_study_contract).values():
            if inspect.isclass(cls) and cls.__module__ == oacs_study_contract.__name__:
                surfaces.extend(
                    inspect.unwrap(method)
                    for name, method in vars(cls).items()
                    if not name.startswith("_")
                    and (
                        inspect.isfunction(method)
                        or isinstance(method, (classmethod, staticmethod))
                    )
                )

        for surface in surfaces:
            with self.subTest(surface=surface):
                get_type_hints(surface)

    def valid_contract(self) -> OacsStudyContractV1:
        catalog, plan = _catalog_and_plan()
        roster, readiness = _baseline_roster_and_readiness()
        common = dict(
            model_binding_sha256=_hash("5"),
            public_input_projection_sha256=_hash("6"),
            token_budget=4096,
            call_budget=12,
            timeout_seconds=90,
            retry_policy_sha256=_hash("7"),
            common_synthesizer_sha256=_hash("8"),
            terminal_evaluator_sha256=_hash("9"),
            usage_accounting_sha256=_hash("e"),
        )
        ids = (
            "solo",
            "rr3",
            "sel3",
            "swm3",
            "refl3",
            "debate3",
            "equal_information_router",
            "oacs",
        )
        treatments = tuple(
            TreatmentSpecV1(
                treatment_id=treatment_id,
                treatment_family=(
                    "oacs_capability" if treatment_id == "oacs" else "core_mas"
                ),
                tool_catalog_sha256=(
                    catalog.sha256() if treatment_id == "oacs" else _hash("f")
                ),
                **common,
            )
            for treatment_id in ids
        )
        return OacsStudyContractV1(treatments, catalog, plan, roster, readiness)

    def mutate_treatment(self, contract, treatment_id: str, **changes):
        treatments = tuple(
            replace(treatment, **changes)
            if treatment.treatment_id == treatment_id
            else treatment
            for treatment in contract.treatments
        )
        return replace(contract, treatments=treatments)

    def test_required_treatment_families_and_parity(self) -> None:
        contract = self.valid_contract()
        self.assertEqual(
            contract.required_treatment_ids,
            (
                "solo",
                "rr3",
                "sel3",
                "swm3",
                "refl3",
                "debate3",
                "equal_information_router",
                "oacs",
            ),
        )
        validate_study_contract(contract)
        with self.assertRaisesRegex(StudyContractError, "token_budget parity"):
            validate_study_contract(
                self.mutate_treatment(contract, "oacs", token_budget=4097)
            )

    def test_each_same_information_and_budget_field_has_a_specific_error(self) -> None:
        contract = self.valid_contract()
        attacks = (
            ("model_binding_sha256", _hash("0")),
            ("public_input_projection_sha256", _hash("1")),
            ("token_budget", 4097),
            ("call_budget", 13),
            ("timeout_seconds", 91),
            ("retry_policy_sha256", _hash("2")),
            ("common_synthesizer_sha256", _hash("3")),
            ("terminal_evaluator_sha256", _hash("4")),
            ("usage_accounting_sha256", _hash("a")),
        )
        for field_name, value in attacks:
            with (
                self.subTest(field_name=field_name),
                self.assertRaisesRegex(StudyContractError, field_name + " parity"),
            ):
                validate_study_contract(
                    self.mutate_treatment(contract, "oacs", **{field_name: value})
                )

    def test_tool_difference_requires_the_bound_oacs_crossover(self) -> None:
        contract = self.valid_contract()
        with self.assertRaisesRegex(StudyContractError, "tool_catalog_sha256 parity"):
            validate_study_contract(
                self.mutate_treatment(contract, "solo", tool_catalog_sha256=_hash("0"))
            )
        with self.assertRaisesRegex(StudyContractError, "capability crossover binding"):
            validate_study_contract(
                self.mutate_treatment(contract, "oacs", tool_catalog_sha256=_hash("0"))
            )

    def test_treatment_census_order_names_and_oracle_are_closed(self) -> None:
        contract = self.valid_contract()
        with self.assertRaisesRegex(StudyContractError, "treatment census"):
            validate_study_contract(
                replace(contract, treatments=contract.treatments[:-1])
            )
        duplicate = replace(contract.treatments[-1], treatment_id="solo")
        with self.assertRaisesRegex(StudyContractError, "treatment census"):
            validate_study_contract(
                replace(contract, treatments=(*contract.treatments[:-1], duplicate))
            )
        with self.assertRaisesRegex(StudyContractError, "treatment order"):
            validate_study_contract(
                replace(
                    contract,
                    treatments=(
                        contract.treatments[1],
                        contract.treatments[0],
                        *contract.treatments[2:],
                    ),
                )
            )
        with self.assertRaisesRegex(StudyContractError, "treatment family"):
            validate_study_contract(
                self.mutate_treatment(
                    contract, "oacs", treatment_family="oracle_router"
                )
            )
        oracle = replace(contract.treatments[-1], treatment_id="retrospective_oracle")
        with self.assertRaisesRegex(StudyContractError, "retrospective oracle"):
            validate_study_contract(
                replace(contract, treatments=(*contract.treatments[:-1], oracle))
            )

    def test_e3_roster_is_complete_byte_sorted_and_preserves_blocked_status(
        self,
    ) -> None:
        contract = self.valid_contract()
        self.assertEqual(len(contract.e3_readiness), 22)
        self.assertEqual(
            contract.e3_readiness[3].status, "unsupported_missing_dependency"
        )
        with self.assertRaisesRegex(StudyContractError, "E3 readiness binding"):
            validate_study_contract(
                replace(contract, e3_readiness=contract.e3_readiness[:-1])
            )
        with self.assertRaisesRegex(StudyContractError, "E3 readiness binding"):
            validate_study_contract(
                replace(
                    contract,
                    e3_readiness=(
                        contract.e3_readiness[1],
                        contract.e3_readiness[0],
                        *contract.e3_readiness[2:],
                    ),
                )
            )
        with self.assertRaisesRegex(StudyContractError, "E3 readiness binding"):
            validate_study_contract(
                replace(
                    contract,
                    e3_readiness=(
                        contract.e3_readiness[-1],
                        *contract.e3_readiness[1:],
                    ),
                )
            )

    def test_bytes_are_canonical_and_fully_resealed_cheaper_oacs_is_rejected(
        self,
    ) -> None:
        contract = self.valid_contract()
        payload = study_contract_bytes(contract)
        self.assertTrue(payload.endswith(b"\n"))
        self.assertEqual(payload.count(b"\n"), 1)
        decoded = payload.decode("utf-8")
        self.assertEqual(
            decoded,
            json.dumps(
                json.loads(decoded),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
        )
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            "f215d2d58ebefe6d640765bd714a8dc387846d8c2aa2a2cb537c79b7d08bbf68",
        )
        resealed = self.mutate_treatment(
            contract, "oacs", token_budget=2048, call_budget=6
        )
        with self.assertRaisesRegex(StudyContractError, "token_budget parity"):
            validate_study_contract(resealed)

    def test_parser_rejects_duplicate_noncanonical_and_stale_hash_bytes(self) -> None:
        contract = self.valid_contract()
        payload = study_contract_bytes(contract)
        parsed = OacsStudyContractV1.from_bytes(payload)
        self.assertEqual(parsed.to_dict(), contract.to_dict())
        duplicate = payload.replace(
            b'"treatments":', b'"treatments":[],"treatments":', 1
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: treatments"):
            OacsStudyContractV1.from_bytes(duplicate)
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            OacsStudyContractV1.from_bytes(b" " + payload)
        stale = payload.replace(
            contract.capability_catalog.sha256().encode("ascii"), b"0" * 64
        )
        with self.assertRaisesRegex(ValueError, "plan_id"):
            OacsStudyContractV1.from_bytes(stale)

    def test_schemas_enums_and_native_budget_types_fail_closed(self) -> None:
        contract = self.valid_contract()
        source = contract.treatments[0].to_dict()
        with self.assertRaisesRegex(TypeError, "token_budget must be a native integer"):
            TreatmentSpecV1(**(source | {"token_budget": True}))
        with self.assertRaisesRegex(ValueError, "exact keys"):
            TreatmentSpecV1.from_dict(source | {"extra": "rejected"})
        with self.assertRaisesRegex(TypeError, "exact MandatoryBaselineRoster"):
            OacsStudyContractV1(
                contract.treatments,
                contract.capability_catalog,
                contract.capability_crossover_plan,
                object(),
                contract.e3_readiness,
            )
        self.assertEqual(
            tuple(ParityFieldV1),
            (
                ParityFieldV1.MODEL_BINDING,
                ParityFieldV1.PUBLIC_INPUT_PROJECTION,
                ParityFieldV1.TOOL_CATALOG,
                ParityFieldV1.TOKEN_BUDGET,
                ParityFieldV1.CALL_BUDGET,
                ParityFieldV1.TIMEOUT_SECONDS,
                ParityFieldV1.RETRY_POLICY,
                ParityFieldV1.COMMON_SYNTHESIZER,
                ParityFieldV1.TERMINAL_EVALUATOR,
                ParityFieldV1.USAGE_ACCOUNTING,
                ParityFieldV1.TREATMENT_CENSUS,
                ParityFieldV1.TREATMENT_ORDER,
                ParityFieldV1.CAPABILITY_CATALOG,
                ParityFieldV1.CAPABILITY_CROSSOVER,
                ParityFieldV1.E3_READINESS_ROSTER,
            ),
        )

    def test_from_dict_rejects_custom_mapping_and_sequence_boundaries(self) -> None:
        contract = self.valid_contract()
        treatment = contract.treatments[0].to_dict()
        with self.assertRaisesRegex(TypeError, "treatment spec must be an exact dict"):
            TreatmentSpecV1.from_dict(_CustomMapping(treatment))

        payload = contract.to_dict()
        attacks = (
            ("root", _CustomMapping(payload)),
            (
                "treatments",
                {**payload, "treatments": _CustomSequence(payload["treatments"])},
            ),
            (
                "treatment row",
                {
                    **payload,
                    "treatments": [
                        _CustomMapping(payload["treatments"][0]),
                        *payload["treatments"][1:],
                    ],
                },
            ),
            (
                "capability catalog",
                {
                    **payload,
                    "capability_catalog": _CustomMapping(payload["capability_catalog"]),
                },
            ),
            (
                "crossover plan",
                {
                    **payload,
                    "capability_crossover_plan": _CustomMapping(
                        payload["capability_crossover_plan"]
                    ),
                },
            ),
            (
                "readiness",
                {**payload, "e3_readiness": _CustomSequence(payload["e3_readiness"])},
            ),
            (
                "readiness row",
                {
                    **payload,
                    "e3_readiness": [
                        _CustomMapping(payload["e3_readiness"][0]),
                        *payload["e3_readiness"][1:],
                    ],
                },
            ),
        )
        for boundary, attack in attacks:
            with (
                self.subTest(boundary=boundary),
                self.assertRaisesRegex(TypeError, "exact dict|exact list or tuple"),
            ):
                OacsStudyContractV1.from_dict(attack)


if __name__ == "__main__":
    unittest.main()
