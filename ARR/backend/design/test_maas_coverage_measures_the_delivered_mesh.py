"""건축면적 is measured on the mesh, so the bound has to be too.

The coverage bound divides the capacity by the source's plan projection. That
denominator used to be the union of the proxy volume footprints and the
sections sampled once per floor at each floor's mid-height. Both are proxies,
and the thing finally measured is neither: it is the delivered mesh.

A body that bulges between its proxy footprints and its sampled section heights
is understated by both, and an understated denominator is a loose bound. That
is what `inflate` and `shift+notch` produce - masses whose sections do not even
close - and they were still over the capacity after the union bound went in.
"""

from dataclasses import replace
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
    _source_surface_plan_projection_area,
    compile_geometry_program_to_source_mass,
    materialize_floorwise_legal_source,
)
from design.maas.source_geometry.ir import SourceSurface, SourceVolume


GROUND_PLATE = box(0.0, 0.0, 10.0, 10.0)
UPPER_PLATE = box(5.0, 0.0, 15.0, 10.0)
PROXY_UNION_AREA_M2 = 150.0
# A mesh that bulges past both proxies and both sampled sections.
BULGED_PLAN = box(0.0, 0.0, 20.0, 10.0)
BULGED_AREA_M2 = 200.0
COVERAGE_CAPACITY_M2 = 120.0


def _plan_surfaces(plan, *, bottom=0.0, top=1.0):
    """Two triangles per horizontal face, so the mesh projects exactly `plan`."""

    minx, miny, maxx, maxy = plan.bounds
    corners = (
        (minx, miny),
        (maxx, miny),
        (maxx, maxy),
        (minx, maxy),
    )
    faces = ((0, 1, 2), (0, 2, 3))
    return tuple(
        SourceSurface(
            role=f"bulge_{height:.2f}_{index}",
            volume_role="geometry_program",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(
                (corners[corner][0], corners[corner][1], height)
                for corner in face
            ),
            operator="extrude",
            semantic_patch_id=f"bulge:{height:.2f}:{index}",
        )
        for height in (bottom, top)
        for index, face in enumerate(faces)
    )


def _active_section(source, *, height_fraction):
    active = [
        volume.footprint
        for volume in source.volumes
        if float(volume.bottom_fraction)
        <= height_fraction
        < float(volume.top_fraction)
    ]
    return unary_union(active) if active else None


class CoverageMeasuresTheDeliveredMeshTests(SimpleTestCase):
    def setUp(self):
        self.legal_sections = (
            box(-50.0, -50.0, 50.0, 50.0),
            box(-50.0, -50.0, 50.0, 50.0),
        )
        authored = compile_geometry_program_to_source_mass(
            architectural_shape_programs()[0],
            box(0.0, 0.0, 100.0, 100.0),
            target_plan_area=PROXY_UNION_AREA_M2,
            name="coverage-mesh-authored-source",
        )
        self.assertIsNotNone(authored)
        self.authored = authored

    def _source(self, surfaces):
        return replace(
            self.authored,
            footprint=unary_union((GROUND_PLATE, UPPER_PLATE)),
            volumes=(
                SourceVolume(
                    role="coverage_mesh_ground",
                    footprint=GROUND_PLATE,
                    bottom_fraction=0.0,
                    top_fraction=0.5,
                    verb="geometry_program",
                ),
                SourceVolume(
                    role="coverage_mesh_upper",
                    footprint=UPPER_PLATE,
                    bottom_fraction=0.5,
                    top_fraction=1.0,
                    verb="geometry_program",
                ),
            ),
            surfaces=surfaces,
        )

    def _materialize(self, source):
        projection = SimpleNamespace(
            certificate=FloorwiseVisualProjectionCertificate(
                hard_pass=True,
                status="certified",
                certification_mode="matrix4_authored_surface",
                failure_reasons=(),
            ),
            surfaces=source.surfaces,
        )
        sink = []
        with patch(
            "design.maas.geometry_language.source_bridge."
            "_exact_authored_mesh_section",
            side_effect=_active_section,
        ), patch(
            "design.maas.geometry_language.floorwise_visual_projection."
            "project_floorwise_visual_mesh",
            return_value=projection,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=self.legal_sections,
                target_plan_coverage=0.5,
                coverage_capacity_m2=COVERAGE_CAPACITY_M2,
                floor_capacity_plan_hash="coverage-mesh-plan",
                target_floor_areas_m2=(110.0, 110.0),
                terminal_failure_sink=sink,
            )
        self.assertIsNotNone(result, sink)
        return result

    def _delivered_plan_area(self, result):
        return float(
            unary_union([volume.footprint for volume in result.volumes]).area
        )

    def test_mesh_projection_is_the_union_of_the_projected_triangles(self):
        flush = self._source(_plan_surfaces(unary_union(
            (GROUND_PLATE, UPPER_PLATE)
        )))
        bulged = self._source(_plan_surfaces(BULGED_PLAN))

        self.assertAlmostEqual(
            _source_surface_plan_projection_area(flush),
            PROXY_UNION_AREA_M2,
            places=6,
        )
        self.assertAlmostEqual(
            _source_surface_plan_projection_area(bulged),
            BULGED_AREA_M2,
            places=6,
        )

    def test_a_mesh_wider_than_its_proxies_tightens_the_bound(self):
        flush = self._materialize(self._source(_plan_surfaces(unary_union(
            (GROUND_PLATE, UPPER_PLATE)
        ))))
        bulged = self._materialize(self._source(_plan_surfaces(BULGED_PLAN)))

        # Same proxies, same targets, same capacity: only the mesh differs. The
        # wider mesh has to be fitted smaller, or its 건축면적 exceeds the cap.
        self.assertLess(
            self._delivered_plan_area(bulged),
            self._delivered_plan_area(flush),
        )
        self.assertLessEqual(
            self._delivered_plan_area(bulged)
            * BULGED_AREA_M2
            / PROXY_UNION_AREA_M2,
            COVERAGE_CAPACITY_M2 + 1e-6,
        )
