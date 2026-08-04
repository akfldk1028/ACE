from types import SimpleNamespace
from unittest import TestCase

from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_analysis import _clean_mass_gate


class _OutcomeGraph:
    def __init__(self):
        self.calls = []

    def observe_geometry_gate_failure(self, **kwargs):
        self.calls.append(kwargs)


class _Program:
    metadata = {"family": "r44-disconnected-bars"}

    def program_hash(self):
        return "r44-program-hash"


class R44CleanMassRejectionEvidenceTests(TestCase):
    def test_clean_mass_rejection_survives_report_and_outcome_graph(self):
        source = SimpleNamespace(
            volumes=(
                SimpleNamespace(footprint=box(0, 0, 4, 4)),
                SimpleNamespace(footprint=box(8, 0, 12, 4)),
            ),
            metadata={
                "family": "r44-disconnected-bars",
                "geometry_program_bridge_evidence": {
                    "program_hash": "r44-program-hash",
                },
                "geometry_program_compilation": {
                    "metrics": {
                        "component_count": 2,
                        "minimum_component_volume_ratio": 0.4,
                    },
                },
            },
            signature=lambda: {
                "surface_count": 32,
                "effective_surface_count": 12,
                "continuous_surface_evidence": {
                    "hard_pass": False,
                    "boundary_edge_count": 8,
                    "non_manifold_edge_count": 2,
                },
            },
        )

        hard_pass, evidence = _clean_mass_gate(source)
        reports = []
        graph = _OutcomeGraph()
        recorder = getattr(
            candidate_generation,
            "_record_clean_mass_rejection",
            None,
        )

        self.assertFalse(hard_pass)
        self.assertIsNotNone(recorder)
        artifact = recorder(
            source=source,
            clean_mass_evidence=evidence,
            report_records=reports,
            outcome_graph=graph,
            program_slug="neighborhood",
            source_seed="r44-seed",
            program=_Program(),
            principle_id="book:operative:split",
            book_scope="1/2",
        )

        self.assertEqual(
            artifact["subreasons"],
            ["disconnected_mesh_component_count"],
        )
        self.assertEqual(artifact["program_hash"], "r44-program-hash")
        self.assertEqual(
            artifact["geometry_family"],
            "r44-disconnected-bars",
        )
        self.assertEqual(artifact["measurements"]["components"], {
            "mesh_component_count": 2,
            "visible_component_count": 2,
            "minimum_component_volume_ratio": 0.4,
        })
        self.assertEqual(
            artifact["measurements"]["manifold"][
                "non_manifold_edge_count"
            ],
            2,
        )
        self.assertEqual(
            artifact["measurements"]["volumes"]["visible_volume_count"],
            2,
        )
        self.assertEqual(
            artifact["measurements"]["topology"]["raw_surface_count"],
            32,
        )
        self.assertEqual(
            artifact["measurements"]["polygon_quality"][
                "valid_polygon_count"
            ],
            2,
        )
        self.assertEqual(reports, [artifact])

        outcome = graph.calls[0]
        self.assertEqual(
            outcome["failure_reasons"],
            ("disconnected_mesh_component_count",),
        )
        certificate = outcome["terminal_certificate_evidence"]
        self.assertEqual(
            certificate["structural_subreason"],
            "disconnected_mesh_component_count",
        )
        self.assertEqual(certificate["program_hash"], "r44-program-hash")
        self.assertEqual(
            certificate["geometry_family"],
            "r44-disconnected-bars",
        )
        self.assertEqual(
            certificate["certificate_causes"][0]["measurements"],
            artifact["measurements"],
        )
