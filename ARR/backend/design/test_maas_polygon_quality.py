"""Regression contracts for scale-independent MAAS plan polygon quality."""

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box
from shapely.affinity import rotate
from shapely.ops import unary_union

from design.maas.source_geometry import (
    SourceVolume,
    evaluate_polygon_quality,
    evaluate_source_volume_coherence,
    repair_source_polygon,
)
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.polygon_quality import evaluate_site_containment


class MaasPolygonQualityTest(SimpleTestCase):
    def test_site_containment_ignores_only_metric_boolean_dust(self):
        site = box(0.0, 0.0, 20.0, 10.0)
        numerical_dust = box(1.0, 1.0, 20.00001, 4.0)
        breach = box(1.0, 1.0, 20.1, 4.0)

        accepted = evaluate_site_containment(site, [numerical_dust])
        rejected = evaluate_site_containment(site, [breach])

        self.assertTrue(accepted["hard_pass"])
        self.assertLessEqual(accepted["outside_area_m2"], accepted["area_tolerance_m2"])
        self.assertFalse(rejected["hard_pass"])
        self.assertIn("outside_site_linear_tolerance", rejected["failure_reasons"])

    def test_clean_and_concave_architectural_plans_pass(self):
        rectangle = box(0, 0, 30, 18)
        courtyard = Polygon(
            [(0, 0), (30, 0), (30, 22), (0, 22)],
            holes=[[(8, 7), (22, 7), (22, 16), (8, 16)]],
        )
        self.assertTrue(evaluate_polygon_quality(rectangle)["hard_pass"])
        self.assertTrue(evaluate_polygon_quality(courtyard)["hard_pass"])

    def test_hairline_sliver_is_a_hard_failure(self):
        sliver = box(0, 0, 100, 0.05)
        evidence = evaluate_polygon_quality(sliver)
        self.assertFalse(evidence["hard_pass"])
        self.assertIn("hairline_polygon", evidence["failure_reasons"])

    def test_starburst_outline_is_rejected_even_when_connected(self):
        polygon = Polygon([
            (0, 0), (18, 2), (7, 6), (22, 11), (7, 10),
            (18, 18), (2, 13), (5, 8), (0, 0),
        ])
        evidence = evaluate_polygon_quality(polygon)
        self.assertFalse(evidence["hard_pass"])
        self.assertIn("over_tortuous_mass_outline", evidence["failure_reasons"])

    def test_invalid_self_intersection_is_repaired(self):
        bow_tie = Polygon([(0, 0), (12, 12), (0, 12), (12, 0), (0, 0)])
        repaired = repair_source_polygon(bow_tie, minimum_area=1.0)
        self.assertIsNotNone(repaired)
        self.assertTrue(repaired.is_valid)

    def test_coherence_exposes_and_enforces_polygon_quality(self):
        volume = SourceVolume("sliver", box(0, 0, 100, 0.05), 0.0, 1.0, "extrude")
        evidence = evaluate_source_volume_coherence((volume,))
        self.assertFalse(evidence["hard_pass"])
        self.assertFalse(evidence["polygon_quality_hard_pass"])
        self.assertEqual(evidence["polygon_quality_failure_count"], 1)

    def test_folded_graph_materializes_non_flat_formal_surfaces(self):
        sequence = VerbSequence(
            "grammar_sloped_roof_envelope",
            "folded roof",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("sloped_roof_mass", {"x_ratio": 0.72, "y_ratio": 0.9}),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 42, 30), sequence)
        self.assertIsNotNone(source)
        roofs = [surface for surface in source.surfaces if surface.surface_type == "profiled_formal_roof"]
        self.assertEqual(len(roofs), 2)
        self.assertTrue(all(len({round(vertex[2], 4) for vertex in roof.vertices_m}) >= 2 for roof in roofs))
        evidence = source.signature()["continuous_surface_evidence"]
        self.assertTrue(evidence["hard_pass"])
        self.assertEqual(evidence["principle"], "folded_section")

    def test_bend_graph_materializes_continuous_ribbon_field(self):
        sequence = VerbSequence(
            "grammar_bend_ribbon",
            "bent mass",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("bend", {"axis": "x", "angle": 28.0, "factor": 0.48}),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 42, 30), sequence)
        self.assertIsNotNone(source)
        roofs = [surface for surface in source.surfaces if surface.surface_type == "profiled_formal_roof"]
        self.assertEqual(len(roofs), 3)
        self.assertTrue(all(len({round(vertex[2], 4) for vertex in roof.vertices_m}) >= 2 for roof in roofs))
        evidence = source.signature()["continuous_surface_evidence"]
        self.assertEqual(evidence["principle"], "continuous_ribbon_field")
        self.assertTrue(all("continuous_ribbon" in role for role in evidence["profiled_roles"]))
        signature = source.signature()
        self.assertGreater(signature["surface_count"], 0)
        self.assertLessEqual(signature["effective_surface_count"], 18)

    def test_split_bridge_is_two_wings_and_one_coherent_connector(self):
        sequence = VerbSequence(
            "grammar_split_bridge_connector",
            "split bridge",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("split", {"axis": "x", "gap_ratio": 0.20, "upper_ratio": 0.78}),
                VerbCall("diagonal_connect", {"angle": 16.0, "distance_ratio": 0.10}),
            ),
            notes=(
                "formal_principle=split_bridge_connector",
                "primary_language=split_bridge",
                "secondary_language=diagonal_connector",
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)

        self.assertIsNotNone(source)
        signature = source.signature()
        self.assertEqual(signature["formal_principle"], "split_bridge_connector")
        self.assertEqual(len(source.volumes), 3)
        self.assertEqual(sum("wing" in volume.role for volume in source.volumes), 2)
        self.assertEqual(sum("bridge" in volume.role or "connector" in volume.role for volume in source.volumes), 1)
        self.assertTrue(signature["coherence_evidence"]["hard_pass"])
        self.assertEqual(signature["coherence_evidence"]["redundant_overlap_pair_count"], 0)

    def test_generation_is_equivariant_to_rotated_site_axis(self):
        sequence = VerbSequence(
            "site_axis_bend",
            "site axis bend",
            (VerbCall("base", {"proportion": "site"}), VerbCall("bend", {"angle": 26.0, "factor": 0.46})),
        )
        base = box(-30, -20, 30, 20)
        rotated_base = rotate(base, 31.0, origin=(0, 0))
        aligned_source = compile_sequence_to_source_mass(base, sequence)
        rotated_source = compile_sequence_to_source_mass(rotated_base, sequence)

        self.assertIsNotNone(aligned_source)
        self.assertIsNotNone(rotated_source)
        restored = rotate(unary_union([volume.footprint for volume in rotated_source.volumes]), -31.0, origin=(0, 0))
        aligned = unary_union([volume.footprint for volume in aligned_source.volumes])
        delta = restored.symmetric_difference(aligned).area / max(aligned.union(restored).area, 1e-9)
        self.assertLess(delta, 0.01)
        frame = rotated_source.signature()["site_frame_evidence"]
        self.assertAlmostEqual(abs(frame["dominant_axis_world_degrees"]), 31.0, places=3)
