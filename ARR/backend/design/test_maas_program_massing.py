"""Program-conditioned MAAS massing contracts."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.grammar import generate_grammar_variants
from design.maas.llm_proposals import build_site_context
from design.maas.interactive.language_brain import propose_language_mutation
from design.maas.program_massing import creative_archive_sequences, creative_seed_sequences, program_archive_sequences, program_search_prior, program_seed_sequences, resolve_program_profile
from design.maas.program_massing.benchmark import run_creative_20_archive_benchmark, run_program_massing_benchmark


class MaasProgramMassingTest(SimpleTestCase):
    def test_building_use_aliases_resolve_to_distinct_profiles(self):
        self.assertEqual(resolve_program_profile("공동주택")["id"], "housing")
        self.assertEqual(resolve_program_profile("근린생활시설 카페")["id"], "cafe")
        self.assertEqual(resolve_program_profile("학교 체육관")["id"], "gymnasium")

    def test_program_seed_graphs_are_distinct_and_compilable(self):
        fingerprints = {}
        for building_type in ("공동주택", "카페", "체육관"):
            sequences = program_seed_sequences(building_type)
            self.assertGreaterEqual(len(sequences), 2)
            self.assertTrue(all(not sequence.validate() for sequence in sequences))
            fingerprints[building_type] = {tuple(call.verb for call in sequence.calls) for sequence in sequences}
            variants = generate_grammar_variants(box(0, 0, 60, 40), building_type=building_type)
            names = {variant.operator for variant in variants}
            self.assertTrue({sequence.name for sequence in sequences}.issubset(names))
        self.assertEqual(len({tuple(sorted(value)) for value in fingerprints.values()}), 3)

    def test_housing_legal_pool_receives_twenty_program_sequences(self):
        sequences = program_archive_sequences(box(0, 0, 60, 40), "housing", target_count=20)
        self.assertEqual(len(sequences), 20)
        self.assertGreaterEqual(len({item.name.split("__search_", 1)[0] for item in sequences}), 12)
        self.assertTrue(all(not item.validate() for item in sequences))

    def test_llm_site_context_contains_program_design_intent(self):
        context = build_site_context(
            site_area_m2=2400,
            building_type="체육관",
            limits={"far": 200, "bcr": 60, "height": 30, "max_seed_floors": 6},
            max_variants=20,
        )
        self.assertEqual(context["program_massing"]["profile_id"], "gymnasium")
        self.assertIn("long-span", context["program_massing"]["design_intent"])
        self.assertEqual(context["program_massing"]["search_prior"]["max_component_nodes"], 3)
        self.assertIn("hall_span_ratio", context["program_massing"]["search_prior"]["archive_descriptors"])

    def test_robotics_transfer_prior_is_program_specific_and_keeps_hard_gate_order(self):
        housing = program_search_prior("housing")
        gym = program_search_prior("gymnasium")
        self.assertNotEqual(housing["archive_descriptors"], gym["archive_descriptors"])
        self.assertEqual(gym["hard_constraint_order"][:3], ["grammar_validity", "law", "parking"])
        self.assertIn("robogrammar_2020", gym["source_ids"])

    def test_cross_program_benchmark_passes_quantitative_separation(self):
        with TemporaryDirectory() as temporary:
            result = run_program_massing_benchmark(
                output_json=Path(temporary) / "benchmark.json",
                output_png=Path(temporary) / "benchmark.png",
            )
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertEqual(result["distinct_profile_fingerprint_count"], 3)
        self.assertGreaterEqual(result["mean_program_fit"], 0.75)
        self.assertGreaterEqual(result["case_count"], 10)
        self.assertGreaterEqual(sum(item["evaluated_count"] for item in result["search_reports"].values()), 300)
        self.assertGreater(sum(item["rejected_count"] for item in result["search_reports"].values()), 0)
        self.assertGreaterEqual(min(item["architectural_score"] for item in result["rows"]), 0.88)

    def test_creative_archive_precedes_program_and_legal_projection(self):
        with TemporaryDirectory() as temporary:
            result = run_creative_20_archive_benchmark(
                output_json=Path(temporary) / "creative-20.json",
                output_png=Path(temporary) / "creative-20.png",
            )
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertFalse(result["program_conditioned"])
        self.assertFalse(result["legal_parking_checked"])
        self.assertEqual(result["selected_count"], 20)
        self.assertGreaterEqual(result["topology_count"], 12)
        self.assertGreaterEqual(result["geometric_language_count"], 14)
        self.assertGreaterEqual(result["sculptural_geometry_count"], 8)
        self.assertGreaterEqual(result["minimum_creative_score"], 0.75)
        self.assertTrue(all(item["hard_pass"] for item in result["rows"]))

    def test_creative_seeds_have_neutral_names(self):
        seeds = creative_seed_sequences()
        self.assertGreaterEqual(len(seeds), 20)
        self.assertTrue(all(item.name.startswith("creative_") for item in seeds))
        self.assertTrue(all("housing" not in item.name for item in seeds))

    def test_experimental_creative_archive_is_quarantined_from_live_pool(self):
        sequences = creative_archive_sequences(box(0, 0, 60, 40), target_count=20)
        self.assertEqual(len(sequences), 20)
        self.assertGreaterEqual(len({item.name.split("__search_", 1)[0] for item in sequences}), 12)
        variants = generate_grammar_variants(box(0, 0, 60, 40), building_type="카페")
        operators = [item.operator for item in variants]
        self.assertFalse(any(item.startswith("creative_") for item in operators))
        self.assertTrue(any(item.startswith("program_cafe_") for item in operators))
        with patch.dict("os.environ", {"MAAS_ENABLE_EXPERIMENTAL_CREATIVE_ARCHIVE": "1"}):
            experimental = generate_grammar_variants(box(0, 0, 60, 40), building_type="移댄럹")
        self.assertTrue(experimental[0].operator.startswith("creative_"))

    def test_reference_language_brain_changes_topology_and_avoids_repetition(self):
        intent = {
            "reference_principles": ["flowing ribbon with a curved court and continuous roof"],
            "operation_rationales": ["embracing landscape roof"],
        }
        first = propose_language_mutation(reference_intent=intent, current_language="creative_court_bar")
        self.assertIsNotNone(first)
        self.assertEqual(first.sequence.name, "creative_ribbon_campus")
        second = propose_language_mutation(
            reference_intent=intent,
            current_language="creative_court_bar",
            used_languages=("creative_ribbon_campus",),
        )
        self.assertIsNotNone(second)
        self.assertEqual(second.sequence.name, "creative_arc_court")
        self.assertNotEqual(first.diversity_group, "cluster")

    def test_reference_language_brain_keeps_lego_as_one_bounded_family(self):
        intent = {"reference_principles": ["interlocking lego modular blocks arranged as a village cluster"]}
        first = propose_language_mutation(reference_intent=intent)
        self.assertEqual(first.sequence.name, "creative_voxel_cascade")
        second = propose_language_mutation(reference_intent=intent, used_languages=(first.sequence.name,))
        self.assertEqual(second.sequence.name, "creative_cluster_village")
