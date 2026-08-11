"""Coverage bounds the placement, not just the plan.

건축면적 is the building's horizontal projection (건축법 시행령 제119조 제1항
제2호) and the coverage limit bounds it. The pose search aimed only at the
legal floor sections - the sunlight envelope - so it scaled bodies until they
filled that, which on PNU 4115011300106840001 put 23 of 28 archived masses
over the 499.938 m2 limit, up to 1.94x. The downstream `bcr_limit_exceeded`
gate then discarded them, after a full legal materialization each.

The pose scales the body in plan and otherwise only translates it, so the
projected area is exactly quadratic in the scale multiplier and the bound is
closed form.
"""

from shapely.geometry import MultiPoint, Polygon, box

from django.test import SimpleTestCase

from design.maas.geometry_language.legal_field_affine_placement import (
    select_legal_field_affine_projection,
)
from design.maas.geometry_language.programs import GeometryProgramBuilder


def _box_program():
    builder = GeometryProgramBuilder("coverage_probe")
    root = builder.add(
        "primitive", "box",
        parameters={"width": 10.0, "depth": 10.0, "height": 9.0},
        semantic_role="main",
    )
    return builder.build(root, family="coverage_probe")


def _projection_area(selection) -> float:
    return float(MultiPoint([
        (vertex[0], vertex[1])
        for vertex in selection.fit.world_vertices
    ]).convex_hull.area)


class CoverageBoundedPlacementTests(SimpleTestCase):
    # A generous legal envelope, so the sections are never what limits the
    # body - the coverage capacity has to be.
    sections = (box(0.0, 0.0, 60.0, 60.0),) * 3
    targets = (300.0, 300.0, 300.0)

    def _select(self, coverage):
        return select_legal_field_affine_projection(
            _box_program(),
            legal_sections=self.sections,
            target_floor_areas_m2=self.targets,
            floor_capacity_plan_hash="probe-plan-hash",
            coverage_capacity_m2=coverage,
            minimum_aggregate_target_ratio=0.5,
        )

    def test_an_unbounded_placement_may_exceed_the_coverage_capacity(self):
        selection = self._select(None)

        self.assertIsNotNone(selection)
        # Establishes the premise: without the bound the search is free to
        # cover far more than a coverage limit would allow.
        self.assertGreater(_projection_area(selection), 400.0)

    def test_a_bounded_placement_stays_inside_the_coverage_capacity(self):
        for coverage in (250.0, 400.0, 500.0):
            with self.subTest(coverage=coverage):
                selection = self._select(coverage)

                self.assertIsNotNone(selection)
                self.assertLessEqual(
                    _projection_area(selection), coverage + 1e-6,
                )

    def test_the_bound_only_tightens_and_never_relaxes(self):
        unbounded = self._select(None)
        bounded = self._select(250.0)

        self.assertIsNotNone(unbounded)
        self.assertIsNotNone(bounded)
        self.assertLessEqual(
            _projection_area(bounded), _projection_area(unbounded) + 1e-6,
        )

    def test_a_capacity_larger_than_any_reachable_body_changes_nothing(self):
        unbounded = self._select(None)
        generous = self._select(1e9)

        self.assertIsNotNone(generous)
        self.assertAlmostEqual(
            _projection_area(generous),
            _projection_area(unbounded),
            places=6,
        )

    def test_an_impossible_capacity_yields_no_placement(self):
        self.assertIsNone(self._select(1e-6))
