"""A floor-band serialization must be judged by its bands, not by a flat five.

`_clean_mass_gate` already says this: "A floorwise projection serializes one
authored connected building as legal height bands. Its volume count is therefore
driven by the law-derived floor count, not by visible object/component
complexity." It read that floor count only from an attached stack record, and
where the record was absent it applied the flat complexity limit to exactly the
kind of mass the comment excludes.

Nothing noticed while stacks were two to four floors tall. Once ground-take
bands made a scheme hold the ground and go up, masses with mesh_component_count
1 - one connected building - were rejected at 9 volumes against a limit of 5,
and program_passed halved on PNU 4115011300106840001.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import portfolio_benchmark


def _volume(bottom, top):
    return SimpleNamespace(
        bottom_fraction=bottom,
        top_fraction=top,
        footprint=box(0.0, 0.0, 10.0, 10.0),
    )


def _source(volumes, *, stack=None):
    metadata = {
        "geometry_program_bridge_evidence": {"program_hash": "recursive"},
        "geometry_program_compilation": {"metrics": {
            "component_count": 1,
            "minimum_component_volume_ratio": 1.0,
        }},
    }
    if stack is not None:
        metadata["floorwise_legal_matrix_stack"] = stack
    return SimpleNamespace(
        volumes=tuple(volumes),
        metadata=metadata,
        signature=lambda: {
            "surface_count": 248,
            "effective_surface_count": 12,
            "continuous_surface_evidence": {"hard_pass": True},
        },
    )


class CleanMassReadsBandsFromFormTests(SimpleTestCase):
    def test_a_tall_one_body_stack_is_measured_by_its_bands(self):
        """Three parts on each of three bands is one building, not nine objects."""

        volumes = [
            _volume(index / 3.0, (index + 1) / 3.0)
            for index in range(3)
            for _part in range(3)
        ]

        hard_pass, evidence = portfolio_benchmark._clean_mass_gate(_source(volumes))

        self.assertEqual(3, evidence["floor_band_count"])
        self.assertEqual(9, evidence["visible_volume_count"])
        self.assertNotIn("visible_volume_count", evidence["failure_reasons"])
        self.assertTrue(hard_pass, evidence)

    def test_an_unbanded_mass_keeps_the_flat_limit(self):
        """One height band is one band; the old complexity limit still applies."""

        volumes = [_volume(0.0, 1.0) for _ in range(6)]

        hard_pass, evidence = portfolio_benchmark._clean_mass_gate(_source(volumes))

        self.assertEqual(1, evidence["floor_band_count"])
        self.assertEqual(5, evidence["volume_limit"])
        self.assertIn("visible_volume_count", evidence["failure_reasons"])
        self.assertFalse(hard_pass)

    def test_the_attached_stack_record_still_wins(self):
        volumes = [_volume(0.0, 1.0) for _ in range(6)]

        _hard_pass, evidence = portfolio_benchmark._clean_mass_gate(
            _source(volumes, stack={"status": "materialized", "floor_count": 6}),
        )

        self.assertEqual(6, evidence["floor_band_count"])

    def test_an_unmaterialized_stack_record_is_not_believed(self):
        volumes = [_volume(0.0, 1.0) for _ in range(6)]

        _hard_pass, evidence = portfolio_benchmark._clean_mass_gate(
            _source(volumes, stack={"status": "infeasible", "floor_count": 6}),
        )

        self.assertEqual(1, evidence["floor_band_count"])

    def test_a_volume_that_states_no_band_is_not_counted_as_one(self):
        """Fail closed: no band stated means the flat limit, never an assumed band."""

        _hard_pass, evidence = portfolio_benchmark._clean_mass_gate(
            _source([object() for _ in range(6)]),
        )

        self.assertEqual(0, evidence["floor_band_count"])
        self.assertEqual(5, evidence["volume_limit"])
