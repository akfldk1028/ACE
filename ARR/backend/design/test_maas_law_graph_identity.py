"""Hash-bound law-graph and parking provenance regressions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from design.maas.agents.shared.types import ExecutionIdentity


def _identity(index: int = 1) -> ExecutionIdentity:
    return ExecutionIdentity(
        execution_id=f"book:gym:maas_{index:02d}",
        program_hash=f"{index:064x}",
        geometry_hash=f"{index + 10:064x}",
        floor_capacity_plan_hash=f"{index + 20:064x}",
        pnu="1168011800104170004",
    )


def _passed_law_binding(
    identity: ExecutionIdentity,
) -> tuple[dict, str]:
    from design.maas.agents.law_graph_agent.evidence import (
        canonical_agent_evidence_hash,
        collect_law_agent_evidence,
    )

    evidence = collect_law_agent_evidence(
        identity,
        {"law": {
            "evaluated": True,
            "hard_pass": True,
            "status": "pass",
        }},
        graph_loader=lambda: {
            "graph_status": {"attempted": True, "available": True},
            "articles": [{"id": "article:84"}],
        },
        searcher=lambda query, limit: {
            "attempted": True,
            "available": True,
            "query": query,
            "results": [{"hang_id": "hang:parking"}],
        },
    )
    payload = evidence.to_dict()
    return payload, canonical_agent_evidence_hash(payload)


def _accepted_probe_row(
    identity: ExecutionIdentity,
    *,
    render_hash: str | None = None,
) -> dict:
    payload, evidence_hash = _passed_law_binding(identity)
    return {
        "variant_id": identity.execution_id.rsplit(":", 1)[-1],
        "selected_execution_id": identity.execution_id,
        "final_legal_program_hash": identity.program_hash,
        "final_legal_geometry_hash": identity.geometry_hash,
        "floor_capacity_plan_hash": identity.floor_capacity_plan_hash,
        "law_graph_agent_evidence": payload,
        "law_graph_evidence_hash": evidence_hash,
        "law_graph_evidence_hard_pass": True,
        "combined_hard_pass": True,
        "legal_projection": {
            "evaluated": True,
            "hard_pass": True,
            "shared_floor_contract_hard_pass": True,
            "floor_contract_hash": f"{identity.geometry_hash}-floor",
        },
        "parking_hard_gate": {
            "hard_pass": True,
            "layout_status": "pass",
        },
        "archive_render_evidence": {
            "hard_pass": True,
            "final_legal_geometry_hash": (
                render_hash
                if render_hash is not None
                else identity.geometry_hash
            ),
        },
        "mass_execution_passport": {
            "final_legal_geometry_hash": identity.geometry_hash,
            "law_graph_agent_evidence": deepcopy(payload),
            "law_graph_evidence_hash": evidence_hash,
            "law_graph_evidence_hard_pass": True,
        },
        "geometry_artifact_law_binding": {
            "schema_version": "arr.maas.geometry_artifact_law_binding.v1",
            "identity": identity.to_dict(),
            "law_graph_agent_evidence": deepcopy(payload),
            "law_graph_evidence_hash": evidence_hash,
            "law_graph_evidence_hard_pass": True,
        },
        "elevation_evidence": {
            "final_legal_geometry_hash": identity.geometry_hash,
        },
        "archive": {
            "final_legal_geometry_hash": identity.geometry_hash,
        },
    }


class MaasLawGraphIdentityTest(TestCase):
    def test_source_snapshot_uses_intact_korean_regulation_query(self):
        from design.maas.agents.law_graph_agent.evidence import (
            collect_law_source_snapshot,
        )

        captured = {}

        def searcher(query, limit):
            captured["query"] = query
            return {
                "attempted": True,
                "available": True,
                "query": query,
                "results": [{"hang_id": "hang:capacity"}],
            }

        collect_law_source_snapshot(
            {"building_type": "neighborhood"},
            graph_loader=lambda: {
                "graph_status": {"attempted": True, "available": True},
                "articles": [{"id": "article:84"}],
            },
            searcher=searcher,
        )

        query = captured["query"]
        self.assertIn("\uc6a9\uc801\ub960", query)
        self.assertIn("\uac74\ud3d0\uc728", query)
        self.assertIn("\uc8fc\ucc28", query)
        self.assertNotIn("?", query)
        self.assertNotIn("\ufffd", query)

    def test_three_identities_share_one_source_query_but_get_bound_payloads(self):
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
            collect_law_agent_evidence_batch,
        )

        calls = {"graph": 0, "search": 0}

        def graph_loader():
            calls["graph"] += 1
            return {
                "graph_status": {"attempted": True, "available": True},
                "articles": [{"id": "article:84"}],
            }

        def searcher(query, limit):
            calls["search"] += 1
            return {
                "attempted": True,
                "available": True,
                "query": query,
                "results": [{"hang_id": "hang:parking"}],
            }

        identities = tuple(_identity(index) for index in range(1, 4))
        context = {
            "law": {
                "evaluated": True,
                "hard_pass": True,
                "status": "pass",
                "far_limit": 200.0,
            },
            "building_type": "gym",
        }
        evidence = collect_law_agent_evidence_batch(
            [(identity, context) for identity in identities],
            graph_loader=graph_loader,
            searcher=searcher,
        )

        self.assertEqual(calls, {"graph": 1, "search": 1})
        self.assertEqual(tuple(row.identity for row in evidence), identities)
        self.assertTrue(all(row.status == "passed" for row in evidence))
        self.assertEqual(
            len({canonical_agent_evidence_hash(row.to_dict()) for row in evidence}),
            3,
        )
        self.assertEqual(
            {
                tuple(row.evidence["article_ids"])
                for row in evidence
            },
            {("article:84",)},
        )

    def test_each_identity_field_is_checked_against_the_persisted_payload(self):
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
            collect_law_agent_evidence,
            validate_persisted_law_agent_evidence,
        )

        identity = _identity()
        evidence = collect_law_agent_evidence(
            identity,
            {"law": {
                "evaluated": True,
                "hard_pass": True,
                "status": "pass",
            }},
            graph_loader=lambda: {
                "graph_status": {"attempted": True, "available": True},
                "articles": [{"id": "article:84"}],
            },
            searcher=lambda query, limit: {
                "attempted": True,
                "available": True,
                "query": query,
                "results": [{"hang_id": "hang:parking"}],
            },
        )
        payload = evidence.to_dict()
        claimed_hash = canonical_agent_evidence_hash(payload)

        self.assertEqual(
            validate_persisted_law_agent_evidence(
                payload,
                claimed_hash,
                expected_identity=identity,
            ),
            (),
        )
        mutations = {
            "pnu": "1168011800104670003",
            "program_hash": "a" * 64,
            "floor_capacity_plan_hash": "b" * 64,
            "geometry_hash": "c" * 64,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                issues = validate_persisted_law_agent_evidence(
                    payload,
                    claimed_hash,
                    expected_identity=replace(identity, **{field: value}),
                )
                self.assertIn(f"law_agent_identity_mismatch:{field}", issues)

        tampered = deepcopy(payload)
        tampered["identity"]["geometry_hash"] = "d" * 64
        self.assertIn(
            "law_agent_payload_hash_mismatch",
            validate_persisted_law_agent_evidence(
                tampered,
                claimed_hash,
                expected_identity=identity,
            ),
        )

    def test_numeric_preflight_status_is_optional_when_boolean_gate_passes(self):
        """The downstream legal gate predates the optional display status."""
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
            collect_law_agent_evidence,
            validate_persisted_law_agent_evidence,
        )

        identity = _identity()
        evidence = collect_law_agent_evidence(
            identity,
            {"law": {
                "evaluated": True,
                "hard_pass": True,
            }},
            graph_loader=lambda: {
                "graph_status": {"attempted": True, "available": True},
                "articles": [{"id": "article:84"}],
            },
            searcher=lambda query, limit: {
                "attempted": True,
                "available": True,
                "query": query,
                "results": [{"hang_id": "hang:parking"}],
            },
        )
        payload = evidence.to_dict()
        self.assertNotIn(
            "status",
            payload["evidence"]["numeric_preflight"],
        )

        self.assertEqual(
            validate_persisted_law_agent_evidence(
                payload,
                canonical_agent_evidence_hash(payload),
                expected_identity=identity,
            ),
            (),
        )

    def test_needs_evidence_fails_selected_product_without_changing_numeric_law(self):
        from design.maas.agents.law_graph_agent.evidence import (
            collect_law_agent_evidence,
        )
        from design.maas.book_language.mass_passport_bridge import (
            persist_selected_law_agent_evidence,
        )

        identity = _identity()
        evidence = collect_law_agent_evidence(
            identity,
            {"law": {
                "evaluated": True,
                "hard_pass": True,
                "status": "pass",
                "far_limit": 200.0,
            }},
            graph_loader=lambda: {
                "graph_status": {"attempted": True, "available": False},
                "articles": [],
            },
            searcher=lambda query, limit: {
                "attempted": True,
                "available": False,
                "query": query,
                "results": [],
            },
        )
        numeric_law = {
            "evaluated": True,
            "hard_pass": True,
            "far_limit": 200.0,
            "constraint_source": "live_pnu_zone_regulation_calculator",
        }
        row = {
            "combined_hard_pass": True,
            "legal_projection": deepcopy(numeric_law),
        }
        passport = {"hard_pass": True}
        artifact = {"hardGates": {"combinedHardPass": True}}

        persisted = persist_selected_law_agent_evidence(
            selected_row=row,
            passport=passport,
            geometry_artifact=artifact,
            evidence=evidence,
            expected_identity=identity,
        )

        self.assertFalse(persisted["law_graph_evidence_hard_pass"])
        self.assertFalse(row["combined_hard_pass"])
        self.assertFalse(artifact["hardGates"]["combinedHardPass"])
        self.assertFalse(passport["law_graph_evidence_hard_pass"])
        self.assertEqual(row["legal_projection"], numeric_law)
        self.assertEqual(
            row["law_graph_agent_evidence"]["status"],
            "needs_evidence",
        )
        self.assertEqual(
            passport["law_graph_agent_evidence"],
            row["law_graph_agent_evidence"],
        )
        self.assertEqual(
            artifact["law_graph_evidence_hash"],
            row["law_graph_evidence_hash"],
        )
        self.assertEqual(
            row["geometry_artifact_law_binding"][
                "law_graph_agent_evidence"
            ],
            passport["law_graph_agent_evidence"],
        )

    def test_verifier_does_not_fabricate_law_hash_from_legal_context(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        summary = summarize_pnu_result({
            "pnu": "1168011800104170004",
            "programs": [{
                "selected_count": 1,
                "downstream_hard_gate": {
                    "legal_context": {
                        "constraint_source": "live_pnu_zone_regulation_calculator",
                        "far_limit_pct": 200.0,
                    },
                },
                "rows": [{
                    "variant_id": "maas_01",
                    "final_legal_geometry_hash": "f" * 64,
                }],
            }],
        })

        self.assertEqual(summary["law_graph_evidence_hashes"], [])
        self.assertEqual(summary["law_graph_missing_count"], 1)
        self.assertFalse(summary["law_graph_evidence_hard_pass"])
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(aggregate_runs_hard_pass([summary]))

    def test_verifier_accepts_complete_explicit_identity_binding(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        identity = _identity()
        row = _accepted_probe_row(identity)
        evidence_hash = row["law_graph_evidence_hash"]
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": identity.pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertTrue(summary["law_graph_evidence_hard_pass"])
        self.assertEqual(
            summary["law_graph_evidence_hashes"],
            [evidence_hash],
        )
        self.assertTrue(aggregate_runs_hard_pass([summary]))

    def test_runner_exit_code_follows_explicit_law_evidence(self):
        from tools.verify_single_authority_mass_pnus import main

        identity = _identity()
        row = _accepted_probe_row(identity)
        valid_result = {
            "status": "diagnostic_only",
            "pnu": identity.pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        }
        missing_result = {
            "pnu": identity.pnu,
            "programs": [{
                "selected_count": 1,
                "rows": [{
                    "variant_id": "maas_01",
                    "final_legal_geometry_hash": identity.geometry_hash,
                }],
            }],
        }

        with TemporaryDirectory() as directory:
            arguments = [
                "--pnu",
                identity.pnu,
                "--output-root",
                directory,
                "--diagnostic-target",
                "1",
            ]
            with patch(
                "tools.verify_single_authority_mass_pnus.run_benchmark",
                return_value=missing_result,
            ):
                self.assertEqual(main(arguments), 1)
            with patch(
                "tools.verify_single_authority_mass_pnus.run_benchmark",
                return_value=valid_result,
            ):
                self.assertEqual(main(arguments), 0)

    def test_valid_law_cannot_bypass_failed_probe_hard_gates(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        rows = [
            _accepted_probe_row(_identity(index))
            for index in range(1, 4)
        ]
        for row in rows:
            row["combined_hard_pass"] = False
            row["parking_hard_gate"]["hard_pass"] = False
        summary = summarize_pnu_result({
            "status": "failed",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 3,
            "programs": [{
                "status": "fail",
                "diagnostic_only": True,
                "selected_count": 3,
                "rows": rows,
                "downstream_hard_gate": {
                    "status": "fail",
                    "rows": rows,
                },
            }],
        })

        self.assertTrue(summary["law_graph_evidence_hard_pass"])
        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        self.assertIn(
            "explicit_result_status_failed",
            summary["bounded_probe_failure_reasons"],
        )
        self.assertIn(
            "selected_row_combined_hard_gate_failed",
            summary["bounded_probe_failure_reasons"],
        )

    def test_distinct_candidates_pass_when_each_row_hash_is_continuous(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        rows = [
            _accepted_probe_row(_identity(1)),
            _accepted_probe_row(_identity(2)),
        ]
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 2,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 2,
                "rows": rows,
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": rows,
                },
            }],
        })

        self.assertEqual(
            summary["final_geometry_hashes"],
            sorted([_identity(1).geometry_hash, _identity(2).geometry_hash]),
        )
        self.assertTrue(summary["final_geometry_hash_agreement"])
        self.assertTrue(summary["bounded_probe_evidence_hard_pass"])
        self.assertTrue(aggregate_runs_hard_pass([summary]))

    def test_one_row_final_hash_mismatch_fails_probe_acceptance(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        row = _accepted_probe_row(
            _identity(),
            render_hash="e" * 64,
        )
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertFalse(summary["final_geometry_hash_agreement"])
        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        self.assertIn(
            "selected_row_final_geometry_identity_mismatch",
            summary["bounded_probe_failure_reasons"],
        )

    def test_missing_optional_archive_channel_is_reported_not_failed(self):
        from tools.verify_single_authority_mass_pnus import (
            summarize_pnu_result,
        )

        row = _accepted_probe_row(_identity())
        row.pop("archive")
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertTrue(summary["final_geometry_hash_agreement"])
        self.assertIn(
            "archive",
            summary["final_geometry_continuity"][0][
                "missing_optional_channels"
            ],
        )

    def test_stale_passport_law_copy_fails_probe_acceptance(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        row = _accepted_probe_row(_identity())
        row["mass_execution_passport"]["law_graph_agent_evidence"][
            "identity"
        ]["geometry_hash"] = "9" * 64
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertFalse(summary["law_graph_evidence_hard_pass"])
        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        reasons = summary["law_graph_continuity_failures"][0]["reasons"]
        self.assertIn("law_agent_passport_payload_mismatch", reasons)

    def test_missing_or_tampered_law_copy_always_fails(self):
        from tools.verify_single_authority_mass_pnus import (
            summarize_pnu_result,
        )

        def missing_passport(row):
            row["mass_execution_passport"].pop(
                "law_graph_agent_evidence"
            )

        def missing_artifact(row):
            row.pop("geometry_artifact_law_binding")

        def tampered_artifact(row):
            row["geometry_artifact_law_binding"][
                "law_graph_agent_evidence"
            ]["identity"]["program_hash"] = "8" * 64

        def tampered_top(row):
            row["law_graph_agent_evidence"]["identity"][
                "floor_capacity_plan_hash"
            ] = "7" * 64

        for label, mutate in (
            ("missing_passport", missing_passport),
            ("missing_artifact", missing_artifact),
            ("tampered_artifact", tampered_artifact),
            ("tampered_top", tampered_top),
        ):
            with self.subTest(label=label):
                row = _accepted_probe_row(_identity())
                mutate(row)
                summary = summarize_pnu_result({
                    "status": "diagnostic_only",
                    "pnu": _identity().pnu,
                    "diagnostic_only": True,
                    "diagnostic_target": 1,
                    "programs": [{
                        "status": "diagnostic_only",
                        "diagnostic_only": True,
                        "selected_count": 1,
                        "rows": [row],
                        "downstream_hard_gate": {
                            "status": "pass",
                            "rows": [row],
                        },
                    }],
                })
                self.assertFalse(
                    summary["law_graph_evidence_hard_pass"]
                )
                self.assertFalse(
                    summary["bounded_probe_evidence_hard_pass"]
                )

    def test_program_fail_status_cannot_pass_diagnostic_probe(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        row = _accepted_probe_row(_identity())
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "fail",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        self.assertIn(
            "program_status_not_diagnostic_only",
            summary["bounded_probe_failure_reasons"],
        )

    def test_non_diagnostic_top_summary_cannot_pass_diagnostic_probe(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        row = _accepted_probe_row(_identity())
        summary = summarize_pnu_result({
            "status": "pass",
            "pnu": _identity().pnu,
            "diagnostic_only": False,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        self.assertIn(
            "top_status_not_diagnostic_only",
            summary["bounded_probe_failure_reasons"],
        )
        self.assertIn(
            "diagnostic_only_flag_missing",
            summary["bounded_probe_failure_reasons"],
        )

    def test_render_hard_gate_must_pass_even_when_hash_matches(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        row = _accepted_probe_row(_identity())
        row["archive_render_evidence"]["hard_pass"] = False
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "diagnostic_only": True,
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        self.assertIn(
            "selected_row_render_hard_gate_failed",
            summary["bounded_probe_failure_reasons"],
        )

    def test_required_shared_floor_contract_cannot_be_false_or_missing(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        for label, floor_value in (
            ("false", False),
            ("missing", None),
        ):
            with self.subTest(shared_floor_contract=label):
                row = _accepted_probe_row(_identity())
                if floor_value is None:
                    row["legal_projection"].pop(
                        "shared_floor_contract_hard_pass"
                    )
                else:
                    row["legal_projection"][
                        "shared_floor_contract_hard_pass"
                    ] = floor_value
                summary = summarize_pnu_result({
                    "status": "diagnostic_only",
                    "pnu": _identity().pnu,
                    "diagnostic_only": True,
                    "diagnostic_target": 1,
                    "programs": [{
                        "status": "diagnostic_only",
                        "diagnostic_only": True,
                        "selected_count": 1,
                        "rows": [row],
                        "downstream_hard_gate": {
                            "status": "pass",
                            "rows": [row],
                        },
                    }],
                })

                self.assertFalse(
                    summary["bounded_probe_evidence_hard_pass"]
                )
                self.assertFalse(aggregate_runs_hard_pass([summary]))
                self.assertIn(
                    "selected_row_shared_floor_contract_failed",
                    summary["bounded_probe_failure_reasons"],
                )

    def test_program_diagnostic_only_flag_is_required(self):
        from tools.verify_single_authority_mass_pnus import (
            aggregate_runs_hard_pass,
            summarize_pnu_result,
        )

        row = _accepted_probe_row(_identity())
        summary = summarize_pnu_result({
            "status": "diagnostic_only",
            "pnu": _identity().pnu,
            "diagnostic_only": True,
            "diagnostic_target": 1,
            "programs": [{
                "status": "diagnostic_only",
                "selected_count": 1,
                "rows": [row],
                "downstream_hard_gate": {
                    "status": "pass",
                    "rows": [row],
                },
            }],
        })

        self.assertFalse(summary["bounded_probe_evidence_hard_pass"])
        self.assertFalse(aggregate_runs_hard_pass([summary]))
        self.assertIn(
            "program_diagnostic_only_flag_missing",
            summary["bounded_probe_failure_reasons"],
        )

    def test_mocked_graph_success_and_local_fallback_report_honest_sources(self):
        from design.maas.parking_requirements import (
            load_parking_requirement_rules,
        )

        rules = {"national": {"parking_appendix1_row_11": {}}, "local": []}
        with (
            patch(
                "design.maas.parking_requirements.GraphDatabase.driver"
            ) as driver_factory,
            patch(
                "design.maas.parking_requirements._load_rules",
                return_value=rules,
            ),
            # The real seed now carries reviewed local ordinance rows (with a
            # source_sha256), which the loader attaches and reports as
            # "neo4j_with_reviewed_local_sources". This test is about the
            # graph source label, so hand it an empty seed.
            patch(
                "design.maas.parking_requirements._load_structured_seed_rules",
                return_value={},
            ),
        ):
            driver = driver_factory.return_value
            driver.session.return_value.__enter__.return_value = object()
            graph = load_parking_requirement_rules(
                options={"use_neo4j": True},
            )

        self.assertEqual(graph["status"], "loaded")
        self.assertEqual(graph["source"], "neo4j")
        self.assertEqual(graph["graph_status"], "available")

        with (
            patch(
                "design.maas.parking_requirements.GraphDatabase.driver"
            ) as driver_factory,
            patch(
                "design.maas.parking_requirements._load_rules",
                return_value=dict(rules),
            ),
            patch(
                "design.maas.parking_requirements._load_structured_seed_rules",
                return_value={"local": [{"pnu_prefix": "41150", "base_rule_id": "r1", "source_sha256": "x"}]},
            ),
        ):
            driver = driver_factory.return_value
            driver.session.return_value.__enter__.return_value = object()
            with_reviewed = load_parking_requirement_rules(
                options={"use_neo4j": True},
            )
        self.assertEqual(with_reviewed["source"], "neo4j_with_reviewed_local_sources")
        with patch(
            "design.maas.parking_requirements.GraphDatabase.driver"
        ) as driver_factory:
            local = load_parking_requirement_rules(options={})
        driver_factory.assert_not_called()
        self.assertEqual(local["source"], "local_structured_seed")
        self.assertEqual(local["graph_status"], "not_requested")

    def test_loaded_rule_provenance_survives_candidate_calculation(self):
        from design.maas.parking_requirements import (
            resolve_candidate_parking_requirement,
        )

        with (
            patch(
                "design.maas.parking_requirements._select_rule",
                return_value={
                    "rule_id": "parking_appendix1_row_11",
                    "source_appendix": "appendix-1",
                },
            ),
            patch(
                "design.maas.parking_requirements.calculate_required_spaces",
                return_value={
                    "status": "computed",
                    "required_spaces": 1,
                    "raw_spaces": 1.0,
                    "rounding_rule": "official_rounding",
                },
            ),
            patch(
                "design.maas.parking_requirements.calculate_accessible_spaces",
                return_value={"status": "computed", "accessible_min": 0},
            ),
        ):
            requirement = resolve_candidate_parking_requirement(
                pnu="1168011800104170004",
                building_type="gym",
                facility_area_m2=300.0,
                rules={"national": {}, "local": []},
                rules_provenance={
                    "source": "neo4j",
                    "graph_status": "available",
                },
            )

        self.assertEqual(requirement["rule_repository_source"], "neo4j")
        self.assertEqual(requirement["graph_status"], "available")
