"""Capacity and physical aisle regressions; no statutory rule changes."""
from unittest import TestCase
from unittest.mock import patch

from shapely.geometry import box
from shapely.ops import unary_union

from design.maas import parking_layout as p


def candidate(x, kind="standard"):
    width = p.DEFAULT_ACCESSIBLE_WIDTH_M if kind == "accessible" else p.DEFAULT_STALL_WIDTH_M
    return {"type": kind, "width_m": width, "length_m": p.DEFAULT_STALL_LENGTH_M,
            "row": 1, "orientation": "u", "start_u": x, "start_v": 0.,
            "stall_polygon": box(x, 0, x + width, p.DEFAULT_STALL_LENGTH_M),
            "drive_polygon": box(x, p.DEFAULT_STALL_LENGTH_M, x + width,
                                 p.DEFAULT_STALL_LENGTH_M + p.DEFAULT_AISLE_WIDTH_M)}


class ParkingGridCapacityTests(TestCase):
    def test_retains_better_partial_layout_after_accessible_minimum(self):
        pool = [candidate(x, "accessible") for x in (0, 3.5, 7, 10.5, 14, 17.5)]
        pool += [candidate(x) for x in (3.5, 6, 8.5, 11, 13.5, 16, 18.5)]
        selected = p._select_compact_grid_candidates(pool, required_spaces=17, accessible_spaces=1)
        self.assertEqual(len(selected), 8)
        self.assertGreaterEqual(sum(c["type"] == "accessible" for c in selected), 1)
        self.assertFalse(p._grid_group_has_overlaps(selected))

    def test_preserves_accessible_minimum_greater_than_one(self):
        pool = [candidate(0, "accessible"), candidate(3.5, "accessible"), candidate(7), candidate(9.5)]
        selected = p._select_compact_grid_candidates(pool, required_spaces=8, accessible_spaces=2)
        self.assertEqual(len(selected), 4)
        self.assertEqual(sum(c["type"] == "accessible" for c in selected), 2)

    def test_constructs_real_full_width_aisle_between_mixed_width_cells(self):
        selected = [candidate(0, "accessible"), candidate(3.5)]
        original = unary_union([c["drive_polygon"] for c in selected])
        cells = p._connect_grid_row_aisles(selected, box(0, 0, 6, 11))
        self.assertTrue(p._drive_components_connected(cells))
        self.assertAlmostEqual(unary_union(cells).difference(original).area, .2 * p.DEFAULT_AISLE_WIDTH_M)
        self.assertTrue(unary_union(cells).covers(box(3.3, 5, 3.5, 11)))
        self.assertTrue(all(cell.intersection(c["stall_polygon"]).area < 1e-6 for cell in cells for c in selected))

    def test_blocked_gap_is_not_connected_or_buffered_away(self):
        selected = [candidate(0, "accessible"), candidate(3.5)]
        drive_area = box(0, 0, 6, 11).difference(box(3.35, 7, 3.45, 9))
        cells = p._connect_grid_row_aisles(selected, drive_area)
        self.assertFalse(p._drive_components_connected(cells))
        self.assertAlmostEqual(unary_union(cells).area, sum(c["drive_polygon"].area for c in selected))

    def test_does_not_pave_through_another_selected_stall(self):
        selected = [candidate(0, "accessible"), candidate(3.5)]
        obstacle = candidate(20)
        obstacle["stall_polygon"] = box(3.35, 7, 3.45, 9)
        selected.append(obstacle)
        cells = p._connect_grid_row_aisles(selected, box(0, 0, 25, 11))
        self.assertFalse(p._drive_components_connected(cells[:2]))

    def test_frontage_on_one_disconnected_component_cannot_make_layout_pass(self):
        selected = [candidate(0, "accessible"), candidate(3.5)]
        drive_area = box(0, 0, 6, 11).difference(box(3.35, 7, 3.45, 9))
        with patch.object(p, "_select_compact_grid_candidates", return_value=selected):
            layout = p._solve_grid_parking_layout(
                box(0, 0, 6, 11), drive_polygon=drive_area,
                required_spaces=2, accessible_spaces=1, strategy="ground_surface",
                road_context={"sharedEdge": [[0, 5], [0, 11]]},
            )
        self.assertTrue(layout["grid_solver"]["entrance_verified"])
        self.assertFalse(layout["grid_solver"]["drive_components_connected"])
        self.assertNotEqual(layout["status"], "pass")
