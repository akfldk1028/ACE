from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import quality_diversity_archive as qd


class MaasQualityDiversityArchiveTest(SimpleTestCase):
    @staticmethod
    def candidate(name, score, scope, phenotype, capacity, plan, genotype):
        return SimpleNamespace(
            name=name,
            score=score,
            scope=scope,
            phenotype=phenotype,
            capacity=capacity,
            plan=plan,
            genotype=genotype,
            principle_id=f"book:{plan}",
            target_pass=True,
        )

    def test_map_elites_keeps_best_cell_member_and_rare_plan_anchor(self):
        common_best = self.candidate("common-best", 0.9, "1/1", "prismatic", "balanced", "rect", "box")
        common_worse = self.candidate("common-worse", 0.4, "1/1", "prismatic", "balanced", "rect", "box")
        rare_triangle = self.candidate("triangle", 0.3, "1/1", "prismatic", "balanced", "triangle", "prism")
        second_cell = self.candidate("void", 0.7, "1/2", "voided", "maximum", "courtyard", "difference")
        pool = [common_worse, rare_triangle, second_cell, common_best]

        with (
            patch.object(qd, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(qd, "_solid_morphology_metrics", side_effect=lambda item: {"phenotype": item.phenotype}),
            patch.object(qd, "_capacity_alternative_key", side_effect=lambda item: item.capacity),
            patch.object(qd, "_capacity_target_gate", side_effect=lambda item: item.target_pass),
            patch.object(qd, "_plan_family", side_effect=lambda item: item.plan),
            patch.object(qd, "_geometry_program_family", side_effect=lambda item: item.genotype),
            patch.object(qd, "_fingerprint", side_effect=lambda item: (item.name,)),
            patch.dict("os.environ", {"MAAS_QD_ELITES_PER_CELL": "1", "MAAS_QD_ARCHIVE_MAX_SIZE": "32"}),
        ):
            retained = qd.map_elites_archive(pool)

        names = {item.name for item in retained}
        self.assertIn("common-best", names)
        self.assertIn("triangle", names)
        self.assertIn("void", names)
        self.assertNotIn("common-worse", names)

    def test_archive_obeys_explicit_memory_bound(self):
        pool = [
            self.candidate(f"item-{index}", float(index), str(index), "p", "c", f"plan-{index}", f"g-{index}")
            for index in range(80)
        ]
        with (
            patch.object(qd, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(qd, "_solid_morphology_metrics", side_effect=lambda item: {"phenotype": item.phenotype}),
            patch.object(qd, "_capacity_alternative_key", side_effect=lambda item: item.capacity),
            patch.object(qd, "_capacity_target_gate", side_effect=lambda item: item.target_pass),
            patch.object(qd, "_plan_family", side_effect=lambda item: item.plan),
            patch.object(qd, "_geometry_program_family", side_effect=lambda item: item.genotype),
            patch.object(qd, "_fingerprint", side_effect=lambda item: (item.name,)),
            patch.dict("os.environ", {"MAAS_QD_ELITES_PER_CELL": "1", "MAAS_QD_ARCHIVE_MAX_SIZE": "32"}),
        ):
            retained = qd.map_elites_archive(pool)
        self.assertEqual(len(retained), 32)

    def test_default_policy_keeps_compatibility_runner_up_per_cell(self):
        best = self.candidate("best", 0.9, "1/1", "prismatic", "balanced", "rect", "box")
        runner_up = self.candidate("runner-up", 0.8, "1/1", "prismatic", "balanced", "rect", "box")
        third = self.candidate("third", 0.7, "1/1", "prismatic", "balanced", "rect", "box")
        with (
            patch.object(qd, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(qd, "_solid_morphology_metrics", side_effect=lambda item: {"phenotype": item.phenotype}),
            patch.object(qd, "_capacity_alternative_key", side_effect=lambda item: item.capacity),
            patch.object(qd, "_capacity_target_gate", side_effect=lambda item: item.target_pass),
            patch.object(qd, "_plan_family", side_effect=lambda item: item.plan),
            patch.object(qd, "_geometry_program_family", side_effect=lambda item: item.genotype),
            patch.object(qd, "_fingerprint", side_effect=lambda item: (item.name,)),
            patch.dict("os.environ", {"MAAS_QD_ARCHIVE_MAX_SIZE": "32"}, clear=True),
        ):
            retained = qd.map_elites_archive([third, runner_up, best])

        self.assertEqual({item.name for item in retained}, {"best", "runner-up"})
