"""Granular synthetic-only tests for the Task 5 Phase-A contracts."""

from __future__ import annotations

from dataclasses import asdict, fields, FrozenInstanceError
import hashlib
import importlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCHEMA_PREFIX = "ace.iclr2027.synthetic_task5_phase_a.v2."
IDENTITY_DOMAIN = "ace.iclr2027.synthetic_task5_phase_a.v2"
IDENTITY_SEED = hashlib.sha256(b"task-5-v2-test-identity-seed").hexdigest()
_IDENTITY_ORDINALS: dict[str, tuple[str, int]] = {}
BASELINE_IDS = (
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
INTERNAL_BASELINES = {
    "always_all_specialists",
    "difficulty_confidence",
    "fixed_topology",
    "random_admissible_action",
    "separated_router_stopper",
    "solo",
}


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _target_action_roster_digest(
    site_ref: str,
    case_ref: str,
    prefix_ref: str,
    packet_ids: tuple[str, ...],
    repeat_seed_cells: tuple[tuple[int, int], ...],
) -> str:
    return hashlib.sha256(
        _json_bytes([site_ref, case_ref, prefix_ref, list(packet_ids), [list(cell) for cell in repeat_seed_cells]])
    ).hexdigest()


def _identity_ordinal(kind: str, label: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{kind}:{label}".encode("utf-8")).digest()[:8], "big"
    )


def _opaque_id(kind: str, label: str) -> str:
    ordinal = _identity_ordinal(kind, label)
    identifier = "o5_" + hashlib.sha256(
        _json_bytes([IDENTITY_DOMAIN, IDENTITY_SEED, kind, ordinal])
    ).hexdigest()
    _IDENTITY_ORDINALS[identifier] = (kind, ordinal)
    return identifier


def _registry(subject: object, *targets: dict[str, object]) -> object:
    seen: dict[str, tuple[str, int]] = {}

    def add(kind: str, identifier: str) -> None:
        if _IDENTITY_ORDINALS[identifier][0] != kind:
            raise AssertionError("fixture identity has wrong kind")
        seen[identifier] = _IDENTITY_ORDINALS[identifier]

    for target in targets:
        for identifier in target.get("auxiliary_identity_refs", []):  # type: ignore[union-attr]
            add("control", identifier)
        for row in target["assignments"]:  # type: ignore[index]
            add("assignment", row.assignment_ref)
            add("slot", row.assigned_opaque_slot_id)
            add("packet", row.assigned_actual_packet_id)
        for row in target["executions"]:  # type: ignore[index]
            add("assignment", row.assignment_ref)
            add("slot", row.assigned_opaque_slot_id)
            add("slot", row.actual_opaque_slot_id)
            add("packet", row.assigned_actual_packet_id)
            add("packet", row.actual_packet_id)
        for row in target["branches"]:  # type: ignore[index]
            if row.opaque_slot_id is not None:
                add("slot", row.opaque_slot_id)
                add("packet", row.actual_packet_id)
        for row in target["bindings"]:  # type: ignore[index]
            add("packet", row.opaque_packet_id)
        for row in target["pairs"]:  # type: ignore[index]
            add("packet", row.high_packet_id)
            add("packet", row.low_packet_id)
        for row in target["control_pairs"]:  # type: ignore[index]
            add("control", row.control_ref)
            add("packet", row.high_packet_id)
            add("packet", row.low_packet_id)

    manifests: dict[str, str] = {}
    for target in targets:
        for row in target["assignments"]:  # type: ignore[index]
            manifests[row.assigned_actual_packet_id] = (
                row.assigned_complete_bundle_manifest_sha256
            )
        for row in target["bindings"]:  # type: ignore[index]
            manifests[row.opaque_packet_id] = row.complete_bundle_manifest_sha256
    entries = tuple(
        sorted(
            ((kind, ordinal, identifier) for identifier, (kind, ordinal) in seen.items()),
            key=lambda item: (item[0].encode("ascii"), item[1]),
        )
    )
    packet_manifest_bindings = tuple(
        sorted(
            ((identifier, manifests[identifier]) for identifier, (kind, _) in seen.items() if kind == "packet"),
            key=lambda item: item[0].encode("ascii"),
        )
    )
    return subject.SyntheticOpaqueIdentityRegistryV2.create(
        derivation_seed_sha256=IDENTITY_SEED,
        entries=entries,
        packet_manifest_bindings=packet_manifest_bindings,
    )


def _ordered(records: list[object], hash_name: str) -> tuple[object, ...]:
    return tuple(sorted(records, key=lambda row: getattr(row, hash_name).encode("ascii")))


def _rebuild(record: object, /, **changes: object) -> object:
    values = {field.name: getattr(record, field.name) for field in fields(record)}
    values.pop("synthetic_only")
    values.pop(tuple(record.__dataclass_fields__)[-1])  # type: ignore[attr-defined]
    values.update(changes)
    return type(record).create(**values)


def _rehash_payload(payload: dict[str, object], hash_field: str) -> None:
    unsigned = dict(payload)
    unsigned.pop(hash_field)
    payload[hash_field] = hashlib.sha256(_json_bytes(unsigned)).hexdigest()


def _target_records(
    subject: object,
    *,
    site: str,
    case: str,
    prefix: str,
    high_qualities: tuple[float, ...],
    low_qualities: tuple[float, ...],
    high_costs: tuple[float, ...],
    low_costs: tuple[float, ...],
    support_status: str = "adequate",
    measure_kind: str = "frozen_stratum",
    packet_identity: tuple[str, str, str, str] | None = None,
    pair_set_sha256: str | None = None,
    evaluator_reference_sha256: str | None = None,
    selection_spec_sha256: str | None = None,
    control_mode: bool = False,
    fixture_tag: str | None = None,
) -> dict[str, object]:
    if not (
        len(high_qualities)
        == len(low_qualities)
        == len(high_costs)
        == len(low_costs)
    ):
        raise AssertionError("fixture vectors differ")
    target = f"{site}:{case}:{prefix}"
    fixture_identity = fixture_tag or target
    if packet_identity is None:
        high_packet = _opaque_id("packet", fixture_identity + ":high")
        low_packet = _opaque_id("packet", fixture_identity + ":low")
        high_manifest = _digest(fixture_identity + ":high-manifest")
        low_manifest = _digest(fixture_identity + ":low-manifest")
    else:
        high_packet, high_manifest, low_packet, low_manifest = packet_identity
    pair_set_sha256 = pair_set_sha256 or _digest(target + ":pair-set")
    evaluator_reference_sha256 = evaluator_reference_sha256 or _digest(target + ":reference")
    selection_spec_sha256 = selection_spec_sha256 or _digest(target + ":selection-spec")
    shared = dict(
        site_ref=site,
        case_ref=case,
        prefix_ref=prefix,
        obligation_ontology_sha256=_digest("ontology"),
        residual_obligation_snapshot_sha256=_digest(target + ":residual"),
        residual_source_receipt_sha256=_digest(target + ":residual-source"),
        capability_matrix_sha256=_digest("matrix"),
        capability_matrix_source_receipt_sha256=_digest("matrix-source"),
        alignment_rule_sha256=_digest("alignment-rule"),
        alignment_measure_kind=measure_kind,
        capability_dimension_sha256=_digest("dimension"),
        obligation_relation_sha256=_digest("relation"),
        effect_modifier_stratum=(
            "matched_residual_absent" if control_mode else "matched_residual_present"
        ),
        support_cell_sha256=_digest(target + ":support"),
        pair_set_sha256=pair_set_sha256,
    )
    high_binding = subject.FrozenResidualCapabilityBinding.create(
        **shared,
        opaque_packet_id=high_packet,
        complete_bundle_manifest_sha256=high_manifest,
        alignment_role="residual_absent_control" if control_mode else "high",
    )
    low_binding = subject.FrozenResidualCapabilityBinding.create(
        **shared,
        opaque_packet_id=low_packet,
        complete_bundle_manifest_sha256=low_manifest,
        alignment_role="residual_absent_control" if control_mode else "low",
    )
    support = subject.SyntheticSupportBalanceRecord.create(
        site_ref=site,
        case_ref=case,
        prefix_ref=prefix,
        support_cell_sha256=shared["support_cell_sha256"],
        target_census=1,
        cost_balance_sha256=_digest(target + ":cost-balance"),
        complete_token_balance_sha256=_digest(target + ":token-balance"),
        information_exposure_balance_sha256=_digest(target + ":information"),
        prompt_profile_length_balance_sha256=_digest(target + ":prompt-length"),
        tool_access_count_balance_sha256=_digest(target + ":tool-access"),
        synthesis_path_balance_sha256=_digest(target + ":synthesis"),
        admissibility_balance_sha256=_digest(target + ":admissibility"),
        global_bundle_strength_control_sha256=None,
        uniform_random_control_sha256=None,
        residual_absent_control_selection_spec_sha256=selection_spec_sha256,
        support_status=support_status,
    )
    high_assignments: list[object] = []
    low_assignments: list[object] = []
    executions: list[object] = []
    branches: list[object] = []
    plan_sha = _digest(target + ":plan")
    packet_roster_sha = _digest(target + ":packet-roster")
    target_roster_sha = _target_action_roster_digest(
        site,
        case,
        prefix,
        tuple(sorted((high_packet, low_packet))),
        tuple((repeat, 100 + repeat) for repeat in range(len(high_qualities))),
    )
    probability_spec_sha = _digest(target + ":probability")
    for repeat, (high_quality, low_quality, high_cost, low_cost) in enumerate(
        zip(high_qualities, low_qualities, high_costs, low_costs, strict=True)
    ):
        seed = 100 + repeat
        for arm, packet, manifest, quality, cost in (
            ("high", high_packet, high_manifest, high_quality, high_cost),
            ("low", low_packet, low_manifest, low_quality, low_cost),
        ):
            assignment_ref = (
                _opaque_id("assignment", f"{fixture_identity}:{repeat}:{arm}")
            )
            slot = _opaque_id("slot", f"{fixture_identity}:{arm}")
            assignment = subject.SyntheticAssignmentCrossoverRecord.create(
                assignment_ref=assignment_ref,
                site_ref=site,
                case_ref=case,
                prefix_ref=prefix,
                repeat_index=repeat,
                seed=seed,
                assigned_opaque_slot_id=slot,
                assigned_actual_packet_id=packet,
                assigned_complete_bundle_manifest_sha256=manifest,
                assignment_probability=0.5,
                assignment_probability_spec_sha256=probability_spec_sha,
                randomization_nonce_sha256=_digest(assignment_ref + ":nonce"),
                cyclic_crossover_plan_sha256=plan_sha,
                complete_packet_roster_sha256=packet_roster_sha,
                immutable_target_roster_sha256=target_roster_sha,
            )
            conformance_sha = _digest(assignment_ref + ":conformance")
            execution = subject.SyntheticExecutionConformanceRecord.create(
                assignment_ref=assignment_ref,
                site_ref=site,
                case_ref=case,
                prefix_ref=prefix,
                repeat_index=repeat,
                seed=seed,
                assigned_opaque_slot_id=slot,
                assigned_actual_packet_id=packet,
                actual_opaque_slot_id=slot,
                actual_packet_id=packet,
                actual_complete_bundle_manifest_sha256=manifest,
                pre_call_execution_isolation_receipt_sha256=_digest(
                    assignment_ref + ":isolation"
                ),
                post_run_execution_usage_conformance_receipt_sha256=conformance_sha,
                usage_ledger_sha256=_digest(assignment_ref + ":usage"),
                compliance_status="verified",
            )
            branch = subject.SyntheticTerminalBranch.create(
                site_ref=site,
                case_ref=case,
                prefix_ref=prefix,
                treatment_kind="capability_packet",
                opaque_slot_id=slot,
                actual_packet_id=packet,
                repeat_index=repeat,
                seed=seed,
                blind_terminal_quality=quality,
                complete_processed_tokens=100 + repeat,
                latency_seconds=1.0 + repeat,
                list_price_cost=cost,
                execution_conformance_sha256=conformance_sha,
                direct_terminal_sha256=_digest(assignment_ref + ":terminal"),
            )
            (high_assignments if arm == "high" else low_assignments).append(assignment)
            executions.append(execution)
            branches.append(branch)
    closure = subject.SyntheticPairAssignmentClosure.create(
        site_ref=site,
        case_ref=case,
        prefix_ref=prefix,
        high_assignment_record_sha256s=tuple(
            sorted(row.record_sha256 for row in high_assignments)
        ),
        low_assignment_record_sha256s=tuple(
            sorted(row.record_sha256 for row in low_assignments)
        ),
        cyclic_crossover_plan_sha256=plan_sha,
        complete_packet_roster_sha256=packet_roster_sha,
        immutable_target_roster_sha256=target_roster_sha,
        assignment_probability_spec_sha256=probability_spec_sha,
    )
    pair = subject.FrozenE2Pair.create(
        site_ref=site,
        case_ref=case,
        prefix_ref=prefix,
        high_packet_id=high_packet,
        high_complete_bundle_manifest_sha256=high_manifest,
        high_residual_capability_binding_sha256=high_binding.binding_sha256,
        low_packet_id=low_packet,
        low_complete_bundle_manifest_sha256=low_manifest,
        low_residual_capability_binding_sha256=low_binding.binding_sha256,
        pair_assignment_closure_sha256=closure.closure_sha256,
        balance_support_record_sha256=support.record_sha256,
        evaluator_reference_sha256=evaluator_reference_sha256,
        pair_set_sha256=shared["pair_set_sha256"],
    )
    return {
        "bindings": [high_binding, low_binding],
        "assignments": high_assignments + low_assignments,
        "closures": [closure],
        "supports": [support],
        "executions": executions,
        "branches": branches,
        "pairs": [pair],
        "control_pairs": [],
        "control_rosters": [],
        "auxiliary_identity_refs": [],
        "uniform_assignment_hashes": [],
        "e1_rosters": [],
        "solo_records": [],
        "auxiliary_plans": [],
        "auxiliary_conformances": [],
        "packet_identity": (high_packet, high_manifest, low_packet, low_manifest),
        "selection_spec_sha256": selection_spec_sha256,
        "evaluator_reference_sha256": evaluator_reference_sha256,
        "pair_set_sha256": pair_set_sha256,
    }


def _focal_pair_key(pair: object) -> str:
    return hashlib.sha256(
        _json_bytes(
            [
                pair.site_ref,
                pair.case_ref,
                pair.prefix_ref,
                pair.high_packet_id,
                pair.high_complete_bundle_manifest_sha256,
                pair.low_packet_id,
                pair.low_complete_bundle_manifest_sha256,
                pair.evaluator_reference_sha256,
                pair.pair_set_sha256,
            ]
        )
    ).hexdigest()


def _add_control(
    subject: object,
    focal: dict[str, object],
    *,
    case: str,
    prefix: str,
    high_qualities: tuple[float, ...],
    low_qualities: tuple[float, ...],
    high_costs: tuple[float, ...],
    low_costs: tuple[float, ...],
    matching_weight: float = 1.0,
    site: str | None = None,
) -> dict[str, object]:
    focal_pair = focal["pairs"][0]  # type: ignore[index]
    control = _target_records(
        subject,
        site=site or focal_pair.site_ref,
        case=case,
        prefix=prefix,
        high_qualities=high_qualities,
        low_qualities=low_qualities,
        high_costs=high_costs,
        low_costs=low_costs,
        packet_identity=focal["packet_identity"],  # type: ignore[arg-type]
        pair_set_sha256=focal["pair_set_sha256"],  # type: ignore[arg-type]
        evaluator_reference_sha256=focal["evaluator_reference_sha256"],  # type: ignore[arg-type]
        selection_spec_sha256=focal["selection_spec_sha256"],  # type: ignore[arg-type]
        measure_kind=focal["bindings"][0].alignment_measure_kind,  # type: ignore[index]
        control_mode=True,
    )
    closure = control["closures"][0]  # type: ignore[index]
    support = control["supports"][0]  # type: ignore[index]
    bindings = control["bindings"]  # type: ignore[assignment]
    high_binding, low_binding = bindings
    focal_key = _focal_pair_key(focal_pair)
    key_payload = {
        "balance_support_record_sha256": support.record_sha256,
        "case_ref": case,
        "control_ref": _opaque_id("control", f"{case}:{prefix}"),
        "evaluator_reference_sha256": focal["evaluator_reference_sha256"],
        "focal_pair_key_sha256": focal_key,
        "high_complete_bundle_manifest_sha256": focal_pair.high_complete_bundle_manifest_sha256,
        "high_packet_id": focal_pair.high_packet_id,
        "high_residual_capability_binding_sha256": high_binding.binding_sha256,
        "low_complete_bundle_manifest_sha256": focal_pair.low_complete_bundle_manifest_sha256,
        "low_packet_id": focal_pair.low_packet_id,
        "low_residual_capability_binding_sha256": low_binding.binding_sha256,
        "matching_weight": matching_weight,
        "pair_assignment_closure_sha256": closure.closure_sha256,
        "pair_set_sha256": focal_pair.pair_set_sha256,
        "prefix_ref": prefix,
        "site_ref": site or focal_pair.site_ref,
    }
    control_key = hashlib.sha256(_json_bytes(key_payload)).hexdigest()
    control_pair = subject.SyntheticResidualAbsentControlPair.create(
        **key_payload,
        residual_absent_control_selection_spec_sha256=focal["selection_spec_sha256"],
        control_pair_key_sha256=control_key,
    )
    roster = subject.SyntheticResidualAbsentControlRoster.create(
        focal_pair_key_sha256=focal_key,
        support_cell_sha256=focal_pair and focal["supports"][0].support_cell_sha256,  # type: ignore[index]
        pair_set_sha256=focal_pair.pair_set_sha256,
        control_pair_key_sha256s=(control_key,),
        matching_weights=(matching_weight,),
        selection_spec_sha256=focal["selection_spec_sha256"],
    )
    for key in ("bindings", "assignments", "closures", "supports", "executions", "branches"):
        focal[key].extend(control[key])  # type: ignore[union-attr]
    focal["control_pairs"].append(control_pair)  # type: ignore[union-attr]
    focal["control_rosters"].append(roster)  # type: ignore[union-attr]
    return focal


def _rekey_control(control: object, /, **changes: object) -> object:
    values = asdict(control)
    values.update(changes)
    values.pop("synthetic_only")
    values.pop("control_pair_sha256")
    values.pop("control_pair_key_sha256")
    key_payload = {
        name: values[name]
        for name in (
            "control_ref",
            "focal_pair_key_sha256",
            "site_ref",
            "case_ref",
            "prefix_ref",
            "high_packet_id",
            "high_complete_bundle_manifest_sha256",
            "high_residual_capability_binding_sha256",
            "low_packet_id",
            "low_complete_bundle_manifest_sha256",
            "low_residual_capability_binding_sha256",
            "pair_assignment_closure_sha256",
            "balance_support_record_sha256",
            "evaluator_reference_sha256",
            "pair_set_sha256",
            "matching_weight",
        )
    }
    values["control_pair_key_sha256"] = hashlib.sha256(_json_bytes(key_payload)).hexdigest()
    return type(control).create(**values)


def _contract(subject: object, *targets: dict[str, object]) -> object:
    def gather(key: str) -> list[object]:
        return [row for target in targets for row in target[key]]  # type: ignore[index]

    # Each focal target receives one pre-outcome uniform admissible leg.  It
    # is not part of the focal contrast closure and can therefore only be
    # reached through its typed auxiliary plan.
    for target in targets:
        pair = target["pairs"][0]  # type: ignore[index]
        focal_cells = tuple(sorted({
            (row.repeat_index, row.seed)
            for row in target["assignments"]
            if (row.site_ref, row.case_ref, row.prefix_ref)
            == (pair.site_ref, pair.case_ref, pair.prefix_ref)
        }))  # type: ignore[index]
        packet_ids = tuple(sorted((pair.high_packet_id, pair.low_packet_id)))
        plan_roster_digest = _target_action_roster_digest(
            pair.site_ref, pair.case_ref, pair.prefix_ref, packet_ids, focal_cells
        )
        for repeat, seed in focal_cells:
            assignment_ref = _opaque_id("assignment", f"{pair.pair_sha256}:{repeat}:uniform")
            slot = _opaque_id("slot", f"{pair.pair_sha256}:{repeat}:uniform")
            assignment = subject.SyntheticAssignmentCrossoverRecord.create(
                assignment_ref=assignment_ref, site_ref=pair.site_ref, case_ref=pair.case_ref,
                prefix_ref=pair.prefix_ref, repeat_index=repeat, seed=seed,
                assigned_opaque_slot_id=slot, assigned_actual_packet_id=pair.high_packet_id,
                assigned_complete_bundle_manifest_sha256=pair.high_complete_bundle_manifest_sha256,
                assignment_probability=0.5,
                assignment_probability_spec_sha256=_digest(pair.pair_sha256 + ":uniform-probability"),
                randomization_nonce_sha256=_digest(assignment_ref + ":nonce"),
                cyclic_crossover_plan_sha256=_digest(pair.pair_sha256 + ":uniform-plan"),
                complete_packet_roster_sha256=_digest(pair.pair_sha256 + ":uniform-roster"),
                immutable_target_roster_sha256=plan_roster_digest,
            )
            execution_receipt = _digest(assignment_ref + ":conformance")
            execution = subject.SyntheticExecutionConformanceRecord.create(
                assignment_ref=assignment_ref, site_ref=pair.site_ref, case_ref=pair.case_ref,
                prefix_ref=pair.prefix_ref, repeat_index=repeat, seed=seed,
                assigned_opaque_slot_id=slot, assigned_actual_packet_id=pair.high_packet_id,
                actual_opaque_slot_id=slot, actual_packet_id=pair.high_packet_id,
                actual_complete_bundle_manifest_sha256=pair.high_complete_bundle_manifest_sha256,
                pre_call_execution_isolation_receipt_sha256=_digest(assignment_ref + ":isolation"),
                post_run_execution_usage_conformance_receipt_sha256=execution_receipt,
                usage_ledger_sha256=_digest(assignment_ref + ":usage"), compliance_status="verified",
            )
            branch = subject.SyntheticTerminalBranch.create(
                site_ref=pair.site_ref, case_ref=pair.case_ref, prefix_ref=pair.prefix_ref,
                treatment_kind="capability_packet", opaque_slot_id=slot,
                actual_packet_id=pair.high_packet_id, repeat_index=repeat, seed=seed,
                blind_terminal_quality=0.0, complete_processed_tokens=1, latency_seconds=0.0,
                list_price_cost=0.0, execution_conformance_sha256=execution_receipt,
                direct_terminal_sha256=_digest(assignment_ref + ":terminal"),
            )
            target["assignments"].append(assignment)  # type: ignore[index]
            target["executions"].append(execution)  # type: ignore[index]
            target["branches"].append(branch)  # type: ignore[index]
            target["uniform_assignment_hashes"].append(assignment.record_sha256)  # type: ignore[index]
        target["auxiliary_identity_refs"].append(_opaque_id("control", pair.pair_sha256 + ":uniform"))  # type: ignore[index]

    registry = _registry(subject, *targets)
    focal_groups: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for target in targets:
        pair = target["pairs"][0]  # type: ignore[index]
        focal_groups.setdefault(
            (pair.site_ref, pair.case_ref, pair.prefix_ref), []
        ).append(target)
    rosters_by_target: dict[tuple[str, str, str], object] = {}
    for target_key, grouped in focal_groups.items():
        packet_ids = tuple(sorted({
            packet_id
            for target in grouped
            for packet_id in (
                target["pairs"][0].high_packet_id,  # type: ignore[index]
                target["pairs"][0].low_packet_id,  # type: ignore[index]
            )
        }))
        cells = tuple(sorted({
            (row.repeat_index, row.seed)
            for target in grouped
            for row in target["assignments"]  # type: ignore[index]
            if row.record_sha256 in set(next(
                closure for closure in target["closures"]  # type: ignore[index]
                if closure.closure_sha256
                == target["pairs"][0].pair_assignment_closure_sha256  # type: ignore[index]
            ).high_assignment_record_sha256s)
        }))
        roster = subject.SyntheticE1ActionRosterV2.create(
            site_ref=target_key[0], case_ref=target_key[1], prefix_ref=target_key[2],
            packet_ids=packet_ids, repeat_seed_cells=cells,
            common_synthesis_spec_sha256=_digest("common-synthesis"),
            opaque_identity_registry_sha256=registry.registry_sha256,
        )
        rosters_by_target[target_key] = roster
        grouped[0]["e1_rosters"].append(roster)  # type: ignore[index]
        for repeat_index, seed in cells:
            solo = subject.SyntheticSoloExecutionConformanceV2.create(
                site_ref=target_key[0], case_ref=target_key[1], prefix_ref=target_key[2],
                repeat_index=repeat_index, seed=seed,
                common_synthesis_spec_sha256=roster.common_synthesis_spec_sha256,
                pre_call_execution_isolation_receipt_sha256=_digest(f"e1-solo-isolation:{repeat_index}"),
                post_run_execution_usage_conformance_receipt_sha256=_digest(f"e1-solo-conformance:{repeat_index}"),
                usage_ledger_sha256=_digest(f"e1-solo-ledger:{repeat_index}"),
                compliance_status="verified",
            )
            grouped[0]["solo_records"].append(solo)  # type: ignore[index]
            grouped[0]["branches"].append(subject.SyntheticTerminalBranch.create(  # type: ignore[index]
                site_ref=target_key[0], case_ref=target_key[1], prefix_ref=target_key[2],
                treatment_kind="solo_synthesis", opaque_slot_id=None, actual_packet_id=None,
                repeat_index=repeat_index, seed=seed, blind_terminal_quality=0.5,
                complete_processed_tokens=1, latency_seconds=0.0, list_price_cost=0.0,
                execution_conformance_sha256=solo.record_sha256,
                direct_terminal_sha256=_digest(f"e1-solo-terminal:{repeat_index}"),
            ))
    for target in targets:
        pair = target["pairs"][0]  # type: ignore[index]
        focal_closure = next(
            row for row in target["closures"]  # type: ignore[index]
            if row.closure_sha256 == pair.pair_assignment_closure_sha256
        )
        focal_cells = tuple(sorted({
            (row.repeat_index, row.seed)
            for row in target["assignments"]  # type: ignore[index]
            if row.record_sha256 in set(focal_closure.high_assignment_record_sha256s)
        }))
        roster = rosters_by_target[(pair.site_ref, pair.case_ref, pair.prefix_ref)]
        focal_hashes = set(
            focal_closure.high_assignment_record_sha256s
            + focal_closure.low_assignment_record_sha256s
        )
        focal_replacements = {
            row.record_sha256: _rebuild(
                row, immutable_target_roster_sha256=roster.roster_sha256
            )
            for row in target["assignments"]  # type: ignore[index]
            if row.record_sha256 in focal_hashes
        }
        replacement_closure = _rebuild(
            focal_closure,
            high_assignment_record_sha256s=tuple(sorted(
                focal_replacements[key].record_sha256
                for key in focal_closure.high_assignment_record_sha256s
            )),
            low_assignment_record_sha256s=tuple(sorted(
                focal_replacements[key].record_sha256
                for key in focal_closure.low_assignment_record_sha256s
            )),
            immutable_target_roster_sha256=roster.roster_sha256,
        )
        replacement_pair = _rebuild(
            pair, pair_assignment_closure_sha256=replacement_closure.closure_sha256
        )
        uniform_plan_digest = _target_action_roster_digest(
            pair.site_ref, pair.case_ref, pair.prefix_ref,
            roster.packet_ids, roster.repeat_seed_cells,
        )
        uniform_hashes = set(target["uniform_assignment_hashes"])  # type: ignore[arg-type]
        uniform_replacements = {
            row.record_sha256: _rebuild(
                row,
                immutable_target_roster_sha256=uniform_plan_digest,
                assignment_probability=1.0 / len(roster.packet_ids),
                assignment_probability_spec_sha256=_digest(
                    replacement_pair.pair_sha256 + ":uniform-probability"
                ),
            )
            for row in target["assignments"]  # type: ignore[index]
            if row.record_sha256 in uniform_hashes
        }
        replacements = {**focal_replacements, **uniform_replacements}
        target["assignments"] = [
            replacements.get(row.record_sha256, row)
            for row in target["assignments"]  # type: ignore[index]
        ]
        target["uniform_assignment_hashes"] = [
            row.record_sha256 for row in target["assignments"]  # type: ignore[index]
            if row.assignment_ref in {
                replacement.assignment_ref for replacement in uniform_replacements.values()
            }
        ]
        target["closures"] = [
            replacement_closure if row.closure_sha256 == focal_closure.closure_sha256 else row
            for row in target["closures"]  # type: ignore[index]
        ]
        target["pairs"] = [replacement_pair]  # type: ignore[index]

    for target in targets:
        pair = target["pairs"][0]  # type: ignore[index]
        focal_key = _focal_pair_key(pair)
        roster = rosters_by_target[(pair.site_ref, pair.case_ref, pair.prefix_ref)]
        support = next(row for row in target["supports"] if row.record_sha256 == pair.balance_support_record_sha256)  # type: ignore[index]
        control = target["control_pairs"][0]  # type: ignore[index]
        control_support = next(row for row in target["supports"] if row.record_sha256 == control.balance_support_record_sha256)  # type: ignore[index]
        try:
            control_closure = next(
                row for row in target["closures"]  # type: ignore[index]
                if row.closure_sha256 == control.pair_assignment_closure_sha256
            )
        except StopIteration as error:
            raise ValueError("control closure does not resolve") from error
        focal_cells = tuple(sorted({(row.repeat_index, row.seed) for row in target["assignments"] if row.record_sha256 in set(next(row for row in target["closures"] if row.closure_sha256 == pair.pair_assignment_closure_sha256).high_assignment_record_sha256s)}))  # type: ignore[index]
        global_assignments = tuple(sorted(control_closure.high_assignment_record_sha256s + control_closure.low_assignment_record_sha256s))
        uniform_assignments = tuple(sorted(target["uniform_assignment_hashes"]))  # type: ignore[index]
        global_plan = subject.AuxiliaryControlPlanV2.create(
            control_ref=control.control_ref, control_kind="global_bundle_strength", focal_pair_key_sha256=focal_key,
            site_ref=control.site_ref, case_ref=control.case_ref, prefix_ref=control.prefix_ref,
            target_action_roster_sha256=_target_action_roster_digest(
                control.site_ref, control.case_ref, control.prefix_ref,
                tuple(sorted((pair.high_packet_id, pair.low_packet_id))), focal_cells,
            ),
            packet_ids=tuple(sorted((pair.high_packet_id, pair.low_packet_id))), repeat_seed_cells=focal_cells,
            assignment_record_sha256s=global_assignments, assignment_reference_multiplicities=(1,) * len(global_assignments),
            selection_probability_spec_sha256=control_support.residual_absent_control_selection_spec_sha256,
            support_cell_sha256=control_support.support_cell_sha256,
        )
        uniform_plan = subject.AuxiliaryControlPlanV2.create(
            control_ref=target["auxiliary_identity_refs"][0], control_kind="uniform_random_admissible", focal_pair_key_sha256=focal_key,  # type: ignore[index]
            site_ref=pair.site_ref, case_ref=pair.case_ref, prefix_ref=pair.prefix_ref,
            target_action_roster_sha256=_target_action_roster_digest(
                pair.site_ref, pair.case_ref, pair.prefix_ref,
                roster.packet_ids, roster.repeat_seed_cells,
            ),
            packet_ids=roster.packet_ids, repeat_seed_cells=roster.repeat_seed_cells,
            assignment_record_sha256s=uniform_assignments, assignment_reference_multiplicities=(1,) * len(uniform_assignments),
            selection_probability_spec_sha256=_digest(pair.pair_sha256 + ":uniform-probability"), support_cell_sha256=support.support_cell_sha256,
        )
        for plan in (global_plan, uniform_plan):
            executions = []
            terminals = []
            for assignment_hash in plan.assignment_record_sha256s:
                assignment = next(row for row in target["assignments"] if row.record_sha256 == assignment_hash)  # type: ignore[index]
                execution = next(row for row in target["executions"] if row.assignment_ref == assignment.assignment_ref)  # type: ignore[index]
                terminal = next(row for row in target["branches"] if row.execution_conformance_sha256 == execution.post_run_execution_usage_conformance_receipt_sha256)  # type: ignore[index]
                executions.append(execution.record_sha256)
                terminals.append(terminal.record_sha256)
            conformance = subject.AuxiliaryControlConformanceV2.create(
                control_plan_sha256=plan.plan_sha256, assignment_record_sha256s=plan.assignment_record_sha256s,
                execution_record_sha256s=tuple(sorted(executions)), terminal_record_sha256s=tuple(sorted(terminals)),
                compliance_status="verified",
            )
            target["auxiliary_plans"].append(plan)  # type: ignore[index]
            target["auxiliary_conformances"].append(conformance)  # type: ignore[index]
        replacement_support = _rebuild(
            support,
            global_bundle_strength_control_sha256=target["auxiliary_conformances"][-2].conformance_sha256,  # type: ignore[index]
            uniform_random_control_sha256=target["auxiliary_conformances"][-1].conformance_sha256,  # type: ignore[index]
        )
        target["supports"] = [replacement_support if row.record_sha256 == support.record_sha256 else row for row in target["supports"]]  # type: ignore[index]
        target["pairs"] = [_rebuild(pair, balance_support_record_sha256=replacement_support.record_sha256)]  # type: ignore[index]

    return subject.E2MechanismContract.create(
        opaque_identity_registry=registry,
        e1_action_rosters=_ordered(gather("e1_rosters"), "roster_sha256"),
        solo_execution_records=_ordered(gather("solo_records"), "record_sha256"),
        auxiliary_control_plans=_ordered(gather("auxiliary_plans"), "plan_sha256"),
        auxiliary_control_conformances=_ordered(gather("auxiliary_conformances"), "conformance_sha256"),
        bindings=_ordered(gather("bindings"), "binding_sha256"),
        assignments=_ordered(gather("assignments"), "record_sha256"),
        pair_assignment_closures=_ordered(gather("closures"), "closure_sha256"),
        support_balance_records=_ordered(gather("supports"), "record_sha256"),
        execution_records=_ordered(gather("executions"), "record_sha256"),
        terminal_branches=_ordered(gather("branches"), "record_sha256"),
        pairs=_ordered(gather("pairs"), "pair_sha256"),
        residual_absent_control_pairs=_ordered(gather("control_pairs"), "control_pair_sha256"),
        residual_absent_control_rosters=_ordered(gather("control_rosters"), "roster_sha256"),
        blind_outcome_schema_sha256=_digest("blind-outcome"),
        common_synthesis_spec_sha256=_digest("common-synthesis"),
        analysis_code_sha256=_digest("analysis-code"),
    )


def _e1_owned_contract(subject: object, *, shared_uniform_leg: bool) -> object:
    focal = _target_records(
        subject, site="site-e1", case="case-e1", prefix="prefix-e1",
        high_qualities=(0.8, 0.6), low_qualities=(0.4, 0.5),
        high_costs=(0.1, 0.1), low_costs=(0.1, 0.1),
    )
    _add_control(
        subject, focal, case="case-control", prefix="prefix-control",
        high_qualities=(0.7, 0.7), low_qualities=(0.3, 0.3),
        high_costs=(0.1, 0.1), low_costs=(0.1, 0.1),
    )
    contract = _contract(subject, focal)
    if not shared_uniform_leg:
        return contract
    pair = contract.pairs[0]
    closure = next(
        row for row in contract.pair_assignment_closures
        if row.closure_sha256 == pair.pair_assignment_closure_sha256
    )
    roster = contract.e1_action_rosters[0]
    uniform_plan = next(
        row for row in contract.auxiliary_control_plans
        if row.control_kind == "uniform_random_admissible"
    )
    owned_hashes = set(
        closure.high_assignment_record_sha256s + closure.low_assignment_record_sha256s
    )
    replacements = {
        row.record_sha256: _rebuild(
            row,
            immutable_target_roster_sha256=roster.roster_sha256,
            **(
                {"assignment_probability_spec_sha256": uniform_plan.selection_probability_spec_sha256}
                if shared_uniform_leg else {}
            ),
        )
        for row in contract.assignments if row.record_sha256 in owned_hashes
    }
    assignments = _ordered(
        [replacements.get(row.record_sha256, row) for row in contract.assignments],
        "record_sha256",
    )
    executions = contract.execution_records
    branches = contract.terminal_branches
    replacement_closure = _rebuild(
        closure,
        high_assignment_record_sha256s=tuple(sorted(
            replacements[key].record_sha256 for key in closure.high_assignment_record_sha256s
        )),
        low_assignment_record_sha256s=tuple(sorted(
            replacements[key].record_sha256 for key in closure.low_assignment_record_sha256s
        )),
        immutable_target_roster_sha256=roster.roster_sha256,
        assignment_probability_spec_sha256=(
            uniform_plan.selection_probability_spec_sha256
            if shared_uniform_leg else closure.assignment_probability_spec_sha256
        ),
    )
    closures = _ordered(
        [
            replacement_closure if row.closure_sha256 == closure.closure_sha256 else row
            for row in contract.pair_assignment_closures
        ],
        "closure_sha256",
    )
    plans = list(contract.auxiliary_control_plans)
    conformances = list(contract.auxiliary_control_conformances)
    support = next(
        row for row in contract.support_balance_records
        if row.record_sha256 == pair.balance_support_record_sha256
    )
    if shared_uniform_leg:
        plan = uniform_plan
        plan_only_hashes = set(plan.assignment_record_sha256s)
        plan_only_refs = {
            row.assignment_ref for row in assignments if row.record_sha256 in plan_only_hashes
        }
        plan_only_receipts = {
            row.post_run_execution_usage_conformance_receipt_sha256
            for row in executions if row.assignment_ref in plan_only_refs
        }
        assignments = _ordered(
            [row for row in assignments if row.record_sha256 not in plan_only_hashes],
            "record_sha256",
        )
        executions = _ordered(
            [row for row in executions if row.assignment_ref not in plan_only_refs],
            "record_sha256",
        )
        branches = _ordered(
            [row for row in branches if row.execution_conformance_sha256 not in plan_only_receipts],
            "record_sha256",
        )
        shared_assignments = tuple(sorted(
            replacements[key].record_sha256 for key in closure.high_assignment_record_sha256s
        ))
        replacement_plan = _rebuild(
            plan, assignment_record_sha256s=shared_assignments,
            assignment_reference_multiplicities=(1,) * len(shared_assignments),
        )
        execution_hashes = []
        terminal_hashes = []
        for assignment_hash in shared_assignments:
            assignment = next(row for row in assignments if row.record_sha256 == assignment_hash)
            execution = next(
                row for row in executions
                if row.assignment_ref == assignment.assignment_ref
            )
            terminal = next(
                row for row in branches
                if row.execution_conformance_sha256
                == execution.post_run_execution_usage_conformance_receipt_sha256
            )
            execution_hashes.append(execution.record_sha256)
            terminal_hashes.append(terminal.record_sha256)
        old_conformance = next(
            row for row in conformances if row.control_plan_sha256 == plan.plan_sha256
        )
        replacement_conformance = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=replacement_plan.plan_sha256,
            assignment_record_sha256s=shared_assignments,
            execution_record_sha256s=tuple(sorted(execution_hashes)),
            terminal_record_sha256s=tuple(sorted(terminal_hashes)),
            compliance_status="verified",
        )
        plans = [
            replacement_plan if row.plan_sha256 == plan.plan_sha256 else row for row in plans
        ]
        conformances = [
            replacement_conformance if row.conformance_sha256 == old_conformance.conformance_sha256 else row
            for row in conformances
        ]
        support = _rebuild(
            support, uniform_random_control_sha256=replacement_conformance.conformance_sha256
        )
    supports = _ordered(
        [
            support if row.record_sha256 == pair.balance_support_record_sha256 else row
            for row in contract.support_balance_records
        ],
        "record_sha256",
    )
    replacement_pair = _rebuild(
        pair, pair_assignment_closure_sha256=replacement_closure.closure_sha256,
        balance_support_record_sha256=support.record_sha256,
    )
    return subject.E2MechanismContract.create(
        opaque_identity_registry=contract.opaque_identity_registry, e1_action_rosters=(roster,),
        solo_execution_records=contract.solo_execution_records,
        auxiliary_control_plans=_ordered(plans, "plan_sha256"),
        auxiliary_control_conformances=_ordered(conformances, "conformance_sha256"),
        bindings=contract.bindings, assignments=assignments,
        pair_assignment_closures=closures, support_balance_records=supports,
        execution_records=executions,
        terminal_branches=branches,
        pairs=(replacement_pair,),
        residual_absent_control_pairs=contract.residual_absent_control_pairs,
        residual_absent_control_rosters=contract.residual_absent_control_rosters,
        blind_outcome_schema_sha256=contract.blind_outcome_schema_sha256,
        common_synthesis_spec_sha256=contract.common_synthesis_spec_sha256,
        analysis_code_sha256=contract.analysis_code_sha256,
    )


def _rebind_auxiliary_assignment(
    subject: object, contract: object, plan: object, old_assignment: object,
    replacement_assignment: object,
) -> object:
    """Propagate an auxiliary assignment replacement through its exact records."""
    assignments = _ordered(
        [
            replacement_assignment if row.record_sha256 == old_assignment.record_sha256 else row
            for row in contract.assignments
        ],
        "record_sha256",
    )
    replacement_plan = _rebuild(
        plan,
        assignment_record_sha256s=tuple(sorted(
            replacement_assignment.record_sha256
            if row == old_assignment.record_sha256 else row
            for row in plan.assignment_record_sha256s
        )),
    )
    old_conformance = next(
        row for row in contract.auxiliary_control_conformances
        if row.control_plan_sha256 == plan.plan_sha256
    )
    replacement_conformance = subject.AuxiliaryControlConformanceV2.create(
        control_plan_sha256=replacement_plan.plan_sha256,
        assignment_record_sha256s=replacement_plan.assignment_record_sha256s,
        execution_record_sha256s=old_conformance.execution_record_sha256s,
        terminal_record_sha256s=old_conformance.terminal_record_sha256s,
        compliance_status=old_conformance.compliance_status,
    )
    plans = _ordered(
        [
            replacement_plan if row.plan_sha256 == plan.plan_sha256 else row
            for row in contract.auxiliary_control_plans
        ],
        "plan_sha256",
    )
    conformances = _ordered(
        [
            replacement_conformance if row.conformance_sha256 == old_conformance.conformance_sha256 else row
            for row in contract.auxiliary_control_conformances
        ],
        "conformance_sha256",
    )
    pair = contract.pairs[0]
    support = next(
        row for row in contract.support_balance_records
        if row.record_sha256 == pair.balance_support_record_sha256
    )
    support_change = (
        {"global_bundle_strength_control_sha256": replacement_conformance.conformance_sha256}
        if plan.control_kind == "global_bundle_strength"
        else {"uniform_random_control_sha256": replacement_conformance.conformance_sha256}
    )
    replacement_support = _rebuild(support, **support_change)
    supports = _ordered(
        [
            replacement_support if row.record_sha256 == support.record_sha256 else row
            for row in contract.support_balance_records
        ],
        "record_sha256",
    )
    replacement_pair = _rebuild(
        pair, balance_support_record_sha256=replacement_support.record_sha256
    )
    return _rebuild(
        contract,
        assignments=assignments,
        auxiliary_control_plans=plans,
        auxiliary_control_conformances=conformances,
        support_balance_records=supports,
        pairs=(replacement_pair,),
    )


def _rebind_e1_focal_assignments(
    contract: object, replacements: dict[str, object]
) -> object:
    """Carry a focal E1 assignment edit through its closure and focal pair."""
    assignments = _ordered(
        [replacements.get(row.record_sha256, row) for row in contract.assignments],
        "record_sha256",
    )
    pair = contract.pairs[0]
    closure = next(
        row for row in contract.pair_assignment_closures
        if row.closure_sha256 == pair.pair_assignment_closure_sha256
    )
    replacement_closure = _rebuild(
        closure,
        high_assignment_record_sha256s=tuple(sorted(
            replacements.get(key, next(
                row for row in contract.assignments if row.record_sha256 == key
            )).record_sha256
            for key in closure.high_assignment_record_sha256s
        )),
        low_assignment_record_sha256s=tuple(sorted(
            replacements.get(key, next(
                row for row in contract.assignments if row.record_sha256 == key
            )).record_sha256
            for key in closure.low_assignment_record_sha256s
        )),
    )
    closures = _ordered(
        [
            replacement_closure if row.closure_sha256 == closure.closure_sha256 else row
            for row in contract.pair_assignment_closures
        ],
        "closure_sha256",
    )
    replacement_pair = _rebuild(
        pair, pair_assignment_closure_sha256=replacement_closure.closure_sha256
    )
    return _rebuild(
        contract, assignments=assignments, pair_assignment_closures=closures,
        pairs=(replacement_pair,),
    )


def _rebind_uniform_menu(
    subject: object,
    contract: object,
    *,
    packet_ids: tuple[str, ...],
    repeat_seed_cells: tuple[tuple[int, int], ...] | None = None,
) -> object:
    """Rehash the full uniform plan chain after a declared-menu mutation."""
    plan = next(
        row for row in contract.auxiliary_control_plans
        if row.control_kind == "uniform_random_admissible"
    )
    cells = repeat_seed_cells if repeat_seed_cells is not None else plan.repeat_seed_cells
    digest = _target_action_roster_digest(
        plan.site_ref, plan.case_ref, plan.prefix_ref, packet_ids, cells
    )
    selected = set(plan.assignment_record_sha256s)
    replacements = {
        row.record_sha256: _rebuild(
            row,
            immutable_target_roster_sha256=digest,
            assignment_probability=1.0 / len(packet_ids),
        )
        for row in contract.assignments if row.record_sha256 in selected
    }
    assignments = _ordered(
        [replacements.get(row.record_sha256, row) for row in contract.assignments],
        "record_sha256",
    )
    replacement_plan = _rebuild(
        plan,
        target_action_roster_sha256=digest,
        packet_ids=packet_ids,
        repeat_seed_cells=cells,
        assignment_record_sha256s=tuple(sorted(
            replacements[key].record_sha256 for key in plan.assignment_record_sha256s
        )),
    )
    old_conformance = next(
        row for row in contract.auxiliary_control_conformances
        if row.control_plan_sha256 == plan.plan_sha256
    )
    replacement_conformance = subject.AuxiliaryControlConformanceV2.create(
        control_plan_sha256=replacement_plan.plan_sha256,
        assignment_record_sha256s=replacement_plan.assignment_record_sha256s,
        execution_record_sha256s=old_conformance.execution_record_sha256s,
        terminal_record_sha256s=old_conformance.terminal_record_sha256s,
        compliance_status=old_conformance.compliance_status,
    )
    plans = _ordered(
        [
            replacement_plan if row.plan_sha256 == plan.plan_sha256 else row
            for row in contract.auxiliary_control_plans
        ],
        "plan_sha256",
    )
    conformances = _ordered(
        [
            replacement_conformance if row.conformance_sha256 == old_conformance.conformance_sha256 else row
            for row in contract.auxiliary_control_conformances
        ],
        "conformance_sha256",
    )
    pair = contract.pairs[0]
    support = next(
        row for row in contract.support_balance_records
        if row.record_sha256 == pair.balance_support_record_sha256
    )
    replacement_support = _rebuild(
        support, uniform_random_control_sha256=replacement_conformance.conformance_sha256
    )
    supports = _ordered(
        [
            replacement_support if row.record_sha256 == support.record_sha256 else row
            for row in contract.support_balance_records
        ],
        "record_sha256",
    )
    replacement_pair = _rebuild(
        pair, balance_support_record_sha256=replacement_support.record_sha256
    )
    return _rebuild(
        contract,
        assignments=assignments,
        auxiliary_control_plans=plans,
        auxiliary_control_conformances=conformances,
        support_balance_records=supports,
        pairs=(replacement_pair,),
    )


def _registered_uniform_superset(subject: object, contract: object) -> object:
    """Make a fully registered uniform strict-superset fixture for rejection."""
    roster = contract.e1_action_rosters[0]
    extra_packet = _opaque_id("packet", "registered-uniform-superset")
    _, extra_ordinal = _IDENTITY_ORDINALS[extra_packet]
    registry = subject.SyntheticOpaqueIdentityRegistryV2.create(
        derivation_seed_sha256=contract.opaque_identity_registry.derivation_seed_sha256,
        entries=tuple(sorted(
            [*contract.opaque_identity_registry.entries, ("packet", extra_ordinal, extra_packet)],
            key=lambda row: (row[0].encode("ascii"), row[1]),
        )),
        packet_manifest_bindings=tuple(sorted(
            [
                *contract.opaque_identity_registry.packet_manifest_bindings,
                (extra_packet, _digest("registered-uniform-superset-manifest")),
            ],
            key=lambda row: row[0].encode("ascii"),
        )),
    )
    replacement_roster = _rebuild(
        roster, opaque_identity_registry_sha256=registry.registry_sha256
    )
    replacements = {
        row.record_sha256: _rebuild(
            row, immutable_target_roster_sha256=replacement_roster.roster_sha256
        )
        for row in contract.assignments
        if row.immutable_target_roster_sha256 == roster.roster_sha256
    }
    assignments = _ordered(
        [replacements.get(row.record_sha256, row) for row in contract.assignments],
        "record_sha256",
    )
    pair = contract.pairs[0]
    closure = next(
        row for row in contract.pair_assignment_closures
        if row.closure_sha256 == pair.pair_assignment_closure_sha256
    )
    replacement_closure = _rebuild(
        closure,
        high_assignment_record_sha256s=tuple(sorted(
            replacements[key].record_sha256 for key in closure.high_assignment_record_sha256s
        )),
        low_assignment_record_sha256s=tuple(sorted(
            replacements[key].record_sha256 for key in closure.low_assignment_record_sha256s
        )),
        immutable_target_roster_sha256=replacement_roster.roster_sha256,
    )
    intermediate = _rebuild(
        contract,
        opaque_identity_registry=registry,
        e1_action_rosters=(replacement_roster,),
        assignments=assignments,
        pair_assignment_closures=_ordered(
            [
                replacement_closure if row.closure_sha256 == closure.closure_sha256 else row
                for row in contract.pair_assignment_closures
            ],
            "closure_sha256",
        ),
        pairs=(_rebuild(pair, pair_assignment_closure_sha256=replacement_closure.closure_sha256),),
    )
    return _rebind_uniform_menu(
        subject,
        intermediate,
        packet_ids=tuple(sorted(
            (*replacement_roster.packet_ids, extra_packet), key=lambda value: value.encode("ascii")
        )),
    )


E3_PARENT_FIELDS = (
    "site_ref", "case_ref", "prefix_ref", "raw_transcript_prefix",
    "numeric_residual_serialization", "complete_capability_table",
    "opaque_packet_binding_cards", "costs", "admissibility", "examples",
    "split_fold", "learner_class_capacity", "tuning_optimization_opportunity",
    "target_action_roster", "action_space_tie_rule",
)


def _action_sha(action: object) -> str:
    return hashlib.sha256(_json_bytes(action)).hexdigest()


def _e3_identity_fixture(subject: object) -> tuple[object, object, object, tuple[dict[str, object], ...]]:
    packets = tuple(sorted((_opaque_id("packet", "e3-packet-a"), _opaque_id("packet", "e3-packet-b"))))
    slots = tuple(sorted((_opaque_id("slot", "e3-slot-a"), _opaque_id("slot", "e3-slot-b"))))
    manifests = {packet: _digest("manifest:" + packet) for packet in packets}
    identities = [
        (*_IDENTITY_ORDINALS[identifier], identifier)
        for identifier in (*packets, *slots)
    ]
    registry = subject.SyntheticOpaqueIdentityRegistryV2.create(
        derivation_seed_sha256=IDENTITY_SEED,
        entries=tuple(sorted(identities, key=lambda row: (row[0].encode("ascii"), row[1]))),
        packet_manifest_bindings=tuple((packet, manifests[packet]) for packet in packets),
    )
    bindings = tuple((slot, packet, manifests[packet]) for slot, packet in zip(slots, packets, strict=True))
    authority = subject.SyntheticE3TargetActionAuthorityV2.create(
        site_ref="site-e3", case_ref="case-e3", prefix_ref="prefix-e3",
        packet_slot_bindings=bindings,
        opaque_identity_registry_sha256=registry.registry_sha256,
    )
    shared_roster = subject.SyntheticE1ActionRosterV2.create(
        site_ref="site-e3", case_ref="case-e3", prefix_ref="prefix-e3",
        packet_ids=packets, repeat_seed_cells=((0, 11), (1, 13)),
        common_synthesis_spec_sha256=_digest("e3-common-synthesis"),
        opaque_identity_registry_sha256=registry.registry_sha256,
    )
    actions: tuple[dict[str, object], ...] = (
        {"action_kind": "stop"},
        {"action_kind": "solo"},
        *(
            {
                "action_kind": "capability_packet",
                "opaque_packet_id": packet,
                "opaque_slot_id": slot,
            }
            for slot, packet, _ in bindings
        ),
    )
    return registry, authority, shared_roster, actions


def _parity_fixture(
    subject: object,
) -> tuple[object, object, object, object, tuple[dict[str, object], ...], dict[str, object]]:
    registry, authority, shared_roster, actions = _e3_identity_fixture(subject)
    action_hashes = tuple(_action_sha(action) for action in actions)
    admissible = action_hashes[:-1]
    tie_rule = {
        "rule_sha256": hashlib.sha256(
            _json_bytes("max_blind_direct_value_then_roster_order")
        ).hexdigest(),
        "ordered_action_sha256s": list(action_hashes),
    }
    parent_obj: dict[str, object] = {
        "schema_version": IDENTITY_DOMAIN + ".e3_source_parent",
        "site_ref": "site-e3", "case_ref": "case-e3", "prefix_ref": "prefix-e3",
        "raw_transcript_prefix": [{"role": "user", "token_ids": [7, 11]}],
        "numeric_residual_serialization": {
            "obligation": [0.25, 0.75], "capability": [0.5, 0.5],
            "alignment": [0.8, 0.2],
        },
        "complete_capability_table": [
            {
                "opaque_slot_id": slot, "opaque_packet_id": packet,
                "complete_bundle_manifest_sha256": manifest,
                "capability_vector": [0.6, 0.4],
            }
            for slot, packet, manifest in authority.packet_slot_bindings
        ],
        "opaque_packet_binding_cards": [
            {"opaque_packet_id": packet, "binding_sha256": _digest("binding:" + packet)}
            for _, packet, _ in authority.packet_slot_bindings
        ],
        "costs": [
            {
                "action_sha256": action_hash, "processed_tokens": index,
                "latency_seconds": float(index), "list_price_cost": float(index) / 10.0,
            }
            for index, action_hash in enumerate(action_hashes)
        ],
        "admissibility": {"admissible_action_sha256s": list(admissible)},
        "examples": sorted(
            [
                {"input_sha256": _digest("example-a"), "action_sha256": admissible[0]},
                {"input_sha256": _digest("example-b"), "action_sha256": admissible[1]},
            ],
            key=lambda row: _json_bytes(row),
        ),
        "split_fold": {
            "held_out_site_ref": "site-e3", "training_site_refs": ["site-train-a", "site-train-b"],
            "manifest_sha256": _digest("fold-manifest"),
        },
        "learner_class_capacity": {
            "learner_class_sha256": _digest("learner-class"), "parameter_budget": 2,
            "context_token_budget": 128, "tool_policy_sha256": _digest("tool-policy"),
        },
        "tuning_optimization_opportunity": {
            "objective_sha256": _digest("objective"), "trial_budget": 2,
            "seeds": [3, 5], "early_stop_rule_sha256": _digest("early-stop"),
        },
        "target_action_roster": list(actions),
        "action_space_tie_rule": tie_rule,
    }
    parent = _json_bytes(parent_obj)
    oacs_map = {"o_" + name: name for name in E3_PARENT_FIELDS}
    raw_map = {"r_" + name: name for name in E3_PARENT_FIELDS}
    projection_schema = IDENTITY_DOMAIN + ".e3_projection_spec"
    oacs_spec_obj = {"schema_version": projection_schema, "field_map": oacs_map}
    raw_spec_obj = {"schema_version": projection_schema, "field_map": raw_map}
    oacs_spec = _json_bytes(oacs_spec_obj)
    raw_spec = _json_bytes(raw_spec_obj)
    oacs_input = _json_bytes({output: parent_obj[source] for output, source in oacs_map.items()})
    raw_input = _json_bytes({output: parent_obj[source] for output, source in raw_map.items()})
    equivalence = _json_bytes([
        {"parent_field": name, "oacs_field": "o_" + name, "raw_router_field": "r_" + name}
        for name in E3_PARENT_FIELDS
    ])
    roster = _json_bytes(list(actions))
    training_obj = {name: parent_obj[name] for name in (
        "costs", "admissibility", "examples", "split_fold", "learner_class_capacity",
        "tuning_optimization_opportunity", "action_space_tie_rule",
    )}
    training = _json_bytes(training_obj)
    oacs_decision = _json_bytes({"action": actions[0]})
    raw_decision = _json_bytes({"action": actions[1]})
    bundle = subject.SyntheticParityReplayBundle.create(
        source_parent_bytes=parent, oacs_input_bytes=oacs_input,
        raw_router_input_bytes=raw_input, oacs_projection_spec_bytes=oacs_spec,
        raw_router_projection_spec_bytes=raw_spec,
        information_equivalence_map_bytes=equivalence, target_action_roster_bytes=roster,
        shared_training_opportunity_bytes=training,
        oacs_pre_outcome_decision_bytes=oacs_decision,
        raw_router_pre_outcome_decision_bytes=raw_decision,
    )
    hash_fields = {
        "source_parent_receipt_sha256": hashlib.sha256(parent).hexdigest(),
        "oacs_input_bytes_sha256": hashlib.sha256(oacs_input).hexdigest(),
        "raw_router_input_bytes_sha256": hashlib.sha256(raw_input).hexdigest(),
        "oacs_projection_spec_sha256": hashlib.sha256(oacs_spec).hexdigest(),
        "raw_router_projection_spec_sha256": hashlib.sha256(raw_spec).hexdigest(),
        "information_equivalence_map_sha256": hashlib.sha256(equivalence).hexdigest(),
        "target_action_roster_sha256": hashlib.sha256(roster).hexdigest(),
        **{f"{key}_sha256": hashlib.sha256(_json_bytes(training_obj[key])).hexdigest() for key in training_obj},
        "oacs_pre_outcome_decisions_sha256": hashlib.sha256(oacs_decision).hexdigest(),
        "raw_router_pre_outcome_decisions_sha256": hashlib.sha256(raw_decision).hexdigest(),
    }
    receipt = subject.PairedInformationParityReceipt.create(
        schema_version=SCHEMA_PREFIX + "PairedInformationParityReceipt.v2",
        **hash_fields, pair_sha256=hashlib.sha256(_json_bytes(hash_fields)).hexdigest(),
    )
    return receipt, bundle, registry, authority, actions, parent_obj


def _baseline_fixture(
    subject: object, bundle: object, actions: tuple[dict[str, object], ...], parent_obj: dict[str, object]
) -> tuple[object, tuple[object, ...], tuple[object, ...]]:
    entries, readiness, conformance = [], [], []
    projection = {
        "schema_version": IDENTITY_DOMAIN + ".e3_projection_spec",
        "field_map": {"admissibility": "admissibility", "costs": "costs", "target_action_roster": "target_action_roster"},
    }
    projection_bytes = _json_bytes(projection)
    baseline_input = _json_bytes({name: parent_obj[source] for name, source in projection["field_map"].items()})
    roster_sha = hashlib.sha256(bundle.target_action_roster_bytes).hexdigest()
    decision = _json_bytes({"action": actions[0]})
    for baseline_id in BASELINE_IDS:
        official = None if baseline_id in INTERNAL_BASELINES else _digest(baseline_id + ":official")
        version = _digest(baseline_id + ":version")
        entry = subject.MandatoryBaselineRosterEntry.create(
            baseline_id=baseline_id, official_source_spec_sha256=official, version_sha256=version,
        )
        ready = subject.BaselinePreOutcomeReadinessAuthority.create(
            baseline_id=baseline_id, version_sha256=version, status="supported",
            reason_code="ready_verified", official_source_spec_sha256=official,
            executed_method_id=baseline_id, adapter_code_sha256=_digest(baseline_id + ":adapter"),
            dependency_environment_lock_sha256=_digest(baseline_id + ":environment"),
            parity_projection_sha256=hashlib.sha256(projection_bytes).hexdigest(),
            synthetic_faithfulness_test_receipt_sha256=_digest(baseline_id + ":faithfulness"),
            reviewer_decision_sha256=_digest(baseline_id + ":review"),
            pre_outcome_amendment_sha256=None,
        )
        adapter_env = hashlib.sha256(_json_bytes([
            ready.status_sha256, ready.version_sha256, ready.adapter_code_sha256,
            ready.dependency_environment_lock_sha256, ready.parity_projection_sha256,
            ready.executed_method_id,
        ])).hexdigest()
        run = subject.BaselineDecisionRunConformanceReceipt.create(
            baseline_id=baseline_id, executed_method_id=baseline_id,
            readiness_status_sha256=ready.status_sha256,
            input_action_roster_sha256=roster_sha,
            baseline_input_bytes=baseline_input,
            baseline_input_bytes_sha256=hashlib.sha256(baseline_input).hexdigest(),
            baseline_projection_spec_bytes=projection_bytes,
            baseline_projection_spec_bytes_sha256=hashlib.sha256(projection_bytes).hexdigest(),
            pre_outcome_decision_bytes=decision,
            pre_outcome_decision_bytes_sha256=hashlib.sha256(decision).hexdigest(),
            adapter_environment_sha256=adapter_env,
            decision_timing_sha256=_digest(baseline_id + ":timing"),
            no_outcome_access_receipt_sha256=_digest(baseline_id + ":no-outcome"),
        )
        entries.append(entry)
        readiness.append(ready)
        conformance.append(run)
    roster = subject.MandatoryBaselineRoster.create(entries=tuple(entries))
    return roster, tuple(readiness), tuple(conformance)


def _e3_contract_fixture(subject: object) -> tuple[object, dict[str, object]]:
    receipt, bundle, registry, authority, actions, parent_obj = _parity_fixture(subject)
    shared = subject.SyntheticE1ActionRosterV2.create(
        site_ref=authority.site_ref, case_ref=authority.case_ref, prefix_ref=authority.prefix_ref,
        packet_ids=tuple(packet for _, packet, _ in authority.packet_slot_bindings),
        repeat_seed_cells=((0, 11), (1, 13)),
        common_synthesis_spec_sha256=_digest("e3-common-synthesis"),
        opaque_identity_registry_sha256=registry.registry_sha256,
    )
    roster, readiness, conformance = _baseline_fixture(subject, bundle, actions, parent_obj)
    table = _json_bytes([
        {"action": action, "blind_direct_value": value}
        for action, value in zip(actions, (0.0, 2.0, 1.0, 99.0), strict=True)
    ])
    oracle = subject.SyntheticRetrospectiveOracleEvaluationV2.create(
        target_action_authority_sha256=authority.authority_sha256,
        direct_action_value_table_bytes=table,
        oracle_decision_bytes=_json_bytes({"action": actions[1]}),
        action_space_tie_rule_sha256=receipt.action_space_tie_rule_sha256,
        admissibility_sha256=receipt.admissibility_sha256,
    )
    values = {
        "parity_receipt": receipt, "parity_replay_bundle": bundle,
        "opaque_identity_registry": registry, "target_action_authority": authority,
        "shared_e1_action_roster": shared, "mandatory_roster": roster,
        "baseline_pre_outcome_readiness": readiness,
        "baseline_decision_conformance": conformance,
        "retrospective_oracle_evaluation": oracle,
        "analysis_code_sha256": _digest("analysis"),
    }
    return subject.E3ComparatorContract.create(**values), values


class OracleSchemaTests(unittest.TestCase):
    def test_exports_are_the_exact_sole_authorized_api(self) -> None:
        from iclr2027 import obligation_oracle as subject

        self.assertEqual(
            subject.__all__,
            (
                "NeedsContextError",
                "SyntheticOpaqueIdentityRegistryV2",
                "AuxiliaryControlPlanV2",
                "AuxiliaryControlConformanceV2",
                "SyntheticE1ActionRosterV2",
                "SyntheticSoloExecutionConformanceV2",
                "SyntheticE3TargetActionAuthorityV2",
                "SyntheticRetrospectiveOracleEvaluationV2",
                "SyntheticTerminalBranch",
                "SyntheticAssignmentCrossoverRecord",
                "SyntheticPairAssignmentClosure",
                "FrozenResidualCapabilityBinding",
                "SyntheticSupportBalanceRecord",
                "SyntheticExecutionConformanceRecord",
                "FrozenE2Pair",
                "SyntheticResidualAbsentControlPair",
                "SyntheticResidualAbsentControlRoster",
                "E2MechanismContract",
                "E2SyntheticSummary",
                "SyntheticParityReplayBundle",
                "PairedInformationParityReceipt",
                "MandatoryBaselineRosterEntry",
                "MandatoryBaselineRoster",
                "BaselinePreOutcomeReadinessAuthority",
                "BaselineDecisionRunConformanceReceipt",
                "E3ComparatorContract",
                "validate_direct_terminal_branches",
                "evaluate_synthetic_e2",
                "validate_paired_information_parity",
                "validate_baseline_pre_outcome_readiness",
                "validate_baseline_decision_run_conformance",
                "require_phase_b_authority",
            ),
        )

    def test_all_records_are_explicit_frozen_slotted_dataclasses(self) -> None:
        from iclr2027 import obligation_oracle as subject

        for name in (
            "SyntheticOpaqueIdentityRegistryV2", "AuxiliaryControlPlanV2",
            "AuxiliaryControlConformanceV2", "SyntheticE1ActionRosterV2",
            "SyntheticSoloExecutionConformanceV2", "SyntheticE3TargetActionAuthorityV2",
            "SyntheticRetrospectiveOracleEvaluationV2", "SyntheticTerminalBranch",
            "SyntheticAssignmentCrossoverRecord", "SyntheticPairAssignmentClosure",
            "FrozenResidualCapabilityBinding", "SyntheticSupportBalanceRecord",
            "SyntheticExecutionConformanceRecord", "FrozenE2Pair",
            "SyntheticResidualAbsentControlPair", "SyntheticResidualAbsentControlRoster",
            "E2MechanismContract", "E2SyntheticSummary", "SyntheticParityReplayBundle",
            "PairedInformationParityReceipt", "MandatoryBaselineRosterEntry",
            "MandatoryBaselineRoster", "BaselinePreOutcomeReadinessAuthority",
            "BaselineDecisionRunConformanceReceipt", "E3ComparatorContract",
        ):
            cls = getattr(subject, name)
            with self.subTest(name=name):
                self.assertNotEqual(fields(cls), ())
                self.assertNotIn("__dict__", cls.__dict__)
                self.assertFalse(hasattr(object.__new__(cls), "__dict__"))
                self.assertFalse(any(field.type is object for field in fields(cls)))

    def test_record_field_sets_match_the_authoritative_brief(self) -> None:
        from iclr2027 import obligation_oracle as subject

        expected = {
            "SyntheticOpaqueIdentityRegistryV2": ("derivation_seed_sha256", "entries", "packet_manifest_bindings", "synthetic_only", "registry_sha256"),
            "AuxiliaryControlPlanV2": ("control_ref", "control_kind", "focal_pair_key_sha256", "site_ref", "case_ref", "prefix_ref", "target_action_roster_sha256", "packet_ids", "repeat_seed_cells", "assignment_record_sha256s", "assignment_reference_multiplicities", "selection_probability_spec_sha256", "support_cell_sha256", "synthetic_only", "plan_sha256"),
            "AuxiliaryControlConformanceV2": ("control_plan_sha256", "assignment_record_sha256s", "execution_record_sha256s", "terminal_record_sha256s", "compliance_status", "synthetic_only", "conformance_sha256"),
            "SyntheticE1ActionRosterV2": ("site_ref", "case_ref", "prefix_ref", "packet_ids", "repeat_seed_cells", "common_synthesis_spec_sha256", "opaque_identity_registry_sha256", "synthetic_only", "roster_sha256"),
            "SyntheticSoloExecutionConformanceV2": ("site_ref", "case_ref", "prefix_ref", "repeat_index", "seed", "common_synthesis_spec_sha256", "pre_call_execution_isolation_receipt_sha256", "post_run_execution_usage_conformance_receipt_sha256", "usage_ledger_sha256", "compliance_status", "synthetic_only", "record_sha256"),
            "SyntheticE3TargetActionAuthorityV2": ("site_ref", "case_ref", "prefix_ref", "packet_slot_bindings", "opaque_identity_registry_sha256", "synthetic_only", "authority_sha256"),
            "SyntheticRetrospectiveOracleEvaluationV2": ("target_action_authority_sha256", "direct_action_value_table_bytes", "oracle_decision_bytes", "action_space_tie_rule_sha256", "admissibility_sha256", "synthetic_only", "evaluation_sha256"),
            "SyntheticSupportBalanceRecord": ("site_ref", "case_ref", "prefix_ref", "support_cell_sha256", "target_census", "cost_balance_sha256", "complete_token_balance_sha256", "information_exposure_balance_sha256", "prompt_profile_length_balance_sha256", "tool_access_count_balance_sha256", "synthesis_path_balance_sha256", "admissibility_balance_sha256", "global_bundle_strength_control_sha256", "uniform_random_control_sha256", "residual_absent_control_selection_spec_sha256", "support_status", "synthetic_only", "record_sha256"),
            "E2MechanismContract": ("opaque_identity_registry", "e1_action_rosters", "solo_execution_records", "auxiliary_control_plans", "auxiliary_control_conformances", "bindings", "assignments", "pair_assignment_closures", "support_balance_records", "execution_records", "terminal_branches", "pairs", "residual_absent_control_pairs", "residual_absent_control_rosters", "blind_outcome_schema_sha256", "common_synthesis_spec_sha256", "analysis_code_sha256", "synthetic_only", "contract_sha256"),
            "SyntheticResidualAbsentControlPair": ("control_ref", "focal_pair_key_sha256", "site_ref", "case_ref", "prefix_ref", "high_packet_id", "high_complete_bundle_manifest_sha256", "high_residual_capability_binding_sha256", "low_packet_id", "low_complete_bundle_manifest_sha256", "low_residual_capability_binding_sha256", "pair_assignment_closure_sha256", "balance_support_record_sha256", "evaluator_reference_sha256", "pair_set_sha256", "matching_weight", "residual_absent_control_selection_spec_sha256", "synthetic_only", "control_pair_key_sha256", "control_pair_sha256"),
            "SyntheticResidualAbsentControlRoster": ("focal_pair_key_sha256", "support_cell_sha256", "pair_set_sha256", "control_pair_key_sha256s", "matching_weights", "selection_spec_sha256", "synthetic_only", "roster_sha256"),
            "SyntheticParityReplayBundle": ("source_parent_bytes", "oacs_input_bytes", "raw_router_input_bytes", "oacs_projection_spec_bytes", "raw_router_projection_spec_bytes", "information_equivalence_map_bytes", "target_action_roster_bytes", "shared_training_opportunity_bytes", "oacs_pre_outcome_decision_bytes", "raw_router_pre_outcome_decision_bytes", "synthetic_only", "bundle_sha256"),
            "PairedInformationParityReceipt": ("schema_version", "source_parent_receipt_sha256", "oacs_input_bytes_sha256", "raw_router_input_bytes_sha256", "oacs_projection_spec_sha256", "raw_router_projection_spec_sha256", "information_equivalence_map_sha256", "target_action_roster_sha256", "costs_sha256", "admissibility_sha256", "examples_sha256", "split_fold_sha256", "learner_class_capacity_sha256", "tuning_optimization_opportunity_sha256", "action_space_tie_rule_sha256", "oacs_pre_outcome_decisions_sha256", "raw_router_pre_outcome_decisions_sha256", "pair_sha256", "synthetic_only", "receipt_sha256"),
            "MandatoryBaselineRosterEntry": ("baseline_id", "official_source_spec_sha256", "version_sha256", "synthetic_only", "entry_sha256"),
            "MandatoryBaselineRoster": ("entries", "synthetic_only", "roster_sha256"),
            "BaselinePreOutcomeReadinessAuthority": ("baseline_id", "version_sha256", "status", "reason_code", "official_source_spec_sha256", "executed_method_id", "adapter_code_sha256", "dependency_environment_lock_sha256", "parity_projection_sha256", "synthetic_faithfulness_test_receipt_sha256", "reviewer_decision_sha256", "pre_outcome_amendment_sha256", "synthetic_only", "status_sha256"),
            "BaselineDecisionRunConformanceReceipt": ("baseline_id", "executed_method_id", "readiness_status_sha256", "input_action_roster_sha256", "baseline_input_bytes", "baseline_input_bytes_sha256", "baseline_projection_spec_bytes", "baseline_projection_spec_bytes_sha256", "pre_outcome_decision_bytes", "pre_outcome_decision_bytes_sha256", "adapter_environment_sha256", "decision_timing_sha256", "no_outcome_access_receipt_sha256", "synthetic_only", "receipt_sha256"),
            "E3ComparatorContract": ("parity_receipt", "parity_replay_bundle", "opaque_identity_registry", "target_action_authority", "shared_e1_action_roster", "mandatory_roster", "baseline_pre_outcome_readiness", "baseline_decision_conformance", "retrospective_oracle_evaluation", "analysis_code_sha256", "synthetic_only", "contract_sha256"),
        }
        for name, wanted in expected.items():
            with self.subTest(name=name):
                self.assertEqual(tuple(field.name for field in fields(getattr(subject, name))), wanted)

    def test_direct_constructor_validates_self_hash_and_synthetic_domain(self) -> None:
        from iclr2027 import obligation_oracle as subject

        row = subject.SyntheticAssignmentCrossoverRecord.create(
            assignment_ref="assignment-a", site_ref="site-a", case_ref="case-a",
            prefix_ref="prefix-a", repeat_index=0, seed=1,
            assigned_opaque_slot_id="slot-a", assigned_actual_packet_id="packet-a",
            assigned_complete_bundle_manifest_sha256=_digest("manifest"),
            assignment_probability=0.5,
            assignment_probability_spec_sha256=_digest("probability"),
            randomization_nonce_sha256=_digest("nonce"),
            cyclic_crossover_plan_sha256=_digest("plan"),
            complete_packet_roster_sha256=_digest("packets"),
            immutable_target_roster_sha256=_digest("targets"),
        )
        with self.assertRaises(ValueError):
            type(row)(**{**asdict(row), "synthetic_only": False})
        with self.assertRaises(ValueError):
            type(row)(**{**asdict(row), "record_sha256": "0" * 64})
        with self.assertRaises(FrozenInstanceError):
            row.seed = 2  # type: ignore[misc]

    def test_raw_json_rejects_duplicate_nonfinite_and_noncanonical_bytes(self) -> None:
        from iclr2027 import obligation_oracle as subject

        target = _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.8,), low_qualities=(0.4,), high_costs=(0.1,), low_costs=(0.1,))
        row = target["bindings"][0]
        raw = row.canonical_json()
        self.assertEqual(type(row).from_json(raw), row)
        with self.assertRaises(ValueError):
            type(row).from_json(raw[:-1] + ',"site_ref":"site-b"}')
        assignment = target["assignments"][0]
        assignment_raw = assignment.canonical_json()
        with self.assertRaises(ValueError):
            type(assignment).from_json(
                assignment_raw.replace('"assignment_probability":0.5', '"assignment_probability":NaN')
            )
        with self.assertRaises(ValueError):
            type(row).from_json(raw.replace(":", ": ", 1))

    def test_native_types_bool_as_int_and_recursive_foreign_containers_reject(self) -> None:
        from iclr2027 import obligation_oracle as subject

        with self.assertRaises((TypeError, ValueError)):
            subject.SyntheticSupportBalanceRecord.create(
                support_cell_sha256=_digest("support"), target_census=True,
                cost_balance_sha256=_digest("a"), complete_token_balance_sha256=_digest("b"),
                information_exposure_balance_sha256=_digest("c"), prompt_profile_length_balance_sha256=_digest("d"),
                tool_access_count_balance_sha256=_digest("e"), synthesis_path_balance_sha256=_digest("f"),
                admissibility_balance_sha256=_digest("g"), global_bundle_strength_control_sha256=_digest("h"),
                uniform_random_control_sha256=_digest("i"), residual_absent_control_sha256=_digest("j"),
                support_status="adequate",
            )
        receipt, bundle, *_ = _parity_fixture(subject)
        payload = bundle.to_dict()
        payload["source_parent_bytes"] = bytearray(bundle.source_parent_bytes)
        with self.assertRaises((TypeError, ValueError)):
            type(bundle).from_dict(payload)
        self.assertEqual(receipt.synthetic_only, True)

    def test_negative_zero_normalizes_to_positive_zero(self) -> None:
        from iclr2027 import obligation_oracle as subject

        branch = subject.SyntheticTerminalBranch.create(
            site_ref="site-a", case_ref="case-a", prefix_ref="prefix-a",
            treatment_kind="stop", opaque_slot_id=None, actual_packet_id=None,
            repeat_index=0, seed=0, blind_terminal_quality=-0.0,
            complete_processed_tokens=0, latency_seconds=-0.0, list_price_cost=-0.0,
            execution_conformance_sha256=_digest("conformance"),
            direct_terminal_sha256=_digest("terminal"),
        )
        for value in (branch.blind_terminal_quality, branch.latency_seconds, branch.list_price_cost):
            self.assertEqual(math.copysign(1.0, value), 1.0)

    def test_phase_a_ids_reject_paths_controls_and_semantic_payload_keys(self) -> None:
        from iclr2027 import obligation_oracle as subject

        target = _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.8,), low_qualities=(0.4,), high_costs=(0.1,), low_costs=(0.1,))
        branch = target["branches"][0]
        with self.assertRaises(ValueError):
            _rebuild(branch, site_ref="../private")
        payload = branch.to_dict()
        payload["gold"] = "forbidden"
        with self.assertRaises(ValueError):
            type(branch).from_dict(payload)


class V2IdentityProvenanceTests(unittest.TestCase):
    def _contract(self) -> tuple[object, object]:
        from iclr2027 import obligation_oracle as subject

        target = _add_control(
            subject,
            _target_records(
                subject,
                site="site-a",
                case="case-a",
                prefix="prefix-a",
                high_qualities=(0.8,),
                low_qualities=(0.4,),
                high_costs=(0.0,),
                low_costs=(0.0,),
            ),
            case="case-control",
            prefix="prefix-control",
            high_qualities=(0.5,),
            low_qualities=(0.5,),
            high_costs=(0.0,),
            low_costs=(0.0,),
        )
        return subject, _contract(subject, target)

    def test_registry_derives_literal_opaque_ids_and_rejects_duplicate_entries(self) -> None:
        from iclr2027 import obligation_oracle as subject

        ordinal = 7
        expected_id = "o5_" + hashlib.sha256(
            _json_bytes([IDENTITY_DOMAIN, IDENTITY_SEED, "packet", ordinal])
        ).hexdigest()
        registry = subject.SyntheticOpaqueIdentityRegistryV2.create(
            derivation_seed_sha256=IDENTITY_SEED,
            entries=(("packet", ordinal, expected_id),),
            packet_manifest_bindings=((expected_id, _digest("manifest")),),
        )
        self.assertEqual(registry.resolve("packet", expected_id), ordinal)
        with self.assertRaises(ValueError):
            subject.SyntheticOpaqueIdentityRegistryV2.create(
                derivation_seed_sha256=IDENTITY_SEED,
                entries=(("packet", ordinal, expected_id), ("packet", ordinal, expected_id)),
                packet_manifest_bindings=((expected_id, _digest("manifest")),),
            )

    def test_registry_rejects_semantic_stale_foreign_and_wrong_kind_ids(self) -> None:
        subject, contract = self._contract()
        registry = contract.opaque_identity_registry
        packet = next(row for row in registry.entries if row[0] == "packet")[2]
        with self.assertRaises(ValueError):
            registry.resolve("packet", "prompt-output-controller")
        with self.assertRaises(ValueError):
            registry.resolve("packet", "o5_" + "0" * 64)
        with self.assertRaises(ValueError):
            registry.resolve("slot", packet)
        foreign = _opaque_id("packet", "foreign-packet")
        with self.assertRaises(ValueError):
            registry.resolve("packet", foreign)

    def test_root_rejects_v1_and_mixed_nested_schemas_and_registry_subclasses(self) -> None:
        subject, contract = self._contract()
        payload = contract.to_dict()
        payload["schema_version"] = payload["schema_version"].replace(".v2.", ".")
        with self.assertRaises(ValueError):
            type(contract).from_dict(payload)
        nested = contract.to_dict()
        nested["bindings"][0]["schema_version"] = nested["bindings"][0]["schema_version"].replace(".v2.", ".")
        with self.assertRaises(ValueError):
            type(contract).from_dict(nested)

        class RegistrySubclass(subject.SyntheticOpaqueIdentityRegistryV2):
            pass

        subclass = RegistrySubclass(**asdict(contract.opaque_identity_registry))
        with self.assertRaises(TypeError):
            _rebuild(contract, opaque_identity_registry=subclass)

    def test_root_rejects_registry_packet_manifest_disagreement(self) -> None:
        subject, contract = self._contract()
        registry = contract.opaque_identity_registry
        packet, _ = registry.packet_manifest_bindings[0]
        altered = subject.SyntheticOpaqueIdentityRegistryV2.create(
            derivation_seed_sha256=registry.derivation_seed_sha256,
            entries=registry.entries,
            packet_manifest_bindings=tuple(
                (identifier, _digest("wrong-manifest") if identifier == packet else manifest)
                for identifier, manifest in registry.packet_manifest_bindings
            ),
        )
        with self.assertRaises(ValueError):
            _rebuild(contract, opaque_identity_registry=altered)

    def test_all_actual_byte_families_reject_negative_zero_at_every_depth(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, bundle, *_ = _parity_fixture(subject)
        raw_by_depth = (b"-0.0", b"[-0.0]", b'{"value":-0.0}')
        fields = tuple(bundle.BYTES_FIELDS - {"shared_training_opportunity_bytes"})
        for field_name in fields:
            for raw in raw_by_depth:
                with self.subTest(field=field_name, raw=raw):
                    with self.assertRaises(ValueError):
                        _rebuild(bundle, **{field_name: raw})
        for raw in raw_by_depth:
            training = json.loads(bundle.shared_training_opportunity_bytes)
            training["costs"] = json.loads(raw)
            with self.subTest(field="shared_training_opportunity_bytes", raw=raw):
                with self.assertRaises(ValueError):
                    _rebuild(
                        bundle,
                        shared_training_opportunity_bytes=_json_bytes(training),
                    )


class E2ContractTests(unittest.TestCase):
    def _two_site_contract(self) -> tuple[object, object, dict[str, object], dict[str, object]]:
        from iclr2027 import obligation_oracle as subject

        first = _add_control(
            subject,
            _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.9,), low_qualities=(0.5,), high_costs=(0.2,), low_costs=(0.1,)),
            case="case-a-control", prefix="prefix-a-control",
            high_qualities=(0.6,), low_qualities=(0.5,),
            high_costs=(0.1,), low_costs=(0.1,),
        )
        second = _add_control(
            subject,
            _target_records(subject, site="site-b", case="case-b", prefix="prefix-b", high_qualities=(0.6,), low_qualities=(0.4,), high_costs=(0.1,), low_costs=(0.1,)),
            case="case-b-control", prefix="prefix-b-control",
            high_qualities=(0.4,), low_qualities=(0.5,),
            high_costs=(0.1,), low_costs=(0.1,),
        )
        return subject, _contract(subject, first, second), first, second

    def test_direct_terminal_validation_rejects_duplicate_and_noncanonical_order(self) -> None:
        subject, contract, _, _ = self._two_site_contract()
        rows = contract.terminal_branches
        subject.validate_direct_terminal_branches(rows)
        with self.assertRaises(ValueError):
            subject.validate_direct_terminal_branches(rows + (rows[0],))
        with self.assertRaises(ValueError):
            subject.validate_direct_terminal_branches(tuple(reversed(rows)))

    def test_terminal_treatment_nullability_quality_and_resource_ranges(self) -> None:
        from iclr2027 import obligation_oracle as subject

        base = dict(site_ref="site-a", case_ref="case-a", prefix_ref="prefix-a", repeat_index=0, seed=0, blind_terminal_quality=0.5, complete_processed_tokens=1, latency_seconds=0.0, list_price_cost=0.0, execution_conformance_sha256=_digest("c"), direct_terminal_sha256=_digest("d"))
        with self.assertRaises(ValueError):
            subject.SyntheticTerminalBranch.create(**base, treatment_kind="stop", opaque_slot_id="slot", actual_packet_id=None)
        with self.assertRaises((TypeError, ValueError)):
            subject.SyntheticTerminalBranch.create(**base, treatment_kind="capability_packet", opaque_slot_id=None, actual_packet_id="packet")
        with self.assertRaises(ValueError):
            subject.SyntheticTerminalBranch.create(**{**base, "blind_terminal_quality": 1.1}, treatment_kind="solo_synthesis", opaque_slot_id=None, actual_packet_id=None)
        with self.assertRaises((TypeError, ValueError)):
            subject.SyntheticTerminalBranch.create(**{**base, "complete_processed_tokens": -1}, treatment_kind="solo_synthesis", opaque_slot_id=None, actual_packet_id=None)

    def test_assignment_probability_and_pair_assignment_closure_are_exact(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        assignment = first["assignments"][0]
        with self.assertRaises(ValueError):
            _rebuild(assignment, assignment_probability=0.0)
        closure = first["closures"][0]
        with self.assertRaises((TypeError, ValueError)):
            _rebuild(closure, high_assignment_record_sha256s=())
        noncanonical = tuple(reversed(tuple(sorted((_digest("x"), _digest("y"))))))
        with self.assertRaises(ValueError):
            _rebuild(closure, high_assignment_record_sha256s=noncanonical)
        self.assertTrue(contract.assignments)

    def test_binding_vocabularies_and_pair_shared_fields_are_enforced(self) -> None:
        _, _, first, _ = self._two_site_contract()
        high = first["bindings"][0]
        for field_name, bad in (
            ("alignment_measure_kind", "learned"),
            ("alignment_role", "medium"),
            ("effect_modifier_stratum", "outcome_selected"),
        ):
            with self.subTest(field=field_name), self.assertRaises(ValueError):
                _rebuild(high, **{field_name: bad})

    def test_support_status_and_none_rules_fail_closed(self) -> None:
        from iclr2027 import obligation_oracle as subject

        for status in ("weak", "empty"):
            target = _add_control(
                subject,
                _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.9,), low_qualities=(0.5,), high_costs=(0.2,), low_costs=(0.1,), support_status=status),
                case="case-control", prefix="prefix-control",
                high_qualities=(0.5,), low_qualities=(0.5,),
                high_costs=(0.1,), low_costs=(0.1,),
            )
            summary = subject.evaluate_synthetic_e2(_contract(subject, target))
            self.assertEqual(summary.status, "non_estimable_support")
            self.assertIsNone(summary.site_clustered_primary_contrast)
            self.assertIsNone(summary.secondary_cost_adjusted_utility)
            self.assertIsNone(summary.secondary_continuous_alignment_cost_interaction)

    def test_complete_e2_arithmetic_uses_equal_site_clusters(self) -> None:
        subject, contract, _, _ = self._two_site_contract()
        summary = subject.evaluate_synthetic_e2(contract)
        self.assertEqual(summary.status, "synthetic_complete")
        self.assertAlmostEqual(summary.site_clustered_primary_contrast, 0.3)
        self.assertIsNone(summary.secondary_cost_adjusted_utility)
        self.assertIsNone(summary.secondary_continuous_alignment_cost_interaction)
        self.assertEqual((summary.site_count, summary.case_count, summary.row_count), (2, 2, 12))

    def test_site_weighting_is_not_row_weighting(self) -> None:
        from iclr2027 import obligation_oracle as subject

        a1 = _add_control(subject, _target_records(subject, site="site-a", case="case-a", prefix="prefix-a1", high_qualities=(1.0,), low_qualities=(0.0,), high_costs=(0.0,), low_costs=(0.0,)), case="case-a-control1", prefix="prefix-a-control1", high_qualities=(0.5,), low_qualities=(0.5,), high_costs=(0.0,), low_costs=(0.0,))
        a2 = _add_control(subject, _target_records(subject, site="site-a", case="case-a", prefix="prefix-a2", high_qualities=(1.0,), low_qualities=(0.0,), high_costs=(0.0,), low_costs=(0.0,)), case="case-a-control2", prefix="prefix-a-control2", high_qualities=(0.5,), low_qualities=(0.5,), high_costs=(0.0,), low_costs=(0.0,))
        b = _add_control(subject, _target_records(subject, site="site-b", case="case-b", prefix="prefix-b", high_qualities=(0.0,), low_qualities=(1.0,), high_costs=(0.0,), low_costs=(0.0,)), case="case-b-control", prefix="prefix-b-control", high_qualities=(0.5,), low_qualities=(0.5,), high_costs=(0.0,), low_costs=(0.0,))
        summary = subject.evaluate_synthetic_e2(_contract(subject, a1, a2, b))
        self.assertAlmostEqual(summary.site_clustered_primary_contrast, 0.0)

    def test_pair_counts_do_not_change_equal_target_weighting(self) -> None:
        from iclr2027 import obligation_oracle as subject

        first_pair = _add_control(
            subject,
            _target_records(
                subject,
                site="site-a",
                case="case-a",
                prefix="target-a",
                high_qualities=(0.9,),
                low_qualities=(0.1,),
                high_costs=(0.0,),
                low_costs=(0.0,),
                pair_set_sha256=_digest("pair-set-a1"),
                evaluator_reference_sha256=_digest("evaluator-a1"),
                selection_spec_sha256=_digest("selection-a1"),
                fixture_tag="target-a-pair-1",
            ),
            case="control-a1",
            prefix="control-a1",
            high_qualities=(0.5,),
            low_qualities=(0.5,),
            high_costs=(0.0,),
            low_costs=(0.0,),
        )
        second_pair = _add_control(
            subject,
            _target_records(
                subject,
                site="site-a",
                case="case-a",
                prefix="target-a",
                high_qualities=(0.7,),
                low_qualities=(0.1,),
                high_costs=(0.0,),
                low_costs=(0.0,),
                pair_set_sha256=_digest("pair-set-a2"),
                evaluator_reference_sha256=_digest("evaluator-a2"),
                selection_spec_sha256=_digest("selection-a2"),
                fixture_tag="target-a-pair-2",
            ),
            case="control-a2",
            prefix="control-a2",
            high_qualities=(0.5,),
            low_qualities=(0.5,),
            high_costs=(0.0,),
            low_costs=(0.0,),
        )
        other_target = _add_control(
            subject,
            _target_records(
                subject,
                site="site-a",
                case="case-a",
                prefix="target-b",
                high_qualities=(0.5,),
                low_qualities=(0.5,),
                high_costs=(0.0,),
                low_costs=(0.0,),
            ),
            case="control-b",
            prefix="control-b",
            high_qualities=(0.5,),
            low_qualities=(0.5,),
            high_costs=(0.0,),
            low_costs=(0.0,),
        )

        summary = subject.evaluate_synthetic_e2(
            _contract(subject, first_pair, second_pair, other_target)
        )

        # target-a mean = ((.9-.1) + (.7-.1)) / 2 = .7;
        # target-b mean = 0; the single case/site mean is therefore .35.
        self.assertEqual(summary.status, "synthetic_complete")
        self.assertAlmostEqual(summary.site_clustered_primary_contrast, 0.35)

    def test_phase_a_continuous_secondary_is_always_none(self) -> None:
        from iclr2027 import obligation_oracle as subject

        target = _add_control(
            subject,
            _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.9,), low_qualities=(0.5,), high_costs=(0.2,), low_costs=(0.1,), measure_kind="predeclared_continuous_secondary"),
            case="case-control", prefix="prefix-control",
            high_qualities=(0.5,), low_qualities=(0.5,),
            high_costs=(0.0,), low_costs=(0.0,),
        )
        summary = subject.evaluate_synthetic_e2(_contract(subject, target))
        self.assertIsNone(summary.secondary_continuous_alignment_cost_interaction)

    def test_residual_control_roster_weight_and_selection_schema_validate(self) -> None:
        subject, _, first, _ = self._two_site_contract()
        roster = first["control_rosters"][0]
        self.assertEqual(roster.matching_weights, (1.0,))
        with self.assertRaises(ValueError):
            subject.SyntheticResidualAbsentControlRoster.create(
                focal_pair_key_sha256=roster.focal_pair_key_sha256,
                support_cell_sha256=roster.support_cell_sha256,
                pair_set_sha256=roster.pair_set_sha256,
                control_pair_key_sha256s=roster.control_pair_key_sha256s,
                matching_weights=(0.5,),
                selection_spec_sha256=roster.selection_spec_sha256,
            )
        with self.assertRaises(ValueError):
            subject.SyntheticResidualAbsentControlRoster.create(
                focal_pair_key_sha256=roster.focal_pair_key_sha256,
                support_cell_sha256=roster.support_cell_sha256,
                pair_set_sha256=roster.pair_set_sha256,
                control_pair_key_sha256s=roster.control_pair_key_sha256s,
                matching_weights=(0.0,),
                selection_spec_sha256=roster.selection_spec_sha256,
            )

    def test_roster_weight_must_equal_typed_control_weight(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        old = first["control_pairs"][0]
        changed = _rekey_control(old, matching_weight=0.5)
        old_roster = first["control_rosters"][0]
        changed_roster = subject.SyntheticResidualAbsentControlRoster.create(
            focal_pair_key_sha256=old_roster.focal_pair_key_sha256,
            support_cell_sha256=old_roster.support_cell_sha256,
            pair_set_sha256=old_roster.pair_set_sha256,
            control_pair_key_sha256s=(changed.control_pair_key_sha256,),
            matching_weights=(1.0,),
            selection_spec_sha256=old_roster.selection_spec_sha256,
        )
        controls = [changed, *[row for row in contract.residual_absent_control_pairs if row.control_pair_sha256 != old.control_pair_sha256]]
        rosters = [changed_roster, *[row for row in contract.residual_absent_control_rosters if row.roster_sha256 != old_roster.roster_sha256]]
        summary = subject.evaluate_synthetic_e2(
            _rebuild(
                contract,
                residual_absent_control_pairs=_ordered(controls, "control_pair_sha256"),
                residual_absent_control_rosters=_ordered(rosters, "roster_sha256"),
            )
        )
        self.assertEqual(summary.status, "non_estimable_support")

    def test_control_must_be_same_site_distinct_target_and_same_pair_set(self) -> None:
        from iclr2027 import obligation_oracle as subject

        cases = (
            _add_control(subject, _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.8,), low_qualities=(0.4,), high_costs=(0.0,), low_costs=(0.0,)), site="site-b", case="case-control", prefix="prefix-control", high_qualities=(0.5,), low_qualities=(0.5,), high_costs=(0.0,), low_costs=(0.0,)),
            _add_control(subject, _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.8,), low_qualities=(0.4,), high_costs=(0.0,), low_costs=(0.0,)), case="case-a", prefix="prefix-a", high_qualities=(0.5,), low_qualities=(0.5,), high_costs=(0.0,), low_costs=(0.0,)),
        )
        for target in cases:
            with self.subTest(control=target["control_pairs"][0].control_ref):
                try:
                    summary = subject.evaluate_synthetic_e2(_contract(subject, target))
                except ValueError:
                    continue
                self.assertEqual(summary.status, "non_estimable_support")
        valid = _add_control(subject, _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.8,), low_qualities=(0.4,), high_costs=(0.0,), low_costs=(0.0,)), case="case-control", prefix="prefix-control", high_qualities=(0.5,), low_qualities=(0.5,), high_costs=(0.0,), low_costs=(0.0,))
        control = valid["control_pairs"][0]
        changed = _rekey_control(control, pair_set_sha256=_digest("wrong-pair-set"))
        valid["control_pairs"] = [changed]
        roster = valid["control_rosters"][0]
        valid["control_rosters"] = [subject.SyntheticResidualAbsentControlRoster.create(
            focal_pair_key_sha256=roster.focal_pair_key_sha256,
            support_cell_sha256=roster.support_cell_sha256,
            pair_set_sha256=roster.pair_set_sha256,
            control_pair_key_sha256s=(changed.control_pair_key_sha256,),
            matching_weights=(1.0,),
            selection_spec_sha256=roster.selection_spec_sha256,
        )]
        self.assertEqual(subject.evaluate_synthetic_e2(_contract(subject, valid)).status, "non_estimable_support")

    def test_control_repeat_cells_must_equal_focal_cells(self) -> None:
        from iclr2027 import obligation_oracle as subject

        target = _add_control(
            subject,
            _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.8, 0.7), low_qualities=(0.4, 0.3), high_costs=(0.0, 0.0), low_costs=(0.0, 0.0)),
            case="case-control", prefix="prefix-control",
            high_qualities=(0.5,), low_qualities=(0.5,),
            high_costs=(0.0,), low_costs=(0.0,),
        )
        self.assertEqual(subject.evaluate_synthetic_e2(_contract(subject, target)).status, "non_estimable_support")

    def test_missing_control_assignment_execution_or_terminal_leg_is_nonestimable(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        control_case = first["control_pairs"][0].case_ref
        collections = (
            ("assignments", "record_sha256", lambda row: row.case_ref == control_case),
            ("execution_records", "record_sha256", lambda row: row.case_ref == control_case),
            ("terminal_branches", "record_sha256", lambda row: row.case_ref == control_case),
        )
        for field_name, _, predicate in collections:
            rows = list(getattr(contract, field_name))
            remove = next(row for row in rows if predicate(row))
            rows.remove(remove)
            with self.subTest(field=field_name):
                summary = subject.evaluate_synthetic_e2(_rebuild(contract, **{field_name: tuple(rows)}))
                self.assertEqual(summary.status, "non_estimable_support")

    def test_duplicate_or_reused_control_record_rejects(self) -> None:
        subject, contract, _, _ = self._two_site_contract()
        duplicate = contract.residual_absent_control_pairs + (contract.residual_absent_control_pairs[0],)
        with self.assertRaises(ValueError):
            _rebuild(contract, residual_absent_control_pairs=duplicate)

    def test_dangling_binding_reference_rejects(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        bad_pair = _rebuild(first["pairs"][0], high_residual_capability_binding_sha256="0" * 64)
        other = [row for row in contract.pairs if row.pair_sha256 != first["pairs"][0].pair_sha256]
        bad = _rebuild(contract, pairs=_ordered([bad_pair, *other], "pair_sha256"))
        self.assertEqual(subject.evaluate_synthetic_e2(bad).status, "non_estimable_support")

    def test_dangling_assignment_closure_rejects(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        bad_pair = _rebuild(first["pairs"][0], pair_assignment_closure_sha256="0" * 64)
        other = [row for row in contract.pairs if row.pair_sha256 != first["pairs"][0].pair_sha256]
        bad = _rebuild(contract, pairs=_ordered([bad_pair, *other], "pair_sha256"))
        self.assertEqual(subject.evaluate_synthetic_e2(bad).status, "non_estimable_support")

    def test_dangling_support_record_rejects(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        bad_pair = _rebuild(first["pairs"][0], balance_support_record_sha256="0" * 64)
        other = [row for row in contract.pairs if row.pair_sha256 != first["pairs"][0].pair_sha256]
        bad = _rebuild(contract, pairs=_ordered([bad_pair, *other], "pair_sha256"))
        self.assertEqual(subject.evaluate_synthetic_e2(bad).status, "non_estimable_support")

    def test_packet_substitution_and_role_reversal_reject(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        pair = first["pairs"][0]
        with self.subTest("packet substitution"):
            bad_pair = _rebuild(pair, high_packet_id="packet-substituted")
            other = [row for row in contract.pairs if row.pair_sha256 != pair.pair_sha256]
            with self.assertRaises(ValueError):
                _rebuild(contract, pairs=_ordered([bad_pair, *other], "pair_sha256"))
        with self.subTest("role reversal"):
            high = first["bindings"][0]
            bad_high = _rebuild(high, alignment_role="low")
            bad_pair = _rebuild(pair, high_residual_capability_binding_sha256=bad_high.binding_sha256)
            bindings = [bad_high, *[row for row in contract.bindings if row.binding_sha256 != high.binding_sha256]]
            other = [row for row in contract.pairs if row.pair_sha256 != pair.pair_sha256]
            bad = _rebuild(contract, bindings=_ordered(bindings, "binding_sha256"), pairs=_ordered([bad_pair, *other], "pair_sha256"))
            self.assertEqual(subject.evaluate_synthetic_e2(bad).status, "non_estimable_support")

    def test_assignment_repeat_cell_coverage_must_match_between_arms(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        closure = first["closures"][0]
        bad_closure = _rebuild(closure, low_assignment_record_sha256s=closure.high_assignment_record_sha256s)
        pair = _rebuild(first["pairs"][0], pair_assignment_closure_sha256=bad_closure.closure_sha256)
        closures = [bad_closure, *[row for row in contract.pair_assignment_closures if row.closure_sha256 != closure.closure_sha256]]
        other = [row for row in contract.pairs if row.pair_sha256 != first["pairs"][0].pair_sha256]
        bad = _rebuild(contract, pair_assignment_closures=_ordered(closures, "closure_sha256"), pairs=_ordered([pair, *other], "pair_sha256"))
        self.assertEqual(subject.evaluate_synthetic_e2(bad).status, "non_estimable_support")

    def test_execution_packet_slot_manifest_and_status_must_match_assignment(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        execution = first["executions"][0]
        mutations = (
            {"actual_packet_id": "packet-substituted"},
            {"actual_opaque_slot_id": "slot-substituted"},
            {"actual_complete_bundle_manifest_sha256": _digest("wrong-manifest")},
            {"compliance_status": "noncompliant"},
        )
        for change in mutations:
            with self.subTest(change=change):
                replacement = _rebuild(execution, **change)
                rows = [replacement, *[row for row in contract.execution_records if row.record_sha256 != execution.record_sha256]]
                try:
                    bad = _rebuild(contract, execution_records=_ordered(rows, "record_sha256"))
                except ValueError:
                    continue
                self.assertEqual(subject.evaluate_synthetic_e2(bad).status, "non_estimable_support")

    def test_missing_terminal_or_extra_unreachable_record_rejects(self) -> None:
        subject, contract, first, _ = self._two_site_contract()
        missing = _rebuild(contract, terminal_branches=contract.terminal_branches[1:])
        self.assertEqual(subject.evaluate_synthetic_e2(missing).status, "non_estimable_support")
        extra = _rebuild(first["assignments"][0], assignment_ref="assignment-extra")
        rows = _ordered([*contract.assignments, extra], "record_sha256")
        with self.assertRaises(ValueError):
            _rebuild(contract, assignments=rows)

    def test_transition_stitch_max_and_imputation_fields_reject(self) -> None:
        _, contract, _, _ = self._two_site_contract()
        payload = contract.to_dict()
        for forbidden in ("transition", "stitched_quality", "max_repeat", "imputed"):
            altered = dict(payload)
            altered[forbidden] = True
            with self.subTest(field=forbidden), self.assertRaises(ValueError):
                type(contract).from_dict(altered)


class E1OwnershipReachabilityTests(unittest.TestCase):
    def _reason(self, subject: object, contract: object, message: str) -> None:
        with self.assertRaisesRegex(ValueError, message):
            subject._validate_synthetic_e2(contract)
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "non_estimable_support")

    def test_complete_task2_contract_with_plan_only_auxiliary_and_e1_closure_is_complete(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        summary = subject.evaluate_synthetic_e2(contract)
        self.assertEqual(summary.status, "synthetic_complete")
        roster = contract.e1_action_rosters[0]
        owned = [
            row for row in contract.assignments
            if row.immutable_target_roster_sha256 == roster.roster_sha256
        ]
        self.assertEqual(len(owned), 4)
        plan_only = [
            row for row in contract.assignments
            if row.immutable_target_roster_sha256 != roster.roster_sha256
        ]
        self.assertTrue(plan_only)

    def test_predeclared_e1_shared_auxiliary_leg_is_complete(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=True)
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "synthetic_complete")

    def test_uniform_plan_cannot_shrink_the_complete_same_target_e1_menu(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        uniform = next(
            row for row in contract.auxiliary_control_plans
            if row.control_kind == "uniform_random_admissible"
        )
        selected = next(
            row for row in contract.assignments
            if row.record_sha256 == uniform.assignment_record_sha256s[0]
        )
        shrunken = _rebind_uniform_menu(
            subject, contract, packet_ids=(selected.assigned_actual_packet_id,)
        )
        self.assertEqual(
            subject.evaluate_synthetic_e2(shrunken).status, "non_estimable_support"
        )

    def test_uniform_plan_requires_a_same_target_e1_roster(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        missing = _rebuild(
            contract,
            e1_action_rosters=(),
            solo_execution_records=(),
            terminal_branches=tuple(
                row for row in contract.terminal_branches
                if row.treatment_kind != "solo_synthesis"
            ),
        )
        self.assertEqual(
            subject.evaluate_synthetic_e2(missing).status, "non_estimable_support"
        )

    def test_uniform_plan_cannot_superset_the_complete_same_target_e1_menu(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        superset = _registered_uniform_superset(subject, contract)
        self._reason(
            subject, superset, "uniform control menu does not equal same-target E1 roster"
        )

    def test_uniform_plan_reordered_or_cell_mismatched_menu_rejects(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        roster = contract.e1_action_rosters[0]
        with self.assertRaisesRegex(ValueError, "packet_ids must be byte sorted and unique"):
            _rebind_uniform_menu(
                subject, contract, packet_ids=tuple(reversed(roster.packet_ids))
            )
        cell_mismatch = _rebind_uniform_menu(
            subject,
            contract,
            packet_ids=roster.packet_ids,
            repeat_seed_cells=(roster.repeat_seed_cells[0],),
        )
        self._reason(
            subject, cell_mismatch,
            "uniform control menu does not equal same-target E1 roster",
        )

    def test_pairless_e1_roster_still_closes_every_declared_leg(self) -> None:
        from iclr2027 import obligation_oracle as subject
        from tests import test_iclr2027_obligation_escalation as escalation_tests

        contract = escalation_tests._e1_e2_contract(subject)
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "non_estimable_support")
        missing = _rebuild(
            contract, solo_execution_records=contract.solo_execution_records[1:]
        )
        with self.assertRaisesRegex(
            ValueError, "E1 SOLO closure does not resolve exactly once and verified"
        ):
            subject._validate_synthetic_e2(missing)

    def test_auxiliary_assignment_owner_is_only_its_plan_or_exact_e1_roster(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        plan = next(
            row for row in contract.auxiliary_control_plans
            if row.control_kind == "uniform_random_admissible"
        )
        assignment = next(
            row for row in contract.assignments
            if row.record_sha256 == plan.assignment_record_sha256s[0]
        )
        bad = _rebind_auxiliary_assignment(
            subject,
            contract,
            plan,
            assignment,
            _rebuild(
                assignment,
                immutable_target_roster_sha256=_digest("foreign-auxiliary-owner"),
            ),
        )
        self._reason(
            subject, bad, "auxiliary assignment owner is neither plan-only nor exact E1 roster"
        )

    def test_e1_owner_rejects_foreign_target_cell_and_assignment_ref_reuse(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=True)
        roster = contract.e1_action_rosters[0]
        owned = next(
            row for row in contract.assignments
            if row.immutable_target_roster_sha256 == roster.roster_sha256
        )
        for name, changes, message in (
            (
                "foreign-target",
                {"case_ref": "foreign-e1-case"},
                "assignment does not match pair closure",
            ),
            (
                "foreign-cell",
                {"repeat_index": 97, "seed": 97},
                "assignment repeat cells do not close",
            ),
        ):
            with self.subTest(name=name):
                bad = _rebind_e1_focal_assignments(
                    contract, {owned.record_sha256: _rebuild(owned, **changes)}
                )
                self._reason(subject, bad, message)
        reused = _rebuild(owned, repeat_index=96, seed=96)
        bad = _rebuild(
            contract,
            assignments=_ordered([*contract.assignments, reused], "record_sha256"),
        )
        self._reason(subject, bad, "assignment_ref must resolve exactly once")

    def test_e1_solo_closure_rejects_missing_and_extra_rows(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract = _e1_owned_contract(subject, shared_uniform_leg=False)
        missing = _rebuild(
            contract, solo_execution_records=contract.solo_execution_records[1:]
        )
        self._reason(
            subject, missing, "E1 SOLO closure does not resolve exactly once and verified"
        )
        roster = contract.e1_action_rosters[0]
        extra_solo = _rebuild(
            contract.solo_execution_records[0], repeat_index=97, seed=97,
            post_run_execution_usage_conformance_receipt_sha256=_digest("extra-e1-solo"),
        )
        extra_terminal = subject.SyntheticTerminalBranch.create(
            site_ref=roster.site_ref, case_ref=roster.case_ref, prefix_ref=roster.prefix_ref,
            treatment_kind="solo_synthesis", opaque_slot_id=None, actual_packet_id=None,
            repeat_index=97, seed=97, blind_terminal_quality=0.5,
            complete_processed_tokens=1, latency_seconds=0.0, list_price_cost=0.0,
            execution_conformance_sha256=extra_solo.record_sha256,
            direct_terminal_sha256=_digest("extra-e1-solo-terminal"),
        )
        extra = _rebuild(
            contract,
            solo_execution_records=_ordered(
                [*contract.solo_execution_records, extra_solo], "record_sha256"
            ),
            terminal_branches=_ordered(
                [*contract.terminal_branches, extra_terminal], "record_sha256"
            ),
        )
        self._reason(subject, extra, "unreachable SOLO conformance")


class E2AuxiliaryControlClosureTests(unittest.TestCase):
    """Task-2 adversarial joins exercise real v2 records, never mock calls."""

    def _fixture(self) -> tuple[object, object, dict[str, object]]:
        from iclr2027 import obligation_oracle as subject

        target = _add_control(
            subject,
            _target_records(
                subject, site="site-a", case="case-a", prefix="prefix-a",
                high_qualities=(0.9,), low_qualities=(0.5,),
                high_costs=(0.0,), low_costs=(0.0,),
            ),
            case="case-control", prefix="prefix-control",
            high_qualities=(0.5,), low_qualities=(0.5,),
            high_costs=(0.0,), low_costs=(0.0,),
        )
        return subject, _contract(subject, target), target

    def _none(self, subject: object, contract: object) -> None:
        summary = subject.evaluate_synthetic_e2(contract)
        self.assertEqual(summary.status, "non_estimable_support")
        self.assertEqual(
            (summary.site_clustered_primary_contrast, summary.secondary_cost_adjusted_utility,
             summary.secondary_continuous_alignment_cost_interaction),
            (None, None, None),
        )

    def _reason(self, subject: object, contract: object, message: str) -> None:
        with self.assertRaisesRegex(ValueError, message):
            subject._validate_synthetic_e2(contract)
        self._none(subject, contract)

    def _rebind_plan(
        self, subject: object, contract: object, plan: object, /, **changes: object
    ) -> object:
        """Propagate a semantic plan change through conformance/support/pair/root."""
        replacement = _rebuild(plan, **changes)
        old_conformance = next(
            row for row in contract.auxiliary_control_conformances
            if row.control_plan_sha256 == plan.plan_sha256
        )
        conformance = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=replacement.plan_sha256,
            assignment_record_sha256s=replacement.assignment_record_sha256s,
            execution_record_sha256s=old_conformance.execution_record_sha256s,
            terminal_record_sha256s=old_conformance.terminal_record_sha256s,
            compliance_status=old_conformance.compliance_status,
        )
        plans = _ordered(
            [replacement, *[row for row in contract.auxiliary_control_plans if row.plan_sha256 != plan.plan_sha256]],
            "plan_sha256",
        )
        conformances = _ordered(
            [conformance, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != old_conformance.conformance_sha256]],
            "conformance_sha256",
        )
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        support_change = (
            {"global_bundle_strength_control_sha256": conformance.conformance_sha256}
            if plan.control_kind == "global_bundle_strength"
            else {"uniform_random_control_sha256": conformance.conformance_sha256}
        )
        replacement_support = _rebuild(support, **support_change)
        supports = _ordered(
            [replacement_support, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]],
            "record_sha256",
        )
        replacement_pair = _rebuild(pair, balance_support_record_sha256=replacement_support.record_sha256)
        pairs = _ordered(
            [replacement_pair, *[row for row in contract.pairs if row.pair_sha256 != pair.pair_sha256]],
            "pair_sha256",
        )
        return _rebuild(
            contract, auxiliary_control_plans=plans,
            auxiliary_control_conformances=conformances,
            support_balance_records=supports, pairs=pairs,
        )

    def test_global_plan_binds_the_residual_control_support_not_focal_support(self) -> None:
        subject, contract, _ = self._fixture()
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "global_bundle_strength")
        focal_support = next(row for row in contract.support_balance_records if row.record_sha256 == contract.pairs[0].balance_support_record_sha256)
        self._none(subject, self._rebind_plan(subject, contract, plan, support_cell_sha256=focal_support.support_cell_sha256))

    def test_auxiliary_plan_target_roster_digest_is_exact(self) -> None:
        subject, contract, _ = self._fixture()
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "global_bundle_strength")
        bad = self._rebind_plan(
            subject, contract, plan,
            target_action_roster_sha256=_digest("foreign-plan-target-roster"),
        )
        self._reason(
            subject, bad, "auxiliary plan target roster digest mismatch",
        )

    def test_rehashed_multiplicity_and_probability_spec_are_not_caller_assertions(self) -> None:
        subject, contract, _ = self._fixture()
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        global_plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "global_bundle_strength")
        self._none(subject, self._rebind_plan(subject, contract, global_plan, assignment_reference_multiplicities=(7,) * len(global_plan.assignment_record_sha256s)))
        uniform_plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "uniform_random_admissible")
        assignment = next(row for row in contract.assignments if row.record_sha256 == uniform_plan.assignment_record_sha256s[0])
        foreign_spec = _rebuild(assignment, assignment_probability_spec_sha256=_digest("foreign-uniform-probability-spec"))
        assignments = _ordered([foreign_spec, *[row for row in contract.assignments if row.record_sha256 != assignment.record_sha256]], "record_sha256")
        self._none(
            subject,
            self._rebind_plan(
                subject, _rebuild(contract, assignments=assignments), uniform_plan,
                assignment_record_sha256s=(foreign_spec.record_sha256,),
            ),
        )

    def test_auxiliary_execution_and_terminal_joins_are_exact_after_rehash(self) -> None:
        subject, contract, _ = self._fixture()
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "uniform_random_admissible")
        assignment = next(row for row in contract.assignments if row.record_sha256 == plan.assignment_record_sha256s[0])
        execution = next(row for row in contract.execution_records if row.assignment_ref == assignment.assignment_ref)
        alternate_packet = contract.pairs[0].low_packet_id
        alternate_manifest = contract.pairs[0].low_complete_bundle_manifest_sha256
        forged_execution = _rebuild(execution, actual_packet_id=alternate_packet, actual_complete_bundle_manifest_sha256=alternate_manifest)
        executions = _ordered([forged_execution, *[row for row in contract.execution_records if row.record_sha256 != execution.record_sha256]], "record_sha256")
        old_conformance = next(row for row in contract.auxiliary_control_conformances if row.control_plan_sha256 == plan.plan_sha256)
        forged_conformance = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=plan.plan_sha256, assignment_record_sha256s=plan.assignment_record_sha256s,
            execution_record_sha256s=(forged_execution.record_sha256,), terminal_record_sha256s=old_conformance.terminal_record_sha256s,
            compliance_status="verified",
        )
        conformances = _ordered([forged_conformance, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != old_conformance.conformance_sha256]], "conformance_sha256")
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        replacement_support = _rebuild(support, uniform_random_control_sha256=forged_conformance.conformance_sha256)
        supports = _ordered([replacement_support, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        pairs = (_rebuild(pair, balance_support_record_sha256=replacement_support.record_sha256),)
        self._none(subject, _rebuild(contract, execution_records=executions, auxiliary_control_conformances=conformances, support_balance_records=supports, pairs=pairs))

    def test_duplicate_assignment_ref_and_second_focal_reuse_are_nonestimable(self) -> None:
        subject, contract, _ = self._fixture()
        self.assertEqual(subject.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "uniform_random_admissible")
        assignment = next(row for row in contract.assignments if row.record_sha256 == plan.assignment_record_sha256s[0])
        borrowed = next(row for row in contract.assignments if row.record_sha256 not in set(plan.assignment_record_sha256s))
        duplicate_ref = _rebuild(assignment, assignment_ref=borrowed.assignment_ref)
        execution = next(row for row in contract.execution_records if row.assignment_ref == assignment.assignment_ref)
        duplicate_execution = _rebuild(execution, assignment_ref=borrowed.assignment_ref)
        assignments = _ordered([duplicate_ref, *[row for row in contract.assignments if row.record_sha256 != assignment.record_sha256]], "record_sha256")
        executions = _ordered([duplicate_execution, *[row for row in contract.execution_records if row.record_sha256 != execution.record_sha256]], "record_sha256")
        old_conformance = next(row for row in contract.auxiliary_control_conformances if row.control_plan_sha256 == plan.plan_sha256)
        duplicate_plan = _rebuild(plan, assignment_record_sha256s=(duplicate_ref.record_sha256,))
        duplicate_conformance = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=duplicate_plan.plan_sha256,
            assignment_record_sha256s=duplicate_plan.assignment_record_sha256s,
            execution_record_sha256s=(duplicate_execution.record_sha256,),
            terminal_record_sha256s=old_conformance.terminal_record_sha256s,
            compliance_status="verified",
        )
        plans = _ordered([duplicate_plan, *[row for row in contract.auxiliary_control_plans if row.plan_sha256 != plan.plan_sha256]], "plan_sha256")
        conformances = _ordered([duplicate_conformance, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != old_conformance.conformance_sha256]], "conformance_sha256")
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        duplicate_support = _rebuild(support, uniform_random_control_sha256=duplicate_conformance.conformance_sha256)
        supports = _ordered([duplicate_support, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        pairs = (_rebuild(pair, balance_support_record_sha256=duplicate_support.record_sha256),)
        self._none(subject, _rebuild(contract, assignments=assignments, execution_records=executions, auxiliary_control_plans=plans, auxiliary_control_conformances=conformances, support_balance_records=supports, pairs=pairs))
        second_support = _rebuild(support, target_census=2)
        second_pair = _rebuild(pair, balance_support_record_sha256=second_support.record_sha256)
        self._none(subject, _rebuild(contract, support_balance_records=_ordered([*contract.support_balance_records, second_support], "record_sha256"), pairs=_ordered([pair, second_pair], "pair_sha256")))

    def test_uniform_actual_slot_substitution_is_rehashed_and_rejected(self) -> None:
        subject, contract, _ = self._fixture()
        plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "uniform_random_admissible")
        assignment = next(row for row in contract.assignments if row.record_sha256 == plan.assignment_record_sha256s[0])
        execution = next(row for row in contract.execution_records if row.assignment_ref == assignment.assignment_ref)
        other_slot = next(row.assigned_opaque_slot_id for row in contract.assignments if row.assigned_opaque_slot_id != assignment.assigned_opaque_slot_id)
        forged_execution = _rebuild(execution, actual_opaque_slot_id=other_slot)
        executions = _ordered([forged_execution, *[row for row in contract.execution_records if row.record_sha256 != execution.record_sha256]], "record_sha256")
        old_conformance = next(row for row in contract.auxiliary_control_conformances if row.control_plan_sha256 == plan.plan_sha256)
        forged_conformance = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=plan.plan_sha256, assignment_record_sha256s=plan.assignment_record_sha256s,
            execution_record_sha256s=(forged_execution.record_sha256,), terminal_record_sha256s=old_conformance.terminal_record_sha256s,
            compliance_status="verified",
        )
        conformances = _ordered([forged_conformance, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != old_conformance.conformance_sha256]], "conformance_sha256")
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        replacement_support = _rebuild(support, uniform_random_control_sha256=forged_conformance.conformance_sha256)
        supports = _ordered([replacement_support, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        pairs = (_rebuild(pair, balance_support_record_sha256=replacement_support.record_sha256),)
        self._reason(
            subject,
            _rebuild(contract, execution_records=executions, auxiliary_control_conformances=conformances, support_balance_records=supports, pairs=pairs),
            "auxiliary conformance join is not exact",
        )

    def test_exact_extra_executed_conformance_row_is_rehashed_and_rejected(self) -> None:
        subject, contract, _ = self._fixture()
        plan = next(row for row in contract.auxiliary_control_plans if row.control_kind == "uniform_random_admissible")
        conformance = next(row for row in contract.auxiliary_control_conformances if row.control_plan_sha256 == plan.plan_sha256)
        extra_assignment = next(row for row in contract.assignments if row.record_sha256 not in set(plan.assignment_record_sha256s))
        extra_execution = next(row for row in contract.execution_records if row.assignment_ref == extra_assignment.assignment_ref)
        extra_terminal = next(row for row in contract.terminal_branches if row.execution_conformance_sha256 == extra_execution.post_run_execution_usage_conformance_receipt_sha256)
        assignment_hashes = tuple(sorted((*plan.assignment_record_sha256s, extra_assignment.record_sha256)))
        execution_hashes = tuple(sorted((*conformance.execution_record_sha256s, extra_execution.record_sha256)))
        terminal_hashes = tuple(sorted((*conformance.terminal_record_sha256s, extra_terminal.record_sha256)))
        extra = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=plan.plan_sha256, assignment_record_sha256s=assignment_hashes,
            execution_record_sha256s=execution_hashes, terminal_record_sha256s=terminal_hashes,
            compliance_status="verified",
        )
        conformances = _ordered([extra, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != conformance.conformance_sha256]], "conformance_sha256")
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        replacement_support = _rebuild(support, uniform_random_control_sha256=extra.conformance_sha256)
        supports = _ordered([replacement_support, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        pairs = (_rebuild(pair, balance_support_record_sha256=replacement_support.record_sha256),)
        self._reason(
            subject,
            _rebuild(contract, auxiliary_control_conformances=conformances, support_balance_records=supports, pairs=pairs),
            "conformance selected an unplanned assignment",
        )

    def test_extreme_finite_costs_cannot_touch_primary_only_estimator(self) -> None:
        from iclr2027 import obligation_oracle as subject

        target = _add_control(
            subject,
            _target_records(subject, site="site-a", case="case-a", prefix="prefix-a", high_qualities=(0.9, 0.8), low_qualities=(0.5, 0.4), high_costs=(1e308, 1e308), low_costs=(0.0, 0.0)),
            case="case-control", prefix="prefix-control", high_qualities=(0.5, 0.5), low_qualities=(0.5, 0.5), high_costs=(0.0, 0.0), low_costs=(0.0, 0.0),
        )
        summary = subject.evaluate_synthetic_e2(_contract(subject, target))
        self.assertEqual(summary.status, "synthetic_complete")
        self.assertAlmostEqual(summary.site_clustered_primary_contrast, 0.4)
        self.assertEqual((summary.secondary_cost_adjusted_utility, summary.secondary_continuous_alignment_cost_interaction), (None, None))

    def test_hash_only_or_unexecuted_auxiliary_control_is_nonestimable(self) -> None:
        subject, contract, _ = self._fixture()
        plan = contract.auxiliary_control_plans[0]
        conformance = next(row for row in contract.auxiliary_control_conformances if row.control_plan_sha256 == plan.plan_sha256)
        unverified = _rebuild(conformance, compliance_status="noncompliant")
        rows = _ordered([unverified, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != conformance.conformance_sha256]], "conformance_sha256")
        self._none(subject, _rebuild(contract, auxiliary_control_conformances=rows))

    def test_hash_only_global_control_cannot_replace_typed_execution(self) -> None:
        subject, contract, _ = self._fixture()
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        hash_only = _rebuild(support, global_bundle_strength_control_sha256=_digest("hash-only-global"))
        supports = _ordered([hash_only, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        bad_pair = _rebuild(pair, balance_support_record_sha256=hash_only.record_sha256)
        pairs = _ordered([bad_pair, *[row for row in contract.pairs if row.pair_sha256 != pair.pair_sha256]], "pair_sha256")
        self._none(subject, _rebuild(contract, support_balance_records=supports, pairs=pairs))

    def test_foreign_focal_or_residual_binding_target_is_nonestimable(self) -> None:
        subject, contract, target = self._fixture()
        focal = target["bindings"][0]
        foreign = _rebuild(focal, prefix_ref="prefix-foreign")
        pair = target["pairs"][0]
        bad_pair = _rebuild(pair, high_residual_capability_binding_sha256=foreign.binding_sha256)
        bindings = _ordered([foreign, *[row for row in contract.bindings if row.binding_sha256 != focal.binding_sha256]], "binding_sha256")
        pairs = _ordered([bad_pair, *[row for row in contract.pairs if row.pair_sha256 != pair.pair_sha256]], "pair_sha256")
        self._none(subject, _rebuild(contract, bindings=bindings, pairs=pairs))

    def test_nonuniform_or_postrun_selected_auxiliary_leg_is_nonestimable(self) -> None:
        subject, contract, _ = self._fixture()
        uniform = next(row for row in contract.auxiliary_control_plans if row.control_kind == "uniform_random_admissible")
        assignment = next(row for row in contract.assignments if row.record_sha256 == uniform.assignment_record_sha256s[0])
        unequal = _rebuild(assignment, assignment_probability=0.25)
        assignments = _ordered([unequal, *[row for row in contract.assignments if row.record_sha256 != assignment.record_sha256]], "record_sha256")
        nonuniform = self._rebind_plan(
            subject, _rebuild(contract, assignments=assignments), uniform,
            assignment_record_sha256s=(unequal.record_sha256,),
        )
        self._reason(subject, nonuniform, "uniform control probability is not exact")
        alternate = next(row for row in contract.assignments if row.record_sha256 not in set(uniform.assignment_record_sha256s))
        conformance = next(row for row in contract.auxiliary_control_conformances if row.control_plan_sha256 == uniform.plan_sha256)
        selected = subject.AuxiliaryControlConformanceV2.create(
            control_plan_sha256=uniform.plan_sha256,
            assignment_record_sha256s=(alternate.record_sha256,),
            execution_record_sha256s=conformance.execution_record_sha256s,
            terminal_record_sha256s=conformance.terminal_record_sha256s,
            compliance_status="verified",
        )
        conformances = _ordered([selected, *[row for row in contract.auxiliary_control_conformances if row.conformance_sha256 != conformance.conformance_sha256]], "conformance_sha256")
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        selected_support = _rebuild(support, uniform_random_control_sha256=selected.conformance_sha256)
        supports = _ordered([selected_support, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        pairs = (_rebuild(pair, balance_support_record_sha256=selected_support.record_sha256),)
        self._reason(
            subject,
            _rebuild(contract, auxiliary_control_conformances=conformances, support_balance_records=supports, pairs=pairs),
            "conformance selected an unplanned assignment",
        )

    def test_altered_multiplicity_wrong_support_or_unreachable_terminal_is_nonestimable(self) -> None:
        subject, contract, _ = self._fixture()
        plan = contract.auxiliary_control_plans[0]
        altered = _rebuild(plan, assignment_reference_multiplicities=(2,) * len(plan.assignment_record_sha256s))
        plans = _ordered([altered, *[row for row in contract.auxiliary_control_plans if row.plan_sha256 != plan.plan_sha256]], "plan_sha256")
        self._none(subject, _rebuild(contract, auxiliary_control_plans=plans))
        pair = contract.pairs[0]
        support = next(row for row in contract.support_balance_records if row.record_sha256 == pair.balance_support_record_sha256)
        wrong_target = _rebuild(support, prefix_ref="prefix-wrong")
        bad_pair = _rebuild(pair, balance_support_record_sha256=wrong_target.record_sha256)
        supports = _ordered([wrong_target, *[row for row in contract.support_balance_records if row.record_sha256 != support.record_sha256]], "record_sha256")
        pairs = _ordered([bad_pair, *[row for row in contract.pairs if row.pair_sha256 != pair.pair_sha256]], "pair_sha256")
        self._none(subject, _rebuild(contract, support_balance_records=supports, pairs=pairs))
        stop = subject.SyntheticTerminalBranch.create(
            site_ref="site-extra", case_ref="case-extra", prefix_ref="prefix-extra",
            treatment_kind="stop", opaque_slot_id=None, actual_packet_id=None,
            repeat_index=0, seed=0, blind_terminal_quality=0.0,
            complete_processed_tokens=0, latency_seconds=0.0, list_price_cost=0.0,
            execution_conformance_sha256=_digest("extra-stop"), direct_terminal_sha256=_digest("extra-stop-terminal"),
        )
        self._none(subject, _rebuild(contract, terminal_branches=_ordered([*contract.terminal_branches, stop], "record_sha256")))


class E3ParityAndBaselineTests(unittest.TestCase):
    def test_paired_parity_has_one_bundle_owned_two_argument_decision_authority(self) -> None:
        from iclr2027 import obligation_oracle as subject

        receipt, bundle, *_ = _parity_fixture(subject)
        subject.validate_paired_information_parity(receipt, bundle)
        with self.assertRaises(TypeError):
            subject.validate_paired_information_parity(
                receipt, bundle, bundle.oacs_pre_outcome_decision_bytes,
                bundle.raw_router_pre_outcome_decision_bytes,
            )

    def test_bundle_rejects_rehashed_false_projection_equivalence_and_decision_bytes(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, bundle, _, _, actions, _ = _parity_fixture(subject)
        bad_spec = json.loads(bundle.oacs_projection_spec_bytes)
        bad_spec["field_map"].pop(next(iter(bad_spec["field_map"])))
        attacks = (
            {"oacs_projection_spec_bytes": _json_bytes(bad_spec)},
            {"information_equivalence_map_bytes": _json_bytes([])},
            {"oacs_input_bytes": _json_bytes({})},
            {"oacs_pre_outcome_decision_bytes": _json_bytes({"action": actions[-1]})},
            {"raw_router_pre_outcome_decision_bytes": _json_bytes({"action_id": "semantic-solo"})},
        )
        for attack in attacks:
            with self.subTest(attack=tuple(attack)), self.assertRaises(ValueError):
                _rebuild(bundle, **attack)

    def test_parent_and_shared_training_require_complete_exact_typed_content(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, bundle, *_ = _parity_fixture(subject)
        parent = json.loads(bundle.source_parent_bytes)
        shared = json.loads(bundle.shared_training_opportunity_bytes)
        mutations = []
        for key in ("raw_transcript_prefix", "numeric_residual_serialization", "complete_capability_table", "opaque_packet_binding_cards"):
            changed = dict(parent)
            changed.pop(key)
            mutations.append({"source_parent_bytes": _json_bytes(changed)})
        changed = json.loads(bundle.source_parent_bytes)
        changed["numeric_residual_serialization"]["alignment"] = [0.5]
        mutations.append({"source_parent_bytes": _json_bytes(changed)})
        for key in ("costs", "admissibility", "examples", "split_fold", "learner_class_capacity", "tuning_optimization_opportunity", "action_space_tie_rule"):
            changed_shared = dict(shared)
            changed_shared.pop(key)
            mutations.append({"shared_training_opportunity_bytes": _json_bytes(changed_shared)})
        for attack in mutations:
            with self.subTest(attack=tuple(attack)), self.assertRaises((TypeError, ValueError)):
                _rebuild(bundle, **attack)

    def test_parity_actual_bytes_reject_noncanonical_duplicate_nonfinite_and_negative_zero(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, bundle, *_ = _parity_fixture(subject)
        for raw in (b'{"a":NaN}', b'{"a": 1}', b'{"a":1,"a":2}', b'{"a":-0.0}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                _rebuild(bundle, source_parent_bytes=raw)

    def test_e3_target_authority_and_shared_e1_menu_close_registry_actions(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, values = _e3_contract_fixture(subject)
        authority = values["target_action_authority"]
        shared = values["shared_e1_action_roster"]
        self.assertEqual(type(contract).from_dict(contract.to_dict()), contract)
        attacks = (
            {"shared_e1_action_roster": _rebuild(shared, packet_ids=shared.packet_ids[:-1])},
            {"shared_e1_action_roster": _rebuild(shared, prefix_ref="foreign-prefix")},
            {"target_action_authority": _rebuild(authority, opaque_identity_registry_sha256=_digest("foreign-registry"))},
        )
        for attack in attacks:
            with self.subTest(attack=tuple(attack)), self.assertRaises(ValueError):
                subject.E3ComparatorContract.create(**{**values, **attack})
        stale_packet = _opaque_id("packet", "foreign-e3-packet")
        slot, _, manifest = authority.packet_slot_bindings[0]
        stale_bindings = ((slot, stale_packet, manifest),) + authority.packet_slot_bindings[1:]
        stale_authority = _rebuild(authority, packet_slot_bindings=stale_bindings)
        with self.assertRaises(ValueError):
            subject.E3ComparatorContract.create(**{**values, "target_action_authority": stale_authority})

    def test_e3_root_from_dict_replays_nested_bytes_instead_of_trusting_rehashed_children(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        raw = contract.to_dict()
        nested = raw["parity_replay_bundle"]
        nested["oacs_pre_outcome_decision_bytes"] = _json_bytes({
            "action": {
                "action_kind": "capability_packet",
                "opaque_packet_id": _opaque_id("packet", "foreign"),
                "opaque_slot_id": _opaque_id("slot", "foreign"),
            }
        }).decode("utf-8")
        nested_unsigned = dict(nested)
        nested_unsigned.pop("bundle_sha256")
        nested["bundle_sha256"] = hashlib.sha256(_json_bytes(nested_unsigned)).hexdigest()
        unsigned = dict(raw)
        unsigned.pop("contract_sha256")
        raw["contract_sha256"] = hashlib.sha256(_json_bytes(unsigned)).hexdigest()
        with self.assertRaises(ValueError):
            subject.E3ComparatorContract.from_dict(raw)

    def test_mandatory_policy_roster_is_exactly_22_and_retrospective_is_not_a_policy(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        roster = contract.mandatory_roster
        self.assertEqual(tuple(entry.baseline_id for entry in roster.entries), BASELINE_IDS)
        self.assertEqual(len(set(BASELINE_IDS)), 22)
        self.assertNotIn("retrospective_oracle", BASELINE_IDS)
        for entries in (roster.entries[:-1], roster.entries + (roster.entries[0],), tuple(reversed(roster.entries))):
            with self.subTest(size=len(entries)), self.assertRaises(ValueError):
                subject.MandatoryBaselineRoster.create(entries=entries)
        with self.assertRaises(ValueError):
            subject.MandatoryBaselineRosterEntry.create(
                baseline_id="retrospective_oracle", official_source_spec_sha256=None,
                version_sha256=_digest("retrospective-version"),
            )

    def test_distinct_resource_allocation_and_scaling_source_version_commitments_cannot_merge(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        entries = {entry.baseline_id: entry for entry in contract.mandatory_roster.entries}
        self.assertNotEqual(
            (entries["self_resource_allocation"].official_source_spec_sha256, entries["self_resource_allocation"].version_sha256),
            (entries["matched_compute_self_agent_scaling"].official_source_spec_sha256, entries["matched_compute_self_agent_scaling"].version_sha256),
        )
        collided = _rebuild(
            entries["self_resource_allocation"],
            official_source_spec_sha256=entries["matched_compute_self_agent_scaling"].official_source_spec_sha256,
            version_sha256=entries["matched_compute_self_agent_scaling"].version_sha256,
        )
        rows = tuple(collided if row.baseline_id == collided.baseline_id else row for row in contract.mandatory_roster.entries)
        with self.assertRaises(ValueError):
            subject.MandatoryBaselineRoster.create(entries=rows)

    def test_distinct_semantic_source_version_swap_is_declared_only_and_accepted(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)
        allocation_id = "self_resource_allocation"
        scaling_id = "matched_compute_self_agent_scaling"
        entries = {row.baseline_id: row for row in values["mandatory_roster"].entries}
        allocation = entries[allocation_id]
        scaling = entries[scaling_id]
        replacements = {
            allocation_id: _rebuild(
                allocation,
                official_source_spec_sha256=scaling.official_source_spec_sha256,
                version_sha256=scaling.version_sha256,
            ),
            scaling_id: _rebuild(
                scaling,
                official_source_spec_sha256=allocation.official_source_spec_sha256,
                version_sha256=allocation.version_sha256,
            ),
        }
        swapped_roster = subject.MandatoryBaselineRoster.create(
            entries=tuple(
                replacements.get(row.baseline_id, row)
                for row in values["mandatory_roster"].entries
            )
        )
        swapped_readiness = []
        readiness_by_id = {}
        for ready in values["baseline_pre_outcome_readiness"]:
            entry = replacements.get(ready.baseline_id)
            changed = ready if entry is None else _rebuild(
                ready,
                official_source_spec_sha256=entry.official_source_spec_sha256,
                version_sha256=entry.version_sha256,
            )
            swapped_readiness.append(changed)
            readiness_by_id[changed.baseline_id] = changed
        swapped_conformance = []
        for run in values["baseline_decision_conformance"]:
            ready = readiness_by_id[run.baseline_id]
            if run.baseline_id not in replacements:
                swapped_conformance.append(run)
                continue
            environment = hashlib.sha256(
                _json_bytes(
                    [
                        ready.status_sha256,
                        ready.version_sha256,
                        ready.adapter_code_sha256,
                        ready.dependency_environment_lock_sha256,
                        ready.parity_projection_sha256,
                        ready.executed_method_id,
                    ]
                )
            ).hexdigest()
            swapped_conformance.append(
                _rebuild(
                    run,
                    readiness_status_sha256=ready.status_sha256,
                    adapter_environment_sha256=environment,
                )
            )
        accepted = subject.E3ComparatorContract.create(
            **{
                **values,
                "mandatory_roster": swapped_roster,
                "baseline_pre_outcome_readiness": tuple(swapped_readiness),
                "baseline_decision_conformance": tuple(swapped_conformance),
            }
        )
        self.assertEqual(type(accepted).from_dict(accepted.to_dict()), accepted)
        with self.assertRaisesRegex(subject.NeedsContextError, "^NEEDS_CONTEXT$"):
            subject.require_phase_b_authority()
        with self.assertRaisesRegex(ValueError, "readiness source/version does not match roster"):
            subject.E3ComparatorContract.create(
                **{**values, "mandatory_roster": swapped_roster}
            )

    def test_internal_and_literature_source_commitment_shapes_are_exact(self) -> None:
        from iclr2027 import obligation_oracle as subject

        with self.assertRaises(ValueError):
            subject.MandatoryBaselineRosterEntry.create(
                baseline_id="automix", official_source_spec_sha256=None, version_sha256=_digest("v")
            )
        with self.assertRaises(ValueError):
            subject.MandatoryBaselineRosterEntry.create(
                baseline_id="solo", official_source_spec_sha256=_digest("paper"), version_sha256=_digest("v")
            )

    def test_readiness_status_reason_version_source_and_executed_identity_are_exact(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        ready = contract.baseline_pre_outcome_readiness[0]
        for changes in (
            {"reason_code": "dependency_unavailable"},
            {"version_sha256": _digest("foreign-version")},
            {"official_source_spec_sha256": _digest("foreign-source")},
            {"executed_method_id": "another-method"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                changed = _rebuild(ready, **changes)
                rows = (changed,) + contract.baseline_pre_outcome_readiness[1:]
                subject.E3ComparatorContract.create(
                    **{**_e3_contract_fixture(subject)[1], "baseline_pre_outcome_readiness": rows}
                )

    def test_unsupported_and_adapted_cardinality_and_method_identity_fail_closed(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)
        ready = values["baseline_pre_outcome_readiness"][0]
        blocked = subject.BaselinePreOutcomeReadinessAuthority.create(
            baseline_id=ready.baseline_id, version_sha256=ready.version_sha256,
            status="unsupported_missing_dependency", reason_code="dependency_unavailable",
            official_source_spec_sha256=ready.official_source_spec_sha256, executed_method_id=None,
            adapter_code_sha256=None,
            dependency_environment_lock_sha256=ready.dependency_environment_lock_sha256,
            parity_projection_sha256=None, synthetic_faithfulness_test_receipt_sha256=None,
            reviewer_decision_sha256=ready.reviewer_decision_sha256,
            pre_outcome_amendment_sha256=None,
        )
        readiness = (blocked,) + values["baseline_pre_outcome_readiness"][1:]
        conformance = tuple(row for row in values["baseline_decision_conformance"] if row.baseline_id != blocked.baseline_id)
        subject.E3ComparatorContract.create(**{**values, "baseline_pre_outcome_readiness": readiness, "baseline_decision_conformance": conformance})
        with self.assertRaises(ValueError):
            subject.E3ComparatorContract.create(**{**values, "baseline_pre_outcome_readiness": readiness})
        amendment = _digest("pre-outcome-amendment")
        adapted_id = "adaptation:" + hashlib.sha256(_json_bytes([ready.baseline_id, amendment])).hexdigest()
        adapted = _rebuild(
            ready, status="inapplicable_predeclared_amendment", reason_code="domain_inapplicable",
            executed_method_id=adapted_id, pre_outcome_amendment_sha256=amendment,
        )
        run = values["baseline_decision_conformance"][0]
        wrong_run = _rebuild(run, executed_method_id=ready.baseline_id, readiness_status_sha256=adapted.status_sha256)
        with self.assertRaises(ValueError):
            subject.E3ComparatorContract.create(**{
                **values, "baseline_pre_outcome_readiness": (adapted,) + values["baseline_pre_outcome_readiness"][1:],
                "baseline_decision_conformance": (wrong_run,) + values["baseline_decision_conformance"][1:],
            })

    def test_baseline_actual_projection_input_roster_decision_and_receipts_are_replayed(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)
        run = values["baseline_decision_conformance"][0]
        attacks = (
            {"readiness_status_sha256": _digest("foreign-readiness")},
            {"input_action_roster_sha256": _digest("foreign-roster")},
            {"baseline_input_bytes": _json_bytes({"external": "field"})},
            {"baseline_projection_spec_bytes": _json_bytes({"schema_version": IDENTITY_DOMAIN + ".e3_projection_spec", "field_map": {"external": "missing"}})},
            {"pre_outcome_decision_bytes": _json_bytes({"action": json.loads(values["parity_replay_bundle"].target_action_roster_bytes)[-1]})},
            {"adapter_environment_sha256": _digest("foreign-environment")},
        )
        for attack in attacks:
            with self.subTest(attack=tuple(attack)), self.assertRaises(ValueError):
                changed = _rebuild(run, **attack)
                rows = (changed,) + values["baseline_decision_conformance"][1:]
                subject.E3ComparatorContract.create(**{**values, "baseline_decision_conformance": rows})

    def test_fully_rehashed_canonical_wrong_baseline_input_reaches_root_replay_from_dict(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        payload = contract.to_dict()
        row = payload["baseline_decision_conformance"][0]
        wrong_input = _json_bytes({"admissibility": {"admissible_action_sha256s": []}})
        row["baseline_input_bytes"] = wrong_input.decode("utf-8")
        row["baseline_input_bytes_sha256"] = hashlib.sha256(wrong_input).hexdigest()
        _rehash_payload(row, "receipt_sha256")
        _rehash_payload(payload, "contract_sha256")
        subject.BaselineDecisionRunConformanceReceipt.from_dict(row)
        with self.assertRaisesRegex(ValueError, "baseline input replay mismatch"):
            subject.E3ComparatorContract.from_dict(payload)

    def test_valid_alternative_baseline_projection_has_one_coherent_acceptance_path(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)
        ready = values["baseline_pre_outcome_readiness"][0]
        run = values["baseline_decision_conformance"][0]
        parent = json.loads(values["parity_replay_bundle"].source_parent_bytes)
        alternative_spec = _json_bytes(
            {
                "schema_version": IDENTITY_DOMAIN + ".e3_projection_spec",
                "field_map": {"held_target": "site_ref", "menu": "target_action_roster"},
            }
        )
        alternative_input = _json_bytes(
            {"held_target": parent["site_ref"], "menu": parent["target_action_roster"]}
        )
        alternative_hash = hashlib.sha256(alternative_spec).hexdigest()
        drift_run = _rebuild(
            run,
            baseline_projection_spec_bytes=alternative_spec,
            baseline_projection_spec_bytes_sha256=alternative_hash,
            baseline_input_bytes=alternative_input,
            baseline_input_bytes_sha256=hashlib.sha256(alternative_input).hexdigest(),
        )
        with self.assertRaisesRegex(ValueError, "baseline projection does not bind readiness"):
            subject.E3ComparatorContract.create(
                **{
                    **values,
                    "baseline_decision_conformance": (
                        drift_run,
                        *values["baseline_decision_conformance"][1:],
                    ),
                }
            )

        alternative_ready = _rebuild(ready, parity_projection_sha256=alternative_hash)
        adapter_environment = hashlib.sha256(
            _json_bytes(
                [
                    alternative_ready.status_sha256,
                    alternative_ready.version_sha256,
                    alternative_ready.adapter_code_sha256,
                    alternative_ready.dependency_environment_lock_sha256,
                    alternative_ready.parity_projection_sha256,
                    alternative_ready.executed_method_id,
                ]
            )
        ).hexdigest()
        coherent_run = _rebuild(
            drift_run,
            readiness_status_sha256=alternative_ready.status_sha256,
            adapter_environment_sha256=adapter_environment,
        )
        accepted = subject.E3ComparatorContract.create(
            **{
                **values,
                "baseline_pre_outcome_readiness": (
                    alternative_ready,
                    *values["baseline_pre_outcome_readiness"][1:],
                ),
                "baseline_decision_conformance": (
                    coherent_run,
                    *values["baseline_decision_conformance"][1:],
                ),
            }
        )
        self.assertEqual(type(accepted).from_dict(accepted.to_dict()), accepted)

    def test_fully_rehashed_well_typed_inadmissible_baseline_decision_reaches_root(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        payload = contract.to_dict()
        actions = json.loads(payload["parity_replay_bundle"]["target_action_roster_bytes"])
        decision = _json_bytes({"action": actions[-1]})
        row = payload["baseline_decision_conformance"][0]
        row["pre_outcome_decision_bytes"] = decision.decode("utf-8")
        row["pre_outcome_decision_bytes_sha256"] = hashlib.sha256(decision).hexdigest()
        _rehash_payload(row, "receipt_sha256")
        _rehash_payload(payload, "contract_sha256")
        subject.BaselineDecisionRunConformanceReceipt.from_dict(row)
        with self.assertRaisesRegex(ValueError, "foreign or inadmissible action"):
            subject.E3ComparatorContract.from_dict(payload)

    def test_baseline_conformance_direct_record_rejects_semantic_decision_and_invalid_projection(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)
        run = values["baseline_decision_conformance"][0]
        attacks = (
            {
                "pre_outcome_decision_bytes": _json_bytes({"action_id": "semantic-solo"}),
                "pre_outcome_decision_bytes_sha256": hashlib.sha256(
                    _json_bytes({"action_id": "semantic-solo"})
                ).hexdigest(),
            },
            {
                "baseline_projection_spec_bytes": _json_bytes({"field_map": {"x": "costs"}}),
                "baseline_projection_spec_bytes_sha256": hashlib.sha256(
                    _json_bytes({"field_map": {"x": "costs"}})
                ).hexdigest(),
            },
            {
                "baseline_input_bytes": _json_bytes([]),
                "baseline_input_bytes_sha256": hashlib.sha256(_json_bytes([])).hexdigest(),
            },
        )
        for attack in attacks:
            with self.subTest(attack=tuple(attack)), self.assertRaises((TypeError, ValueError)):
                _rebuild(run, **attack)

    def test_difficulty_confidence_is_an_ordinary_policy_with_actual_decision(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)
        self.assertNotIn("difficulty_confidence_comparator_sha256", values)
        missing = tuple(row for row in values["baseline_decision_conformance"] if row.baseline_id != "difficulty_confidence")
        with self.assertRaises(ValueError):
            subject.E3ComparatorContract.create(**{**values, "baseline_decision_conformance": missing})
        with self.assertRaises(ValueError):
            subject.E3ComparatorContract.create(**{**values, "difficulty_confidence_comparator_sha256": _digest("difficulty")})

    def test_retrospective_oracle_is_complete_post_outcome_and_admissible_only(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, values = _e3_contract_fixture(subject)
        oracle = contract.retrospective_oracle_evaluation
        table = json.loads(oracle.direct_action_value_table_bytes)
        self.assertEqual(json.loads(oracle.oracle_decision_bytes), {"action": table[1]["action"]})
        self.assertGreater(table[-1]["blind_direct_value"], table[1]["blind_direct_value"])
        attacks = (
            {"direct_action_value_table_bytes": _json_bytes(table[:-1])},
            {"oracle_decision_bytes": _json_bytes({"action": table[-1]["action"]})},
            {"admissibility_sha256": _digest("foreign-admissibility")},
            {"action_space_tie_rule_sha256": _digest("foreign-tie")},
        )
        for attack in attacks:
            changed = _rebuild(oracle, **attack)
            with self.subTest(attack=tuple(attack)), self.assertRaises(ValueError):
                subject.E3ComparatorContract.create(**{**values, "retrospective_oracle_evaluation": changed})

    def test_retrospective_oracle_direct_record_rejects_duplicate_actions(self) -> None:
        from iclr2027 import obligation_oracle as subject

        contract, _ = _e3_contract_fixture(subject)
        oracle = contract.retrospective_oracle_evaluation
        table = json.loads(oracle.direct_action_value_table_bytes)
        table[1]["action"] = table[0]["action"]
        with self.assertRaises(ValueError):
            _rebuild(oracle, direct_action_value_table_bytes=_json_bytes(table))

    def test_e3_root_rejects_subclass_duck_and_hash_only_bypasses(self) -> None:
        from iclr2027 import obligation_oracle as subject

        _, values = _e3_contract_fixture(subject)

        class ReceiptSubclass(subject.PairedInformationParityReceipt):
            __slots__ = ()

        subclass = ReceiptSubclass(**asdict(values["parity_receipt"]))
        with self.assertRaises(TypeError):
            subject.E3ComparatorContract.create(**{**values, "parity_receipt": subclass})
        with self.assertRaises(TypeError):
            subject.E3ComparatorContract.create(**{**values, "target_action_authority": values["target_action_authority"].to_dict()})


class PhaseBoundaryTests(unittest.TestCase):
    def test_phase_b_gate_rejects_before_argument_property_or_path_access(self) -> None:
        from iclr2027 import obligation_oracle as subject

        class Observer:
            touched = 0

            def __fspath__(self) -> str:
                type(self).touched += 1
                raise AssertionError("must not inspect")

            def __getattr__(self, _name: str) -> object:
                type(self).touched += 1
                raise AssertionError("must not inspect")

        with self.assertRaisesRegex(subject.NeedsContextError, "^NEEDS_CONTEXT$"):
            subject.require_phase_b_authority(Observer(), source=Observer())
        self.assertEqual(Observer.touched, 0)

    def test_oracle_cli_help_is_zero_call_and_every_source_flag_needs_context(self) -> None:
        cli = importlib.import_module("analyze_iclr2027_obligation_oracle")
        self.assertEqual(cli.main([]), 0)
        for flag in ("--inventory", "--source", "--data", "--output"):
            with self.subTest(flag=flag), mock.patch.object(Path, "exists", side_effect=AssertionError("I/O")):
                with self.assertRaisesRegex(SystemExit, "^NEEDS_CONTEXT$"):
                    cli.main([flag, str(Path(tempfile.gettempdir()) / "must-not-open")])


if __name__ == "__main__":
    unittest.main()
