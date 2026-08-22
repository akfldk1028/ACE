import inspect
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.book_language import portfolio_replenishment
from design.maas.book_language import portfolio_benchmark
from design.maas.book_language.candidate_analysis import _Candidate, _fingerprint
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.projected_visual_contract import (
    final_floorwise_visual_geometry_hash,
)
from design.maas.geometry_language.source_bridge import source_surface_payload_hash
from design.maas.source_geometry.ir import SourceMass, SourceSurface


def _live_candidate(name: str, *, x_offset: float = 0.0) -> _Candidate:
    program = GeometryProgram(
        nodes=(GeometryNode(
            id="mass",
            kind="primitive",
            operator="box",
            parameters={"width": 4.0, "depth": 3.0, "height": 3.0},
            semantic_role="primary_mass",
        ),),
        root_id="mass",
        name=name,
    )
    program_hash = program.program_hash()
    surface = SourceSurface(
        role="final_surface",
        volume_role="primary_mass",
        verb="geometry_program",
        surface_type="profiled_recursive_solid_mesh",
        vertices_m=(
            (x_offset, 0.0, 0.0),
            (x_offset + 4.0, 0.0, 0.0),
            (x_offset, 3.0, 3.0),
        ),
    )
    source = SourceMass(
        name=name,
        footprint=Polygon([
            (x_offset, 0.0),
            (x_offset + 4.0, 0.0),
            (x_offset + 4.0, 3.0),
            (x_offset, 3.0),
        ]),
        surfaces=(surface,),
        metadata={},
    )
    geometry_hash = final_floorwise_visual_geometry_hash(source)
    surface_hash = source_surface_payload_hash(source.surfaces)
    source = replace(source, metadata={
        "final_geometry_hash": geometry_hash,
        "final_program_hash": program_hash,
        "final_surface_payload_hash": surface_hash,
        "geometry_program": program.to_dict(),
        "geometry_program_bridge_evidence": {
            "program_hash": program_hash,
            "geometry_hash": geometry_hash,
            "surface_payload_hash": surface_hash,
        },
        "authored_projection_identity": {
            "schema_version": "arr.maas.authored_projection_identity.v1",
            "hard_pass": True,
        },
        "authored_legal_projection_certificate": {
            "schema_version": "arr.maas.authored_legal_projection_certificate.v1",
            "status": "verified",
            "hard_pass": True,
            "input_authored_program_hash": program_hash,
            "projected_surface_hash": geometry_hash,
            "projected_surface_payload_hash": surface_hash,
        },
        "book_generation_lineage": {
            "schema_version": "arr.maas.book_generation_lineage.v1",
            "stage": "base",
            "parent_key": f"parent:{program_hash}",
        },
        "program_gate_result": {"hard_pass": True},
        "program_review_authority": {
            "hard_pass": True,
            "legal_archive_authority": True,
            "selection_eligible": True,
        },
        "legal_capacity_authority": {"legal_hard_pass": True},
        "shared_floor_contract": {"hard_pass": True},
        "geometry_family": "test_prism",
        "plan_family": "rectilinear",
    })
    return _Candidate(
        principle_id="book:operative:expand",
        principle_kind="base_operative",
        operation="expand",
        sequence=SimpleNamespace(name=name),
        source=source,
        feature={
            "type": "Feature",
            "properties": {
                "book_scope": {"base_volume_label": "1/1"},
                "capacity_alternative_projection": {
                    "alternative_id": "balanced_yield",
                },
            },
        },
        score=0.8,
    )


class ReplenishmentLiveQdReserveTests(SimpleTestCase):
    def setUp(self):
        self.assertIn(
            "reviewed_final_vlm_fingerprints",
            portfolio_replenishment.ReplenishmentCycleResult.__dataclass_fields__,
        )

    def test_two_real_cycles_carry_live_reserve_and_skip_unchanged_final_review(self):
        first = _live_candidate("cycle-1")
        duplicate = _live_candidate("cycle-1")
        new_candidate = _live_candidate("cycle-2-new", x_offset=8.0)
        repaired_candidate = _live_candidate("cycle-1-repair", x_offset=16.0)
        detached_archive_record = {
            "schema_version": "arr.maas.legal_mass_archive.v1",
            "geometry_hash": first.source.metadata["final_geometry_hash"],
            "program_hash": first.source.metadata["final_program_hash"],
        }
        generated = iter(([first], [duplicate, new_candidate]))
        downstream_seen = []
        paid_reviews = []
        final_review_calls = 0

        def program_pool(*_args, **_kwargs):
            return list(next(generated)), {
                "llm_author_request_executed": True,
                "geometry_program_llm_author_stage_counts": {
                    "directed_geometry_materialized": 1,
                },
                "two_phase_base_vlm": {
                    "active": True,
                    "base_vlm_gate": {
                        "required": True,
                        "status": "complete",
                        "reviewed_parent_keys": [],
                        "reviewed_parent_fingerprints": [],
                    },
                },
            }

        def base_review(pool, **_kwargs):
            return list(pool), {
                "reviewed_parent_keys": [],
                "reviewed_parent_fingerprints": [],
            }

        def downstream(pool, **_kwargs):
            downstream_seen.append(list(pool))
            return {
                "rows": [
                    {"combined_hard_pass": True, "semantic_projection_hard_gate": {}}
                    for _candidate in pool
                ],
            }

        def final_review(pool, **_kwargs):
            nonlocal final_review_calls
            final_review_calls += 1
            paid_reviews.append(list(pool))
            repair_pool = [repaired_candidate] if final_review_calls == 1 else []
            repair_gate = {
                "input_count": len(repair_pool),
                "audit_records": [
                    {
                        "hard_pass": False,
                        "final_program_hash": candidate.source.metadata["final_program_hash"],
                        "final_geometry_hash": candidate.source.metadata["final_geometry_hash"],
                        "final_surface_payload_hash": candidate.source.metadata["final_surface_payload_hash"],
                    }
                    for candidate in repair_pool
                ],
            }
            return SimpleNamespace(
                selection_pool=[],
                initial_vlm_gate={"audit_records": []},
                repair_pool=repair_pool,
                repair_vlm_passes=[],
                repair_evidence={"final_book_vlm_gate": repair_gate},
                final_vlm_gate={},
            )

        def run_cycle(index, reserve, reviewed, dispositions=()):
            return portfolio_replenishment.run_replenishment_cycle(
                cycle_index=index,
                parent_variant_index=index,
                retained_selection_pool=[],
                retained_live_qd_reserve=reserve,
                reviewed_final_vlm_fingerprints=reviewed,
                replenishment_work_dispositions=dispositions,
                excluded_parent_keys=set(),
                excluded_parent_fingerprints=set(),
                excluded_program_hashes=set(),
                generation_site=SimpleNamespace(),
                building_type="neighborhood_living",
                height=14.0,
                floors=4,
                generation_context=SimpleNamespace(),
                typed_graph_mutations=[],
                geometry_program_mutations=[],
                synthesis_requests=[],
                outcome_graph=None,
                recursive_only=True,
                target_count=5,
                exact_compile_limit=12,
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                runtime_live_vlm=True,
                live_vlm_selection_required=False,
                base_capacity_contract={},
                trusted_legal_floor_field={},
                trusted_legal_floor_field_hash="",
                trusted_clear_span_floor_plan={},
                capacity_site=SimpleNamespace(),
                output_dir=Path("test-output"),
                program_slug="neighborhood",
                visual_directive={},
                downstream_context={},
                hard_gate_summary=lambda _report, candidates: {
                    "candidate_count": len(candidates),
                },
            )

        with (
            patch.object(portfolio_replenishment, "_program_pool", side_effect=program_pool),
            patch.object(portfolio_replenishment, "audit_book_base_stage_with_vlm", side_effect=base_review),
            patch.object(portfolio_replenishment, "evaluate_accepted_sources_downstream", side_effect=downstream),
            patch.object(portfolio_replenishment, "_bind_final_visual_authority_for_review"),
            patch.object(portfolio_replenishment, "run_final_vlm_cycle", side_effect=final_review),
        ):
            cycle_1 = run_cycle(1, [], set())
            cycle_2 = run_cycle(
                2,
                [*cycle_1.live_qd_reserve, detached_archive_record],
                cycle_1.reviewed_final_vlm_fingerprints,
                cycle_1.replenishment_work_dispositions,
            )

        first_fingerprint = _fingerprint(first)
        new_fingerprint = _fingerprint(new_candidate)
        repaired_fingerprint = _fingerprint(repaired_candidate)
        self.assertEqual(cycle_1.live_qd_reserve, [first])
        self.assertEqual(len(cycle_2.live_qd_reserve), 2)
        self.assertIs(cycle_2.live_qd_reserve[0], first)
        self.assertNotIn(detached_archive_record, cycle_2.live_qd_reserve)
        self.assertEqual(downstream_seen[0], [first])
        self.assertEqual(downstream_seen[1], [new_candidate])
        self.assertEqual(paid_reviews, [[first], [new_candidate]])
        self.assertEqual(
            cycle_1.reviewed_final_vlm_fingerprints,
            {first_fingerprint, repaired_fingerprint},
        )
        self.assertEqual(
            cycle_2.reviewed_final_vlm_fingerprints,
            {first_fingerprint, repaired_fingerprint, new_fingerprint},
        )

    def test_reserve_rejects_tampered_live_surface_program_and_certificate(self):
        valid = _live_candidate("valid")
        tampered_surface = replace(
            valid,
            source=replace(valid.source, surfaces=(SourceSurface(
                role="tampered",
                volume_role="primary_mass",
                verb="geometry_program",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=((0.0, 0.0, 0.0), (9.0, 0.0, 0.0), (0.0, 9.0, 9.0)),
            ),)),
        )
        bad_program_metadata = dict(valid.source.metadata)
        bad_program_metadata["final_program_hash"] = "forged-program-hash"
        tampered_program = replace(
            valid,
            source=replace(valid.source, metadata=bad_program_metadata),
        )
        bad_certificate_metadata = dict(valid.source.metadata)
        bad_certificate_metadata["authored_legal_projection_certificate"] = {
            **bad_certificate_metadata["authored_legal_projection_certificate"],
            "projected_surface_hash": "forged-geometry-hash",
        }
        tampered_certificate = replace(
            valid,
            source=replace(valid.source, metadata=bad_certificate_metadata),
        )

        reserve = portfolio_replenishment._merge_live_qd_reserve(
            [],
            [valid, tampered_surface, tampered_program, tampered_certificate],
        )

        self.assertEqual(reserve, [valid])

    def test_benchmark_loop_uses_live_state_boundary_to_forward_and_refresh(self):
        self.assertTrue(
            hasattr(portfolio_benchmark, "_ReplenishmentLiveState"),
            "benchmark replenishment live-state boundary is missing",
        )
        current_candidate = _live_candidate("current")
        next_candidate = _live_candidate("next", x_offset=8.0)
        current_fingerprint = _fingerprint(current_candidate)
        next_fingerprint = _fingerprint(next_candidate)
        state = portfolio_benchmark._ReplenishmentLiveState(
            live_qd_reserve=(current_candidate,),
            reviewed_final_vlm_fingerprints=frozenset({current_fingerprint}),
        )
        received = {}
        cycle_result = SimpleNamespace(
            live_qd_reserve=[next_candidate],
            reviewed_final_vlm_fingerprints={
                current_fingerprint,
                next_fingerprint,
            },
        )

        def cycle_boundary(cycle_function, **kwargs):
            received.update(kwargs)
            self.assertIs(cycle_function, portfolio_replenishment.run_replenishment_cycle)
            return cycle_result

        cycle, next_state = (
            portfolio_benchmark._run_replenishment_cycle_with_live_state(
                cycle_boundary,
                portfolio_replenishment.run_replenishment_cycle,
                state=state,
                exact_compile_remaining=7,
            )
        )

        self.assertIs(cycle, cycle_result)
        self.assertEqual(
            received["retained_live_qd_reserve"],
            [current_candidate],
        )
        self.assertEqual(
            received["reviewed_final_vlm_fingerprints"],
            {current_fingerprint},
        )
        self.assertEqual(next_state.live_qd_reserve, (next_candidate,))
        self.assertEqual(
            next_state.reviewed_final_vlm_fingerprints,
            frozenset({current_fingerprint, next_fingerprint}),
        )
        loop_source = inspect.getsource(
            portfolio_benchmark.run_book_program_portfolios
        )
        self.assertIn(
            "_run_replenishment_cycle_with_live_state(",
            loop_source,
        )
        self.assertNotIn(
            "live_qd_reserve = cycle.live_qd_reserve",
            loop_source,
        )
        self.assertNotIn(
            "reviewed_final_vlm_fingerprints = (\n"
            "                    cycle.reviewed_final_vlm_fingerprints",
            loop_source,
        )
