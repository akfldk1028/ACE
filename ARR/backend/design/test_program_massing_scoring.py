from unittest import TestCase
from unittest.mock import patch

from .maas.program_massing.scoring import attach_program_massing_evidence


class ProgramMassingScoringObservabilityTests(TestCase):
    def _score(self, *, coherence: dict, spatial: dict) -> dict:
        feature = {
            "properties": {
                "num_floors": 8,
                "source_signature": {
                    "family": "preferred_family",
                    "volume_count": 2,
                    "coherence_evidence": coherence,
                },
            }
        }
        profile = {
            "id": "test-profile",
            "design_intent": "test intent",
            "target_volume_range": [1, 4],
            "target_floor_range": [1, 20],
            "preferred_families": ["preferred_family"],
        }
        with (
            patch(
                "design.maas.program_massing.scoring.resolve_program_profile",
                return_value=profile,
            ),
            patch(
                "design.maas.program_massing.scoring.attach_program_spatial_evidence",
                return_value=spatial,
            ),
        ):
            return attach_program_massing_evidence(feature, building_type="test")

    def test_high_score_exposes_hidden_coherence_component_failure(self) -> None:
        evidence = self._score(
            coherence={
                "score": 0.99,
                "hard_pass": False,
                "failure_reasons": ["coherence_topology_not_supported"],
            },
            spatial={"architectural_score": 1.0, "hard_pass": True},
        )

        self.assertGreater(evidence["program_fit_score"], 0.9)
        self.assertFalse(evidence["hard_pass"])
        self.assertTrue(evidence["volume_hard_pass"])
        self.assertTrue(evidence["floor_hard_pass"])
        self.assertFalse(evidence["coherence_hard_pass"])
        self.assertTrue(evidence["spatial_hard_pass"])
        self.assertEqual(
            evidence["component_failure_reasons"],
            {
                "volume": [],
                "floor": [],
                "coherence": ["coherence_topology_not_supported"],
                "spatial": [],
            },
        )
        self.assertEqual(evidence["failure_reasons"], ["coherence_topology_not_supported"])

    def test_high_score_exposes_hidden_spatial_component_failure(self) -> None:
        evidence = self._score(
            coherence={"score": 1.0, "hard_pass": True},
            spatial={
                "architectural_score": 0.99,
                "hard_pass": False,
                "failures": ["circulation_path_disconnected"],
            },
        )

        self.assertGreater(evidence["program_fit_score"], 0.9)
        self.assertFalse(evidence["hard_pass"])
        self.assertTrue(evidence["coherence_hard_pass"])
        self.assertFalse(evidence["spatial_hard_pass"])
        self.assertEqual(
            evidence["component_failure_reasons"]["spatial"],
            ["circulation_path_disconnected"],
        )
        self.assertEqual(evidence["failure_reasons"], ["circulation_path_disconnected"])
