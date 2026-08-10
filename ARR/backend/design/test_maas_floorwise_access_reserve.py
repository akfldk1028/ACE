from math import cos, pi, sin

from django.test import SimpleTestCase
from shapely.affinity import affine_transform, rotate
from shapely.geometry import Polygon, box


class FloorwiseAccessReserveTests(SimpleTestCase):
    def test_matrix_fit_recovers_from_point_only_access_reserve(self):
        """A legal reserve point must not collapse an otherwise feasible mass."""
        from design.maas.geometry_language.source_bridge import (
            _access_reserve_target_center,
            _matrix_fit_polygon_to_host,
            _principal_frame,
        )

        legal = Polygon((
            (19.2093017867, 10.3031964626),
            (7.9523689583, 4.0761290228),
            (4.4638355661, 10.3707856369),
            (4.0776683608, 11.0675501865),
            (15.3279146364, 17.3083091784),
        ))
        source = box(0.0, 0.0, 1.58208, 1.0)
        source_angle, _source_width, _source_depth = _principal_frame(source)
        legal_angle, _legal_width, _legal_depth = _principal_frame(legal)
        reserve_center = _access_reserve_target_center(legal, "west")
        target_area = 68.5074

        fitted = _matrix_fit_polygon_to_host(
            source,
            legal,
            target_area=target_area,
            target_center=(reserve_center.x, reserve_center.y),
            target_angle_offset_degrees=legal_angle - source_angle,
            allow_legal_csg_projection=True,
            allow_pose_reflow=False,
        )

        self.assertIsNotNone(fitted)
        assert fitted is not None
        occupied, _matrix = fitted
        self.assertTrue(legal.buffer(1e-7).covers(occupied))
        self.assertAlmostEqual(float(occupied.area), target_area, delta=1e-4)

    def test_access_reserve_center_moves_away_in_principal_frame(self):
        from design.maas.geometry_language.source_bridge import (
            _access_reserve_target_center,
            _principal_frame,
        )

        legal = rotate(box(-10.0, -5.0, 10.0, 5.0), 28.0, origin=(0, 0))
        angle, _width, _depth = _principal_frame(legal)
        radians = angle * pi / 180.0
        along = (cos(radians), sin(radians))
        across = (-sin(radians), cos(radians))

        west = _access_reserve_target_center(legal, "west")
        east = _access_reserve_target_center(legal, "east")
        south = _access_reserve_target_center(legal, "south")
        north = _access_reserve_target_center(legal, "north")

        self.assertGreater(west.x * along[0] + west.y * along[1], 0.0)
        self.assertLess(east.x * along[0] + east.y * along[1], 0.0)
        self.assertGreater(south.x * across[0] + south.y * across[1], 0.0)
        self.assertLess(north.x * across[0] + north.y * across[1], 0.0)
        self.assertTrue(all(legal.covers(point) for point in (west, east, south, north)))

    def test_closed_access_keeps_legal_centroid(self):
        from design.maas.geometry_language.source_bridge import (
            _access_reserve_target_center,
        )

        legal = box(-10.0, -5.0, 10.0, 5.0)

        self.assertTrue(
            _access_reserve_target_center(legal, "closed").equals_exact(
                legal.centroid,
                1e-9,
            )
        )

    def test_default_reserve_uses_bounded_maximum_for_small_lot_parking(self):
        from design.maas.geometry_language.source_bridge import (
            _access_reserve_target_center,
            _principal_frame,
        )

        legal = box(-10.0, -5.0, 10.0, 5.0)
        angle, _width, _depth = _principal_frame(legal)
        radians = angle * pi / 180.0
        along = (cos(radians), sin(radians))

        west = _access_reserve_target_center(legal, "west")

        self.assertAlmostEqual(
            west.x * along[0] + west.y * along[1],
            8.0,
            places=6,
        )

    def test_shared_legal_center_is_covered_by_every_floor(self):
        """One global Matrix4 pose must be feasible across the legal stack."""
        from design.maas.geometry_language.source_bridge import (
            _shared_legal_target_center,
        )

        ground = box(0.0, 0.0, 10.0, 10.0)
        upper = box(4.0, 0.0, 10.0, 10.0)

        center = _shared_legal_target_center((ground, upper), "west")

        self.assertTrue(ground.covers(center))
        self.assertTrue(upper.covers(center))
        self.assertGreaterEqual(center.x, 4.0)

    def test_stack_translation_preserves_all_authored_floor_sections(self):
        from design.maas.geometry_language.source_bridge import (
            _optimize_floorwise_matrix_translation,
        )

        source_sections = (
            box(-3.0, -3.0, 3.0, 3.0),
            box(-2.0, -2.0, 2.0, 2.0),
        )
        legal_sections = (
            box(0.0, 0.0, 10.0, 10.0),
            box(4.0, 0.0, 10.0, 10.0),
        )
        identity = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )

        matrix = _optimize_floorwise_matrix_translation(
            identity,
            source_sections=source_sections,
            legal_sections=legal_sections,
            site_access_side="west",
        )
        transformed = tuple(
            affine_transform(section, [
                matrix[0][0], matrix[0][1],
                matrix[1][0], matrix[1][1],
                matrix[0][3], matrix[1][3],
            ])
            for section in source_sections
        )

        self.assertTrue(all(
            legal.covers(section)
            for legal, section in zip(legal_sections, transformed)
        ))

    def test_capacity_minimum_reuses_bounded_area_measurement_tolerance(self):
        from design.maas.book_language.capacity_alternatives import (
            evaluate_capacity_alternative,
        )
        from design.maas.book_language.capacity_contract import (
            measure_source_capacity,
        )
        from design.maas.book_language.mass_passport_bridge import (
            resolve_capacity_band_evidence,
        )
        from design.maas.source_geometry.ir import SourceMass

        measurement = measure_source_capacity(
            SourceMass(name="numeric-boundary", footprint=box(0, 0, 1, 1)),
            {
                "feasible_maximum_floor_area_m2": 332.322,
                "minimum_utilization": 0.6,
                "minimum_floor_area_m2": 199.393,
            },
            site_local_utm=box(0, 0, 20, 20),
            height_m=14.0,
            floors=4,
            shared_floor_contract={
                "schema_version": "arr.maas.shared_floor_contract.v1",
                "hard_pass": True,
                "floor_contract_hash": "numeric-boundary",
                "totals": {"total_floor_area_m2": 199.355},
            },
        )
        projected = evaluate_capacity_alternative({
            "alternative_id": "spatial_reserve",
            "target_utilization": 0.6,
            "feasible_minimum_utilization": 0.6,
            "program_brief_target_utilization": 0.7,
        }, measurement)
        resolved = resolve_capacity_band_evidence(
            projected,
            capacity_measurement=measurement,
        )

        self.assertTrue(measurement["hard_pass"])
        self.assertTrue(projected["selectable_capacity_hard_pass"])
        self.assertEqual(
            projected["selectable_capacity_alternative_id"],
            "spatial_reserve",
        )
        self.assertTrue(resolved["resolved_capacity_hard_pass"])
