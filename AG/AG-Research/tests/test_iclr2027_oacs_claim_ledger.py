from dataclasses import replace
import unittest

from iclr2027.oacs_claim_ledger import (
    ClaimLedgerError,
    ClaimLedgerV1,
    ClaimRecordV1,
    claim_ledger_bytes,
    verify_claim_ledger_bytes,
)


class OacsClaimLedgerTests(unittest.TestCase):
    def _record(self) -> ClaimRecordV1:
        return ClaimRecordV1(
            claim_id="claim:mechanism-e2",
            exact_span=(
                "Residual-obligation--capability alignment changes "
                "collaboration payoff."
            ),
            claim_type="causal_mechanism",
            status="prospective",
            evidence_sha256=(),
            falsifier=(
                "The cost-matched high-minus-low complete-bundle contrast "
                "has a nonpositive site-clustered lower bound."
            ),
            severity_if_wrong="critical",
        )

    def _ledger(self) -> ClaimLedgerV1:
        return ClaimLedgerV1(
            design_sha256="a" * 64,
            records=(
                ClaimRecordV1(
                    claim_id="claim:limit-l1",
                    exact_span="Observed outcomes do not establish generality.",
                    claim_type="limitation",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="A held-out domain reproduces the same effect estimate.",
                    severity_if_wrong="important",
                ),
                self._record(),
                ClaimRecordV1(
                    claim_id="claim:policy-c3",
                    exact_span="Budgeting complete bundles can improve collaboration.",
                    claim_type="policy_consequence",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="The complete-bundle policy contrast is nonpositive.",
                    severity_if_wrong="important",
                ),
                ClaimRecordV1(
                    claim_id="claim:problem-p1",
                    exact_span="Coordination costs can undermine team performance.",
                    claim_type="problem",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="A preregistered cost contrast has no measurable gap.",
                    severity_if_wrong="important",
                ),
                ClaimRecordV1(
                    claim_id="claim:scope-s1",
                    exact_span="The mechanism applies to multi-agent teams.",
                    claim_type="domain_scope",
                    status="prospective",
                    evidence_sha256=(),
                    falsifier="The preregistered team sample excludes the mechanism.",
                    severity_if_wrong="minor",
                ),
            ),
        )

    def test_round_trip_is_canonical(self):
        ledger = self._ledger()
        raw = claim_ledger_bytes(ledger)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(verify_claim_ledger_bytes(raw), ledger)

    def test_executed_claim_requires_evidence(self):
        with self.assertRaisesRegex(ClaimLedgerError, "executed claim evidence"):
            replace(self._record(), status="executed")

    def test_duplicate_claim_id_rejects(self):
        row = self._record()
        with self.assertRaisesRegex(ClaimLedgerError, "claim IDs"):
            ClaimLedgerV1(
                design_sha256="a" * 64,
                records=(row, row),
            )

    def test_closed_enums_reject_mutations(self):
        for field, value in (
            ("claim_type", "causal_mechanism_v2"),
            ("status", "observed"),
            ("severity_if_wrong", "major"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ClaimLedgerError, "closed enum"):
                    replace(self._record(), **{field: value})

    def test_claim_id_must_be_lowercase_and_prefixed(self):
        for claim_id in ("Claim:mechanism-e2", "mechanism-e2"):
            with self.subTest(claim_id=claim_id):
                with self.assertRaisesRegex(ClaimLedgerError, "claim"):
                    replace(self._record(), claim_id=claim_id)

    def test_empty_exact_span_and_falsifier_reject(self):
        for field in ("exact_span", "falsifier"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ClaimLedgerError, "nonempty"):
                    replace(self._record(), **{field: ""})

    def test_ledger_requires_every_headline_category(self):
        for missing in (
            "problem",
            "causal_mechanism",
            "policy_consequence",
            "domain_scope",
            "limitation",
        ):
            records = tuple(
                row for row in self._ledger().records if row.claim_type != missing
            )
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(ClaimLedgerError, "required claim types"):
                    ClaimLedgerV1(design_sha256="a" * 64, records=records)

    def test_evidence_status_pairing_is_closed(self):
        for status in ("executed", "frozen_diagnostic"):
            with self.subTest(status=status):
                row = replace(
                    self._record(), status=status, evidence_sha256=("b" * 64,)
                )
                self.assertEqual(row.status, status)
        for status in ("prospective", "blocked", "unsupported", "not_assessable"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ClaimLedgerError, "may not carry"):
                    replace(self._record(), status=status, evidence_sha256=("b" * 64,))

    def test_evidence_hashes_are_sorted_unique_and_well_formed(self):
        for evidence in (("b" * 64, "a" * 64), ("a" * 64, "a" * 64), ("g" * 64,)):
            with self.subTest(evidence=evidence):
                with self.assertRaises(ClaimLedgerError):
                    replace(self._record(), status="executed", evidence_sha256=evidence)

    def test_records_and_claim_ids_must_be_byte_sorted(self):
        rows = self._ledger().records
        with self.assertRaisesRegex(ClaimLedgerError, "byte-sorted"):
            ClaimLedgerV1(design_sha256="a" * 64, records=tuple(reversed(rows)))

    def test_design_hash_must_be_sha256(self):
        with self.assertRaisesRegex(ClaimLedgerError, "SHA-256"):
            ClaimLedgerV1(design_sha256="g" * 64, records=self._ledger().records)

    def test_canonical_bytes_reject_whitespace_missing_lf_and_duplicate_keys(self):
        raw = claim_ledger_bytes(self._ledger())
        mutations = (
            raw.replace(b'{"design_sha256"', b'{ "design_sha256"', 1),
            raw[:-1],
            raw.replace(
                b'"claim_id":"claim:limit-l1","claim_type"',
                b'"claim_id":"claim:limit-l1","claim_id":"claim:limit-l1","claim_type"',
                1,
            ),
            raw.replace(
                b'{"design_sha256":"' + b"a" * 64 + b'","records":',
                b'{"design_sha256":"'
                + b"a" * 64
                + b'","design_sha256":"'
                + b"a" * 64
                + b'","records":',
                1,
            ),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated[:40]):
                with self.assertRaises(ClaimLedgerError):
                    verify_claim_ledger_bytes(mutated)

    def test_root_and_row_key_mutations_reject(self):
        raw = claim_ledger_bytes(self._ledger())
        root_mutations = (
            raw.replace(b'"design_sha256"', b'"design_sha256_x"', 1),
            raw.replace(b'"records"', b'"records_x"', 1),
        )
        row_mutations = tuple(
            raw.replace(('"' + key + '"').encode(), ('"' + key + '_x"').encode(), 1)
            for key in (
                "claim_id",
                "exact_span",
                "claim_type",
                "status",
                "evidence_sha256",
                "falsifier",
                "severity_if_wrong",
            )
        )
        for mutated in root_mutations + row_mutations:
            with self.subTest(mutated=mutated[:40]):
                with self.assertRaises(ClaimLedgerError):
                    verify_claim_ledger_bytes(mutated)

    def test_json_enum_and_hash_mutations_reject(self):
        raw = claim_ledger_bytes(self._ledger())
        mutations = (
            raw.replace(b'"causal_mechanism"', b'"causal_mechanism_x"', 1),
            raw.replace(b'"prospective"', b'"observed"', 1),
            raw.replace(b'"important"', b'"major"', 1),
            raw.replace(
                b'"design_sha256":"' + b"a" * 64, b'"design_sha256":"' + b"g" * 64, 1
            ),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated[:80]):
                with self.assertRaises(ClaimLedgerError):
                    verify_claim_ledger_bytes(mutated)

    def test_verifier_rejects_non_bytes_and_non_objects(self):
        with self.assertRaises(ClaimLedgerError):
            verify_claim_ledger_bytes(bytearray(claim_ledger_bytes(self._ledger())))
        for raw in (b"[]\n", b"null\n", b'{"design_sha256":null,"records":[]}\n'):
            with self.subTest(raw=raw):
                with self.assertRaises(ClaimLedgerError):
                    verify_claim_ledger_bytes(raw)
