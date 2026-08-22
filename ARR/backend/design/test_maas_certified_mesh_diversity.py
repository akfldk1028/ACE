from django.test import SimpleTestCase

from design.maas.book_language.diversity_contract import (
    certified_mesh_cluster_key_from_payload,
)


class CertifiedMeshDiversityTests(SimpleTestCase):
    def test_nearby_measurements_share_a_label_free_cluster(self):
        first = {
            "floor_area_by_height": [1.0, 0.81, 0.62],
            "setback_transition_sequence": [[0.02, 0.19], [0.21, 0.39]],
            "roof_breakline_profile": [0.0, 0.18, 0.42],
            "plan_profile": [1.0, 0.61, 0.41],
        }
        nearby = {
            "floor_area_by_height": [0.99, 0.79, 0.61],
            "setback_transition_sequence": [[0.01, 0.18], [0.19, 0.41]],
            "roof_breakline_profile": [0.01, 0.19, 0.39],
            "plan_profile": [0.98, 0.59, 0.39],
        }

        self.assertEqual(
            certified_mesh_cluster_key_from_payload(first),
            certified_mesh_cluster_key_from_payload(nearby),
        )

    def test_materially_different_measurements_form_another_cluster(self):
        compact = {
            "floor_area_by_height": [1.0, 1.0, 1.0],
            "setback_transition_sequence": [[0.0], [0.0]],
            "roof_breakline_profile": [0.0, 0.0, 0.0],
            "plan_profile": [1.0, 1.0, 1.0],
        }
        sectional = {
            "floor_area_by_height": [1.0, 0.6, 0.2],
            "setback_transition_sequence": [[0.4], [0.4]],
            "roof_breakline_profile": [0.0, 0.4, 0.8],
            "plan_profile": [1.0, 0.4, 0.2],
        }

        self.assertNotEqual(
            certified_mesh_cluster_key_from_payload(compact),
            certified_mesh_cluster_key_from_payload(sectional),
        )
