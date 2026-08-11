from django.test import SimpleTestCase

from design.maas.book_language.competition_candidate_screen import (
    _balanced_principle_window,
    _balanced_principle_window_with_lineage_bases,
    _lineage_stable_scope_label,
    resolve_competition_breadth_generation_budget,
)
from design.maas.book_language.candidate_generation import (
    _competition_base_anchor_keys,
    _competition_exact_principle_schedule,
    _competition_exact_variant_schedule,
    _competition_language_anchor_keys,
)


class CompetitionPrincipleWindowTests(SimpleTestCase):
    def test_target_twenty_diagnostic_uses_the_same_breadth_supply(self):
        budget = resolve_competition_breadth_generation_budget(
            target_count=20,
            recursive_only=True,
            explicit_diagnostic_budget=True,
            smoke_mode=False,
        )

        self.assertEqual(len(budget["scope_labels"]), 6)
        self.assertEqual(budget["exact_shortlist_maximum"], 64)

    def test_one_probe_per_parent_rotates_through_descendant_languages(self):
        schedule = tuple(
            (index, {"principle_id": f"book:{kind}:{index}", "kind": kind})
            for index, kind in enumerate((
                "base_operative",
                "base_operative",
                "base_operative",
                "combination",
                "aggregation",
                "case_study",
            ))
        )

        selected = tuple(
            _balanced_principle_window(
                schedule,
                seed_index=seed_index,
                count=1,
            )[0][1]["kind"]
            for seed_index in range(6)
        )

        self.assertEqual(selected, (
            "base_operative",
            "base_operative",
            "base_operative",
            "combination",
            "aggregation",
            "case_study",
        ))

    def test_window_wraps_without_dropping_requested_probe_count(self):
        schedule = tuple((index, {"principle_id": str(index)}) for index in range(6))

        selected = _balanced_principle_window(
            schedule,
            seed_index=2,
            count=3,
        )

        self.assertEqual([item[0] for item in selected], [0, 1, 2])

    def test_descendant_probe_carries_its_exact_base_dependency(self):
        schedule = (
            (0, {
                "principle_id": "book:operative:expand",
                "lineage_base_operative_id": "book:operative:expand",
            }),
            (1, {
                "principle_id": "book:combination:expand+shift",
                "lineage_base_operative_id": "book:operative:expand",
            }),
        )

        selected = _balanced_principle_window_with_lineage_bases(
            schedule,
            seed_index=1,
            count=1,
        )

        self.assertEqual(
            [item[1]["principle_id"] for item in selected],
            [
                "book:operative:expand",
                "book:combination:expand+shift",
            ],
        )

    def test_scope_rotation_is_stable_for_base_and_descendant_lineage(self):
        labels = ("1/1", "1/2", "1/8")

        base_scope = _lineage_stable_scope_label(
            labels,
            seed_index=7,
            lineage_base_index=11,
            variant_index=2,
        )
        descendant_scope = _lineage_stable_scope_label(
            labels,
            seed_index=7,
            lineage_base_index=11,
            variant_index=10,
        )

        self.assertEqual(base_scope, descendant_scope)
        self.assertIn(base_scope, labels)

    def test_scope_rotation_separates_lineage_bases_under_one_seed(self):
        """Stability must not collapse into "one seed, one scope, forever".

        The scope used to be a function of the seed alone, so every language a
        seed authored drew the same base volume for the life of the run. Six
        scopes existed and each seed reached exactly one of them.
        """

        labels = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")

        reached = {
            _lineage_stable_scope_label(
                labels,
                seed_index=3,
                lineage_base_index=lineage_base_index,
                variant_index=0,
            )
            for lineage_base_index in range(len(labels))
        }

        self.assertEqual(set(labels), reached)

    def test_exact_schedule_uses_shortlist_principles_outside_local_window(self):
        principles = (
            {"principle_id": "book:operative:expand", "generation_stage": "base"},
            {"principle_id": "book:operative:shift", "generation_stage": "base"},
            {
                "principle_id": "book:case:shift+expand",
                "generation_stage": "case_study",
                "lineage_base_operative_id": "book:operative:shift",
            },
        )
        exact_keys = frozenset({
            "17:book:operative:shift:10",
            "17:book:case:shift+expand:10",
        })

        scheduled = _competition_exact_principle_schedule(
            exact_keys,
            principles,
            seed_index=17,
        )

        self.assertEqual(
            [principle["principle_id"] for _index, principle in scheduled],
            ["book:operative:shift", "book:case:shift+expand"],
        )

    def test_exact_variant_schedule_executes_keyed_variant(self):
        indexed_variants = (
            (0, ("v0",)),
            (5, ("v5",)),
            (10, ("v10",)),
        )

        scheduled = _competition_exact_variant_schedule(
            frozenset({"17:book:operative:shift:10"}),
            seed_index=17,
            principle_id="book:operative:shift",
            indexed_variants=indexed_variants,
        )

        self.assertEqual(scheduled, ((10, ("v10",)),))

    def test_publishable_base_runway_covers_every_parent_with_base_only(self):
        principles = (
            {"principle_id": "book:operative:expand", "generation_stage": "base"},
            {"principle_id": "book:operative:shift", "generation_stage": "base"},
            {
                "principle_id": "book:case:shift+expand",
                "generation_stage": "case_study",
                "lineage_base_operative_id": "book:operative:shift",
            },
        )

        keys = _competition_base_anchor_keys(
            parent_count=7,
            principles=principles,
            book_probe_count=3,
        )

        self.assertEqual(len(keys), 7)
        self.assertEqual(
            {key.rsplit(":", 1)[1] for key in keys},
            {"0", "5", "10"},
        )
        self.assertFalse(any("book:case:" in key for key in keys))

    def test_language_runway_pairs_each_descendant_with_its_exact_base(self):
        principles = (
            {"principle_id": "book:operative:expand", "generation_stage": "base"},
            {"principle_id": "book:operative:shift", "generation_stage": "base"},
            {
                "principle_id": "book:combination:expand+expand",
                "generation_stage": "combination",
                "lineage_base_operative_id": "book:operative:expand",
            },
            {
                "principle_id": "book:aggregation:shift",
                "generation_stage": "aggregation",
                "lineage_base_operative_id": "book:operative:shift",
            },
            {
                "principle_id": "book:case:expand+shift",
                "generation_stage": "case_study",
                "lineage_base_operative_id": "book:operative:expand",
            },
        )

        keys = _competition_language_anchor_keys(
            parent_count=6,
            principles=principles,
            book_probe_count=3,
        )

        self.assertEqual(len(keys), 12)
        self.assertTrue(any("book:combination:" in key for key in keys))
        self.assertTrue(any("book:aggregation:" in key for key in keys))
        self.assertTrue(any("book:case:" in key for key in keys))
