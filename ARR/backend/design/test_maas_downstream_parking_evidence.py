from django.test import SimpleTestCase


class DownstreamParkingEvidenceTests(SimpleTestCase):
    def test_parking_layout_evidence_preserves_solver_diagnostics(self):
        from design.maas.book_language.downstream_hard_gate import (
            _parking_layout_evidence,
        )

        evidence = _parking_layout_evidence({
            "placement_mode": "grid_connected_90",
            "reason": "grid_drive_cells_need_entrance_connection_review",
            "adjacency": {"contiguous_ok": False},
            "drive_aisle_clearance": {"status": "pass"},
            "turning_clearance": {"status": "needs_review"},
            "grid_solver": {
                "drive_components_connected": False,
                "entrance_verified": False,
            },
            "stalls": [{"stall_id": "P01"}, {"stall_id": "P02"}],
            "unrelated_large_payload": {"drop": True},
        })

        self.assertEqual(evidence["placement_mode"], "grid_connected_90")
        self.assertFalse(evidence["adjacency"]["contiguous_ok"])
        self.assertFalse(evidence["grid_solver"]["entrance_verified"])
        self.assertEqual(evidence["stall_count"], 2)
        self.assertNotIn("unrelated_large_payload", evidence)
