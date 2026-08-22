from dataclasses import FrozenInstanceError
import unittest

from iclr2027.study_contract import StudyContract


class StudyContractTests(unittest.TestCase):
    def test_primary_contract_is_exact_and_immutable(self) -> None:
        contract = StudyContract.primary()

        self.assertEqual(contract.epsilon, 0.02)
        self.assertEqual(contract.alpha, 0.10)
        self.assertEqual(contract.patience, 2)
        self.assertEqual(contract.group_seed, 20260819)
        self.assertEqual(contract.site_partition_counts, (2, 1, 2))
        self.assertEqual(contract.epsilon_sensitivity, (0.01, 0.05))
        self.assertEqual(contract.alpha_sensitivity, (0.05, 0.20))

        with self.assertRaises(FrozenInstanceError):
            contract.epsilon = 0.01

