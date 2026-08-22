import json
from copy import deepcopy
from math import nan
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box

from design.maas.book_language.actual_gfa_stop_certificate import (
    certify_candidate_actual_gfa_stop,
    validate_candidate_actual_gfa_stop_certificate,
)
from design.maas.book_language.final_mesh_floor_evidence import (
    CandidateFinalizationContext,
    FinalMeshFloorEvidenceError,
    certify_final_mesh_actual_gfa_stop,
    measure_final_mesh_floor_evidence,
    resolve_candidate_finalization_context,
)
from design.maas.book_language.downstream_hard_gate import (
    evaluate_accepted_sources_downstream,
)
from design.maas.book_language.legal_floor_field import (
    materialize_legal_floor_field,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import CompilationResult


PNU = "1168011800104170004"


def _field(site=None):
    site = site or box(0.0, 0.0, 10.0, 10.0)
    context = SimpleNamespace(
        envelope=SimpleNamespace(
            floor_height=3.0,
            height_limit=75.0,
            bcr_limit=100.0,
            far_limit=2500.0,
        ),
        generation_site=site,
        sunlight_ring=(),
        evidence={},
    )
    return materialize_legal_floor_field(
        context,
        site_local_utm=site,
        pnu=PNU,
    )


def _program():
    return GeometryProgram(
        nodes=(
            GeometryNode(
                id="unit",
                kind="primitive",
                operator="box",
                parameters={"size": [1.0, 1.0, 1.0]},
            ),
        ),
        root_id="unit",
        name="final-visible-floor-evidence",
    )


def _prism_mesh(
    *,
    x_min=-5.0,
    y_min=-5.0,
    x_max=5.0,
    y_max=5.0,
    z_min=0.0,
    z_max=1.0,
):
    vertices = (
        (x_min, y_min, z_min),
        (x_max, y_min, z_min),
        (x_max, y_max, z_min),
        (x_min, y_max, z_min),
        (x_min, y_min, z_max),
        (x_max, y_min, z_max),
        (x_max, y_max, z_max),
        (x_min, y_max, z_max),
    )
    triangles = (
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    )
    return vertices, triangles


def _identity(program, seed="a"):
    return {
        "program_hash": program.program_hash(),
        "final_geometry_hash": seed * 64,
        "visual_hash": chr(ord(seed) + 1) * 64,
    }


def _compilation(*, floor_count, seed="a", mesh=None, solid=None):
    program = _program()
    identity = _identity(program, seed)
    vertices, triangles = mesh or _prism_mesh()
    return (
        CompilationResult(
            program=program,
            status="compiled",
            vertices=vertices,
            triangles=triangles,
            metrics={
                "coordinate_space": (
                    "source_footprint_centroid_local_xy_normalized_z"
                ),
                "geometry_authority": "certified_projected_visual_mesh",
            },
            geometry_hash=identity["visual_hash"],
            _solid=solid,
        ),
        identity,
        {
            "status": "certified",
            "hard_pass": True,
            "certification_mode": (
                "final_floorwise_legal_geometry_authority"
            ),
            "projected_surface_coordinate_frame": (
                "source_footprint_centroid_local_xy_normalized_z"
            ),
            "source_footprint_centroid_utm": [5.0, 5.0],
            "final_program_hash": identity["program_hash"],
            "final_geometry_hash": identity["final_geometry_hash"],
            "visual_hash": identity["visual_hash"],
            "candidate_floor_count": floor_count,
        },
    )


def _measure(*, floor_count, seed="a", mesh=None, solid=None, certificate=None):
    field = _field()
    compilation, identity, projected = _compilation(
        floor_count=floor_count,
        seed=seed,
        mesh=mesh,
        solid=solid,
    )
    if certificate:
        projected.update(certificate)
    evidence = measure_final_mesh_floor_evidence(
        certified_compilation=compilation,
        projected_visual_certificate=projected,
        legal_floor_field=field,
        expected_legal_floor_field_hash=field["legal_floor_field_hash"],
        candidate_height_m=floor_count * 3.0,
        candidate_floor_count=floor_count,
        expected_identity=identity,
    )
    return field, compilation, identity, projected, evidence


def _finalization_metadata(field, *, floors, target, target_areas):
    legal_hash = field["legal_floor_field_hash"]
    height = float(field["legal_floor_top_heights_m"][floors - 1])
    return {
        "candidate_floor_context": {
            "status": "materialized",
            "hard_pass": True,
            "height_m": height,
            "floors": floors,
            "floor_top_heights_m": list(
                field["legal_floor_top_heights_m"][:floors]
            ),
            "legal_floor_field_hash": legal_hash,
        },
        "candidate_capacity_contract": {
            "requested_height_m": height,
            "requested_floors": floors,
            "candidate_target_gfa_m2": target,
            "target_floor_area_m2": target,
            "target_floor_areas_m2": list(target_areas),
            "candidate_target_reachable": True,
            "candidate_floor_top_heights_m": list(
                field["legal_floor_top_heights_m"][:floors]
            ),
            "legal_floor_section_areas_m2": list(
                field["legal_floor_section_areas_m2"][:floors]
            ),
            "bcr_adjusted_floor_areas_m2": list(
                field["bcr_adjusted_floor_capacities_m2"][:floors]
            ),
            "candidate_prefix_capacity_m2": sum(
                field["bcr_adjusted_floor_capacities_m2"][:floors]
            ),
            "legal_floor_field_hash": legal_hash,
            "candidate_legal_floor_field_hash": legal_hash,
        },
        "final_semantic_projection_context": {
            "candidate_requested_floors": floors,
            "candidate_target_gfa_m2": target,
            "legal_floor_field_hash": legal_hash,
            "pnu": PNU,
        },
    }


class FinalMeshFloorEvidenceTests(SimpleTestCase):
    def test_physical_meter_visual_mesh_uses_candidate_height_contract(self):
        field = _field()
        program = _program()
        identity = _identity(program)
        vertices, triangles = _prism_mesh(z_max=9.0)
        compilation = CompilationResult(
            program=program,
            status="compiled",
            vertices=vertices,
            triangles=triangles,
            metrics={
                "coordinate_space": "source_footprint_centroid_local_xyz_m",
                "geometry_authority": "certified_projected_visual_mesh",
            },
            geometry_hash=identity["visual_hash"],
        )
        certificate = {
            "status": "certified",
            "hard_pass": True,
            "certification_mode": "authored_projected_surface_authority",
            "projected_surface_coordinate_frame": (
                "source_footprint_centroid_local_xyz_m"
            ),
            "physical_height_m": 9.0,
            "source_footprint_centroid_utm": [5.0, 5.0],
            "final_program_hash": identity["program_hash"],
            "final_geometry_hash": identity["final_geometry_hash"],
            "visual_hash": identity["visual_hash"],
        }

        evidence = measure_final_mesh_floor_evidence(
            certified_compilation=compilation,
            projected_visual_certificate=certificate,
            legal_floor_field=field,
            expected_legal_floor_field_hash=field["legal_floor_field_hash"],
            candidate_height_m=9.0,
            candidate_floor_count=3,
            expected_identity=identity,
        )

        self.assertEqual(evidence.actual_floor_areas_m2[:3], (100.0,) * 3)

    def test_physical_meter_mesh_accepts_submicron_overlay_without_expanding_area(self):
        field = _field()
        program = _program()
        identity = _identity(program)
        vertices, triangles = _prism_mesh(
            x_min=-4.9999994,
            x_max=5.0000006,
            z_max=9.0,
        )
        compilation = CompilationResult(
            program=program,
            status="compiled",
            vertices=vertices,
            triangles=triangles,
            metrics={
                "coordinate_space": "source_footprint_centroid_local_xyz_m",
                "geometry_authority": "certified_projected_visual_mesh",
            },
            geometry_hash=identity["visual_hash"],
        )
        certificate = {
            "status": "certified",
            "hard_pass": True,
            "certification_mode": "authored_projected_surface_authority",
            "projected_surface_coordinate_frame": (
                "source_footprint_centroid_local_xyz_m"
            ),
            "physical_height_m": 9.0,
            "source_footprint_centroid_utm": [5.0, 5.0],
            "final_program_hash": identity["program_hash"],
            "final_geometry_hash": identity["final_geometry_hash"],
            "visual_hash": identity["visual_hash"],
        }

        evidence = measure_final_mesh_floor_evidence(
            certified_compilation=compilation,
            projected_visual_certificate=certificate,
            legal_floor_field=field,
            expected_legal_floor_field_hash=field["legal_floor_field_hash"],
            candidate_height_m=9.0,
            candidate_floor_count=3,
            expected_identity=identity,
        )

        self.assertEqual(evidence.actual_floor_areas_m2[:3], (100.0,) * 3)

    def test_floor_section_ignores_coplanar_tessellation_faces(self):
        from design.maas.book_language.final_mesh_floor_evidence import (
            _mesh_section_segments,
            _polygonize_section_segments,
            _raw_section_area_m2,
        )

        vertices, triangles = _prism_mesh()
        vertices = (*vertices, (
            -5.0, -5.0, 0.5
        ), (
            5.0, -5.0, 0.5
        ), (
            5.0, 5.0, 0.5
        ), (
            -5.0, 5.0, 0.5
        ))
        triangles = (*triangles, (8, 9, 10), (8, 10, 11))

        segments = _mesh_section_segments(vertices, triangles, 0.5)
        section = _polygonize_section_segments(segments)

        self.assertIsNotNone(section)
        self.assertAlmostEqual(float(section.area), 100.0, places=6)
        self.assertAlmostEqual(
            _raw_section_area_m2(segments),
            100.0,
            places=6,
        )

    def test_floor_section_accepts_closed_mesh_with_mixed_triangle_winding(self):
        vertices, triangles = _prism_mesh()
        mixed_winding = tuple(
            tuple(reversed(triangle)) if index % 2 else triangle
            for index, triangle in enumerate(triangles)
        )

        *_context, evidence = _measure(
            floor_count=3,
            mesh=(vertices, mixed_winding),
        )

        self.assertEqual(
            evidence.actual_floor_areas_m2[:3],
            (100.0, 100.0, 100.0),
        )

    def test_three_floor_visible_mesh_produces_full_field_rows_without_mutation(self):
        retained_solid = {"private_replay_shape": "must_not_be_read"}
        compilation, identity, projected = _compilation(
            floor_count=3,
            solid=retained_solid,
        )
        field = _field()
        before = json.dumps(
            {
                "program": compilation.program.to_dict(),
                "vertices": compilation.vertices,
                "triangles": compilation.triangles,
                "certificate": projected,
                "program_hash": compilation.program.program_hash(),
                "geometry_hash": compilation.geometry_hash,
            },
            sort_keys=True,
        )

        evidence = measure_final_mesh_floor_evidence(
            certified_compilation=compilation,
            projected_visual_certificate=projected,
            legal_floor_field=field,
            expected_legal_floor_field_hash=field[
                "legal_floor_field_hash"
            ],
            candidate_height_m=9.0,
            candidate_floor_count=3,
            expected_identity=identity,
        )

        self.assertEqual(evidence.actual_floor_areas_m2[:3], (100.0,) * 3)
        self.assertEqual(evidence.actual_floor_areas_m2[3:], (0.0,) * 22)
        self.assertEqual(len(evidence.containment_evidence), 25)
        self.assertTrue(all(
            row["contained"] is True
            for row in evidence.containment_evidence
        ))
        self.assertEqual(evidence.measured_identity, identity)
        self.assertIs(compilation._solid, retained_solid)
        after = json.dumps(
            {
                "program": compilation.program.to_dict(),
                "vertices": compilation.vertices,
                "triangles": compilation.triangles,
                "certificate": projected,
                "program_hash": compilation.program.program_hash(),
                "geometry_hash": compilation.geometry_hash,
            },
            sort_keys=True,
        )
        self.assertEqual(after, before)

    def test_three_seven_and_twenty_three_floor_certificates_share_legal_field(self):
        field = _field()
        stop_hashes = set()
        legal_hashes = set()

        for index, floor_count in enumerate((3, 7, 23)):
            compilation, identity, projected = _compilation(
                floor_count=floor_count,
                seed=chr(ord("a") + index * 2),
            )
            evidence = measure_final_mesh_floor_evidence(
                certified_compilation=compilation,
                projected_visual_certificate=projected,
                legal_floor_field=field,
                expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
                candidate_height_m=floor_count * 3.0,
                candidate_floor_count=floor_count,
                expected_identity=identity,
            )
            target = floor_count * 100.0
            certificate = certify_candidate_actual_gfa_stop(
                legal_floor_field=field,
                expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
                expected_pnu=PNU,
                expected_identity=identity,
                measured_identity=evidence.measured_identity,
                actual_floor_areas_m2=evidence.actual_floor_areas_m2,
                containment_evidence=evidence.containment_evidence,
                target_gfa_m2=target,
            )

            self.assertTrue(certificate["hard_pass"])
            self.assertTrue(validate_candidate_actual_gfa_stop_certificate(
                certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
                expected_pnu=PNU,
                expected_identity=identity,
                expected_target=target,
            ))
            self.assertEqual(
                certificate["selected_floor_count"],
                floor_count,
            )
            legal_hashes.add(certificate["legal_floor_field_hash"])
            stop_hashes.add(certificate["candidate_actual_gfa_stop_hash"])

        self.assertEqual(legal_hashes, {field["legal_floor_field_hash"]})
        self.assertEqual(len(stop_hashes), 3)

    def test_xy_escape_rejects_with_typed_evidence(self):
        shifted_mesh = _prism_mesh(
            x_min=15.0,
            x_max=25.0,
        )

        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            _measure(floor_count=3, mesh=shifted_mesh)

        self.assertEqual(raised.exception.code, "final_mesh_legal_escape")
        self.assertEqual(raised.exception.evidence["floor_number"], 1)

    def test_sub_eight_decimal_positive_xy_escape_is_not_snapped_inward(self):
        tiny_escape_mesh = _prism_mesh(x_max=5.000000004)

        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            _measure(floor_count=3, mesh=tiny_escape_mesh)

        self.assertEqual(raised.exception.code, "final_mesh_legal_escape")
        self.assertGreater(
            raised.exception.evidence["escaped_boundary_length_m"],
            0.0,
        )

    def test_sub_nanometre_overlay_area_is_numeric_equivalent(self):
        kernel_overlay_mesh = _prism_mesh(x_max=5.00000000005)

        _field_value, _compilation, _identity, _projected, evidence = (
            _measure(floor_count=3, mesh=kernel_overlay_mesh)
        )

        self.assertEqual(evidence.actual_floor_areas_m2[:3], (100.0,) * 3)
        self.assertTrue(all(
            row["contained"] is True
            for row in evidence.containment_evidence[:3]
        ))

    def test_two_nanometre_boundary_overlay_is_numeric_equivalent(self):
        kernel_overlay_mesh = _prism_mesh(x_max=5.000000002)

        _field_value, _compilation, _identity, _projected, evidence = (
            _measure(floor_count=3, mesh=kernel_overlay_mesh)
        )

        self.assertEqual(evidence.actual_floor_areas_m2[:3], (100.0,) * 3)
        self.assertTrue(all(
            row["contained"] is True
            for row in evidence.containment_evidence[:3]
        ))

    def test_raw_section_segment_crossing_concave_legal_void_rejects(self):
        concave_site = Polygon((
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (7.0, 10.0),
            (7.0, 3.0),
            (3.0, 3.0),
            (3.0, 10.0),
            (0.0, 10.0),
        ))
        field = _field(concave_site)
        origin = concave_site.centroid
        mesh = _prism_mesh(
            x_min=2.0 - origin.x,
            x_max=8.0 - origin.x,
            y_min=5.0 - origin.y,
            y_max=6.0 - origin.y,
        )
        compilation, identity, projected = _compilation(
            floor_count=3,
            mesh=mesh,
        )
        projected["source_footprint_centroid_utm"] = [
            origin.x,
            origin.y,
        ]

        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            measure_final_mesh_floor_evidence(
                certified_compilation=compilation,
                projected_visual_certificate=projected,
                legal_floor_field=field,
                expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
                candidate_height_m=9.0,
                candidate_floor_count=3,
                expected_identity=identity,
            )

        self.assertEqual(raised.exception.code, "final_mesh_legal_escape")
        self.assertGreater(
            raised.exception.evidence["escaped_boundary_length_m"],
            0.0,
        )

    def test_geometry_above_candidate_height_rejects_instead_of_truncating(self):
        for z_max in (1.05, 1.0000000005):
            with self.subTest(z_max=z_max):
                above_height_mesh = _prism_mesh(z_max=z_max)
                with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
                    _measure(floor_count=3, mesh=above_height_mesh)
                self.assertEqual(
                    raised.exception.code,
                    "final_mesh_above_candidate_height",
                )

    def test_missing_section_below_candidate_floor_count_rejects(self):
        short_mesh = _prism_mesh(z_max=0.45)

        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            _measure(floor_count=3, mesh=short_mesh)

        self.assertEqual(raised.exception.code, "final_mesh_floor_section_missing")
        self.assertEqual(raised.exception.evidence["floor_number"], 2)

    def test_invalid_coordinate_space_centroid_identity_and_nonfinite_vertices_reject(self):
        cases = (
            (
                {"projected_surface_coordinate_frame": "world_m"},
                None,
                "invalid_final_mesh_coordinate_space",
            ),
            (
                {"certification_mode": "authored_visual_legal_validation"},
                None,
                "invalid_final_mesh_authority",
            ),
            (
                {"source_footprint_centroid_utm": [50.0, 50.0]},
                None,
                "final_mesh_legal_escape",
            ),
            (
                {"visual_hash": "f" * 64},
                None,
                "final_mesh_identity_mismatch",
            ),
            (
                None,
                (
                    ((-5.0, -5.0, nan),) + _prism_mesh()[0][1:],
                    _prism_mesh()[1],
                ),
                "nonfinite_final_mesh_vertex",
            ),
        )
        for certificate, mesh, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
                    _measure(
                        floor_count=3,
                        mesh=mesh,
                        certificate=certificate,
                    )
                self.assertEqual(raised.exception.code, expected_code)

    def test_retained_private_solid_never_overrides_visible_mesh(self):
        outside_private_solid = {
            "vertices": _prism_mesh(x_min=100.0, x_max=110.0)[0],
            "triangles": _prism_mesh()[1],
        }
        field, compilation, identity, _projected, evidence = _measure(
            floor_count=3,
            solid=outside_private_solid,
        )

        self.assertEqual(evidence.actual_floor_areas_m2[:3], (100.0,) * 3)
        self.assertEqual(
            evidence.containment_evidence[0]["legal_floor_field_hash"],
            field["legal_floor_field_hash"],
        )
        self.assertEqual(evidence.measured_identity, identity)
        self.assertIs(compilation._solid, outside_private_solid)

    def test_wrong_candidate_height_and_floor_count_fail_closed(self):
        field = _field()
        compilation, identity, projected = _compilation(floor_count=3)
        cases = (
            (8.5, 3, "candidate_height_floor_prefix_mismatch"),
            (9.0, 0, "invalid_candidate_floor_count"),
            (9.0, 26, "invalid_candidate_floor_count"),
            (nan, 3, "invalid_candidate_height"),
        )
        for height, count, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
                    measure_final_mesh_floor_evidence(
                        certified_compilation=compilation,
                        projected_visual_certificate=deepcopy(projected),
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=field[
                            "legal_floor_field_hash"
                        ],
                        candidate_height_m=height,
                        candidate_floor_count=count,
                        expected_identity=identity,
                    )
                self.assertEqual(raised.exception.code, expected_code)

    def test_candidate_finalization_context_requires_one_coherent_candidate_identity(self):
        field = _field()
        legal_hash = field["legal_floor_field_hash"]
        metadata = _finalization_metadata(
            field,
            floors=7,
            target=650.0,
            target_areas=(650.0 / 7.0,) * 6 + (650.0 / 7.0,),
        )

        context = resolve_candidate_finalization_context(
            metadata,
            trusted_legal_floor_field=field,
            expected_legal_floor_field_hash=legal_hash,
            expected_pnu=PNU,
        )

        self.assertEqual(
            context,
            CandidateFinalizationContext(
                candidate_height_m=21.0,
                candidate_floor_count=7,
                candidate_target_gfa_m2=650.0,
                legal_floor_field_hash=legal_hash,
            ),
        )
        for key, value in (
            ("requested_height_m", 15.0),
            ("requested_floors", 5),
            ("candidate_target_gfa_m2", 649.0),
            ("legal_floor_field_hash", "f" * 64),
        ):
            tampered = deepcopy(metadata)
            tampered["candidate_capacity_contract"][key] = value
            with self.subTest(key=key):
                with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
                    resolve_candidate_finalization_context(
                        tampered,
                        trusted_legal_floor_field=field,
                        expected_legal_floor_field_hash=legal_hash,
                        expected_pnu=PNU,
                    )
                self.assertEqual(
                    raised.exception.code,
                    "candidate_finalization_context_mismatch",
                )
        semantic_tampers = (
            ("candidate_requested_floors", True),
            ("candidate_target_gfa_m2", "650.0"),
            ("legal_floor_field_hash", "f" * 64),
            ("pnu", "1168011800104170005"),
        )
        for key, value in semantic_tampers:
            tampered = deepcopy(metadata)
            tampered["final_semantic_projection_context"][key] = value
            with self.subTest(semantic_key=key):
                with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
                    resolve_candidate_finalization_context(
                        tampered,
                        trusted_legal_floor_field=field,
                        expected_legal_floor_field_hash=legal_hash,
                        expected_pnu=PNU,
                    )
                self.assertEqual(
                    raised.exception.code,
                    "candidate_finalization_context_mismatch",
                )
        boolean_alias = deepcopy(metadata)
        boolean_alias["candidate_floor_context"].update({
            "height_m": 3.0,
            "floors": 1,
        })
        boolean_alias["candidate_capacity_contract"].update({
            "requested_height_m": 3.0,
            "requested_floors": 1,
            "candidate_target_gfa_m2": 1.0,
        })
        boolean_alias["final_semantic_projection_context"].update({
            "candidate_requested_floors": True,
            "candidate_target_gfa_m2": True,
        })
        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            resolve_candidate_finalization_context(
                boolean_alias,
                trusted_legal_floor_field=field,
                expected_legal_floor_field_hash=legal_hash,
                expected_pnu=PNU,
            )
        self.assertEqual(
            raised.exception.code,
            "candidate_finalization_context_mismatch",
        )

    def test_joint_candidate_and_semantic_target_rewrite_cannot_override_capacity_aliases(self):
        field = _field()
        metadata = _finalization_metadata(
            field,
            floors=7,
            target=650.0,
            target_areas=(100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 50.0),
        )
        metadata["candidate_capacity_contract"][
            "candidate_target_gfa_m2"
        ] = 700.0
        metadata["final_semantic_projection_context"][
            "candidate_target_gfa_m2"
        ] = 700.0

        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            resolve_candidate_finalization_context(
                metadata,
                trusted_legal_floor_field=field,
                expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
                expected_pnu=PNU,
            )

        self.assertEqual(
            raised.exception.code,
            "candidate_finalization_target_identity_mismatch",
        )

    def test_downstream_gate_uses_each_candidate_height_and_floor_count(self):
        legal_hash = _field()["legal_floor_field_hash"]

        def candidate(height, floors):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "candidate_floor_context": {
                    "status": "materialized",
                    "hard_pass": True,
                    "height_m": height,
                    "floors": floors,
                    "legal_floor_field_hash": legal_hash,
                },
            }))

        seen = []

        def evaluate_one(_candidate, **kwargs):
            seen.append((kwargs["height_m"], kwargs["floors"]))
            return {
                "legal_projection": {
                    "failure_reasons": [],
                    "geometry_failure_reasons": [],
                    "volume_retention": 1.0,
                    "hard_pass": True,
                    "geometry_retention_pass": True,
                    "timing_seconds": 0.0,
                },
                "parking_hard_gate": {
                    "failure_reasons": [],
                    "hard_pass": True,
                    "timing_seconds": 0.0,
                },
                "semantic_projection_hard_gate": {
                    "timing_seconds": 0.0,
                },
                "combined_hard_pass": True,
            }

        context = SimpleNamespace(
            envelope=SimpleNamespace(
                bcr_limit=100.0,
                far_limit=2500.0,
                height_limit=75.0,
                buildable_footprint=box(0.0, 0.0, 10.0, 10.0),
                outputs_def={},
            ),
            generation_site=box(0.0, 0.0, 10.0, 10.0),
            sunlight_ring=(),
            evidence={},
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate."
                "_evaluate_candidate",
                side_effect=evaluate_one,
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate."
                "load_parking_requirement_rules",
                return_value={"status": "missing"},
            ),
        ):
            evaluate_accepted_sources_downstream(
                (candidate(9.0, 3), candidate(69.0, 23)),
                site_local_utm=box(0.0, 0.0, 10.0, 10.0),
                site_origin_utm=(0.0, 0.0),
                pnu=PNU,
                building_type="neighborhood living",
                height_m=15.0,
                floors=5,
                constraints=[],
                regulation_evidence={},
                sunlight_envelope=None,
                generation_context=context,
            )

        self.assertEqual(seen, [(9.0, 3), (69.0, 23)])

    def test_downstream_trusted_path_rejects_missing_candidate_floor_context(self):
        candidate = SimpleNamespace(
            source=SimpleNamespace(metadata={}),
        )
        context = SimpleNamespace(
            envelope=SimpleNamespace(
                bcr_limit=100.0,
                far_limit=2500.0,
                height_limit=75.0,
                buildable_footprint=box(0.0, 0.0, 10.0, 10.0),
                outputs_def={},
            ),
            generation_site=box(0.0, 0.0, 10.0, 10.0),
            sunlight_ring=(),
            evidence={},
        )

        with self.assertRaises(ValueError) as raised:
            evaluate_accepted_sources_downstream(
                (candidate,),
                site_local_utm=box(0.0, 0.0, 10.0, 10.0),
                site_origin_utm=(0.0, 0.0),
                pnu=PNU,
                building_type="neighborhood living",
                height_m=15.0,
                floors=5,
                constraints=[],
                regulation_evidence={},
                sunlight_envelope=None,
                generation_context=context,
            )

        self.assertEqual(
            getattr(raised.exception, "code", ""),
            "missing_candidate_floor_context",
        )
        self.assertFalse(
            raised.exception.evidence["publishable"]
        )

    def test_final_mesh_stop_record_certifies_and_independently_revalidates(self):
        field = _field()
        compilation, identity, projected = _compilation(floor_count=3)

        record = certify_final_mesh_actual_gfa_stop(
            certified_compilation=compilation,
            projected_visual_certificate=projected,
            legal_floor_field=field,
            expected_legal_floor_field_hash=field[
                "legal_floor_field_hash"
            ],
            expected_pnu=PNU,
            candidate_height_m=9.0,
            candidate_floor_count=3,
            candidate_target_gfa_m2=300.0,
            expected_identity=identity,
        )

        self.assertTrue(record["hard_pass"])
        self.assertEqual(record["candidate_floor_count"], 3)
        self.assertEqual(record["candidate_target_gfa_m2"], 300.0)
        self.assertEqual(
            record["legal_floor_field_hash"],
            field["legal_floor_field_hash"],
        )
        self.assertEqual(
            record["candidate_actual_gfa_stop_hash"],
            record["candidate_actual_gfa_stop_certificate"][
                "candidate_actual_gfa_stop_hash"
            ],
        )

    def test_final_mesh_stop_preserves_requested_target_but_certifies_accepted_actual_gfa(self):
        field = _field()
        program = _program()
        identity = _identity(program)
        vertices, triangles = _prism_mesh(z_max=9.0)
        compilation = CompilationResult(
            program=program,
            status="compiled",
            vertices=vertices,
            triangles=triangles,
            metrics={
                "coordinate_space": (
                    "source_footprint_centroid_local_xyz_m"
                ),
                "geometry_authority": (
                    "certified_projected_visual_mesh"
                ),
            },
            geometry_hash=identity["visual_hash"],
        )
        projected = {
            "status": "certified",
            "hard_pass": True,
            "certification_mode": "authored_projected_surface_authority",
            "projected_surface_coordinate_frame": (
                "source_footprint_centroid_local_xyz_m"
            ),
            "source_footprint_centroid_utm": [5.0, 5.0],
            "final_program_hash": identity["program_hash"],
            "final_geometry_hash": identity["final_geometry_hash"],
            "visual_hash": identity["visual_hash"],
            "candidate_floor_count": 3,
        }

        record = certify_final_mesh_actual_gfa_stop(
            certified_compilation=compilation,
            projected_visual_certificate=projected,
            legal_floor_field=field,
            expected_legal_floor_field_hash=field[
                "legal_floor_field_hash"
            ],
            expected_pnu=PNU,
            candidate_height_m=9.0,
            candidate_floor_count=3,
            candidate_target_gfa_m2=315.0,
            candidate_feasible_maximum_gfa_m2=400.0,
            candidate_minimum_capacity_utilization=0.7,
            candidate_capacity_resolution_hard_pass=True,
            expected_identity=identity,
        )

        self.assertTrue(record["hard_pass"])
        self.assertEqual(
            record["requested_candidate_target_gfa_m2"],
            315.0,
        )
        self.assertAlmostEqual(record["achieved_gfa_m2"], 300.0)
        self.assertAlmostEqual(
            record["achieved_capacity_utilization"],
            0.75,
        )
        self.assertEqual(
            record["candidate_actual_gfa_stop_certificate"][
                "target_gfa_m2"
            ],
            record["achieved_gfa_m2"],
        )

    def test_capacity_underfill_is_advisory_and_fully_evidenced(self):
        field = _field()
        program = _program()
        identity = _identity(program)
        vertices, triangles = _prism_mesh(z_max=9.0)
        compilation = CompilationResult(
            program=program,
            status="compiled",
            vertices=vertices,
            triangles=triangles,
            metrics={
                "coordinate_space": (
                    "source_footprint_centroid_local_xyz_m"
                ),
                "geometry_authority": (
                    "certified_projected_visual_mesh"
                ),
            },
            geometry_hash=identity["visual_hash"],
        )
        projected = {
            "status": "certified",
            "hard_pass": True,
            "certification_mode": "authored_projected_surface_authority",
            "projected_surface_coordinate_frame": (
                "source_footprint_centroid_local_xyz_m"
            ),
            "source_footprint_centroid_utm": [5.0, 5.0],
            "final_program_hash": identity["program_hash"],
            "final_geometry_hash": identity["final_geometry_hash"],
            "visual_hash": identity["visual_hash"],
            "candidate_floor_count": 3,
        }

        evidence = certify_final_mesh_actual_gfa_stop(
            certified_compilation=compilation,
            projected_visual_certificate=projected,
            legal_floor_field=field,
            expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
            expected_pnu=PNU,
            candidate_height_m=9.0,
            candidate_floor_count=3,
            candidate_target_gfa_m2=450.0,
            candidate_feasible_maximum_gfa_m2=500.0,
            candidate_minimum_capacity_utilization=0.7,
            candidate_capacity_resolution_hard_pass=True,
            expected_identity=identity,
            )

        # FAR is a statutory ceiling, so yielding less than the requested
        # capacity band is lawful and must not reject the mass. It may never
        # pass silently either: the shortfall is carried as evidence, and every
        # legal maximum stays a hard gate elsewhere.
        self.assertEqual(
            evidence["capacity_contract_mode"],
            "advisory_actual_gfa_underfill",
        )
        advisory = evidence["capacity_underfill_advisory"]
        self.assertIs(advisory["statutory_minimum"], False)
        self.assertAlmostEqual(
            advisory["achieved_capacity_utilization"], 0.6
        )
        self.assertLess(
            advisory["achieved_capacity_utilization"],
            advisory["candidate_minimum_capacity_utilization"],
        )
        self.assertEqual(
            advisory["achieved_gfa_m2"],
            evidence["achieved_gfa_m2"],
        )

    def test_final_mesh_stop_record_rejects_uncertified_target_with_certificate_evidence(self):
        field = _field()
        compilation, identity, projected = _compilation(floor_count=3)

        with self.assertRaises(FinalMeshFloorEvidenceError) as raised:
            certify_final_mesh_actual_gfa_stop(
                certified_compilation=compilation,
                projected_visual_certificate=projected,
                legal_floor_field=field,
                expected_legal_floor_field_hash=field[
                    "legal_floor_field_hash"
                ],
                expected_pnu=PNU,
                candidate_height_m=9.0,
                candidate_floor_count=3,
                candidate_target_gfa_m2=299.0,
                expected_identity=identity,
            )

        self.assertEqual(
            raised.exception.code,
            "candidate_actual_gfa_stop_not_certified",
        )
        self.assertEqual(
            raised.exception.evidence["certificate"]["failure_reasons"],
            ["uncorrected_gfa_overshoot"],
        )
