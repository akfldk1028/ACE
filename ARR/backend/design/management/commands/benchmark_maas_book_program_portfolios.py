"""Run bounded BOOK × program 20-mass boards on a live PNU parcel."""

import json
import os
from functools import wraps
from collections import Counter
from copy import deepcopy
from math import isfinite
from pathlib import Path
from time import perf_counter

from django.core.management.base import BaseCommand, CommandError
from shapely.affinity import translate
from shapely.geometry import LineString, mapping

from design.maas.book_language.portfolio_benchmark import (
    attach_legal_mass_archive_boards,
    apply_diagnostic_summary_policy as _apply_diagnostic_summary_policy,
    persist_book_program_summary,
    run_book_program_portfolios,
)
from design.maas.book_language.agent_authored_supply import (
    AgentAuthoredAdmission,
    AgentAuthoredSupplyError,
)
from design.maas.book_language.competition_portfolio_contract import (
    competition_portfolio_contract,
)
from design.maas.book_language.actual_gfa_stop_certificate import (
    validate_candidate_actual_gfa_stop_certificate,
)
from design.maas.book_language.run_budget import progressive_mass_run_budget
from design.maas.paid_provider_budget import paid_provider_budget_scope
from design.maas.preference.vlm_scorer import live_vlm_request_count_scope
from design.maas.book_language.legal_floor_field import (
    validate_legal_floor_field,
)
from design.maas.agents.law_graph_agent.evidence import (
    validate_persisted_law_agent_evidence,
)
from design.maas.agents.shared.types import ExecutionIdentity
from design.maas.program_massing.competition_gestalt import (
    CompetitionGestaltKey,
    certified_mesh_morphology_payload_hash,
    competition_gestalt_distance,
    validate_certified_mesh_gestalt_evidence,
)
from design.maas.program_massing.certified_artifact_measurement import (
    measure_authoritative_geometry_artifact,
)
from design.maas.geometry_language.run_state import tracked_mass_command
from design.services.constraint_bridge import regulations_to_constraints
from design.services.site_geometry import fetch_parcel_boundary, geojson_to_polygon, wgs84_to_utm


def _with_site_local_parking_frontage(
    parking_options: dict,
    site_access_geometry: dict | None,
) -> dict:
    """Put the road edge in the same local UTM frame as MASS/parking geometry."""

    result = deepcopy(parking_options or {})
    if not isinstance(site_access_geometry, dict):
        return result
    road_context = dict(result.get("road_context") or {})
    road_context["frontage_geometry"] = deepcopy(site_access_geometry)
    road_context["coordinate_frame"] = "site_local_utm"
    result["road_context"] = road_context
    return result


def _publishable_deficit(
    *,
    code: str,
    program: str,
    axis: str,
    expected,
    actual,
) -> dict:
    return {
        "code": str(code),
        "program": str(program),
        "axis": str(axis),
        "expected": deepcopy(expected),
        "actual": deepcopy(actual),
    }


def _book_scope_label(row: dict) -> str:
    scope = row.get("book_scope")
    if isinstance(scope, dict):
        return str(
            scope.get("base_volume_label")
            or scope.get("label")
            or scope.get("base_scope")
            or ""
        )
    return str(scope or "")


def _resolved_capacity_band(row: dict) -> str:
    return str(
        row.get("resolved_capacity_alternative_id")
        or row.get("achieved_capacity_band")
        or row.get("capacity_alternative_id")
        or ""
    )


def _selected_identity(row: dict) -> dict:
    passport = (
        row.get("mass_execution_passport")
        if isinstance(row.get("mass_execution_passport"), dict)
        else {}
    )
    return {
        "variant_id": str(row.get("variant_id") or ""),
        "program_hash": str(
            row.get("final_legal_program_hash")
            or passport.get("program_hash")
            or ""
        ),
        "geometry_hash": str(
            row.get("final_legal_geometry_hash")
            or passport.get("final_legal_geometry_hash")
            or ""
        ),
        "visual_hash": str(
            passport.get("visual_hash")
            or ""
        ),
        "floor_capacity_plan_hash": str(
            row.get("floor_capacity_plan_hash")
            or passport.get("floor_capacity_plan_hash")
            or ""
        ),
        "legal_floor_field_hash": str(
            row.get("legal_floor_field_hash")
            or passport.get("legal_floor_field_hash")
            or ""
        ),
        "candidate_actual_gfa_stop_hash": str(
            row.get("candidate_actual_gfa_stop_hash")
            or passport.get("candidate_actual_gfa_stop_hash")
            or ""
        ),
    }


def build_publishable_20_manifest_evidence(
    summary: dict,
    *,
    phase_durations_seconds: dict[str, float],
) -> dict:
    """Independently re-audit target-20 output before it is publishable."""

    contract = competition_portfolio_contract(20)
    program_evidence = []
    all_deficits = []
    for raw_program in summary.get("programs") or ():
        if not isinstance(raw_program, dict):
            continue
        slug = str(
            raw_program.get("slug")
            or raw_program.get("program")
            or "unknown"
        )
        rows = [
            row for row in raw_program.get("rows") or ()
            if isinstance(row, dict)
        ]
        identities = [_selected_identity(row) for row in rows]
        capacity_counts = Counter(
            _resolved_capacity_band(row) for row in rows
        )
        capacity_counts.pop("", None)
        scope_counts = Counter(_book_scope_label(row) for row in rows)
        scope_counts.pop("", None)
        completion = (
            raw_program.get("portfolio_completion")
            if isinstance(raw_program.get("portfolio_completion"), dict)
            else {}
        )
        counts = (
            raw_program.get("counts")
            if isinstance(raw_program.get("counts"), dict)
            else {}
        )
        selection_trace = (
            counts.get("selection_trace")
            if isinstance(counts.get("selection_trace"), dict)
            else {}
        )
        compatibility_evidence = (
            selection_trace.get("compatibility_analysis")
            if isinstance(
                selection_trace.get("compatibility_analysis"),
                dict,
            )
            else {}
        )
        solver_evidence = {
            "target_count": int(
                selection_trace.get(
                    "portfolio_contract_target_count"
                )
                or 0
            ),
            "selected_count": int(
                selection_trace.get(
                    "portfolio_contract_solver_count"
                )
                or 0
            ),
            "target_reached": (
                selection_trace.get(
                    "portfolio_contract_solver_target_reached"
                )
                is True
            ),
            "compatibility_threshold": float(
                compatibility_evidence.get(
                    "compatibility_threshold"
                )
                or 0.0
            ),
            "minimum_pair_distance": (
                contract.minimum_pair_distance
            ),
            "shared_language_minimum_composite_distance": (
                contract.shared_language_minimum_composite_distance
            ),
            "deficits": list(
                selection_trace.get("portfolio_contract_deficits")
                or ()
            ),
        }
        program_deficits = []

        def add(code: str, axis: str, expected, actual) -> None:
            deficit = _publishable_deficit(
                code=code,
                program=slug,
                axis=axis,
                expected=expected,
                actual=actual,
            )
            program_deficits.append(deficit)
            all_deficits.append(deficit)

        gestalt_keys: list[CompetitionGestaltKey | None] = []
        certified_morphologies: list[dict] = []
        candidate_actual_gfa_stop_valid_count = 0
        for index, row in enumerate(rows):
            payload = (
                row.get("certified_gestalt_key")
                if isinstance(row.get("certified_gestalt_key"), dict)
                else {}
            )
            render_evidence = (
                row.get("archive_render_evidence")
                if isinstance(
                    row.get("archive_render_evidence"),
                    dict,
                )
                else {}
            )
            authoritative_measurement = None
            authoritative_issues = []
            try:
                authoritative_measurement = (
                    measure_authoritative_geometry_artifact(
                        row.get("authoritative_geometry_artifact"),
                        expected_program_hash=identities[index][
                            "program_hash"
                        ],
                        expected_final_geometry_hash=identities[index][
                            "geometry_hash"
                        ],
                        expected_visual_hash=identities[index][
                            "visual_hash"
                        ],
                        semantic_projection_hard_gate=(
                            row.get("semantic_projection_hard_gate")
                            if isinstance(
                                row.get(
                                    "semantic_projection_hard_gate"
                                ),
                                dict,
                            )
                            else {}
                        ),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                authoritative_issues.append(
                    f"{type(exc).__name__}:{str(exc)[:160]}"
                )
            if authoritative_measurement is not None:
                if (
                    payload
                    != authoritative_measurement.gestalt_key.to_payload()
                ):
                    authoritative_issues.append(
                        "authoritative_gestalt_payload_mismatch"
                    )
                authoritative_morphology_hash = (
                    certified_mesh_morphology_payload_hash(
                        authoritative_measurement.morphology
                    )
                )
                if (
                    str(
                        render_evidence.get(
                            "exact_mesh_payload_hash"
                        )
                        or ""
                    )
                    != authoritative_measurement.exact_mesh_payload_hash
                ):
                    authoritative_issues.append(
                        "authoritative_render_mesh_hash_mismatch"
                    )
                if (
                    str(
                        render_evidence.get(
                            "morphology_payload_hash"
                        )
                        or ""
                    )
                    != authoritative_morphology_hash
                ):
                    authoritative_issues.append(
                        "authoritative_render_morphology_hash_mismatch"
                    )
            if authoritative_issues:
                add(
                    "gestalt.authoritative_geometry_artifact_invalid",
                    f"row[{index}].authoritative_geometry_artifact",
                    (
                        "immutable exact AST + certified visual bytes "
                        "recompile to selected identities and measurements"
                    ),
                    authoritative_issues,
                )
            try:
                persisted_key = CompetitionGestaltKey.from_payload(payload)
            except (TypeError, ValueError):
                persisted_key = None
            key = (
                authoritative_measurement.gestalt_key
                if authoritative_measurement is not None
                else None
            )
            if (
                persisted_key is None
                or persisted_key.measurement_authority
                != "certified_final_mesh"
                or key is None
            ):
                add(
                    "gestalt.certified_final_mesh_evidence_missing",
                    f"row[{index}].certified_gestalt_key",
                    "complete certified_final_mesh descriptor",
                    payload.get("measurement_authority"),
                )
            gestalt_keys.append(key)
            mesh_evidence = (
                row.get("certified_mesh_evidence")
                if isinstance(row.get("certified_mesh_evidence"), dict)
                else {}
            )
            mesh_issues = validate_certified_mesh_gestalt_evidence(
                mesh_evidence,
                expected_visual_hash=identities[index]["visual_hash"],
                expected_exact_mesh_payload_hash=str(
                    authoritative_measurement.exact_mesh_payload_hash
                    if authoritative_measurement is not None
                    else ""
                ),
                expected_morphology_payload_hash=str(
                    certified_mesh_morphology_payload_hash(
                        authoritative_measurement.morphology
                    )
                    if authoritative_measurement is not None
                    else ""
                ),
                gestalt_payload=payload,
            )
            if mesh_issues:
                add(
                    "gestalt.certified_mesh_evidence_invalid",
                    f"row[{index}].certified_mesh_evidence",
                    (
                        "hash-bound certified projected visual mesh "
                        "gestalt and morphology"
                    ),
                    list(mesh_issues),
                )
            certified_morphologies.append(
                dict(authoritative_measurement.morphology)
                if authoritative_measurement is not None
                else {}
            )
        stepped_count = sum(
            key.visible_stepped
            for key in gestalt_keys
            if key is not None
        )
        body_counts = Counter(
            str(item.get("body_phenotype") or "")
            for item in certified_morphologies
        )
        body_counts.pop("", None)
        roof_counts = Counter(
            str(item.get("roof_archetype") or "")
            for item in certified_morphologies
        )
        roof_counts.pop("", None)
        chassis_counts = Counter(
            str(item.get("chassis_family") or "")
            for item in certified_morphologies
        )
        chassis_counts.pop("", None)
        plan_counts = Counter(
            str(item.get("plan_family") or "")
            for item in certified_morphologies
        )
        plan_counts.pop("", None)
        pair_certificate = (
            raw_program.get("selected_pair_certificate")
            if isinstance(
                raw_program.get("selected_pair_certificate"),
                dict,
            )
            else {}
        )
        certificate_pairs = {}
        certificate_pair_rows = [
            pair
            for pair in pair_certificate.get("pairs") or ()
            if isinstance(pair, dict)
        ]
        for pair in certificate_pair_rows:
            pair_id = frozenset({
                str(pair.get("left_variant_id") or ""),
                str(pair.get("right_variant_id") or ""),
            })
            if len(pair_id) == 2 and pair_id not in certificate_pairs:
                certificate_pairs[pair_id] = pair
        expected_pair_count = len(rows) * (len(rows) - 1) // 2
        if (
            pair_certificate.get("schema_version")
            != "arr.maas.competition_gestalt_pair_certificate.v1"
            or pair_certificate.get("expected_pair_count")
            != expected_pair_count
            or pair_certificate.get("hard_pass") is not True
        ):
            add(
                "gestalt.pair_certificate_invalid",
                "selected_pair_certificate",
                {
                    "schema_version": (
                        "arr.maas.competition_gestalt_pair_certificate.v1"
                    ),
                    "expected_pair_count": expected_pair_count,
                    "hard_pass": True,
                },
                {
                    "schema_version": pair_certificate.get(
                        "schema_version"
                    ),
                    "expected_pair_count": pair_certificate.get(
                        "expected_pair_count"
                    ),
                    "hard_pass": pair_certificate.get("hard_pass"),
                },
            )
        if (
            pair_certificate.get("measurement_authority")
            != "certified_final_mesh"
            or pair_certificate.get("pair_count") != expected_pair_count
            or len(certificate_pairs) != expected_pair_count
        ):
            add(
                "gestalt.pair_certificate_incomplete",
                "selected_pair_certificate",
                {
                    "measurement_authority": "certified_final_mesh",
                    "pair_count": expected_pair_count,
                },
                {
                    "measurement_authority": pair_certificate.get(
                        "measurement_authority"
                    ),
                    "pair_count": pair_certificate.get("pair_count"),
                    "unique_pair_count": len(certificate_pairs),
                },
            )
        recomputed_pair_count = 0
        for right_index, right_key in enumerate(gestalt_keys):
            for left_index in range(right_index):
                left_key = gestalt_keys[left_index]
                if left_key is None or right_key is None:
                    continue
                recomputed_pair_count += 1
                same_body = (
                    certified_morphologies[left_index].get(
                        "body_phenotype"
                    )
                    == certified_morphologies[right_index].get(
                        "body_phenotype"
                    )
                )
                same_roof = (
                    certified_morphologies[left_index].get(
                        "roof_archetype"
                    )
                    == certified_morphologies[right_index].get(
                        "roof_archetype"
                    )
                )
                required_distance = (
                    contract.shared_language_minimum_composite_distance
                    if same_body or same_roof
                    else contract.minimum_pair_distance
                )
                measured_distance = competition_gestalt_distance(
                    left_key,
                    right_key,
                )
                pair_axis = (
                    f"{identities[left_index]['variant_id']}:"
                    f"{identities[right_index]['variant_id']}"
                )
                if measured_distance < required_distance:
                    add(
                        "gestalt.pair_distance_below_contract",
                        pair_axis,
                        {"minimum": required_distance},
                        {"distance": measured_distance},
                    )
                certificate_pair = certificate_pairs.get(frozenset({
                    identities[left_index]["variant_id"],
                    identities[right_index]["variant_id"],
                }))
                try:
                    certificate_distance = float(
                        (certificate_pair or {}).get("distance")
                    )
                    certificate_required = float(
                        (certificate_pair or {}).get(
                            "required_distance"
                        )
                    )
                except (TypeError, ValueError):
                    certificate_distance = -1.0
                    certificate_required = -1.0
                certificate_valid = bool(
                    certificate_pair
                    and isfinite(certificate_distance)
                    and isfinite(certificate_required)
                    and abs(
                        certificate_distance - measured_distance
                    ) <= 1e-8
                    and abs(
                        certificate_required - required_distance
                    ) <= 1e-8
                    and certificate_pair.get(
                        "same_body_phenotype"
                    ) is same_body
                    and certificate_pair.get(
                        "same_roof_archetype"
                    ) is same_roof
                    and certificate_pair.get("hard_pass") is (
                        measured_distance >= required_distance
                    )
                )
                if (
                    isfinite(certificate_distance)
                    and abs(
                        certificate_distance - measured_distance
                    ) > 1e-8
                ):
                    add(
                        "gestalt.pair_certificate_distance_mismatch",
                        pair_axis,
                        measured_distance,
                        certificate_distance,
                    )
                if not certificate_valid:
                    add(
                        "gestalt.pair_certificate_invalid",
                        pair_axis,
                        {
                            "distance": measured_distance,
                            "required_distance": required_distance,
                            "same_body_phenotype": same_body,
                            "same_roof_archetype": same_roof,
                            "hard_pass": (
                                measured_distance >= required_distance
                            ),
                        },
                        certificate_pair or {},
                    )
        if recomputed_pair_count != expected_pair_count:
            add(
                "gestalt.recomputed_pair_count_mismatch",
                "selected_pair_certificate",
                expected_pair_count,
                recomputed_pair_count,
            )

        selected_count = int(raw_program.get("selected_count") or 0)
        if (
            solver_evidence["target_count"] != contract.target_count
            or solver_evidence["selected_count"] != contract.target_count
            or solver_evidence["target_reached"] is not True
            or solver_evidence["deficits"]
        ):
            add(
                "solver.target_twenty_not_certified",
                "portfolio_contract_solver",
                {
                    "target_count": contract.target_count,
                    "selected_count": contract.target_count,
                    "target_reached": True,
                    "deficits": [],
                },
                solver_evidence,
            )
        if (
            solver_evidence["compatibility_threshold"]
            != contract.minimum_pair_distance
        ):
            add(
                "solver.compatibility_threshold_mismatch",
                "minimum_pair_distance",
                contract.minimum_pair_distance,
                solver_evidence["compatibility_threshold"],
            )
        if selected_count != contract.target_count:
            add(
                "selection.selected_count_mismatch",
                "selected_count",
                contract.target_count,
                selected_count,
            )
        if len(rows) != contract.target_count:
            add(
                "manifest.row_count_mismatch",
                "row_count",
                contract.target_count,
                len(rows),
            )
        for field in ("program_hash", "geometry_hash", "visual_hash"):
            values = [
                str(identity.get(field) or "").strip()
                for identity in identities
            ]
            if len(values) != len(set(values)):
                add(
                    f"identity.duplicate_{field}",
                    field,
                    {"unique_count": contract.target_count},
                    {"unique_count": len(set(values))},
                )
        legal_floor_field_hashes = {
            str(identity.get("legal_floor_field_hash") or "").strip()
            for identity in identities
            if str(identity.get("legal_floor_field_hash") or "").strip()
        }
        floor_plan = (
            raw_program.get("floor_capacity_plan")
            if isinstance(raw_program.get("floor_capacity_plan"), dict)
            else {}
        )
        trusted_legal_floor_field = (
            floor_plan.get("legal_floor_field")
            if isinstance(floor_plan.get("legal_floor_field"), dict)
            else {}
        )
        trusted_legal_floor_field_hash = str(
            floor_plan.get("legal_floor_field_hash") or ""
        ).strip()
        trusted_floor_field_valid = bool(
            validate_legal_floor_field(trusted_legal_floor_field)
            and trusted_legal_floor_field.get("legal_floor_field_hash")
            == trusted_legal_floor_field_hash
        )
        if (
            not trusted_floor_field_valid
            or legal_floor_field_hashes
            != {trusted_legal_floor_field_hash}
        ):
            add(
                "identity.legal_floor_field_not_shared_or_trusted",
                "legal_floor_field_hash",
                {
                    "unique_count": 1,
                    "trusted_hash": trusted_legal_floor_field_hash,
                    "trusted_field_valid": True,
                },
                {
                    "unique_count": len(legal_floor_field_hashes),
                    "hashes": sorted(legal_floor_field_hashes),
                    "trusted_field_valid": trusted_floor_field_valid,
                },
            )
        expected_capacity = dict(contract.capacity_band_exact_counts)
        capacity_band_objective = {
            "expected_exact_counts": expected_capacity,
            "actual_counts": dict(sorted(capacity_counts.items())),
            "objective_met": dict(capacity_counts) == expected_capacity,
            "hard_gate_effect": "none_diagnostic_only",
        }
        expected_scopes = set(contract.base_scopes)
        if (
            set(scope_counts) != expected_scopes
            or any(
                count < contract.base_scope_minimum_each
                or (
                    contract.base_scope_maximum_each is not None
                    and count > contract.base_scope_maximum_each
                )
                for count in scope_counts.values()
            )
        ):
            add(
                "quota.base_scope_outside_range",
                "base_scope",
                {
                    "cells": list(contract.base_scopes),
                    "minimum_each": contract.base_scope_minimum_each,
                    "maximum_each": contract.base_scope_maximum_each,
                },
                dict(sorted(scope_counts.items())),
            )
        if not (
            stepped_count >= contract.visible_stepped_minimum
            and (
                contract.visible_stepped_maximum is None
                or stepped_count <= contract.visible_stepped_maximum
            )
        ):
            add(
                "quota.visible_stepped_outside_range",
                "visible_stepped",
                {
                    "minimum": contract.visible_stepped_minimum,
                    "maximum": contract.visible_stepped_maximum,
                },
                stepped_count,
            )
        for axis, counts, minimum_distinct, maximum_each in (
            (
                "body_phenotype",
                body_counts,
                contract.body_phenotype_minimum_distinct,
                contract.body_phenotype_maximum_each,
            ),
            (
                "roof_archetype",
                roof_counts,
                contract.roof_archetype_minimum_distinct,
                contract.roof_archetype_maximum_each,
            ),
            (
                "chassis_family",
                chassis_counts,
                contract.chassis_family_minimum_distinct,
                contract.chassis_family_maximum_each,
            ),
            (
                "plan_family",
                plan_counts,
                contract.plan_family_minimum_distinct,
                contract.plan_family_maximum_each,
            ),
        ):
            if (
                len(counts) < minimum_distinct
                or (
                    maximum_each is not None
                    and max(counts.values(), default=0) > maximum_each
                )
            ):
                add(
                    f"quota.{axis}_outside_contract",
                    axis,
                    {
                        "minimum_distinct": minimum_distinct,
                        "maximum_each": maximum_each,
                    },
                    dict(sorted(counts.items())),
                )
        operation_count = len({
            str(
                row.get("book_principle_id")
                or row.get("book_operation")
                or ""
            )
            for row in rows
            if str(
                row.get("book_principle_id")
                or row.get("book_operation")
                or ""
            )
        })
        if operation_count < 10:
            add(
                "quota.book_principle_count_below_10",
                "book_principle",
                {"minimum_distinct": 10},
                operation_count,
            )
        void_or_courtyard_count = sum(
            int(item.get("solid_genus") or 0) > 0
            or str(item.get("body_phenotype") or "").lower()
            == "voided"
            or str(item.get("plan_family") or "").lower()
            == "courtyard"
            for item in certified_morphologies
        )
        winged_or_curved_count = sum(
            item.get("winged_or_curved") is True
            for item in certified_morphologies
        )
        wedge_count = sum(
            item.get("wedge_like") is True
            for item in certified_morphologies
        )
        pyramid_count = sum(
            item.get("pyramidal_like") is True
            for item in certified_morphologies
        )
        for code, axis, expected, actual in (
            (
                "quota.void_or_courtyard_below_3",
                "void_or_courtyard",
                {"minimum": 3},
                void_or_courtyard_count,
            ),
            (
                "quota.winged_or_curved_below_3",
                "winged_or_curved",
                {"minimum": 3},
                winged_or_curved_count,
            ),
            (
                "quota.wedge_above_2",
                "wedge_like",
                {"maximum": 2},
                wedge_count,
            ),
            (
                "quota.pyramid_above_2",
                "pyramidal_like",
                {"maximum": 2},
                pyramid_count,
            ),
        ):
            failed = (
                actual < expected["minimum"]
                if "minimum" in expected
                else actual > expected["maximum"]
            )
            if failed:
                add(code, axis, expected, actual)
        downstream = raw_program.get("downstream_hard_gate")
        for index, row in enumerate(rows):
            for field in (
                "inside_site",
                "program_hard_pass",
            ):
                if row.get(field) is not True:
                    add(
                        f"hard_gate.{field}_not_pass",
                        f"row[{index}].{field}",
                        True,
                        row.get(field),
                    )
            if row.get("law_graph_evidence_hard_pass") is not True:
                add(
                    "hard_gate.law_graph_not_pass",
                    f"row[{index}].law_graph_evidence_hard_pass",
                    True,
                    row.get("law_graph_evidence_hard_pass"),
                )
            legal_projection = (
                row.get("legal_projection")
                if isinstance(row.get("legal_projection"), dict)
                else {}
            )
            if (
                legal_projection.get("evaluated") is not True
                or legal_projection.get("hard_pass") is not True
                or str(
                    legal_projection.get("status") or ""
                ).lower() not in {"pass", "passed"}
            ):
                add(
                    "hard_gate.legal_projection_not_pass",
                    f"row[{index}].legal_projection",
                    {
                        "evaluated": True,
                        "hard_pass": True,
                        "status": "pass",
                    },
                    legal_projection,
                )
            identity = identities[index]
            parking_gate = (
                row.get("parking_hard_gate")
                if isinstance(row.get("parking_hard_gate"), dict)
                else {}
            )
            parking_source = str(
                parking_gate.get("rule_repository_source")
                or row.get("parking_rule_source")
                or ""
            )
            parking_graph_status = str(
                parking_gate.get("graph_status")
                or row.get("parking_graph_status")
                or ""
            )
            if (
                parking_gate.get("evaluated") is not True
                or parking_gate.get("hard_pass") is not True
                or not parking_source
                or parking_graph_status != "available"
            ):
                add(
                    "hard_gate.parking_graph_rule_not_pass",
                    f"row[{index}].parking_hard_gate",
                    {
                        "evaluated": True,
                        "hard_pass": True,
                        "rule_repository_source": "resolved",
                        "graph_status": "available",
                    },
                    {
                        "evaluated": parking_gate.get("evaluated"),
                        "hard_pass": parking_gate.get("hard_pass"),
                        "rule_repository_source": parking_source,
                        "graph_status": parking_graph_status,
                    },
                )
            for field in (
                "program_hash",
                "geometry_hash",
                "visual_hash",
                "floor_capacity_plan_hash",
                "legal_floor_field_hash",
                "candidate_actual_gfa_stop_hash",
            ):
                value = str(identity[field] or "").strip()
                if not value or "UNRESOLVED" in value.upper():
                    add(
                        f"identity.{field}_missing",
                        f"row[{index}].{field}",
                        "non-empty resolved hash",
                        value,
                    )
            try:
                law_identity = ExecutionIdentity(
                    execution_id=str(
                        row.get("selected_execution_id") or ""
                    ),
                    program_hash=identity["program_hash"],
                    geometry_hash=identity["geometry_hash"],
                    floor_capacity_plan_hash=identity[
                        "floor_capacity_plan_hash"
                    ],
                    pnu=str(summary.get("pnu") or ""),
                )
                law_issues = validate_persisted_law_agent_evidence(
                    (
                        row.get("law_graph_agent_evidence")
                        if isinstance(
                            row.get("law_graph_agent_evidence"),
                            dict,
                        )
                        else None
                    ),
                    str(row.get("law_graph_evidence_hash") or ""),
                    expected_identity=law_identity,
                )
                law_payload = row.get("law_graph_agent_evidence") or {}
                law_evidence = (
                    law_payload.get("evidence")
                    if isinstance(law_payload, dict)
                    and isinstance(law_payload.get("evidence"), dict)
                    else {}
                )
                neo4j = (
                    law_evidence.get("neo4j")
                    if isinstance(law_evidence.get("neo4j"), dict)
                    else {}
                )
                if neo4j.get("available") is not True:
                    law_issues = tuple(law_issues) + (
                        "law_agent_neo4j_unavailable",
                    )
            except (TypeError, ValueError):
                law_issues = ("law_agent_expected_identity_invalid",)
            if law_issues:
                add(
                    "hard_gate.law_graph_payload_invalid",
                    f"row[{index}].law_graph_agent_evidence",
                    "valid exact-identity law payload with Neo4j available",
                    list(law_issues),
                )
            passport = (
                row.get("mass_execution_passport")
                if isinstance(
                    row.get("mass_execution_passport"),
                    dict,
                )
                else {}
            )
            render_evidence = (
                row.get("archive_render_evidence")
                if isinstance(
                    row.get("archive_render_evidence"),
                    dict,
                )
                else {}
            )
            passport_bindings = (
                ("program_hash", "program_hash"),
                (
                    "floor_capacity_plan_hash",
                    "floor_capacity_plan_hash",
                ),
                (
                    "final_legal_geometry_hash",
                    "geometry_hash",
                ),
                ("geometry_hash", "visual_hash"),
                ("visual_hash", "visual_hash"),
                (
                    "legal_floor_field_hash",
                    "legal_floor_field_hash",
                ),
                (
                    "candidate_actual_gfa_stop_hash",
                    "candidate_actual_gfa_stop_hash",
                ),
            )
            for passport_field, identity_field in passport_bindings:
                passport_value = str(
                    passport.get(passport_field) or ""
                ).strip()
                if not passport_value:
                    add(
                        f"identity.passport_{passport_field}_missing",
                        f"row[{index}].mass_execution_passport."
                        f"{passport_field}",
                        "non-empty exact hash",
                        passport_value,
                    )
                elif passport_value != identity[identity_field]:
                    add(
                        f"identity.passport_{passport_field}_mismatch",
                        f"row[{index}].mass_execution_passport."
                        f"{passport_field}",
                        identity[identity_field],
                        passport_value,
                    )
            expected_geometry_hash = str(
                render_evidence.get("final_legal_geometry_hash")
                or passport.get("final_legal_geometry_hash")
                or ""
            )
            if expected_geometry_hash != identity["geometry_hash"]:
                add(
                    "identity.geometry_hash_mismatch",
                    f"row[{index}].geometry_hash",
                    expected_geometry_hash or "render/passport identity",
                    identity["geometry_hash"],
                )
            expected_visual_hash = str(
                render_evidence.get(
                    "projected_visual_geometry_hash"
                )
                or ""
            )
            if expected_visual_hash != identity["visual_hash"]:
                add(
                    "identity.visual_hash_mismatch",
                    f"row[{index}].visual_hash",
                    expected_visual_hash or "render identity",
                    identity["visual_hash"],
                )
            stop_certificate = (
                row.get("candidate_actual_gfa_stop_certificate")
                if isinstance(
                    row.get("candidate_actual_gfa_stop_certificate"),
                    dict,
                )
                else passport.get("candidate_actual_gfa_stop_certificate")
                if isinstance(
                    passport.get("candidate_actual_gfa_stop_certificate"),
                    dict,
                )
                else {}
            )
            passport_stop_certificate = (
                passport.get("candidate_actual_gfa_stop_certificate")
                if isinstance(
                    passport.get(
                        "candidate_actual_gfa_stop_certificate"
                    ),
                    dict,
                )
                else {}
            )
            target_gfa = row.get("candidate_target_gfa_m2")
            stop_valid = bool(
                trusted_floor_field_valid
                and stop_certificate == passport_stop_certificate
                and validate_candidate_actual_gfa_stop_certificate(
                    stop_certificate,
                    legal_floor_field=trusted_legal_floor_field,
                    expected_legal_floor_field_hash=(
                        trusted_legal_floor_field_hash
                    ),
                    expected_pnu=str(summary.get("pnu") or ""),
                    expected_identity={
                        "program_hash": identity["program_hash"],
                        "final_geometry_hash": identity["geometry_hash"],
                        "visual_hash": identity["visual_hash"],
                    },
                    expected_target=target_gfa,
                )
                and stop_certificate.get(
                    "candidate_actual_gfa_stop_hash"
                )
                == identity["candidate_actual_gfa_stop_hash"]
            )
            if stop_valid:
                candidate_actual_gfa_stop_valid_count += 1
            if not stop_valid:
                add(
                    "identity.actual_gfa_stop_invalid",
                    f"row[{index}].candidate_actual_gfa_stop_certificate",
                    "valid final-mesh stop certificate bound to trusted field",
                    {
                        "hash": identity[
                            "candidate_actual_gfa_stop_hash"
                        ],
                        "target_gfa_m2": target_gfa,
                    },
                )

        contract_metrics = {
            "selected_count": selected_count,
            "row_count": len(rows),
            "book_principle_count": operation_count,
            "visible_stepped_count": stepped_count,
            "body_phenotype_distinct_count": len(body_counts),
            "roof_archetype_distinct_count": len(roof_counts),
            "chassis_family_distinct_count": len(chassis_counts),
            "plan_family_distinct_count": len(plan_counts),
            "combined_hard_pass_count": sum(
                row.get("combined_hard_pass") is True for row in rows
            ),
            "law_graph_hard_pass_count": sum(
                row.get("law_graph_evidence_hard_pass") is True
                for row in rows
            ),
            "identity_complete_count": sum(
                all(
                    str(identity[field] or "").strip()
                    and "UNRESOLVED"
                    not in str(identity[field]).upper()
                    for field in (
                        "program_hash",
                        "geometry_hash",
                        "visual_hash",
                        "floor_capacity_plan_hash",
                        "legal_floor_field_hash",
                        "candidate_actual_gfa_stop_hash",
                    )
                )
                for identity in identities
            ),
            "shared_legal_floor_field_hash": (
                trusted_legal_floor_field_hash
                if trusted_floor_field_valid
                and legal_floor_field_hashes
                == {trusted_legal_floor_field_hash}
                else ""
            ),
            "shared_legal_floor_field_hash_count": len(
                legal_floor_field_hashes
            ),
            "candidate_actual_gfa_stop_valid_count": (
                candidate_actual_gfa_stop_valid_count
            ),
            "candidate_actual_gfa_stop_hashes": [
                identity["candidate_actual_gfa_stop_hash"]
                for identity in identities
                if identity["candidate_actual_gfa_stop_hash"]
            ],
            "candidate_floor_count_distribution": dict(
                sorted(Counter(
                    int(row.get("candidate_floor_count") or 0)
                    for row in rows
                    if int(row.get("candidate_floor_count") or 0) > 0
                ).items())
            ),
            "solver_evidence": solver_evidence,
            "recomputed_certified_mesh_pair_count": recomputed_pair_count,
        }
        program_evidence.append({
            "program": slug,
            "status": "pass" if not program_deficits else "fail",
            "target_count": contract.target_count,
            "contract_metrics": contract_metrics,
            "quota_evidence": {
                "capacity_band_objective": capacity_band_objective,
                "capacity_band_counts": dict(
                    sorted(capacity_counts.items())
                ),
                "base_scope_counts": dict(sorted(scope_counts.items())),
                "body_phenotype_counts": dict(
                    sorted(body_counts.items())
                ),
                "roof_archetype_counts": dict(
                    sorted(roof_counts.items())
                ),
                "chassis_family_counts": dict(
                    sorted(chassis_counts.items())
                ),
                "plan_family_counts": dict(
                    sorted(plan_counts.items())
                ),
            },
            "aggregate_diagnostics": {
                "hard_gate_effect": "none_diagnostic_only",
                "program_status": str(raw_program.get("status") or ""),
                "portfolio_completion": deepcopy(completion),
                "downstream_hard_gate": (
                    deepcopy(downstream)
                    if isinstance(downstream, dict)
                    else {}
                ),
                "combined_hard_pass_count": sum(
                    row.get("combined_hard_pass") is True
                    for row in rows
                ),
            },
            "identity_hashes": identities,
            "typed_failure_deficits": program_deficits,
        })
    if not program_evidence:
        all_deficits.append(_publishable_deficit(
            code="manifest.no_program_results",
            program="",
            axis="programs",
            expected="at least one target-20 program",
            actual=0,
        ))
    if summary.get("diagnostic_only") is True:
        all_deficits.append(_publishable_deficit(
            code="mode.diagnostic_summary_forbidden",
            program="",
            axis="diagnostic_only",
            expected=False,
            actual=True,
        ))
    normalized_timings = {}
    for phase in (
        "pnu_context",
        "breadth_enumeration",
        "cheap_screen",
        "exact_compile",
        "law",
        "parking",
        "solver",
        "render",
        "total",
    ):
        raw_duration = phase_durations_seconds.get(phase)
        try:
            duration = float(raw_duration)
        except (TypeError, ValueError):
            duration = -1.0
        if not isfinite(duration) or duration <= 0.0:
            all_deficits.append(_publishable_deficit(
                code=f"timing.{phase}_missing",
                program="",
                axis=f"phase_durations_seconds.{phase}",
                expected="finite positive duration in seconds",
                actual=raw_duration,
            ))
            continue
        normalized_timings[phase] = duration
    evidence = {
        "schema_version": "arr.maas.publishable_20_manifest.v1",
        "status": "pass" if not all_deficits else "fail",
        "target_count": contract.target_count,
        "fail_closed": True,
        "phase_durations_seconds": normalized_timings,
        "programs": program_evidence,
        "typed_failure_deficits": all_deficits,
    }
    return evidence


def persist_publishable_20_result(
    output_dir: Path,
    result: dict,
    *,
    phase_durations_seconds: dict[str, float],
) -> dict:
    """Persist the audited manifest before returning success or failure."""

    evidence = build_publishable_20_manifest_evidence(
        result,
        phase_durations_seconds=phase_durations_seconds,
    )
    result["publishable_20"] = True
    result["publishable_target_count"] = 20
    result["publishable_20_manifest"] = evidence
    result["final_pass"] = evidence["status"] == "pass"
    if evidence["status"] != "pass":
        result["status"] = "fail"
    directory = Path(output_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    persist_book_program_summary(directory, result)
    if evidence["status"] != "pass":
        codes = sorted({
            str(deficit.get("code") or "")
            for deficit in evidence["typed_failure_deficits"]
            if isinstance(deficit, dict) and deficit.get("code")
        })
        raise CommandError(
            "publishable target-20 contract failed: "
            + ", ".join(codes)
        )
    return evidence


def _progressive_provider_budget_lifecycle(method):
    @wraps(method)
    def wrapped(self, *args, **options):
        progressive_target = options.get("progressive_target")
        if progressive_target is None:
            return method(self, *args, **options)
        budget = progressive_mass_run_budget(int(progressive_target))
        with paid_provider_budget_scope(
            budget.total_provider_request_limit,
            quotas=budget.provider_request_quotas,
            run_metadata={"target_count": budget.target_count},
            environment_updates={
                "MAAS_PAID_PROVIDER_MAX_REQUESTS": str(
                    budget.total_provider_request_limit
                ),
                "MAAS_MASS_RUN_TIMEOUT_SECONDS": str(budget.timeout_seconds),
                "MAAS_LIVE_VLM_MAX_REQUESTS": str(
                    budget.live_vlm_request_limit
                ),
            },
        ), live_vlm_request_count_scope():
            return method(self, *args, **options)
    return wrapped


class Command(BaseCommand):
    help = "Compile BOOK-operation portfolios for neighborhood, gym and cultural programs"

    def add_arguments(self, parser):
        parser.add_argument("--pnu", default="1168011800104170004")
        parser.add_argument(
            "--output-dir",
            default="../../docs/playwright/design-route-live-verify/book-program-portfolios",
        )
        parser.add_argument("--program", action="append", choices=("neighborhood", "gymnasium", "cultural"))
        parser.add_argument("--recursive-only", action="store_true")
        parser.add_argument(
            "--publishable-20",
            action="store_true",
            help=(
                "Require the fail-closed competition target-20 contract and "
                "persist its acceptance evidence."
            ),
        )
        parser.add_argument(
            "--diagnostic-target",
            type=int,
            choices=(1, 2, 3, 5, 20),
            default=None,
            help=(
                "Bound a diagnostic-only probe to 1, 2, 3, 5, or 20 rendered "
                "candidates. "
                "This can never claim a completed alternative portfolio."
            ),
        )
        parser.add_argument(
            "--progressive-target",
            type=int,
            choices=(3, 5, 10, 20),
            default=None,
            help=(
                "Run a complete LLM-authored, law/parking, exact-VLM "
                "promotion portfolio for target 3, 5, 10, or 20."
            ),
        )
        parser.add_argument(
            "--smoke",
            action="store_true",
            help=(
                "Run the bounded minimum 10-alternative portfolio search. "
                "Smoke controls cost and search depth, never portfolio completeness."
            ),
        )
        parser.add_argument(
            "--live-vlm",
            action="store_true",
            help=(
                "Run the image-grounded critic and typed repair after the shared "
                "universal form bank, BOOK projection and program projection; "
                "requires MAAS_LIVE_GEOMETRY_VLM=1, "
                "MAAS_LIVE_VLM_CREDENTIAL_ROTATED=1 and OPENAI_API_KEY"
            ),
        )
        parser.add_argument(
            "--live-llm-author",
            action="store_true",
            help=(
                "Make one bounded OpenAI LLM request for typed GeometryProgram/AST "
                "alternatives before BOOK, deterministic law/FAR/parking gates and VLM."
            ),
        )
        parser.add_argument(
            "--agent-authored-manifest",
            default=None,
            help=(
                "Load fail-closed typed GeometryPrograms authored by the "
                "current Codex OAuth LLM session; this path never falls back "
                "to paid or deterministic geometry authorship."
            ),
        )
        parser.add_argument(
            "--agent-authored-session-id",
            default=None,
            help="Trusted current Codex OAuth authoring session ID.",
        )
        parser.add_argument(
            "--agent-authored-request-id",
            default=None,
            help="Trusted Codex OAuth request ID bound to the manifest.",
        )
        parser.add_argument(
            "--agent-authored-manifest-sha256",
            default=None,
            help="Trusted SHA-256 digest of the exact manifest bytes.",
        )
        parser.add_argument(
            "--agent-authored-program-hash",
            action="append",
            default=[],
            help=(
                "Trusted admitted pre-BOOK GeometryProgram SHA-256; repeat "
                "once for each manifest program."
            ),
        )
        parser.add_argument(
            "--agent-authored-replay-program-hash",
            action="append",
            default=[],
            help=(
                "Replay only this admitted pre-BOOK program hash after the "
                "complete source manifest has passed its trust contract; "
                "repeat for each shortlisted program."
            ),
        )
        parser.add_argument("--visual-directive", default=None)
        parser.add_argument(
            "--outcome-graph",
            default=None,
            help=(
                "Explicitly opt into a controlled cross-run typed outcome graph. "
                "By default every output directory owns one isolated causal graph."
            ),
        )

    @tracked_mass_command
    @_progressive_provider_budget_lifecycle
    def handle(self, *args, **options):
        progressive_target = options.get("progressive_target")
        if progressive_target is not None:
            if (
                options.get("publishable_20")
                or options.get("diagnostic_target") is not None
                or options.get("smoke")
            ):
                raise CommandError(
                    "--progressive-target cannot be combined with "
                    "--publishable-20, --diagnostic-target, or --smoke"
                )
            options["live_vlm"] = True
            options["live_llm_author"] = True
        if (
            options.get("publishable_20")
            and options.get("diagnostic_target") is not None
        ):
            raise CommandError(
                "--publishable-20 cannot be combined with --diagnostic-target"
            )
        if options.get("publishable_20") and options.get("smoke"):
            raise CommandError(
                "--publishable-20 cannot be combined with --smoke"
            )
        command_started = perf_counter()
        pnu_context_started = perf_counter()
        pnu = str(options["pnu"])
        if options.get("live_vlm"):
            missing = [
                name for name in (
                    "MAAS_LIVE_GEOMETRY_VLM",
                    "MAAS_LIVE_VLM_CREDENTIAL_ROTATED",
                    "OPENAI_API_KEY",
                )
                if not os.getenv(name)
            ]
            if missing:
                raise CommandError(
                    "--live-vlm requires explicit runtime credentials/opt-in: "
                    + ", ".join(missing)
                )
        boundary = fetch_parcel_boundary(pnu)
        if boundary is None:
            raise CommandError("VWorld parcel boundary is required; no synthetic fallback is allowed")
        try:
            from land.services import land_api, regulation_calculator, road_frontage, zoning_mapper
            from land.services.setback_geometry import compute_setback_lines

            land_info = land_api.get_land_use_info(pnu)
            zones = land_info.get("zones", []) or []
            limits = zoning_mapper.resolve_limits(zones) if zones else {}
            zone_names = [
                item["zone_name"] if isinstance(item, dict) else str(item)
                for item in ((limits or {}).get("zones") or zones)
            ]
            if not zone_names:
                raise ValueError("PNU zoning lookup returned no executable zone")
            regulation = regulation_calculator.calculate_all(
                zone_names,
                land_info=land_info,
                sigungu_code=pnu[:5],
                use_llm_extraction=False,
            )
            constraints = regulations_to_constraints(regulation)
            if not constraints:
                raise ValueError("PNU regulation lookup returned no constraints")
            roads_result = road_frontage.fetch_neighbor_roads(boundary)
            road_frontages = roads_result.get("roads") if isinstance(roads_result, dict) and roads_result.get("success") else []
            neighbors_result = road_frontage.fetch_neighbor_parcels(boundary)
            neighbor_parcels = neighbors_result.get("neighbors") if isinstance(neighbors_result, dict) and neighbors_result.get("success") else []
            setback_lines = compute_setback_lines(
                boundary,
                regulation,
                compute_datum=False,
                road_frontages=road_frontages or [],
                neighbor_parcels=neighbor_parcels or [],
            )
            sunlight_envelope = setback_lines.get("sunlight_envelope")
            widths = []
            frontage_records = []
            metric_site = wgs84_to_utm(geojson_to_polygon(boundary))
            site_center = metric_site.centroid
            for road in road_frontages or []:
                try:
                    width = float(road.get("roadWidthM") or road.get("road_width_m") or 0.0)
                except (TypeError, ValueError):
                    width = 0.0
                if width > 0:
                    widths.append(width)
                shared_edge = road.get("sharedEdge") if isinstance(road, dict) else None
                if not isinstance(shared_edge, list) or len(shared_edge) < 2:
                    continue
                try:
                    metric_edge = wgs84_to_utm(LineString(shared_edge))
                except Exception:
                    continue
                midpoint = metric_edge.centroid
                dx = float(midpoint.x - site_center.x)
                dy = float(midpoint.y - site_center.y)
                frontage_records.append({
                    "side": (
                        ("east" if dx >= 0 else "west")
                        if abs(dx) >= abs(dy)
                        else ("north" if dy >= 0 else "south")
                    ),
                    "shared_length_m": round(float(metric_edge.length), 3),
                    "road_width_m": round(width, 3),
                    "metric_edge": metric_edge,
                })
            primary_frontage = (
                max(frontage_records, key=lambda item: item["shared_length_m"])
                if frontage_records
                else None
            )
            site_access_context = {
                "status": "vworld_neighbor_road" if primary_frontage else "road_frontage_unresolved",
                "primary_access_edge": str((primary_frontage or {}).get("side") or ""),
                "road_width_m": max(widths) if widths else None,
                "frontages": [
                    {key: value for key, value in item.items() if key != "metric_edge"}
                    for item in frontage_records
                ],
            }
            parking_options = {
                "road_context": {
                    "road_width_m": max(widths) if widths else None,
                    "road_frontages": road_frontages or [],
                },
            }
            regulation_evidence = {
                "zones": zone_names,
                "bcr_pct": regulation.get("bcr_pct"),
                "far_pct": regulation.get("far_pct"),
                "height_limit_m": regulation.get("height_limit_m"),
                "adjacent_setback_m": regulation.get("adjacent_setback_m"),
                "building_line_setback_m": regulation.get("building_line_setback_m"),
                "landscaping_min_pct": regulation.get("landscaping_min_pct"),
                "sunlight_applies": regulation.get("sunlight_applies"),
                "road_frontage_count": len(road_frontages or []),
                "neighbor_parcel_count": len(neighbor_parcels or []),
            }
        except Exception as exc:
            raise CommandError(f"live PNU regulation/parking context is required; no synthetic fallback: {exc}") from exc
        site = wgs84_to_utm(geojson_to_polygon(boundary))
        minx, miny, _maxx, _maxy = site.bounds
        local_site = translate(site, xoff=-minx, yoff=-miny)
        site_access_geometry = (
            mapping(translate(primary_frontage["metric_edge"], xoff=-minx, yoff=-miny))
            if primary_frontage is not None
            else None
        )
        parking_options = _with_site_local_parking_frontage(
            parking_options,
            site_access_geometry,
        )
        pnu_context_duration = perf_counter() - pnu_context_started
        agent_authored_manifest_path = (
            Path(str(options["agent_authored_manifest"])).resolve()
            if options.get("agent_authored_manifest")
            else None
        )
        agent_authored_admission = None
        if agent_authored_manifest_path is not None:
            try:
                agent_authored_admission = AgentAuthoredAdmission(
                    authoring_session_id=str(
                        options.get("agent_authored_session_id") or ""
                    ),
                    request_id=str(
                        options.get("agent_authored_request_id") or ""
                    ),
                    manifest_sha256=str(
                        options.get("agent_authored_manifest_sha256") or ""
                    ),
                    admitted_program_hashes=tuple(
                        options.get("agent_authored_program_hash") or ()
                    ),
                )
            except AgentAuthoredSupplyError as exc:
                raise CommandError(
                    "--agent-authored-manifest requires a complete trusted "
                    "Codex admission contract: session ID, request ID, manifest "
                    "SHA-256, and admitted program hashes"
                ) from exc
        result = run_book_program_portfolios(
            local_site,
            pnu=pnu,
            output_dir=Path(options["output_dir"]).resolve(),
            site_origin_utm=(float(minx), float(miny)),
            constraints=constraints,
            regulation_evidence=regulation_evidence,
            sunlight_envelope=sunlight_envelope,
            parking_options=parking_options,
            site_boundary_source="vworld_live_pnu",
            site_access_context=site_access_context,
            site_access_geometry=site_access_geometry,
            program_slugs=tuple(options.get("program") or ()),
            recursive_only=bool(options.get("recursive_only")),
            live_geometry_vlm_revision=bool(options.get("live_vlm")),
            live_llm_author=bool(options.get("live_llm_author")),
            agent_authored_manifest_path=agent_authored_manifest_path,
            agent_authored_admission=agent_authored_admission,
            agent_authored_replay_program_hashes=tuple(
                options.get("agent_authored_replay_program_hash") or ()
            ),
            smoke_mode=bool(options.get("smoke")),
            diagnostic_target=options.get("diagnostic_target"),
            progressive_target=progressive_target,
            visual_directive_path=(
                Path(str(options["visual_directive"])).resolve()
                if options.get("visual_directive")
                else None
            ),
            outcome_graph_path=(
                Path(str(options["outcome_graph"])).resolve()
                if options.get("outcome_graph")
                else None
            ),
        )
        diagnostic_target = options.get("diagnostic_target")
        if diagnostic_target is not None:
            _apply_diagnostic_summary_policy(
                result,
                target=int(diagnostic_target),
            )
            attach_legal_mass_archive_boards(
                result,
                output_dir=Path(options["output_dir"]).resolve(),
            )
            persist_book_program_summary(
                Path(options["output_dir"]).resolve(),
                result,
            )
        if options.get("publishable_20"):
            internal_timings = (
                result.get("phase_durations_seconds")
                if isinstance(
                    result.get("phase_durations_seconds"),
                    dict,
                )
                else {}
            )
            persist_publishable_20_result(
                Path(options["output_dir"]).resolve(),
                result,
                phase_durations_seconds={
                    "pnu_context": pnu_context_duration,
                    **internal_timings,
                    "total": perf_counter() - command_started,
                },
            )
        self.stdout.write(self.style.SUCCESS(
            f"BOOK program portfolios: {result['status']} · "
            + ", ".join(
                (
                    f"{item['program']} {item['selected_count']}/"
                    f"{int(progressive_target) if progressive_target is not None else (int(diagnostic_target) if diagnostic_target is not None else (10 if options.get('smoke') else 20))} "
                    f"({item['book_operation_count']} ops)"
                )
                for item in result["programs"]
            )
        ))
        # Django writes a non-None ``handle`` return value as command output,
        # so returning the structured result here makes ``BaseCommand`` call
        # ``dict.endswith`` after every otherwise-complete benchmark run.
        # The canonical structured result is already persisted in the output
        # directory; the management command must return text or ``None``.
        return None
