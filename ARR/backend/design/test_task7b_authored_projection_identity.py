from copy import deepcopy
from dataclasses import replace
from unittest import TestCase
from math import cos, radians, sin

from shapely.geometry import box

from design.maas.book_language.candidate_generation import (
    _admit_legal_mass_candidate,
    _authored_projection_identity_evidence,
    _authored_projection_terminal_stage,
)
from design.maas.book_language.candidate_analysis import (
    _solid_morphology_metrics,
)
from design.maas.book_language.legal_mass_archive import LegalMassArchive
from design.maas.geometry_language.floorwise_profiled_legal_clip import (
    clip_profiled_mesh_to_floorwise_legal_solids,
    profiled_legal_section_authority_binding_hash,
)
from design.maas.geometry_language.floorwise_visual_projection import (
    _profiled_export_completeness_failure,
)
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.geometry_language.projected_visual_contract import (
    final_floorwise_visual_geometry_hash,
)
from design.maas.geometry_language.source_bridge import source_surface_payload_hash
from design.maas.program_massing.morphology import (
    authoritative_surface_silhouette_distance,
    authoritative_surface_morphology,
)


IDENTITY_MATRIX4 = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)


def _box_surfaces(width=10.0, depth=6.0, height=4.0):
    x0, x1 = -width / 2.0, width / 2.0
    y0, y1 = -depth / 2.0, depth / 2.0
    z0, z1 = 0.0, height
    corners = (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    )
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
            vertices_m=tuple(corners[item] for item in triangle),
        )
        for index, triangle in enumerate(triangles)
    )


def _pyramid_surfaces(width=10.0, depth=6.0, height=4.0):
    x0, x1 = -width / 2.0, width / 2.0
    y0, y1 = -depth / 2.0, depth / 2.0
    base = ((x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0))
    apex = (0.0, 0.0, height)
    triangles = ((base[0], base[2], base[1]), (base[0], base[3], base[2])) + tuple(
        (base[index], base[(index + 1) % 4], apex) for index in range(4)
    )
    return tuple(
        SourceSurface(
            role=f"surface_{index}",
            volume_role="mass",
            verb="slice",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=triangle,
        )
        for index, triangle in enumerate(triangles)
    )


def _source(*, surfaces, volumes=None):
    footprint = box(-5.0, -3.0, 5.0, 3.0)
    return SourceMass(
        name="identity",
        footprint=footprint,
        volumes=tuple(volumes or (
            SourceVolume("mass", footprint, 0.0, 1.0, "extrude"),
        )),
        surfaces=tuple(surfaces),
        metadata={
            "geometry_program": {
                "nodes": [{"id": "root", "operator": "split_wing"}],
            },
            "floorwise_visual_projection": {"visible_step_fallback": False},
        },
    )


def _transform_surfaces(surfaces, *, scale=1.0, angle=0.0, offset=(0.0, 0.0, 0.0)):
    theta = radians(angle)
    transformed = []
    for surface in surfaces:
        vertices = []
        for x, y, z in surface.vertices_m:
            x, y, z = x * scale, y * scale, z * scale
            vertices.append((
                x * cos(theta) - y * sin(theta) + offset[0],
                x * sin(theta) + y * cos(theta) + offset[1],
                z + offset[2],
            ))
        transformed.append(SourceSurface(
            role=surface.role,
            volume_role=surface.volume_role,
            verb=surface.verb,
            surface_type=surface.surface_type,
            vertices_m=tuple(vertices),
        ))
    return tuple(transformed)


def _certified_profiled_legal_clip_source(legal_sections):
    legal_sections = tuple(legal_sections)
    floor_count = len(legal_sections)
    authored = _source(surfaces=_box_surfaces(height=1.0))
    authored = replace(
        authored,
        metadata={
            **{
                key: value
                for key, value in authored.metadata.items()
                if key != "geometry_program"
            },
            "candidate_floor_context": {"height_m": 12.0},
            "geometry_program_bridge_evidence": {
                "raw_mesh_triangle_count": len(authored.surfaces),
                "exported_surface_count": len(authored.surfaces),
            },
            "floorwise_legal_matrix_stack": {
                "status": "materialized",
                "floor_capacity_plan_hash": "task7b-r341-plan",
                "floors": [
                    {"floor": index + 1, "matrix4": IDENTITY_MATRIX4}
                    for index in range(floor_count)
                ],
            },
        },
    )
    capacity_plates = tuple(
        SourceVolume(
            f"floor_{index + 1}",
            section,
            index / floor_count,
            (index + 1) / floor_count,
            "floorwise_legal_matrix4",
        )
        for index, section in enumerate(legal_sections)
    )
    projection = clip_profiled_mesh_to_floorwise_legal_solids(
        authored,
        occupied_sections=legal_sections,
        legal_sections=legal_sections,
        floor_matrices=(IDENTITY_MATRIX4,) * floor_count,
        capacity_plates=capacity_plates,
        output_origin=(0.0, 0.0),
    )
    return replace(
        authored,
        surfaces=projection.surfaces,
        volumes=capacity_plates,
        metadata={
            **authored.metadata,
            "floorwise_visual_projection": projection.certificate.to_dict(),
            "profiled_legal_section_authority_binding_hash": (
                profiled_legal_section_authority_binding_hash(
                    legal_sections,
                    legal_sections,
                    (0.0, 0.0),
                )
            ),
        },
    )


def _strictly_contracting_legal_sections():
    return (
        box(-5.0, -3.0, 5.0, 3.0),
        box(-0.50, -0.30, 0.50, 0.30),
        box(-0.45, -0.27, 0.45, 0.27),
        box(-0.40, -0.24, 0.40, 0.24),
        box(-0.35, -0.21, 0.35, 0.21),
        box(-0.30, -0.18, 0.30, 0.18),
        box(-0.25, -0.15, 0.25, 0.15),
        box(-0.20, -0.12, 0.20, 0.12),
        box(-0.15, -0.09, 0.15, 0.09),
        box(-0.10, -0.06, 0.10, 0.06),
    )


class AuthoredProjectionVisualIdentityTests(TestCase):
    def test_portfolio_phenotype_uses_renderer_authoritative_surfaces(self):
        source = _source(surfaces=_pyramid_surfaces(height=1.0))

        self.assertEqual(
            _solid_morphology_metrics(source)["phenotype"],
            authoritative_surface_morphology(source)["phenotype"],
        )

    def test_morphology_keeps_renderer_certified_short_mesh_edges(self):
        """Morphology must not coarsen a mesh accepted by the render gate."""
        epsilon = 5e-8
        vertices = (
            (0.0, 0.0, 0.0),
            (epsilon, 0.0, 0.0),
            (0.0, 10.0, 0.0),
            (0.0, 0.0, 10.0),
        )
        triangles = (
            (0, 2, 1),
            (0, 1, 3),
            (0, 3, 2),
            (1, 2, 3),
        )
        surfaces = tuple(
            SourceSurface(
                role=f"short_edge_{index}",
                volume_role="mass",
                verb="intersection",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=tuple(vertices[item] for item in triangle),
            )
            for index, triangle in enumerate(triangles)
        )
        source = _source(surfaces=surfaces)

        self.assertEqual(
            _profiled_export_completeness_failure(source, surfaces),
            "",
        )
        self.assertTrue(authoritative_surface_morphology(source)["hard_pass"])

    def test_morphology_ignores_certified_csg_sliver_for_visual_metrics(self):
        """A harmless CSG transport sliver must not erase the whole mass."""
        surfaces = list(_box_surfaces())
        top = surfaces.pop(2)
        a, b, c = top.vertices_m
        sliver_point = (0.0, -3.0 + 1e-12, 4.0)
        for index, triangle in enumerate((
            (a, b, sliver_point),
            (b, c, sliver_point),
            (c, a, sliver_point),
        )):
            surfaces.append(SourceSurface(
                role=f"csg_split_{index}",
                volume_role="mass",
                verb="intersection",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=triangle,
            ))
        surfaces = tuple(surfaces)
        source = _source(surfaces=surfaces)

        self.assertEqual(
            _profiled_export_completeness_failure(source, surfaces),
            "",
        )
        self.assertTrue(authoritative_surface_morphology(source)["hard_pass"])

    def test_surface_identity_is_invariant_to_plan_unit_conversion(self):
        normalized = _source(surfaces=_box_surfaces(
            width=1.0,
            depth=0.6,
            height=1.0,
        ))
        site_scaled = _source(surfaces=_box_surfaces(
            width=10.0,
            depth=6.0,
            height=1.0,
        ))

        self.assertAlmostEqual(
            authoritative_surface_silhouette_distance(
                normalized,
                site_scaled,
            ),
            0.0,
            places=8,
        )

    def test_profiled_clip_uses_one_continuous_legal_envelope_without_band_terraces(self):
        legal_sections = (
            box(-5.0, -3.0, 5.0, 3.0),
            box(-4.5, -2.7, 4.7, 2.7),
            box(-3.8, -2.3, 4.2, 2.3),
            box(-3.0, -1.8, 3.7, 1.8),
        )

        projected = _certified_profiled_legal_clip_source(legal_sections)
        certificate = projected.metadata["floorwise_visual_projection"]

        self.assertTrue(certificate["hard_pass"], certificate)
        self.assertEqual(
            certificate["certification_mode"],
            "floorwise_profiled_continuous_envelope_clip",
        )
        self.assertEqual(
            certificate["visible_geometry_operation"],
            "authored_profiled_mesh_continuous_legal_envelope_intersection",
        )
        internal_horizontal = []
        for surface in projected.surfaces:
            levels = {
                round(float(vertex[2]), 10)
                for vertex in surface.vertices_m
            }
            if len(levels) == 1 and next(iter(levels)) not in {0.0, 1.0}:
                internal_horizontal.append(surface.role)
        self.assertEqual(internal_horizontal, [])

    def test_r341_certified_strict_legal_contraction_is_mandatory_setback(self):
        authored = _source(surfaces=_box_surfaces(height=1.0))
        projected = _certified_profiled_legal_clip_source(
            _strictly_contracting_legal_sections()
        )

        evidence = _authored_projection_identity_evidence(authored, projected)

        self.assertTrue(evidence["mandatory_legal_field_setback"])
        self.assertFalse(evidence["hard_pass"])
        self.assertGreater(evidence["silhouette_distance"], 0.40)
        self.assertAlmostEqual(
            evidence["frozen_identity_evidence"]["raw_silhouette_distance"],
            evidence["silhouette_distance"],
            places=4,
        )
        self.assertEqual(evidence["maximum_silhouette_distance"], 0.10)
        self.assertNotIn(
            "unrequested_legal_step_collapse",
            evidence["failure_reasons"],
        )
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["failure_reasons"],
        )
        self.assertEqual(
            evidence["frozen_identity_evidence"]["predicate_version"],
            "arr.maas.authored_projection_identity_predicate.v6_bounded_legal_csg_distortion",
        )

    def test_mandatory_legal_contraction_does_not_waive_authored_identity(self):
        """A legal mask may reject an AST, but may not re-author its silhouette."""
        authored = _source(surfaces=_box_surfaces(height=1.0))
        projected = _certified_profiled_legal_clip_source(
            _strictly_contracting_legal_sections()
        )

        evidence = _authored_projection_identity_evidence(authored, projected)

        self.assertTrue(evidence["mandatory_legal_field_setback"])
        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["failure_reasons"],
        )
        self.assertTrue(evidence["typed_revision_signal"]["active"])
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["typed_revision_signal"]["reasons"],
        )

    def test_legal_csg_cannot_consume_portfolio_scale_visual_distance(self):
        """Projection distortion must stay below the final diversity spacing."""
        authored = _source(surfaces=_box_surfaces(height=1.0))
        lower = box(-5.0, -3.0, 5.0, 3.0)
        projected = _certified_profiled_legal_clip_source((
            lower,
            lower,
            box(-3.0, -1.8, 3.0, 1.8),
            box(-3.0, -1.8, 3.0, 1.8),
        ))

        evidence = _authored_projection_identity_evidence(authored, projected)

        self.assertTrue(evidence["mandatory_legal_field_setback"])
        self.assertGreater(evidence["silhouette_distance"], 0.10)
        self.assertLess(evidence["silhouette_distance"], 0.40)
        self.assertEqual(evidence["maximum_silhouette_distance"], 0.10)
        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["failure_reasons"],
        )

    def test_certified_monotone_legal_field_with_equal_lower_floors_is_contraction(self):
        authored = _source(surfaces=_box_surfaces(height=1.0))
        lower = box(-5.0, -3.0, 5.0, 3.0)
        projected = _certified_profiled_legal_clip_source((
            lower,
            lower,
            box(-4.0, -2.4, 4.0, 2.4),
            box(-3.0, -1.8, 3.0, 1.8),
        ))

        evidence = _authored_projection_identity_evidence(authored, projected)
        morphology = authoritative_surface_morphology(projected)

        self.assertTrue(evidence["mandatory_legal_field_setback"])
        self.assertFalse(morphology["visible_stepped"], morphology)
        self.assertFalse(evidence["hard_pass"], evidence)
        self.assertNotIn(
            "unrequested_legal_step_collapse",
            evidence["failure_reasons"],
        )
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["failure_reasons"],
        )

    def test_r341_identity_distance_and_synthetic_fallback_are_hard(self):
        authored = _source(surfaces=_box_surfaces(height=1.0))
        certified = _certified_profiled_legal_clip_source(
            _strictly_contracting_legal_sections()
        )
        cases = (
            ("matrix_projection", "floorwise_matrix_projection", "matrix_projection", False),
            ("matrix_replay", "floorwise_matrix_replay", "matrix_replay", False),
            ("section_loft", "floorwise_csg_section_loft", "exact_legal_section_profile_loft", False),
            ("matrix_prism", "floorwise_matrix_prism_exact_containment", "floorwise_matrix_prism_recomposition", True),
        )
        for label, mode, operation, fallback in cases:
            with self.subTest(label):
                metadata = deepcopy(certified.metadata)
                certificate = metadata["floorwise_visual_projection"]
                certificate["certification_mode"] = mode
                certificate["visible_geometry_operation"] = operation
                certificate["visible_step_fallback"] = fallback
                projected = replace(certified, metadata=metadata)

                evidence = _authored_projection_identity_evidence(
                    authored,
                    projected,
                )

                self.assertFalse(evidence["mandatory_legal_field_setback"])
                self.assertFalse(evidence["hard_pass"])
                if fallback:
                    self.assertIn(
                        "unrequested_visible_step_fallback",
                        evidence["failure_reasons"],
                    )
                self.assertIn(
                    "authored_projection_silhouette_distance_exceeded",
                    evidence["failure_reasons"],
                )
                self.assertTrue(evidence["typed_revision_signal"]["hard_gate"])

    def test_r341_equal_sections_and_invalid_bindings_remain_fail_closed(self):
        authored = _source(surfaces=_box_surfaces(height=1.0))
        equal = _certified_profiled_legal_clip_source((
            box(-2.0, -1.0, 2.0, 1.0),
            box(-2.0, -1.0, 2.0, 1.0),
        ))
        strict = _certified_profiled_legal_clip_source(
            _strictly_contracting_legal_sections()
        )
        malformed_metadata = deepcopy(strict.metadata)
        malformed_metadata["floorwise_visual_projection"][
            "exact_surface_payload_hash"
        ] = "tampered"
        unbound_metadata = deepcopy(strict.metadata)
        del unbound_metadata["profiled_legal_section_authority_binding_hash"]

        for label, projected in (
            ("equal_sections", equal),
            ("malformed_payload", replace(strict, metadata=malformed_metadata)),
            ("unbound_sections", replace(strict, metadata=unbound_metadata)),
        ):
            with self.subTest(label):
                evidence = _authored_projection_identity_evidence(
                    authored,
                    projected,
                )
                self.assertFalse(evidence["mandatory_legal_field_setback"])
    def test_surface_identity_is_invariant_to_pose_and_uniform_global_scale(self):
        visual = _box_surfaces(width=10.0, depth=6.0, height=4.0)
        transformed = _transform_surfaces(
            visual,
            scale=3.25,
            angle=37.0,
            offset=(120.0, -84.0, 17.0),
        )

        evidence = _authored_projection_identity_evidence(
            _source(surfaces=visual),
            _source(surfaces=transformed),
        )

        self.assertTrue(evidence["hard_pass"])
        self.assertAlmostEqual(evidence["silhouette_distance"], 0.0, places=5)

    def test_legal_proxy_steps_do_not_change_preserved_visual_identity(self):
        visual = _box_surfaces()
        authored = _source(surfaces=visual)
        projected = _source(
            surfaces=visual,
            volumes=(
                SourceVolume("floor_1", box(-5, -3, 5, 3), 0.0, 0.5, "fit"),
                SourceVolume("floor_2", box(-3, -2, 3, 2), 0.5, 1.0, "fit"),
            ),
        )

        evidence = _authored_projection_identity_evidence(authored, projected)

        self.assertTrue(evidence["hard_pass"])
        self.assertEqual(evidence["silhouette_distance"], 0.0)
        self.assertEqual(evidence["visual_identity_authority"], "profiled_surface_payload")
        self.assertTrue(evidence["proxy_volume_hashes_diagnostic_only"])
        self.assertNotEqual(
            evidence["authored_proxy_volume_payload_hash"],
            evidence["projected_proxy_volume_payload_hash"],
        )

    def test_large_projection_identity_change_is_hard_rejection(self):
        evidence = _authored_projection_identity_evidence(
            _source(surfaces=_box_surfaces()),
            _source(surfaces=_box_surfaces(depth=1.0)),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertEqual(evidence["maximum_silhouette_distance"], 0.40)
        self.assertFalse(evidence["projected_visible_stepped"])
        self.assertFalse(evidence["projected_pyramidal_like"])
        self.assertGreater(evidence["silhouette_distance"], 0.40)
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["failure_reasons"],
        )
        self.assertEqual(evidence["status"], "fail")
        self.assertTrue(evidence["typed_revision_signal"]["hard_gate"])

    def test_independent_z_stretch_and_compression_cross_unchanged_threshold(self):
        authored = _source(surfaces=_box_surfaces(height=4.0))
        for label, height in (("tall", 20.0), ("flat", 0.25)):
            with self.subTest(label):
                evidence = _authored_projection_identity_evidence(
                    authored,
                    _source(surfaces=_box_surfaces(height=height)),
                )
                self.assertFalse(evidence["hard_pass"])
                self.assertEqual(evidence["maximum_silhouette_distance"], 0.40)
                self.assertGreater(evidence["silhouette_distance"], 0.40)
                self.assertIn(
                    "authored_projection_silhouette_distance_exceeded",
                    evidence["failure_reasons"],
                )

    def test_valid_continuous_projection_and_large_distance_reach_legal_archive(self):
        authored = _source(surfaces=_box_surfaces(height=1.0))
        projected = _certified_profiled_legal_clip_source(
            _strictly_contracting_legal_sections()
        )
        metadata = deepcopy(projected.metadata)
        certificate = deepcopy(metadata["floorwise_visual_projection"])
        certificate["certification_mode"] = "floorwise_matrix_projection"
        certificate["visible_geometry_operation"] = "matrix_projection"
        metadata["floorwise_visual_projection"] = certificate
        surface_hash = source_surface_payload_hash(tuple(projected.surfaces))
        geometry_hash = final_floorwise_visual_geometry_hash(projected)
        metadata.update({
            "final_program_hash": "projected-step-program",
            "final_geometry_hash": geometry_hash,
            "final_surface_payload_hash": surface_hash,
            "legal_capacity_authority": {"legal_hard_pass": True},
            "authored_legal_projection_certificate": {
                "schema_version": "arr.maas.authored_legal_projection_certificate.v1",
                "status": "verified",
                "hard_pass": True,
                "input_authored_program_hash": "projected-step-program",
                "projected_surface_hash": geometry_hash,
                "projected_surface_payload_hash": surface_hash,
            },
        })
        projected = replace(projected, metadata=metadata)

        evidence = _authored_projection_identity_evidence(authored, projected)
        archived = _admit_legal_mass_candidate(
            LegalMassArchive(),
            projected,
            compiler_clean_passed=True,
            site_containment_passed=True,
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertNotIn(
            "unrequested_legal_step_collapse",
            evidence["failure_reasons"],
        )
        self.assertIn(
            "authored_projection_silhouette_distance_exceeded",
            evidence["failure_reasons"],
        )
        self.assertIsNotNone(archived)
        self.assertIsNone(_admit_legal_mass_candidate(
            LegalMassArchive(),
            projected,
            compiler_clean_passed=True,
            site_containment_passed=False,
        ))

    def test_missing_visual_surface_payload_fails_closed(self):
        evidence = _authored_projection_identity_evidence(
            _source(surfaces=_box_surfaces()),
            _source(surfaces=()),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "projected_authoritative_visual_surfaces_missing",
            evidence["failure_reasons"],
        )

    def test_open_and_degenerate_compiler_triangle_shells_fail_closed(self):
        complete = _box_surfaces()
        degenerate = list(complete)
        degenerate[0] = SourceSurface(
            role="degenerate",
            volume_role="mass",
            verb="extrude",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=((0.0, 0.0, 0.0),) * 3,
        )
        for label, malformed in (
            ("open_shell", complete[:-1]),
            ("degenerate_triangle", tuple(degenerate)),
        ):
            with self.subTest(label):
                evidence = _authored_projection_identity_evidence(
                    _source(surfaces=malformed),
                    _source(surfaces=complete),
                )
                self.assertFalse(evidence["hard_pass"])
                self.assertIn(
                    "authored_authoritative_visual_surfaces_missing",
                    evidence["failure_reasons"],
                )

    def test_inconsistent_triangle_winding_fails_closed(self):
        complete = _box_surfaces()
        inconsistent = list(complete)
        surface = inconsistent[0]
        inconsistent[0] = SourceSurface(
            role=surface.role,
            volume_role=surface.volume_role,
            verb=surface.verb,
            surface_type=surface.surface_type,
            vertices_m=tuple(reversed(surface.vertices_m)),
        )

        evidence = _authored_projection_identity_evidence(
            _source(surfaces=tuple(inconsistent)),
            _source(surfaces=complete),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "authored_authoritative_visual_surfaces_missing",
            evidence["failure_reasons"],
        )

    def test_two_closed_shells_sharing_only_one_vertex_fail_closed(self):
        first = _box_surfaces()
        second = _transform_surfaces(first, offset=(10.0, 6.0, 4.0))

        evidence = _authored_projection_identity_evidence(
            _source(surfaces=first + second),
            _source(surfaces=first),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "authored_authoritative_visual_surfaces_missing",
            evidence["failure_reasons"],
        )

    def test_authored_ast_and_required_book_noops_are_independent_failures(self):
        source = _source(surfaces=_box_surfaces())
        evidence = _authored_projection_identity_evidence(
            source,
            source,
            base_primitive_geometry_hash="geometry-same",
            authored_ast_geometry_hash="geometry-same",
            book_projection_required=True,
            pre_book_program_hash="program-same",
            post_book_program_hash="program-same",
            pre_book_geometry_hash="book-geometry-same",
            post_book_geometry_hash="book-geometry-same",
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn("authored_ast_noop", evidence["failure_reasons"])
        self.assertIn("book_projection_noop", evidence["failure_reasons"])

    def test_r335_proxy_steps_do_not_mask_independent_book_noop(self):
        visual = _box_surfaces()
        authored = _source(surfaces=visual)
        projected = _source(
            surfaces=visual,
            volumes=(
                SourceVolume("floor_1", box(-5, -3, 5, 3), 0.0, 0.34, "fit"),
                SourceVolume("floor_2", box(-4, -2, 4, 2), 0.34, 0.67, "fit"),
                SourceVolume("floor_3", box(-2, -1, 2, 1), 0.67, 1.0, "fit"),
            ),
        )

        evidence = _authored_projection_identity_evidence(
            authored,
            projected,
            book_projection_required=True,
            pre_book_program_hash="same-program",
            post_book_program_hash="same-program",
            pre_book_geometry_hash="same-geometry",
            post_book_geometry_hash="same-geometry",
        )

        self.assertEqual(evidence["failure_reasons"], ["book_projection_noop"])
        self.assertEqual(
            _authored_projection_terminal_stage(evidence),
            "book_projection_noop",
        )
        self.assertEqual(evidence["silhouette_distance"], 0.0)
