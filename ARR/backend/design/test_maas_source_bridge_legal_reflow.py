"""Focused regressions for bounded legal reflow in the source bridge."""

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from design.maas.geometry_language.source_bridge import (
    compile_site_bound_geometry_program_to_source_mass,
    _has_single_canonical_unitbox_authority,
    _matrix_fit_polygon_to_host,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language import base_seed_program


class SourceBridgeLegalReflowTests(SimpleTestCase):
    def test_site_bound_export_uses_explicit_certified_floor_count(self):
        source = compile_site_bound_geometry_program_to_source_mass(
            base_seed_program("block"),
            box(-10.0, -10.0, 10.0, 10.0),
            floor_count=4,
        )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(4, bridge["requested_proxy_band_count"])
        self.assertEqual(4, bridge["exported_proxy_band_count"])

    def test_typed_profile_primitive_does_not_replace_unitbox_authority(self):
        unit = GeometryNode(
            "unit",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        profile = GeometryNode(
            "profile",
            "primitive",
            "loft",
            parameters={
                "profiles": [
                    {"z": 0.0, "points": [[0, 0], [2, 0], [2, 1], [0, 1]]},
                    {"z": 1.0, "points": [[0, 0.2], [2, 0.2], [2, 1], [0, 1]]},
                ],
            },
        )
        root = GeometryNode(
            "root",
            "boolean",
            "intersection",
            inputs=(unit.id, profile.id),
        )

        self.assertTrue(_has_single_canonical_unitbox_authority(
            GeometryProgram((unit, profile, root), root.id),
        ))

    def test_csg_growth_cannot_replace_a_cross_with_the_legal_host(self):
        authored = unary_union((
            box(-5.0, -1.0, 5.0, 1.0),
            box(-1.0, -5.0, 1.0, 5.0),
        ))
        legal_host = box(-3.0, -3.0, 3.0, 3.0)
        evidence = {}

        result = _matrix_fit_polygon_to_host(
            authored,
            legal_host,
            target_area=30.0,
            target_center=(0.0, 0.0),
            anisotropy_ratio=1.0,
            allow_legal_csg_projection=True,
            allow_pose_reflow=False,
            minimum_contained_area_ratio=0.78,
            fit_evidence=evidence,
        )

        self.assertIsNotNone(result)
        assert result is not None
        fitted, _matrix = result
        self.assertLess(float(fitted.area), 20.0)
        self.assertEqual(
            evidence["fit_mode"],
            "affine_maximum_contained_lower",
        )

    def test_fixed_pose_csg_keeps_best_lower_when_void_intersection_is_non_monotonic(self):
        authored = Polygon(
            ((-2.0, -2.0), (2.0, -2.0), (2.0, 2.0), (-2.0, 2.0)),
            holes=(((-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0)),),
        )
        legal_host = box(-1.0, -1.0, 1.0, 1.0)
        evidence = {}

        result = _matrix_fit_polygon_to_host(
            authored,
            legal_host,
            target_area=3.5,
            target_center=(0.0, 0.0),
            anisotropy_ratio=1.0,
            allow_legal_csg_projection=True,
            allow_pose_reflow=False,
            fit_evidence=evidence,
        )

        self.assertIsNotNone(result)
        assert result is not None
        fitted, _matrix = result
        # Growing a ring eventually puts the whole legal host inside its void.
        # The best sampled lower is near factor 1; the last positive sample is
        # much worse and must never replace it merely because it came later.
        self.assertGreater(float(fitted.area), 2.6)
        self.assertGreater(float(evidence["best_sampled_lower_area_m2"]), 2.6)

    def test_fixed_pose_csg_does_not_reauthor_requested_aspect(self):
        """Legal clipping may scale a pose, but may not search a new pose."""
        authored = box(-2.0, -1.0, 2.0, 1.0)
        legal_host = box(-1.5, -1.5, 1.5, 1.5)
        requested_anisotropy = 1.0

        result = _matrix_fit_polygon_to_host(
            authored,
            legal_host,
            target_area=float(legal_host.area) * 0.8,
            target_center=(
                float(legal_host.centroid.x),
                float(legal_host.centroid.y),
            ),
            anisotropy_ratio=requested_anisotropy,
            allow_legal_csg_projection=True,
            allow_pose_reflow=False,
        )

        self.assertIsNotNone(result)
        assert result is not None
        fitted, matrix = result
        fitted_anisotropy = (
            (float(matrix[0][0]) ** 2 + float(matrix[1][0]) ** 2) ** 0.5
            / (
                (float(matrix[0][1]) ** 2 + float(matrix[1][1]) ** 2)
                ** 0.5
            )
        )
        self.assertAlmostEqual(fitted_anisotropy, requested_anisotropy)
        self.assertTrue(legal_host.buffer(1e-7).covers(fitted))

    def test_bounded_aspect_reflow_preserves_silhouette_before_csg(self):
        authored = Polygon(
            ((0.0, 0.0), (10.0, 0.0), (10.0, 4.0), (0.0, 4.0)),
            holes=(((4.0, 1.0), (6.0, 1.0), (6.0, 3.0), (4.0, 3.0)),),
        )
        legal_host = box(-1.5, -1.5, 11.5, 5.5)

        result = _matrix_fit_polygon_to_host(
            authored,
            legal_host,
            target_area=72.0,
            anisotropy_ratio=1.0,
            allow_legal_csg_projection=True,
        )

        self.assertIsNotNone(result)
        assert result is not None
        fitted, matrix = result
        plan_determinant = abs(
            float(matrix[0][0]) * float(matrix[1][1])
            - float(matrix[0][1]) * float(matrix[1][0])
        )
        self.assertAlmostEqual(float(fitted.area), 72.0, places=5)
        self.assertAlmostEqual(
            float(fitted.area),
            float(authored.area) * plan_determinant,
            places=5,
        )
        self.assertEqual(len(fitted.interiors), 1)
        self.assertTrue(legal_host.buffer(1e-7).covers(fitted))

    def test_bounded_center_reflow_handles_concave_legal_centroid_void(self):
        authored = box(-1.0, -1.0, 1.0, 1.0)
        legal_host = Polygon((
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (7.0, 10.0),
            (7.0, 3.0),
            (3.0, 3.0),
            (3.0, 10.0),
            (0.0, 10.0),
        ))
        self.assertFalse(legal_host.covers(legal_host.centroid))

        result = _matrix_fit_polygon_to_host(
            authored,
            legal_host,
            target_area=6.0,
            target_center=(
                float(legal_host.centroid.x),
                float(legal_host.centroid.y),
            ),
            anisotropy_ratio=1.0,
            allow_legal_csg_projection=True,
        )

        self.assertIsNotNone(result)
        assert result is not None
        fitted, _matrix = result
        self.assertAlmostEqual(float(fitted.area), 6.0, places=5)
        self.assertTrue(legal_host.buffer(1e-7).covers(fitted))
