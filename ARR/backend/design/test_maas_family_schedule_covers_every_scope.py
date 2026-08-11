"""Every creative family has to meet every BOOK scope, or the grid has holes.

`balanced_family_schedule` walks families in registry order and used to take
each item's BOOK scope from its position in the schedule. Position modulo six
is family index modulo six, so family i was pinned to scope i mod 6 - not for
one pass, but permanently.

With 15 families against 6 scopes that meant every family only ever saw two
scopes and every scope only ever saw five of the fifteen families. Two thirds
of the family x scope grid was never generated, and the three blocks it did
generate were disjoint - which is how the 1/2 and 1/4 scopes ended up supplied
entirely with single-body languages and failed the program gate's hierarchy
range while 1/1 and 3/8 passed it easily.
"""

from collections import Counter

from django.test import SimpleTestCase

from design.maas.creative_family_registry import (
    BOOK_SCOPE_LABELS,
    balanced_family_schedule,
    registered_creative_families,
)


class FamilyScheduleCoversEveryScopeTests(SimpleTestCase):
    def _schedule(self, count=240):
        return balanced_family_schedule(count)

    def test_every_family_reaches_every_scope(self):
        scopes_by_family = {}
        for item in self._schedule():
            scopes_by_family.setdefault(item.family_id, set()).add(
                item.context.book_scope_label
            )

        self.assertEqual(
            len(scopes_by_family),
            len(registered_creative_families()),
        )
        for family_id, scopes in sorted(scopes_by_family.items()):
            self.assertEqual(
                set(BOOK_SCOPE_LABELS),
                scopes,
                f"{family_id} never reaches {set(BOOK_SCOPE_LABELS) - scopes}",
            )

    def test_every_scope_receives_every_family(self):
        families_by_scope = {}
        for item in self._schedule():
            families_by_scope.setdefault(
                item.context.book_scope_label, set()
            ).add(item.family_id)

        expected = {spec.family_id for spec in registered_creative_families()}
        self.assertEqual(set(BOOK_SCOPE_LABELS), set(families_by_scope))
        for scope, families in sorted(families_by_scope.items()):
            self.assertEqual(
                expected,
                families,
                f"scope {scope} never receives {expected - families}",
            )

    def test_the_scopes_stay_evenly_supplied(self):
        """Covering the grid must not come at the cost of a lopsided run."""

        counts = Counter(
            item.context.book_scope_label for item in self._schedule()
        )

        self.assertEqual(set(BOOK_SCOPE_LABELS), set(counts))
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 2)

    def test_the_schedule_is_deterministic(self):
        first = [
            (item.family_id, item.context.book_scope_label)
            for item in self._schedule()
        ]
        second = [
            (item.family_id, item.context.book_scope_label)
            for item in self._schedule()
        ]

        self.assertEqual(first, second)
