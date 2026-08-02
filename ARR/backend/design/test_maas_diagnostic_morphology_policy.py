import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import candidate_generation, portfolio_benchmark


class _StopAfterDiagnosticPolicy(RuntimeError):
    pass


class DiagnosticMorphologyPolicyTests(SimpleTestCase):
    def test_diagnostic_target_does_not_enable_visible_step_fallback(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MAAS_ALLOW_VISIBLE_STEP_FALLBACK", None)
            with TemporaryDirectory() as temporary_directory:
                with patch.object(
                    portfolio_benchmark,
                    "_load_visual_directive",
                    side_effect=_StopAfterDiagnosticPolicy,
                ):
                    with self.assertRaises(_StopAfterDiagnosticPolicy):
                        portfolio_benchmark.run_book_program_portfolios(
                            box(0.0, 0.0, 20.0, 20.0),
                            pnu="1168011800104170004",
                            output_dir=Path(temporary_directory),
                            program_slugs=("neighborhood",),
                            diagnostic_target=3,
                        )

            self.assertNotIn(
                "MAAS_ALLOW_VISIBLE_STEP_FALLBACK",
                os.environ,
            )

    def test_identity_protection_cannot_be_disabled_for_non_step_authorship(self):
        authored = SimpleNamespace(metadata={
            "geometry_program": {
                "nodes": [
                    {"operator": "box"},
                    {"operator": "bend"},
                    {"operator": "courtyard"},
                ]
            }
        })
        projected = SimpleNamespace(metadata={
            "floorwise_visual_projection": {
                "visible_step_fallback": True,
            }
        })
        authored_metrics = {
            "phenotype": "voided",
            "visible_stepped": False,
            "pyramidal_like": False,
        }
        projected_metrics = {
            "phenotype": "stepped",
            "visible_stepped": True,
            "pyramidal_like": True,
        }

        with (
            patch.dict(
                os.environ,
                {"MAAS_ALLOW_VISIBLE_STEP_FALLBACK": "1"},
            ),
            patch.object(
                candidate_generation,
                "_solid_morphology_metrics",
                side_effect=(authored_metrics, projected_metrics),
            ),
            patch.object(
                candidate_generation,
                "intrinsic_silhouette_distance",
                return_value=0.41,
            ),
        ):
            evidence = (
                candidate_generation._authored_projection_identity_evidence(
                    authored,
                    projected,
                    enforce_morphology_preservation=False,
                )
            )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "unrequested_legal_step_collapse",
            evidence["failure_reasons"],
        )
        self.assertIn(
            "unrequested_visible_step_fallback",
            evidence["failure_reasons"],
        )
