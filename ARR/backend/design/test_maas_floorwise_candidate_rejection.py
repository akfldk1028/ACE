from collections import Counter
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.geometry_language import base_seed_program
from design.maas.geometry_language.source_bridge import (
    materialize_floorwise_legal_source,
)
from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import program_seed_sequences
from design.maas.program_massing.semantic_carriers import semantic_site_context_hash
from design.maas.source_geometry.ir import SourceMass, SourceVolume


def _slab_fallback_case():
    source_footprint = box(0.0, 0.0, 10.0, 10.0)
    source = SourceMass(
        name="source-placeholder",
        footprint=source_footprint,
        volumes=(
            SourceVolume(
                "gym_main_long_span_hall",
                source_footprint,
                0.0,
                1.0,
                "geometry_program",
            ),
            SourceVolume(
                "gym_service_spine",
                box(1.0, 4.0, 3.0, 6.0),
                0.0,
                0.5,
                "attach",
            ),
            SourceVolume(
                "gym_entry_canopy",
                box(7.0, 4.0, 8.5, 6.0),
                0.0,
                0.5,
                "attach",
            ),
        ),
        metadata={
            "component_graph": graph_from_sequence(
                program_seed_sequences("gymnasium")[0]
            ).to_dict(),
            "candidate_floor_context": {
                "height_m": 16.0,
                "floors": 4,
            },
        },
    )
    legal_section = box(-15.0, -10.0, 15.0, 10.0)
    program = base_seed_program("slab")
    sequence = VerbSequence(
        "real-slab",
        "real-slab",
        (),
        ("geometry_program_directive=real-slab",),
    )
    context = {
        "building_type": "gymnasium",
        "site_access_side": "south",
        "pnu": "1168011800104170004",
        "capacity_alternative_id": "balanced_yield",
        "capacity_measurement_hash": "pending_capacity_measurement",
        "site_context_hash": semantic_site_context_hash(
            pnu="1168011800104170004",
            building_type="gymnasium",
            site=legal_section,
        ),
    }
    return source, program, legal_section, sequence, context


class FloorwiseCandidateReplayRejectionTests(SimpleTestCase):
    def test_floorwise_containment_uses_each_legal_section_not_upper_host(self):
        lower = box(0.0, 0.0, 10.0, 10.0)
        upper = box(2.0, 2.0, 8.0, 8.0)
        source = SourceMass(
            name="legal-floorwise-source",
            footprint=lower,
            volumes=(
                SourceVolume("lower", lower, 0.0, 0.5, "legal_proxy"),
                SourceVolume("upper", upper, 0.5, 1.0, "legal_proxy"),
            ),
        )

        self.assertFalse(candidate_generation._inside_site(source, upper))
        self.assertTrue(
            candidate_generation._inside_floorwise_legal_sections(
                source,
                (lower, upper),
            )
        )

    def test_floorwise_containment_rejects_volume_outside_its_own_section(self):
        lower = box(0.0, 0.0, 10.0, 10.0)
        upper = box(2.0, 2.0, 8.0, 8.0)
        source = SourceMass(
            name="illegal-floorwise-source",
            footprint=lower,
            volumes=(
                SourceVolume("lower", lower, 0.0, 0.5, "legal_proxy"),
                SourceVolume(
                    "upper",
                    box(1.0, 1.0, 8.0, 8.0),
                    0.5,
                    1.0,
                    "legal_proxy",
                ),
            ),
        )

        self.assertFalse(
            candidate_generation._inside_floorwise_legal_sections(
                source,
                (lower, upper),
            )
        )

    def _materialize_directed(
        self,
        source,
        legal_section,
        sequence,
        context,
        *,
        terminal_failure_sink,
        floor_capacity_plan_hash="contained-stack-plan",
    ):
        return candidate_generation._materialize_directed_geometry(
            source,
            sequence,
            containment_host=legal_section,
            upper_containment_host=legal_section,
            floor_containment_hosts=(legal_section,) * 4,
            floor_capacity_plan_hash=floor_capacity_plan_hash,
            target_floor_areas_m2=(180.0,) * 4,
            terminal_failure_sink=terminal_failure_sink,
            **context,
        )

    def test_floorwise_bridge_reports_floor_affine_fit_failure(self):
        source, _program, _legal_section, _sequence, _context = (
            _slab_fallback_case()
        )
        failure_sink = []

        materialized = materialize_floorwise_legal_source(
            source,
            legal_sections=(box(-1.0, -1.0, 1.0, 1.0),) * 4,
            target_plan_coverage=0.6,
            floor_capacity_plan_hash="contained-stack-plan",
            target_floor_areas_m2=(180.0,) * 4,
            terminal_failure_sink=failure_sink,
        )

        self.assertIsNone(materialized)
        self.assertEqual(["floor_affine_fit"], [
            record["stage"] for record in failure_sink
        ])

    def test_directed_candidate_reports_outer_and_book_preconditions(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()

        with self.subTest("outer_precondition"):
            failure_sink = []
            with patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ):
                self.assertIsNone(self._materialize_directed(
                    source,
                    legal_section,
                    sequence,
                    context,
                    terminal_failure_sink=failure_sink,
                    floor_capacity_plan_hash="",
                ))
            self.assertEqual("outer_precondition", failure_sink[0]["stage"])

        with self.subTest("book_projection"):
            failure_sink = []
            failed_compilation = SimpleNamespace(status="failed")
            with (
                patch.object(
                    candidate_generation,
                    "_geometry_program_registry",
                    return_value={"real-slab": program},
                ),
                patch.object(
                    candidate_generation,
                    "compile_geometry_program",
                    return_value=failed_compilation,
                ),
            ):
                self.assertIsNone(self._materialize_directed(
                    source,
                    legal_section,
                    sequence,
                    context,
                    terminal_failure_sink=failure_sink,
                ))
            self.assertEqual("book_projection", failure_sink[0]["stage"])

    def test_directed_candidate_reports_identity_and_replay_compile_failures(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()

        with self.subTest("authored_identity_collapse"):
            failure_sink = []
            with (
                patch.object(
                    candidate_generation,
                    "_geometry_program_registry",
                    return_value={"real-slab": program},
                ),
                patch.object(
                    candidate_generation,
                    "select_legal_field_affine_projection",
                    return_value=None,
                ),
                patch.object(
                    candidate_generation,
                    "_authored_projection_identity_evidence",
                    return_value={"hard_pass": False},
                ),
            ):
                self.assertIsNone(self._materialize_directed(
                    source,
                    legal_section,
                    sequence,
                    context,
                    terminal_failure_sink=failure_sink,
                ))
            self.assertEqual(
                "authored_identity_collapse",
                failure_sink[0]["stage"],
            )

        with self.subTest("replay_compile"):
            failure_sink = []
            gate_issue = SimpleNamespace(
                code="forced_replay_compile_failure",
                to_dict=lambda: {"code": "forced_replay_compile_failure"},
            )
            with (
                patch.object(
                    candidate_generation,
                    "_geometry_program_registry",
                    return_value={"real-slab": program},
                ),
                patch.object(
                    candidate_generation,
                    "select_legal_field_affine_projection",
                    return_value=None,
                ),
                patch.object(
                    candidate_generation,
                    "_authored_projection_identity_evidence",
                    return_value={"hard_pass": True},
                ),
                patch.object(
                    candidate_generation,
                    "compilation_gate",
                    side_effect=((), (gate_issue,)),
                ),
            ):
                self.assertIsNone(self._materialize_directed(
                    source,
                    legal_section,
                    sequence,
                    context,
                    terminal_failure_sink=failure_sink,
                ))
            self.assertEqual("replay_compile", failure_sink[0]["stage"])

    def test_directed_candidate_reports_binding_and_semantic_failures(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()

        with self.subTest("final_identity_binding"):
            failure_sink = []
            direct_projection = SimpleNamespace(
                projection=SimpleNamespace(
                    program=program,
                    certificate={
                        "hard_pass": True,
                        "final_geometry_hash": "expected-geometry-hash",
                        "achieved_floor_areas_m2": (180.0,) * 4,
                    },
                ),
                evidence={},
            )
            with (
                patch.object(
                    candidate_generation,
                    "_geometry_program_registry",
                    return_value={"real-slab": program},
                ),
                patch.object(
                    candidate_generation,
                    "select_legal_field_affine_projection",
                    return_value=direct_projection,
                ),
                patch.object(
                    candidate_generation,
                    "compile_site_bound_geometry_program_to_source_mass",
                    return_value=source,
                ),
            ):
                self.assertIsNone(self._materialize_directed(
                    source,
                    legal_section,
                    sequence,
                    context,
                    terminal_failure_sink=failure_sink,
                ))
            self.assertEqual(
                "final_identity_binding",
                failure_sink[0]["stage"],
            )

        with self.subTest("semantic_carrier"):
            failure_sink = []
            with (
                patch.object(
                    candidate_generation,
                    "_geometry_program_registry",
                    return_value={"real-slab": program},
                ),
                patch.object(
                    candidate_generation,
                    "select_legal_field_affine_projection",
                    return_value=None,
                ),
                patch.object(
                    candidate_generation,
                    "_authored_projection_identity_evidence",
                    return_value={"hard_pass": True},
                ),
                patch.object(
                    candidate_generation,
                    "build_program_semantic_carrier_evidence",
                    return_value={"hard_pass": False},
                ),
            ):
                self.assertIsNone(self._materialize_directed(
                    source,
                    legal_section,
                    sequence,
                    context,
                    terminal_failure_sink=failure_sink,
                ))
            self.assertEqual("semantic_carrier", failure_sink[0]["stage"])

    def test_program_pool_reports_terminal_counts_separately_from_affine_misses(self):
        source, _program, legal_section, _sequence, _context = _slab_fallback_case()
        floor_context = {
            "hard_pass": True,
            "height_m": 16.0,
            "floors": 4,
            "legal_sections": (legal_section,) * 4,
            "floor_top_heights_m": (4.0, 8.0, 12.0, 16.0),
            "upper_legal_section": legal_section,
            "authority": "focused_test",
            "legal_floor_field_hash": "focused-test-field",
        }

        def terminal_failure(*_args, **kwargs):
            kwargs["terminal_failure_sink"].append({
                "stage": "semantic_carrier",
                "evidence": {"hard_pass": False},
            })
            return None

        with (
            patch.object(
                candidate_generation,
                "compile_sequence_to_source_mass",
                return_value=source,
            ),
            patch.object(
                candidate_generation,
                "_candidate_floor_context",
                return_value=floor_context,
            ),
            patch.object(
                candidate_generation,
                "_materialize_directed_geometry",
                side_effect=terminal_failure,
            ),
        ):
            _candidates, diagnostics = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                parent_variant_indices=(0,),
                diagnostic_evaluation_cap=1,
                diagnostic_candidate_cap=1,
            )

        self.assertEqual(
            {"semantic_carrier": 1},
            diagnostics["terminal_materialization_failure_reason_counts"],
        )
        self.assertEqual(
            {},
            diagnostics["legal_fit_failure_reason_counts"],
        )

    def test_floorwise_bridge_reports_one_typed_source_section_failure(self):
        source, _program, legal_section, _sequence, _context = (
            _slab_fallback_case()
        )
        source = replace(source, volumes=())
        failure_sink = []

        materialized = materialize_floorwise_legal_source(
            source,
            legal_sections=(legal_section,) * 4,
            target_plan_coverage=0.6,
            floor_capacity_plan_hash="contained-stack-plan",
            target_floor_areas_m2=(180.0,) * 4,
            terminal_failure_sink=failure_sink,
        )

        self.assertIsNone(materialized)
        self.assertEqual(1, len(failure_sink))
        self.assertEqual("source_floor_section", failure_sink[0]["stage"])
        self.assertLessEqual(len(failure_sink[0]["evidence"]), 8)

    def test_floorwise_bridge_reports_visual_projection_failure(self):
        source, _program, legal_section, _sequence, _context = (
            _slab_fallback_case()
        )
        failure_sink = []
        rejected_projection = SimpleNamespace(
            certificate=SimpleNamespace(
                hard_pass=False,
                failure_reasons=("forced_visual_projection_failure",),
            )
        )

        with (
            patch(
                "design.maas.geometry_language.floorwise_visual_projection."
                "project_floorwise_visual_mesh",
                return_value=rejected_projection,
            ),
            patch(
                "design.maas.geometry_language.floorwise_visual_projection."
                "FloorwiseVisualProjection",
                side_effect=lambda **_kwargs: rejected_projection,
            ),
        ):
            materialized = materialize_floorwise_legal_source(
                source,
                legal_sections=(legal_section,) * 4,
                target_plan_coverage=0.6,
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0,) * 4,
                terminal_failure_sink=failure_sink,
            )

        self.assertIsNone(materialized)
        self.assertEqual(1, len(failure_sink))
        self.assertEqual(
            "authored_visual_authority",
            failure_sink[0]["stage"],
        )
        self.assertLessEqual(len(failure_sink[0]["evidence"]), 24)

    def test_floorwise_bridge_records_each_failure_in_a_reused_sink(self):
        source, _program, legal_section, _sequence, _context = (
            _slab_fallback_case()
        )
        source = replace(source, volumes=())
        failure_sink = []

        for _ in range(2):
            self.assertIsNone(materialize_floorwise_legal_source(
                source,
                legal_sections=(legal_section,) * 4,
                target_plan_coverage=0.6,
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0,) * 4,
                terminal_failure_sink=failure_sink,
            ))

        self.assertEqual(
            ["source_floor_section", "source_floor_section"],
            [record["stage"] for record in failure_sink],
        )

    def test_directed_candidate_propagates_one_terminal_reason(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()
        failure_sink = []

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=None,
            ),
            patch.object(
                candidate_generation,
                "materialize_floorwise_legal_source",
                side_effect=lambda *_args, **kwargs: (
                    kwargs["terminal_failure_sink"].append({
                        "stage": "visual_projection_or_replay",
                        "evidence": {"floor_count": 4},
                    })
                    or None
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=legal_section,
                upper_containment_host=legal_section,
                floor_containment_hosts=(legal_section,) * 4,
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0,) * 4,
                terminal_failure_sink=failure_sink,
                **context,
            )

        self.assertIsNone(materialized)
        self.assertEqual(
            [{
                "stage": "visual_projection_or_replay",
                "evidence": {"floor_count": 4},
            }],
            failure_sink,
        )

    def test_known_unreplayable_floor_volume_is_typed_once_per_candidate(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()
        failure_sink = []

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=None,
            ),
            patch.object(
                candidate_generation,
                "_authored_projection_identity_evidence",
                return_value={"hard_pass": True},
            ),
        ):
            for _ in range(2):
                materialized = candidate_generation._materialize_directed_geometry(
                    source,
                    sequence,
                    containment_host=legal_section,
                    upper_containment_host=legal_section,
                    floor_containment_hosts=(legal_section,) * 4,
                    floor_capacity_plan_hash="contained-stack-plan",
                    target_floor_areas_m2=(180.0,) * 4,
                    terminal_failure_sink=failure_sink,
                    **context,
                )
                self.assertIsNone(materialized)

        self.assertEqual(
            {"semantic_carrier": 2},
            dict(Counter(record["stage"] for record in failure_sink)),
        )

    def test_unknown_floorwise_replay_value_error_is_reraised(self):
        source, program, legal_section, sequence, context = _slab_fallback_case()

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"real-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=None,
            ),
            patch.object(
                candidate_generation,
                "_authored_projection_identity_evidence",
                return_value={"hard_pass": True},
            ),
            patch.object(
                candidate_generation,
                "floorwise_source_to_geometry_program",
                side_effect=ValueError(
                    "source has no materialized floorwise legal matrix stack"
                ),
            ),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "source has no materialized floorwise legal matrix stack",
            ):
                candidate_generation._materialize_directed_geometry(
                    source,
                    sequence,
                    containment_host=legal_section,
                    upper_containment_host=legal_section,
                    floor_containment_hosts=(legal_section,) * 4,
                    floor_capacity_plan_hash="contained-stack-plan",
                    target_floor_areas_m2=(180.0,) * 4,
                    **context,
                )
