"""The BOOK is the language; a second implementation of one of its words is a dialect.

A dialect is allowed - `shear` genuinely is used both ways and sentences depend
on each reading - but it has to be written down. What is not allowed is drift:
a word gaining a rival implementation, or losing its recorded reading, without
anybody noticing. Both cost the same thing downstream, a jury looking at a
building that does not match its sentence.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from design.maas.book_language.execution import (
    BOOK_VERB_OPERATOR,
    book_verbs,
    conformance_report,
    operator_for,
    undeclared_divergences,
)
from design.maas.book_language.execution.canonical import semantics_of

# What was true when this test was written, on 2026-09-08: thirty-one of the
# BOOK's thirty-five words also exist in `massv2._VERBS`, and four of those had
# been read side by side. The number may fall - that is the work - and it may
# not rise without somebody recording why.
REVIEWED_BASELINE = 27


class BookOwnsItsWordsTests(SimpleTestCase):
    def test_every_book_word_names_an_operator(self):
        for verb in BOOK_VERB_OPERATOR:
            self.assertTrue(operator_for(verb), f"{verb} realizes nothing")

    def test_the_table_is_assembled_from_one_file_per_word(self):
        # Adding a word means adding a file; no table is edited anywhere, so
        # the two cannot disagree.
        self.assertEqual(len(BOOK_VERB_OPERATOR), 35)
        self.assertIn("carve", book_verbs())
        self.assertEqual(operator_for("carve"), "book_carve")

    def test_a_word_carries_the_books_own_reading_of_it(self):
        carve = semantics_of("carve")
        self.assertEqual(carve["action"],
                         "remove a bounded recess from an exposed side")
        self.assertEqual(carve["topology"],
                         "single_volume -> single_recessed_volume")

    def test_undeclared_divergences_do_not_grow(self):
        undeclared = undeclared_divergences()
        self.assertLessEqual(
            len(undeclared), REVIEWED_BASELINE,
            "a BOOK word gained a rival implementation in massv2 without anyone "
            "recording what the two readings are: "
            f"{sorted(set(undeclared))}. Read them side by side and write the "
            "reading into that word's file under DIVERGENCE, with REVIEWED = True.")

    def test_a_declared_divergence_carries_its_reading(self):
        report = conformance_report()
        for row in report["rows"]:
            if row["divergence_declared"]:
                self.assertTrue(row["reading"].strip(),
                                f"{row['verb']} is declared but says nothing")
