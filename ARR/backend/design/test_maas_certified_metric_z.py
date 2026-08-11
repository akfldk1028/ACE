"""Every certified source carries normalized Z, from either identity export.

`_compile_geometry_program_to_source_mass` has two identity-export modes. Both
divide Z by the compiled vertical span, so Z arrives in [0, 1] and the
certificate multiplies it back by the physical height.

The site-bound export used to pass the compiled vertices through in metres.
That stayed invisible while every affine placement failed and the repair
producers - which do normalize - served every candidate. Once placement
started succeeding it surfaced twice: first as `certified final visual source
Z is not normalized`, and then, after the certificate was taught to accept
metres, as an invalid certificate - because a metric source makes the metric
and normalized payloads identical and the contract's normalized-source
comparison meaningless. One frame is the fix; these tests pin it.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.geometry_language.projected_visual_contract import (
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

    def test_a_site_bound_source_is_normalized_like_any_other(self):
        source = _source(
            legal_fit_mode="site_bound_matrix4",
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

    def test_a_source_still_carrying_metres_is_rejected(self):
        source = _source(
            legal_fit_mode="site_bound_matrix4",
            vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 7.5), (0.0, 1.0, 15.0)),
        )

        with self.assertRaises(ValueError) as raised:
            canonical_metric_surface_payload(source)

        self.assertIn("is not normalized", str(raised.exception))

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
