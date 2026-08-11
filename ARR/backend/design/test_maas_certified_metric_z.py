"""A certified source carries Z in one of two frames; both must certify.

`_compile_geometry_program_to_source_mass` has two identity-export modes. The
normalized one divides Z by the compiled vertical span, so Z arrives in [0, 1]
and the certificate multiplies it back by the physical height. The site-bound
one exports an already placed compilation and passes the compiled vertices
straight through, so Z is already metres.

The certificate assumed the normalized frame unconditionally. That held only
while every affine placement failed and the repair producers - which do
normalize - served every candidate. Once placement started succeeding, the
first site-bound source to reach certification raised. These tests pin both
frames so the next change to either export cannot silently break the other.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.geometry_language.projected_visual_contract import (
    AUTHORED_COORDINATE_SPACE,
    NORMALIZED_AUTHORED_COORDINATE_SPACE,
    canonical_metric_surface_payload,
)


def _surface(vertices):
    return SimpleNamespace(
        vertices_m=tuple(vertices),
        surface_type="profiled_recursive_solid_mesh",
        role="recursive_mesh_0",
        volume_role="cultural_main_gallery_hall",
        verb="geometry_program",
        operator="union",
        semantic_patch_id="",
    )


def _source(*, legal_fit_mode, vertices, height_m=15.0):
    bridge = {"legal_fit_mode": legal_fit_mode} if legal_fit_mode else {}
    return SimpleNamespace(
        surfaces=(_surface(vertices),),
        metadata={
            "geometry_program_bridge_evidence": bridge,
            "candidate_floor_context": {"height_m": height_m},
        },
    )


class CertifiedMetricZTests(SimpleTestCase):
    def test_a_normalized_source_is_scaled_by_its_physical_height(self):
        source = _source(
            legal_fit_mode="normalized_authored_identity",
            vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.5), (0.0, 1.0, 1.0)),
        )

        payload = canonical_metric_surface_payload(source)

        self.assertEqual(
            payload["source_coordinate_space"],
            NORMALIZED_AUTHORED_COORDINATE_SPACE,
        )
        self.assertEqual(
            [vertex[2] for vertex in payload["triangles"][0]["vertices_m"]],
            [0.0, 7.5, 15.0],
        )

    def test_a_site_bound_source_keeps_the_metres_it_was_placed_in(self):
        source = _source(
            legal_fit_mode="site_bound_matrix4",
            vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 7.5), (0.0, 1.0, 15.0)),
        )

        payload = canonical_metric_surface_payload(source)

        self.assertEqual(
            payload["source_coordinate_space"], AUTHORED_COORDINATE_SPACE,
        )
        self.assertEqual(
            [vertex[2] for vertex in payload["triangles"][0]["vertices_m"]],
            [0.0, 7.5, 15.0],
        )

    def test_a_site_bound_source_may_not_stand_above_its_certified_height(self):
        source = _source(
            legal_fit_mode="site_bound_matrix4",
            vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 7.5), (0.0, 1.0, 15.4)),
        )

        with self.assertRaises(ValueError) as raised:
            canonical_metric_surface_payload(source)

        self.assertIn("exceeds its certified height", str(raised.exception))

    def test_a_normalized_source_out_of_range_is_still_rejected(self):
        source = _source(
            legal_fit_mode="normalized_authored_identity",
            vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.5), (0.0, 1.0, 1.4)),
        )

        with self.assertRaises(ValueError) as raised:
            canonical_metric_surface_payload(source)

        self.assertIn("is not normalized", str(raised.exception))

    def test_a_source_with_no_declared_mode_is_treated_as_normalized(self):
        source = _source(
            legal_fit_mode="",
            vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.5), (0.0, 1.0, 1.0)),
        )

        payload = canonical_metric_surface_payload(source)

        self.assertEqual(
            payload["source_coordinate_space"],
            NORMALIZED_AUTHORED_COORDINATE_SPACE,
        )
