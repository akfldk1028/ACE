"""Holding the ground has to reach the delivered plates, not only the record.

The ground-take bands existed for two commits before this one and changed
nothing: c227 came out byte-identical to c225 because the band was published as
evidence while the geometry kept reading floor targets derived from floor area.
25 of 28 delivered masses still sat within one percent of the coverage cap.

What the geometry actually reads is the candidate's own plate vector - the
capacity prefix written by `_apply_candidate_floor_prefix` and distributed by
`_alternative_floor_targets`. These tests hold that vector, and the floor count
that follows from it, against the band.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language.capacity_alternatives import (
    CAPACITY_ALTERNATIVE_SPECS,
    build_capacity_alternative,
    capacity_contract_for_alternative,
)
from design.maas.book_language.candidate_floor_authority import (
    _candidate_floor_context,
)
from design.maas.book_language.capacity_contract import (
    build_feasible_capacity_contract,
)
from design.maas.book_language.floor_capacity_plan import (
    derive_program_floor_capacity_plan,
)
from design.maas.design_space import COVERAGE_BANDS


PNU = "4115011300106840001"


def _context(*, legal_floors=25, far_limit=562.5):
    """A parcel whose plates are bound by 건폐율, not by the section they sit in.

    The generation site is 324 m2 against a 240 m2 coverage capacity, so every
    lawful plate is already at the ceiling and a band that lowers the ceiling
    is the only thing that can lower the plate. A smaller site would leave the
    plates below every band's ceiling and the tests would pass without the code
    under test ever running - which is how the first coverage-band fixture in
    this repo proved nothing twice.
    """

    return SimpleNamespace(
        envelope=SimpleNamespace(
            floor_height=3.0,
            height_limit=3.0 * legal_floors,
            bcr_limit=60.0,
            far_limit=far_limit,
        ),
        generation_site=box(0.0, 0.0, 18.0, 18.0),
        sunlight_ring=(),
        evidence={},
    )


def _base_contract(*, legal_floors=25, far_limit=562.5):
    context = _context(legal_floors=legal_floors, far_limit=far_limit)
    site = box(0.0, 0.0, 20.0, 20.0)
    plan = derive_program_floor_capacity_plan(
        context,
        site_local_utm=site,
        building_type="neighborhood living",
        target_utilization=0.90,
        legacy_floor_hint=4,
        pnu=PNU,
    )
    return build_feasible_capacity_contract(
        context,
        site_local_utm=site,
        height_m=float(plan["selected_height_m"]),
        floors=int(plan["selected_floor_count"]),
        target_utilization=0.90,
        minimum_utilization=0.40,
        floor_capacity_plan=plan,
    )


def _projected(contract, *, band=None, alternative="brief_target"):
    spec = next(
        item
        for item in CAPACITY_ALTERNATIVE_SPECS
        if item.alternative_id == alternative
    )
    return capacity_contract_for_alternative(
        contract,
        build_capacity_alternative(contract, spec, coverage_band=band),
    )


class GroundTakeMovesTheStackTests(SimpleTestCase):
    def setUp(self):
        self.contract = _base_contract()
        self.bands = {band.band_id: band for band in COVERAGE_BANDS}

    def test_the_fixture_plates_are_bound_by_coverage_not_by_the_section(self):
        """Guard the fixture itself: without this the code never branches."""

        field = self.contract["legal_floor_field"]
        capacity = float(field["bcr_footprint_capacity_m2"])
        plates = [float(value) for value in field["bcr_adjusted_floor_capacities_m2"]]

        self.assertGreater(len(plates), 4)
        for plate in plates:
            self.assertAlmostEqual(capacity, plate, places=6)
        for band in COVERAGE_BANDS:
            if band.plan_fraction < 1.0:
                self.assertLess(capacity * band.plan_fraction, plates[0])

    def test_holding_the_ground_lowers_every_plate(self):
        full = _projected(self.contract, band=self.bands["full_ground"])
        dispersed = _projected(self.contract, band=self.bands["dispersed_ground"])

        for plate in dispersed["bcr_adjusted_floor_areas_m2"]:
            self.assertLess(plate, full["bcr_adjusted_floor_areas_m2"][0])

    def test_the_stack_answers_by_growing(self):
        full = _projected(self.contract, band=self.bands["full_ground"])
        dispersed = _projected(self.contract, band=self.bands["dispersed_ground"])

        self.assertGreater(
            dispersed["requested_floors"],
            full["requested_floors"],
        )
        self.assertGreater(
            dispersed["requested_height_m"],
            full["requested_height_m"],
        )

    def test_the_floor_targets_the_geometry_fits_follow_the_band(self):
        """`target_floor_areas_m2[0]` is what the plan-axis fit scales to."""

        first_targets = {
            band.band_id: _projected(self.contract, band=band)[
                "target_floor_areas_m2"
            ][0]
            for band in COVERAGE_BANDS
        }

        ordered = [
            first_targets[band.band_id]
            for band in sorted(COVERAGE_BANDS, key=lambda item: item.plan_fraction)
        ]
        for lower, upper in zip(ordered, ordered[1:]):
            self.assertLess(lower, upper)

    def test_no_band_delivers_another_bands_stack(self):
        signatures = {
            (
                tuple(projected["bcr_adjusted_floor_areas_m2"]),
                projected["requested_floors"],
            )
            for projected in (
                _projected(self.contract, band=band) for band in COVERAGE_BANDS
            )
        }

        self.assertEqual(len(COVERAGE_BANDS), len(signatures))

    def test_every_band_and_alternative_stays_reachable(self):
        for band in COVERAGE_BANDS:
            for spec in CAPACITY_ALTERNATIVE_SPECS:
                projected = _projected(
                    self.contract,
                    band=band,
                    alternative=spec.alternative_id,
                )
                self.assertTrue(
                    projected["candidate_target_reachable"],
                    f"{band.band_id}/{spec.alternative_id}",
                )

    def test_the_second_authority_agrees_with_the_banded_prefix(self):
        """The prefix is re-derived, not believed - and must still agree.

        `_candidate_floor_context` recomputes the minimum lawful prefix from the
        trusted field so a candidate cannot invent its own stack. On the live
        parcel this rejected every banded candidate: 24 of 30 masses died before
        compiling and only full_ground survived, because full_ground is the one
        band that leaves the plates untouched. The band has to reach both
        authorities or it reaches neither.
        """

        field = self.contract["legal_floor_field"]
        for band in COVERAGE_BANDS:
            for spec in CAPACITY_ALTERNATIVE_SPECS:
                projected = _projected(
                    self.contract,
                    band=band,
                    alternative=spec.alternative_id,
                )
                context = _candidate_floor_context(
                    projected,
                    fallback_height=0.0,
                    fallback_floors=0,
                    trusted_legal_floor_field=field,
                    expected_legal_floor_field_hash=str(
                        field["legal_floor_field_hash"]
                    ),
                )
                self.assertTrue(
                    context.get("hard_pass"),
                    f"{band.band_id}/{spec.alternative_id}: "
                    f"{context.get('failure_reasons')}",
                )

    def test_a_forged_ground_take_is_refused(self):
        """A band is a declaration, so the closed set is what keeps it honest."""

        projected = _projected(self.contract, band=self.bands["dispersed_ground"])
        field = self.contract["legal_floor_field"]
        for forged in ("as_much_as_possible", "", 0.45):
            projected["coverage_band_id"] = forged
            context = _candidate_floor_context(
                projected,
                fallback_height=0.0,
                fallback_floors=0,
                trusted_legal_floor_field=field,
                expected_legal_floor_field_hash=str(
                    field["legal_floor_field_hash"]
                ),
            )
            self.assertFalse(context.get("hard_pass"), forged)

    def test_a_tight_height_field_makes_the_scheme_smaller_not_impossible(self):
        """Four lawful floors cannot answer a 45% ground take by going up.

        The honest consequence is a smaller building, which is one of the
        proposals an architect is choosing between. Holding utilization against
        the maximal capacity instead would have made this corner unreachable and
        silently deleted the low-coverage schemes from the portfolio.
        """

        # FAR must stay clear of both stacks, or it binds each of them to the
        # same ceiling and the height field never gets to be the constraint the
        # test is about: 4 x 240 = 960 and 4 x 108 = 432 both sit under 1200.
        contract = _base_contract(legal_floors=4, far_limit=300.0)
        full = build_capacity_alternative(
            contract,
            CAPACITY_ALTERNATIVE_SPECS[2],
            coverage_band=self.bands["full_ground"],
        )
        dispersed = build_capacity_alternative(
            contract,
            CAPACITY_ALTERNATIVE_SPECS[2],
            coverage_band=self.bands["dispersed_ground"],
        )

        self.assertLess(
            dispersed["target_floor_area_m2"],
            full["target_floor_area_m2"],
        )
        self.assertTrue(
            _projected(
                contract,
                band=self.bands["dispersed_ground"],
            )["candidate_target_reachable"]
        )

    def test_without_a_band_the_lawful_plates_are_untouched(self):
        """The axis is opt-in; every existing caller keeps its exact stack."""

        unbanded = _projected(self.contract, band=None)
        lawful = [
            round(float(value), 3)
            for value in self.contract["legal_floor_field"][
                "bcr_adjusted_floor_capacities_m2"
            ]
        ]

        self.assertEqual(
            lawful[: unbanded["requested_floors"]],
            unbanded["bcr_adjusted_floor_areas_m2"],
        )
        self.assertIsNone(
            build_capacity_alternative(
                self.contract,
                CAPACITY_ALTERNATIVE_SPECS[2],
            )["coverage_band"]
        )
