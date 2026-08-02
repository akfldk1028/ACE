from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import fields
import unittest

from design.maas import creative_floor_portfolio
from design.maas.creative_family_contract import CreativeFamilySpec
from design.maas.creative_family_registry import (
    CAPACITY_BANDS,
    balanced_family_schedule,
    registered_creative_families,
)


EXPECTED_ORDER = (
    "bent",
    "carved_void",
    "courtyard",
    "cross",
    "grid",
    "inflated",
    "notch",
    "radial",
    "split_wing",
    "stepped",
    "triangular_shard",
    "oblique_crystal",
    "thin_disc_cluster",
    "interlocking_tilted_discs",
    "long_span_bridge",
)
EXPECTED = set(EXPECTED_ORDER)


class CreativeFamilyRegistryTests(unittest.TestCase):
    def test_registry_has_fifteen_unique_families(self):
        specs = registered_creative_families()

        self.assertEqual({spec.family_id for spec in specs}, EXPECTED)
        self.assertEqual(len({spec.recipe_id for spec in specs}), 15)

    def test_family_spec_is_metadata_only_until_recipe_binding(self):
        self.assertEqual(
            tuple(field.name for field in fields(CreativeFamilySpec)),
            ("family_id", "recipe_id", "form_class", "contact_type"),
        )
        self.assertTrue(
            all(not hasattr(spec, "builder") for spec in registered_creative_families())
        )

    def test_portfolio_boundary_exposes_schedule_without_materialization(self):
        self.assertIs(
            creative_floor_portfolio.balanced_family_schedule,
            balanced_family_schedule,
        )
        self.assertEqual(
            tuple(
                item.family_id
                for item in creative_floor_portfolio.balanced_family_schedule(15)
            ),
            EXPECTED_ORDER,
        )

    def test_registry_and_schedule_lock_stable_order_and_remainder(self):
        specs = registered_creative_families()
        schedule = balanced_family_schedule(100)
        counts = Counter(item.family_id for item in schedule)

        self.assertEqual(tuple(spec.family_id for spec in specs), EXPECTED_ORDER)
        self.assertEqual(
            tuple(item.family_id for item in schedule[:20]),
            (*EXPECTED_ORDER, *EXPECTED_ORDER[:5]),
        )
        self.assertEqual(
            tuple(item.context.variation_index for item in schedule[:15]),
            (0,) * 15,
        )
        self.assertEqual(
            tuple(family_id for family_id in EXPECTED_ORDER if counts[family_id] == 7),
            EXPECTED_ORDER[:10],
        )
        self.assertEqual(
            tuple(family_id for family_id in EXPECTED_ORDER if counts[family_id] == 6),
            EXPECTED_ORDER[10:],
        )

    def test_balanced_hundred_schedule_limits_stepped_quota(self):
        schedule = balanced_family_schedule(100)
        counts = Counter(item.family_id for item in schedule)

        self.assertEqual(len(schedule), 100)
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)
        self.assertLessEqual(counts["stepped"], 7)

    def test_schedule_rotates_all_capacity_bands_within_each_family(self):
        schedule = balanced_family_schedule(100)
        bands_by_family: dict[str, set[str]] = defaultdict(set)
        variations_by_family: dict[str, list[int]] = defaultdict(list)
        for item in schedule:
            bands_by_family[item.family_id].add(item.context.capacity_band)
            variations_by_family[item.family_id].append(
                item.context.variation_index
            )

        self.assertEqual(set(bands_by_family), EXPECTED)
        for family_id in EXPECTED:
            self.assertEqual(bands_by_family[family_id], set(CAPACITY_BANDS))
            self.assertEqual(
                variations_by_family[family_id],
                list(range(len(variations_by_family[family_id]))),
            )


if __name__ == "__main__":
    unittest.main()
