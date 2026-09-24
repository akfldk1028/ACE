from dataclasses import replace
import unittest

from iclr2027.oacs_claim_ledger import ClaimLedgerV1, ClaimRecordV1
from iclr2027.oacs_review_harness import (
    FindingV1,
    ReviewHarnessError,
    adjudicate_review_union,
    build_review_package,
    lock_review_record,
    locked_review_bytes,
    review_package_bytes,
    verify_locked_review_bytes,
    verify_locked_reviews,
    verify_review_package_bytes,
)


ICLR_QUESTIONS = (
    "What precise problem does the paper address?",
    "Is the approach motivated and situated in prior work?",
    "Are the claims correct and rigorously supported?",
    "Does the work contribute significant knowledge or value?",
)
ROLES = (
    "problem_novelty",
    "causal_statistics",
    "experiment_reproducibility",
    "adversarial_falsifier",
)
PREAMBLE = (
    "Read only the listed frozen inputs. Do not inspect another review. State the\n"
    "paper's exact problem and contribution before judging it. Cite an exact claim\n"
    "ID and evidence hash for every decision-relevant finding. Answer the four ICLR\n"
    "questions. Give the strongest accept case, strongest reject case, an explicit\n"
    "falsifier, the smallest correction, and one of ACCEPT, REVISE, or REJECT. Do\n"
    "not infer completed results from prospective work and do not use a score from\n"
    "another reviewer."
)


class OacsReviewHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_hashes = ("1" * 64, "2" * 64)
        self.ledger = ClaimLedgerV1(
            design_sha256="a" * 64,
            records=(
                ClaimRecordV1(
                    claim_id="claim:causal-c1",
                    exact_span="The intervention changes the coordination mechanism.",
                    claim_type="causal_mechanism",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="The preregistered contrast is nonpositive.",
                    severity_if_wrong="critical",
                ),
                ClaimRecordV1(
                    claim_id="claim:limit-l1",
                    exact_span="The result is limited to the registered context.",
                    claim_type="limitation",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="A held-out context reproduces the same estimate.",
                    severity_if_wrong="important",
                ),
                ClaimRecordV1(
                    claim_id="claim:policy-p1",
                    exact_span="The policy reduces coordination burden.",
                    claim_type="policy_consequence",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="The registered policy contrast is nonpositive.",
                    severity_if_wrong="important",
                ),
                ClaimRecordV1(
                    claim_id="claim:problem-p1",
                    exact_span="Teams can lose value through coordination burden.",
                    claim_type="problem",
                    status="executed",
                    evidence_sha256=("1" * 64,),
                    falsifier="The observed coordination burden is zero.",
                    severity_if_wrong="important",
                ),
                ClaimRecordV1(
                    claim_id="claim:scope-s1",
                    exact_span="The claim concerns multi-agent teams.",
                    claim_type="domain_scope",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="The registered sample does not contain a team.",
                    severity_if_wrong="minor",
                ),
            ),
        )

    def _package(self):
        return build_review_package(self.ledger, self.source_hashes)

    def _finding(self, severity="I", evidence_sha256="1" * 64, resolved=False):
        return FindingV1(
            failure_code="support-gap",
            severity=severity,
            claim_id="claim:problem-p1",
            evidence_sha256=evidence_sha256,
            falsifier_result="The observed burden does not establish a causal effect.",
            resolved=resolved,
        )

    def locked_reviews(self, one_important=False):
        package = self._package()
        reviews = []
        for assignment in package.assignments:
            findings = (
                (self._finding(),)
                if one_important and assignment.role == ROLES[-1]
                else ()
            )
            reviews.append(
                lock_review_record(
                    role=assignment.role,
                    assignment_sha256=assignment.assignment_sha256,
                    verdict="REJECT" if findings else "ACCEPT",
                    findings=findings,
                )
            )
        return package, tuple(reviews)

    def test_exact_roles_and_official_questions(self):
        package = self._package()
        self.assertEqual(tuple(row.role for row in package.assignments), ROLES)
        for row in package.assignments:
            self.assertNotIn("other review", row.visible_inputs)
            self.assertEqual(row.iclr_questions, ICLR_QUESTIONS)
            self.assertEqual(
                row.iclr_guidelines_url,
                "https://iclr.cc/Conferences/2027/ReviewerGuidelines",
            )
            self.assertTrue(row.prompt.startswith(PREAMBLE))

    def test_valid_four_role_package_and_locked_records_round_trip(self):
        package, reviews = self.locked_reviews()
        self.assertEqual(
            verify_review_package_bytes(review_package_bytes(package)), package
        )
        self.assertEqual(
            verify_locked_review_bytes(locked_review_bytes(reviews[0])), reviews[0]
        )
        self.assertEqual(verify_locked_reviews(package, reviews), reviews)

    def test_meta_review_cannot_average_important_away(self):
        package, reviews = self.locked_reviews(one_important=True)
        with self.assertRaisesRegex(ReviewHarnessError, "unresolved important"):
            adjudicate_review_union(package, reviews, proposed_status="go")

    def test_adjudication_rejects_fully_rehashed_forged_assignment_and_evidence(self):
        package, reviews = self.locked_reviews()
        forged_assignment = list(reviews)
        forged_assignment[0] = lock_review_record(
            role=forged_assignment[0].role,
            assignment_sha256="f" * 64,
            verdict="ACCEPT",
            findings=(),
        )
        with self.assertRaisesRegex(ReviewHarnessError, "assignment"):
            adjudicate_review_union(
                package, tuple(forged_assignment), proposed_status="hold"
            )

        forged_evidence = list(reviews)
        forged_evidence[-1] = lock_review_record(
            role=forged_evidence[-1].role,
            assignment_sha256=forged_evidence[-1].assignment_sha256,
            verdict="REJECT",
            findings=(self._finding(evidence_sha256="f" * 64),),
        )
        with self.assertRaisesRegex(ReviewHarnessError, "evidence"):
            adjudicate_review_union(
                package, tuple(forged_evidence), proposed_status="hold"
            )

    def test_conflicting_duplicate_identity_cannot_hide_unresolved_important(self):
        package, reviews = self.locked_reviews()
        conflicting = list(reviews)
        conflicting[0] = lock_review_record(
            role=conflicting[0].role,
            assignment_sha256=conflicting[0].assignment_sha256,
            verdict="ACCEPT",
            findings=(self._finding(severity="M", resolved=True),),
        )
        conflicting[1] = lock_review_record(
            role=conflicting[1].role,
            assignment_sha256=conflicting[1].assignment_sha256,
            verdict="REJECT",
            findings=(
                FindingV1(
                    failure_code="support-gap",
                    severity="I",
                    claim_id="claim:problem-p1",
                    evidence_sha256="1" * 64,
                    falsifier_result="The record is insufficient for the claimed causal effect.",
                    resolved=False,
                ),
            ),
        )
        with self.assertRaisesRegex(ReviewHarnessError, "conflicting duplicate"):
            adjudicate_review_union(package, tuple(conflicting), proposed_status="go")

    def test_meta_review_preserves_union_without_score_or_vote(self):
        package, reviews = self.locked_reviews(one_important=True)
        union = adjudicate_review_union(package, reviews, proposed_status="hold")
        self.assertEqual(len(union), 1)
        self.assertEqual(union[0].failure_code, "support-gap")
        self.assertEqual(union[0].severity, "I")

    def test_majority_accept_cannot_override_one_important_reject(self):
        package, reviews = self.locked_reviews(one_important=True)
        self.assertEqual(tuple(row.verdict for row in reviews).count("ACCEPT"), 3)
        with self.assertRaisesRegex(ReviewHarnessError, "unresolved important"):
            adjudicate_review_union(package, reviews, proposed_status="go")

    def test_altered_prompt_bytes_fail_closed(self):
        raw = review_package_bytes(self._package())
        altered = raw.replace(b"Read only", b"Read oNly", 1)
        with self.assertRaises(ReviewHarnessError):
            verify_review_package_bytes(altered)

    def test_stale_assignment_hash_fails_closed(self):
        package, reviews = self.locked_reviews()
        stale = list(reviews)
        stale[0] = lock_review_record(
            role=stale[0].role,
            assignment_sha256="f" * 64,
            verdict=stale[0].verdict,
            findings=stale[0].findings,
        )
        with self.assertRaisesRegex(ReviewHarnessError, "assignment"):
            verify_locked_reviews(package, tuple(stale))

    def test_invented_evidence_hash_fails_closed(self):
        package, reviews = self.locked_reviews()
        forged = list(reviews)
        forged[-1] = lock_review_record(
            role=forged[-1].role,
            assignment_sha256=forged[-1].assignment_sha256,
            verdict="REJECT",
            findings=(self._finding(evidence_sha256="f" * 64),),
        )
        with self.assertRaisesRegex(ReviewHarnessError, "evidence"):
            verify_locked_reviews(package, tuple(forged))

    def test_cross_visible_review_path_fails_closed(self):
        raw = review_package_bytes(self._package())
        altered = raw.replace(b"claim_ledger_sha256=", b"other review=", 1)
        with self.assertRaises(ReviewHarnessError):
            verify_review_package_bytes(altered)

    def test_reordered_locked_records_fail_closed(self):
        package, reviews = self.locked_reviews()
        with self.assertRaisesRegex(ReviewHarnessError, "role order"):
            verify_locked_reviews(package, tuple(reversed(reviews)))

    def test_score_injection_and_noncanonical_review_bytes_fail_closed(self):
        _, reviews = self.locked_reviews()
        raw = locked_review_bytes(reviews[0])
        score_injected = raw.replace(
            b'"review_sha256"', b'"score":10,"review_sha256"', 1
        )
        for altered in (score_injected, raw[:-1], raw.replace(b"{", b"{ ", 1)):
            with self.subTest(altered=altered[:32]):
                with self.assertRaises(ReviewHarnessError):
                    verify_locked_review_bytes(altered)

    def test_duplicate_review_keys_and_native_boolean_requirement_fail_closed(self):
        _, reviews = self.locked_reviews(one_important=True)
        raw = locked_review_bytes(reviews[-1])
        duplicate = raw.replace(
            b'"role":"adversarial_falsifier",',
            b'"role":"adversarial_falsifier","role":"adversarial_falsifier",',
            1,
        )
        non_boolean = raw.replace(b'"resolved":false', b'"resolved":0', 1)
        for altered in (duplicate, non_boolean):
            with self.subTest(altered=altered[:64]):
                with self.assertRaises(ReviewHarnessError):
                    verify_locked_review_bytes(altered)

    def test_finding_requires_bound_claim_evidence_and_falsifier(self):
        package, reviews = self.locked_reviews()
        forged = list(reviews)
        forged[0] = lock_review_record(
            role=forged[0].role,
            assignment_sha256=forged[0].assignment_sha256,
            verdict="REJECT",
            findings=(replace(self._finding(), claim_id="claim:missing"),),
        )
        with self.assertRaisesRegex(ReviewHarnessError, "claim"):
            verify_locked_reviews(package, tuple(forged))
        with self.assertRaisesRegex(ReviewHarnessError, "nonempty"):
            replace(self._finding(), falsifier_result="")


if __name__ == "__main__":
    unittest.main()
