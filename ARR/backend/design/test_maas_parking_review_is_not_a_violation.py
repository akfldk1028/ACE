"""A parking strategy this pipeline does not draw is not an illegal one.

`parking_layout.py` already separates the two verdicts. It returns `fail` when
the required count cannot be met, and `needs_mechanical_parking_review` only
when `unmet == 0` - the count *is* satisfied - while stating in its own evidence
that "mechanical equipment bay, pit, and structural grid are not modeled".
Mechanical parking is a lawful means under 주차장법; the review flag marks the
edge of what this pipeline models, not a code violation.

The downstream gate collapsed both into one hard failure. Measured on PNU
4115011300106840001: 5 of 12 selectable candidates rejected, every one of them
with its required parking count satisfied - 3 mechanical, 2 drive connectivity.
"""

from django.test import SimpleTestCase

from design.maas.book_language.downstream_hard_gate import (
    parking_layout_verdict,
)


REVIEW_STATUSES = (
    "needs_mechanical_parking_review",
    "needs_drive_connectivity_review",
    "needs_aisle_review",
    "needs_swept_path_review",
)


class ParkingReviewIsNotAViolationTests(SimpleTestCase):
    def test_a_passing_layout_raises_nothing(self):
        self.assertEqual(
            ([], []),
            parking_layout_verdict(
                layout_status="pass",
                required_spaces=12,
                provided_spaces=12,
            ),
        )

    def test_a_met_count_under_review_is_a_review_not_a_failure(self):
        for status in REVIEW_STATUSES:
            failures, reviews = parking_layout_verdict(
                layout_status=status,
                required_spaces=12,
                provided_spaces=12,
            )

            self.assertEqual([], failures, status)
            self.assertEqual([f"parking_layout_{status}"], reviews, status)

    def test_an_unmet_count_is_a_violation_however_it_is_labelled(self):
        """The count is the law. A review label does not excuse missing spaces."""

        for status in ("fail", *REVIEW_STATUSES):
            failures, reviews = parking_layout_verdict(
                layout_status=status,
                required_spaces=12,
                provided_spaces=11,
            )

            self.assertIn("parking_spaces_below_required", failures, status)
            self.assertIn(f"parking_layout_{status}", failures, status)
            self.assertEqual([], reviews, status)

    def test_an_outright_failure_stays_a_failure(self):
        failures, reviews = parking_layout_verdict(
            layout_status="fail",
            required_spaces=12,
            provided_spaces=12,
        )

        self.assertEqual(["parking_layout_fail"], failures)
        self.assertEqual([], reviews)

    def test_a_missing_layout_stays_a_failure(self):
        for status in (None, "", "missing"):
            failures, _reviews = parking_layout_verdict(
                layout_status=status,
                required_spaces=12,
                provided_spaces=12,
            )

            self.assertEqual(["parking_layout_missing"], failures, status)

    def test_an_unknown_status_is_refused_rather_than_reviewed(self):
        """Only the engine's own review vocabulary is treated as reviewable."""

        for status in ("probably_fine", "needs_a_quick_look_review"):
            failures, reviews = parking_layout_verdict(
                layout_status=status,
                required_spaces=12,
                provided_spaces=12,
            )

            self.assertEqual([f"parking_layout_{status}"], failures, status)
            self.assertEqual([], reviews, status)
