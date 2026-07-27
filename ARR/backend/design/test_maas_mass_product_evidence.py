from django.test import SimpleTestCase

from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.mass_product_evidence import serialize_mass_product_evidence


class MaasMassProductEvidenceTest(SimpleTestCase):
    def test_serializes_floor_product_from_typed_contract_without_recalculation(self):
        builder = GeometryProgramBuilder("plan_aware_mass")
        floor = builder.add(
            "primitive",
            "box",
            parameters={
                "width": 12.0,
                "depth": 8.0,
                "height": 3.0,
            },
            semantic_role="floor_volume",
        )
        program = builder.build(
            floor,
            shared_floor_contract={
                "schema_version": "arr.maas.shared_floor_contract.v1",
                "floor_capacity_plan_hash": "capacity-plan-123",
                "floor_contract_hash": "floor-contract-123",
                "floor_height_m": 3.0,
                "totals": {
                    "num_floors": 5,
                    "total_floor_area_m2": 294.2,
                    "far_pct": 111.287,
                },
            },
            floorwise_legal_matrix_stack={
                "matrix_convention": "row_major_column_vector",
                "floor_capacity_plan_hash": "capacity-plan-123",
            },
        )
        evidence = serialize_mass_product_evidence(
            program=program,
            hard_gates={
                "projectedMetrics": {
                    "bcr_pct": 55.4,
                    "far_pct": 111.287,
                    "floor_area_m2": 294.2,
                    "floor_contract_hash": "floor-contract-123",
                },
                "parking": {
                    "required_spaces": 2,
                    "provided_spaces": 2,
                },
            },
            passport={
                "activation_graph": {
                    "nodes": [{
                        "id": "elevation:result",
                        "status": "blocked",
                        "evidence": {},
                    }],
                },
            },
        )

        self.assertEqual(evidence["num_floors"], 5)
        self.assertEqual(evidence["floor_height_m"], 3.0)
        self.assertEqual(evidence["total_floor_area_m2"], 294.2)
        self.assertEqual(evidence["bcr_pct"], 55.4)
        self.assertEqual(evidence["far_pct"], 111.287)
        self.assertEqual(evidence["parking_required"], 2)
        self.assertEqual(evidence["parking_provided"], 2)
        self.assertEqual(evidence["floor_contract_hash"], "floor-contract-123")
        self.assertEqual(evidence["floor_capacity_plan_hash"], "capacity-plan-123")
        self.assertEqual(evidence["elevation_status"], "blocked")
        self.assertEqual(evidence["matrix_convention"], "row_major_column_vector")
        self.assertEqual(len(evidence["floor_matrix_stack"]), 1)
        self.assertEqual(
            evidence["floor_matrix_stack"][0]["matrix4"],
            [
                [12.0, 0.0, 0.0, 0.0],
                [0.0, 8.0, 0.0, 0.0],
                [0.0, 0.0, 3.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        )

    def test_missing_product_evidence_is_explicitly_not_evaluated(self):
        builder = GeometryProgramBuilder("legacy_mass")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )

        evidence = serialize_mass_product_evidence(program=builder.build(root))

        self.assertIsNone(evidence["num_floors"])
        self.assertIsNone(evidence["total_floor_area_m2"])
        self.assertEqual(evidence["floor_capacity_plan_hash"], "")
        self.assertEqual(evidence["elevation_status"], "not_evaluated")
        self.assertEqual(len(evidence["floor_matrix_stack"]), 1)
