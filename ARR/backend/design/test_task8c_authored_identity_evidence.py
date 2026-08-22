from unittest import TestCase

from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_generation import (
    _authored_projection_identity_evidence,
    _authored_visual_authority_subreason,
    _propagate_terminal_materialization_failure,
)
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


def _box_surfaces(*, top_scale=1.0):
    bottom = ((-5.0, -3.0, 0.0), (5.0, -3.0, 0.0), (5.0, 3.0, 0.0), (-5.0, 3.0, 0.0))
    top = tuple((x * top_scale, y * top_scale, 4.0) for x, y, _z in bottom)
    vertices = bottom + top
    triangles = (
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    )
    return tuple(
        SourceSurface(
            role=f"surface_{index}",
            volume_role="mass",
            verb="extrude",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(vertices[item] for item in triangle),
        )
        for index, triangle in enumerate(triangles)
    )


def _source(surfaces):
    footprint = box(-5.0, -3.0, 5.0, 3.0)
    return SourceMass(
        name="task8c",
        footprint=footprint,
        volumes=(SourceVolume("mass", footprint, 0.0, 1.0, "extrude"),),
        surfaces=tuple(surfaces),
        metadata={
            "geometry_program": {"nodes": [{"id": "root", "operator": "split_wing"}]},
            "floorwise_visual_projection": {"visible_step_fallback": False},
        },
    )


class _Program:
    metadata = {"family": "focused"}

    def to_dict(self):
        return {"metadata": self.metadata}

    def program_hash(self):
        return "task8c-program"


class Task8CAuthoredIdentityEvidenceTests(TestCase):
    def test_book_projection_branch_reasons_survive_terminal_artifact(self):
        evidence_builder = getattr(
            candidate_generation,
            "_book_projection_terminal_evidence",
            None,
        )
        self.assertIsNotNone(evidence_builder)
        branch_evidence = (
            ("geometry_edit_binding_failed", {"mutation_status": "failed"}),
            ("book_projection_application_failed", {"failure_type": "ValueError"}),
            ("source_role_scaffold_binding_failed", {"stage_detail": "role_scaffold"}),
            ("projected_program_missing", {"stage_detail": "book_program"}),
            ("book_projection_adapter_inactive", {"book_projection_call_count": 1}),
            ("projected_compile_or_geometry_gate_failed", {"compilation_status": "failed"}),
            ("authored_source_construction_failed", {"stage_detail": "authored_source"}),
            ("legal_projection_selector_failed", {"stage_detail": "legal_projection"}),
            ("projected_program_materialization_failed", {"stage_detail": "site_bound_compile"}),
        )
        survived = []

        for reason, safe_evidence in branch_evidence:
            with self.subTest(reason=reason):
                reports = []
                _propagate_terminal_materialization_failure(
                    terminal_record={
                        "stage": "book_projection",
                        "evidence": evidence_builder(
                            reason,
                            **safe_evidence,
                        ),
                    },
                    report_records=reports,
                    outcome_graph=None,
                    program_slug="task8c",
                    source_seed="task8c-seed",
                    program=_Program(),
                    principle_id="focused",
                    book_scope="1/2",
                )

                recorded = reports[0]
                self.assertEqual(
                    recorded["evidence"]["failure_reason"],
                    reason,
                )
                self.assertEqual(
                    recorded["terminal_certificate_evidence"][
                        "failure_reason"
                    ],
                    reason,
                )
                survived.append(recorded["evidence"]["failure_reason"])

        self.assertEqual(
            survived,
            [reason for reason, _safe_evidence in branch_evidence],
        )

    def test_terminal_certificate_preserves_exact_pair_identity_evidence(self):
        identity = _authored_projection_identity_evidence(
            _source(_box_surfaces()),
            _source(_box_surfaces(top_scale=0.05)),
        )
        frozen = identity["frozen_identity_evidence"]
        self.assertTrue(frozen["frozen_at_source_pair_comparison"])
        self.assertEqual(frozen["step_requested"], identity["authored_step_intent"])
        self.assertEqual(frozen["maximum_silhouette_distance"], 0.40)
        self.assertEqual(
            frozen["raw_silhouette_distance"],
            identity["silhouette_distance"],
        )

        reports = []
        _propagate_terminal_materialization_failure(
            terminal_record={
                "stage": "authored_identity_collapse",
                "evidence": {
                    "failure_reason": identity["failure_reasons"][0],
                    "identity_evidence": identity,
                    # Simulate contradictory later diagnostics. These must not
                    # replace the exact-pair decision record.
                    "authored_visible_stepped": not frozen["before_step_visible"],
                    "projected_visible_stepped": not frozen["after_step_visible"],
                },
            },
            report_records=reports,
            outcome_graph=None,
            program_slug="task8c",
            source_seed="task8c-seed",
            program=_Program(),
            principle_id="focused",
            book_scope="1/2",
        )

        recorded = reports[0]["evidence"]["frozen_identity_evidence"]
        certified = reports[0]["terminal_certificate_evidence"]["frozen_identity_evidence"]
        self.assertEqual(recorded, frozen)
        self.assertEqual(certified, frozen)
        self.assertEqual(
            certified["predicate_version"],
            "arr.maas.authored_projection_identity_predicate.v6_bounded_legal_csg_distortion",
        )

    def test_plural_missing_surfaces_normalizes_to_empty_typed_subreason(self):
        subreason = _authored_visual_authority_subreason(
            stage="authored_visual_authority",
            repair_reason="authored_profiled_legal_clip_failed",
            failure_reason="projected_authoritative_visual_surfaces_missing",
            certificate_causes=("profiled_surfaces_missing",),
            certificate_modes=("clip_output_empty",),
        )

        self.assertEqual(
            subreason,
            "authored_visual_authority_empty_or_no_valid_surface",
        )
