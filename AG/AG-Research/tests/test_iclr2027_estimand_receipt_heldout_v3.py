"""Adjudicated status-vocabulary wrapper for the sealed held-out V2 harness."""

import unittest

from tests import test_iclr2027_estimand_receipt_heldout as sealed_v2


class HeldOutEstimandReceiptV3Test(unittest.TestCase):
    def test_full_gate_with_public_status_vocabulary(self) -> None:
        public_rows, trust_root_bytes, v2_expected = sealed_v2._build_public_rows(
            sealed_v2._load_pack()
        )
        token_map = {
            "certified": "CERTIFIED",
            "blocked": "NOT_CERTIFIED",
        }
        self.assertEqual(len(v2_expected), 24 * 3)
        expected = {key: token_map[value] for key, value in v2_expected.items()}

        rows = sealed_v2.evaluate_frozen_artifacts(public_rows, trust_root_bytes)
        actual = {}
        for row in rows:
            if row.configuration != "full_estimand_gate":
                continue
            self.assertNotEqual(row.status, "BOUNDED")
            key = (row.public_case_id, row.estimand)
            self.assertNotIn(key, actual)
            actual[key] = row.status

        self.assertEqual(len(actual), 24 * 3)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
