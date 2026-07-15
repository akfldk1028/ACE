"""Contracts for the architect-supplied BOOK language registry."""

from django.test import SimpleTestCase

from design.maas.book_language import audited_book_language_registry, book_base_verbs, build_book_language_registry
from design.maas.grammar.vocab import BOOK_BASE_VERBS, SUPPORTED_VERBS


class MaasBookLanguageRegistryTest(SimpleTestCase):
    def test_registry_reconciles_all_pages_and_principle_groups(self):
        registry = build_book_language_registry()

        self.assertEqual(registry["page_count"], 69)
        self.assertEqual(registry["base_volume_count"], 6)
        self.assertEqual([item["label"] for item in registry["base_volumes"]], [
            "1/1 Base Volume", "3/8 Base Volume", "1/2 Base Volume",
            "1/4 Base Volume", "1/8 Base Volume", "1/16 Base Volume",
        ])
        self.assertEqual(len(registry["pages"]), 69)
        self.assertEqual(registry["base_operative_count"], 30)
        self.assertEqual(registry["combination_count"], 20)
        self.assertEqual(registry["aggregation_recipe_count"], 9)
        self.assertEqual(registry["case_study_count"], 10)
        self.assertEqual([page["page"] for page in registry["pages"]], list(range(1, 70)))
        self.assertTrue(all(page["sha256"] for page in registry["pages"]))
        self.assertEqual(len(registry["taxonomy"]["operations"]["add"]["single"]), 3)
        self.assertEqual(len(registry["taxonomy"]["operations"]["add"]["multiple"]), 4)
        self.assertEqual(len(registry["taxonomy"]["operations"]["displace"]["single"]), 4)
        self.assertEqual(len(registry["taxonomy"]["operations"]["displace"]["multiple"]), 7)
        self.assertEqual(len(registry["taxonomy"]["operations"]["subtract"]["single"]), 8)
        self.assertEqual(len(registry["taxonomy"]["operations"]["subtract"]["multiple"]), 4)
        self.assertEqual(len(registry["pages"][2]["principle_ids"]), 6)

    def test_every_base_operative_preserves_book_procedure_and_variation_semantics(self):
        base = [item for item in build_book_language_registry()["principles"] if item["kind"] == "base_operative"]

        self.assertEqual(len(base), 30)
        self.assertTrue(all(len(item["semantics"]["procedure"]) == 3 for item in base))
        self.assertTrue(all(item["semantics"]["variation_parameters"] for item in base))
        self.assertTrue(all(item["semantics"]["base_volume_fractions"] == ["1/1", "3/8", "1/2", "1/4", "1/8", "1/16"] for item in base))
        self.assertEqual(next(item for item in base if item["label"] == "bend")["semantics"]["output_topology"], "single_bent_volume")
        self.assertEqual(next(item for item in base if item["label"] == "merge")["semantics"]["output_topology"], "single_fused_volume")

    def test_case_studies_preserve_the_books_combined_operations(self):
        cases = {item["page_refs"][0]: item for item in build_book_language_registry()["case_studies"]}

        self.assertEqual(cases[60]["verbs"], ["carve", "offset"])
        self.assertEqual(cases[61]["verbs"], ["embed", "branch"])
        self.assertEqual(cases[63]["verbs"], ["expand", "nest"])
        self.assertEqual(cases[69]["verbs"], ["overlap", "rotate"])

    def test_book_aggregation_display_and_execution_orders_are_both_preserved(self):
        aggregations = [item for item in build_book_language_registry()["principles"] if item["kind"] == "aggregation"]
        reflect_expand = next(item for item in aggregations if item["label"].startswith("reflect"))

        self.assertEqual(reflect_expand["verbs"], ["reflect", "expand"])
        self.assertEqual(reflect_expand["execution_verbs"], ["expand", "reflect"])

    def test_page_count_is_not_presented_as_principle_count(self):
        registry = build_book_language_registry()
        principles = registry["principles"]

        self.assertEqual(len([item for item in principles if item["kind"] == "base_operative"]), 30)
        self.assertEqual(len([item for item in principles if item["kind"] == "combination"]), 20)
        self.assertEqual(len(registry["case_studies"]), 10)
        self.assertNotEqual(registry["page_count"], len(principles))

    def test_compile_evidence_is_required_for_active_status(self):
        principle_id = "book:operative:expand"
        typed = build_book_language_registry()["principles"]
        active = build_book_language_registry({
            principle_id: {"compile_passed": True, "hard_pass": True, "geometry_delta": 0.12},
        })["principles"]

        self.assertEqual(next(item for item in typed if item["principle_id"] == principle_id)["status"], "typed")
        self.assertEqual(next(item for item in active if item["principle_id"] == principle_id)["status"], "active")

    def test_base_operative_vocabulary_is_exact(self):
        self.assertEqual(len(book_base_verbs()), 30)
        self.assertIn("inflate", book_base_verbs())
        self.assertIn("rotate", book_base_verbs())
        self.assertIn("puncture", book_base_verbs())
        self.assertEqual(BOOK_BASE_VERBS, set(book_base_verbs()))
        self.assertTrue(BOOK_BASE_VERBS.issubset(SUPPORTED_VERBS))

    def test_every_base_operative_has_multi_site_compile_evidence(self):
        registry = audited_book_language_registry()
        base = [item for item in registry["principles"] if item["kind"] == "base_operative"]

        self.assertEqual(len(base), 30)
        self.assertTrue(all(item["compile_evidence"]["compile_pass_count"] == 4 for item in base))
        self.assertTrue(all(item["status"] == "active" for item in base))
        self.assertTrue(all(item["compile_evidence"]["clean_pass_count"] == 4 for item in base))

    def test_all_book_operations_combinations_and_aggregations_have_clean_execution_evidence(self):
        registry = audited_book_language_registry()

        self.assertEqual(len(registry["principles"]), 59)
        self.assertTrue(all(item["status"] == "active" for item in registry["principles"]))
        self.assertTrue(all(item["compile_evidence"]["clean_pass_count"] == 4 for item in registry["principles"]))
