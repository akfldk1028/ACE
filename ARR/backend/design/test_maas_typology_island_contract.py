"""Target-five contract for measured final-mesh phenotype islands."""

from django.test import SimpleTestCase

from design.maas.book_language import portfolio_selection
from design.maas.book_language.competition_portfolio_contract import (
    competition_portfolio_contract,
)


class MaasTypologyIslandContractTests(SimpleTestCase):
    def test_target_five_requires_four_measured_phenotype_islands(self):
        contract = competition_portfolio_contract(5)
        phenotypes = ("curved", "voided", "winged", "oblique", "oblique")
        facts = tuple(
            portfolio_selection.ConstraintCandidateFacts(
                score=1.0 - index * 0.01,
                cap_keys=(),
                visible_stepped=False,
                body_phenotype=phenotype,
                roof_archetype=f"roof_{index}",
                body_roof_signature=f"{phenotype}|roof_{index}",
            )
            for index, phenotype in enumerate(phenotypes)
        )
        compatibility = tuple(tuple(True for _ in range(5)) for _ in range(5))

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            compatibility,
            target_count=5,
            maximum_key_counts={},
            portfolio_contract=contract,
        )

        self.assertEqual(selected, (0, 1, 2, 3, 4))

        collapsed = tuple(
            portfolio_selection.ConstraintCandidateFacts(
                score=fact.score,
                cap_keys=fact.cap_keys,
                visible_stepped=False,
                body_phenotype=("curved", "voided", "oblique", "oblique", "oblique")[index],
                roof_archetype=fact.roof_archetype,
                body_roof_signature=(
                    f"{('curved', 'voided', 'oblique', 'oblique', 'oblique')[index]}"
                    f"|roof_{index}"
                ),
            )
            for index, fact in enumerate(facts)
        )
        self.assertEqual(
            portfolio_selection.solve_milp_compatible_subset(
                collapsed,
                compatibility,
                target_count=5,
                maximum_key_counts={},
                portfolio_contract=contract,
            ),
            (),
        )
