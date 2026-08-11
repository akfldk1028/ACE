"""건축면적 bounds the union of the plates, not each plate on its own.

건축법 시행령 제119조 제1항 제2호 defines 건축면적 as the horizontal projection
of the building. Every floor here rides one global plan-linear transform, so
that projection is the transformed union of the source sections. Plates that
sit side by side each fit under a per-plate cap while their union does not.

This is not hypothetical. On PNU 4115011300106840001 an archived mass sliced at
its floor mid-heights measured 499.9 m2 on both floors - exactly the 499.938 m2
capacity - while the union of those two laterally offset plates projected
587.6 m2. The capacity record reported 2 x 499.938 and the mass passed as
lawful.

The cap therefore has to be stated in ground-plate units, because the capacity
compensation loop re-fits against `ground_design_cap` to recover FAR: a cap
stated per plate lets it climb straight back to the per-plate limit.
"""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box
from shapely.ops import unary_union

from design.maas.geometry_language.floorwise_visual_projection import (
    FloorwiseVisualProjectionCertificate,
)
from design.maas.geometry_language.programs import architectural_shape_programs
from design.maas.geometry_language.source_bridge import (
    compile_geometry_program_to_source_mass,
    materialize_floorwise_legal_source,
)
from design.maas.source_geometry.ir import SourceVolume

from dataclasses import replace


GROUND_PLATE = box(0.0, 0.0, 10.0, 10.0)
UPPER_PLATE = box(5.0, 0.0, 15.0, 10.0)
# 100 m2 each, overlapping by half, so the pair projects 150 m2.
SOURCE_UNION_AREA_M2 = 150.0
COVERAGE_CAPACITY_M2 = 120.0


def _active_section(source, *, height_fraction):
    """Section the passed source the way the delivered mesh would be sectioned."""

    active = [
        volume.footprint
        for volume in source.volumes
        if float(volume.bottom_fraction)
        <= height_fraction
        < float(volume.top_fraction)
    ]
    return unary_union(active) if active else None


class CoverageBoundsTheProjectedUnionTests(SimpleTestCase):
    def setUp(self):
        # A legal envelope far larger than the coverage capacity, so the only
        # thing that can bound the body is 건축면적 itself.
        self.legal_sections = (
            box(-50.0, -50.0, 50.0, 50.0),
            box(-50.0, -50.0, 50.0, 50.0),
        )
        authored = compile_geometry_program_to_source_mass(
            architectural_shape_programs()[0],
            box(0.0, 0.0, 100.0, 100.0),
            target_plan_area=SOURCE_UNION_AREA_M2,
            name="coverage-union-authored-source",
        )
        self.assertIsNotNone(authored)
        self.source = replace(
            authored,
            footprint=unary_union((GROUND_PLATE, UPPER_PLATE)),
            volumes=(
                SourceVolume(
                    role="coverage_union_ground",
                    footprint=GROUND_PLATE,
                    bottom_fraction=0.0,
                    top_fraction=0.5,
                    verb="geometry_program",
                ),
                SourceVolume(
                    role="coverage_union_upper",
                    footprint=UPPER_PLATE,
                    bottom_fraction=0.5,
                    top_fraction=1.0,
                    verb="geometry_program",
                ),
            ),
        )
        self.projection = SimpleNamespace(
            certificate=FloorwiseVisualProjectionCertificate(
                hard_pass=True,
                status="certified",
                certification_mode="matrix4_authored_surface",
                failure_reasons=(),
            ),
            surfaces=self.source.surfaces,
        )

    def _materialize(self, coverage_capacity_m2):
        sink = []
        with patch(
            "design.maas.geometry_language.source_bridge._exact_authored_mesh_section",
            side_effect=_active_section,
        ), patch(
            "design.maas.geometry_language.floorwise_visual_projection.project_floorwise_visual_mesh",
            return_value=self.projection,
        ):
            result = materialize_floorwise_legal_source(
                self.source,
                legal_sections=self.legal_sections,
                target_plan_coverage=0.5,
                coverage_capacity_m2=coverage_capacity_m2,
                floor_capacity_plan_hash="coverage-union-plan",
                # Each floor asks for more than the union bound leaves it, but
                # no more than a single plate could hold, so the request is
                # allocatable and the capacity compensation loop still runs and
                # tries to grow the body toward the per-plate limit.
                target_floor_areas_m2=(110.0, 110.0),
                terminal_failure_sink=sink,
            )
        return result, sink

    def projected_union_area(self, result):
        return float(
            unary_union([volume.footprint for volume in result.volumes]).area
        )

    def test_the_delivered_plates_project_within_the_coverage_capacity(self):
        result, sink = self._materialize(COVERAGE_CAPACITY_M2)

        self.assertIsNotNone(result, sink)
        self.assertLessEqual(
            self.projected_union_area(result),
            COVERAGE_CAPACITY_M2 + 1e-6,
        )

    def test_no_single_plate_carries_the_whole_capacity(self):
        """The failure this pins: each plate under the cap, the union over it."""

        result, sink = self._materialize(COVERAGE_CAPACITY_M2)

        self.assertIsNotNone(result, sink)
        for volume in result.volumes:
            self.assertLessEqual(
                float(volume.footprint.area),
                COVERAGE_CAPACITY_M2 + 1e-6,
            )
        # Offset plates: the union has to exceed the largest plate, or the
        # fixture is not exercising the case it claims to.
        largest_plate = max(
            float(volume.footprint.area) for volume in result.volumes
        )
        self.assertGreater(self.projected_union_area(result), largest_plate)

    def test_without_a_declared_capacity_the_bound_does_not_apply(self):
        """The cap is opt-in; absent one, this path stays as it was."""

        result, sink = self._materialize(None)

        self.assertIsNotNone(result, sink)
        self.assertGreater(
            self.projected_union_area(result),
            COVERAGE_CAPACITY_M2,
        )
