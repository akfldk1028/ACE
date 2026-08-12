"""A vertex on the ground is not an unnormalized source.

`canonical_metric_surface_payload` requires certified visual sources to carry
normalized Z, which is right: a source already in metres would make the metric
and normalized payloads identical and the certificate's comparison meaningless.

It enforced that with `z < 0.0 or z > 1.0`. A vertex sitting exactly on the
ground or the roof arrives at 0.0 or 1.0 through a subtraction, and float64 puts
it a few 1e-17 outside. Measured on a publishable target-20 run: the whole
run died on `z=-0.000000` inside a payload whose full range was
[-0.0000, 1.0000] - a correctly normalized source, refused.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.geometry_language.projected_visual_contract import (
    canonical_metric_surface_payload,
)


HEIGHT_M = 15.0


def _source(z_values):
    return SimpleNamespace(
        surfaces=[
            SimpleNamespace(
                surface_type="profiled_recursive_solid_mesh",
                role="recursive_mesh_20",
                volume_role="primary",
                verb="extrude",
                vertices_m=[
                    (0.0, 0.0, z_values[0]),
                    (10.0, 0.0, z_values[1]),
                    (10.0, 8.0, z_values[2]),
                ],
            )
        ],
        metadata={"candidate_floor_context": {"height_m": HEIGHT_M}},
    )


class NormalizedZToleranceTests(SimpleTestCase):
    def _payload(self, z_values):
        return canonical_metric_surface_payload(_source(z_values))

    def test_a_vertex_a_float_hair_below_zero_is_accepted(self):
        payload = self._payload((-1e-17, 0.5, 1.0))

        self.assertTrue(payload)

    def test_a_vertex_a_float_hair_above_one_is_accepted(self):
        payload = self._payload((0.0, 0.5, 1.0 + 1e-17))

        self.assertTrue(payload)

    def test_the_accepted_value_is_passed_through_untouched(self):
        """Tidying it is changing it, and this payload is hashed.

        Clamping the accepted epsilon to 0.0 rewrote the bytes the payload is
        hashed from, so the recomputed final_geometry_hash stopped matching the
        certificate that sealed the unclamped value, and the publishable run
        died on identity instead of on Z.
        """

        epsilon = -1e-17
        payload = self._payload((epsilon, 0.5, 1.0))
        zs = [
            vertex[2]
            for triangle in payload["triangles"]
            for vertex in triangle["vertices_m"]
        ]

        self.assertAlmostEqual(epsilon * HEIGHT_M, min(zs), places=20)

    def test_a_source_in_metres_is_still_refused(self):
        """This is what the check exists to catch and it must keep catching it."""

        with self.assertRaises(ValueError):
            self._payload((0.0, 7.5, HEIGHT_M))

    def test_the_tolerance_is_a_physical_length_not_a_float_guess(self):
        """10 micrometres, converted through the building's own height.

        Stating it as a bare float meant guessing an order of magnitude, and the
        first guess (1e-9) was still too tight for the value the live run
        carried. A length can be argued about: 10 um is below anything a drawing
        represents and above what a mesh operation accumulates.
        """

        # 1e-5 m over 15 m of height.
        inside = 6.0e-7
        outside = 1.0e-5

        self.assertTrue(self._payload((-inside, 0.5, 1.0 + inside)))
        with self.assertRaises(ValueError):
            self._payload((0.0, 0.5, 1.0 + outside))

    def test_a_real_excursion_is_still_refused(self):
        """A centimetre below ground on a 15 m building is a geometry error."""

        for z in (-0.001, 1.001):
            with self.assertRaises(ValueError):
                self._payload((0.0, 0.5, z))

    def test_the_refusal_says_what_it_saw(self):
        """"not normalized" alone cannot be acted on; metres and drift differ."""

        with self.assertRaises(ValueError) as caught:
            self._payload((0.0, 7.5, HEIGHT_M))

        message = str(caught.exception)
        self.assertIn("z=", message)
        self.assertIn("z_range=", message)
