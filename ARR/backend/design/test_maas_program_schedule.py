"""A brief computed from a head count has to land on the issued document.

Korean public procurement does not hand an architect a room schedule somebody
invented; it computes one from 「청사 등의 표준 설계면적 기준」, and the
설계공모지침서 for 파주 법원읍 prints the formulae in a column beside the areas.
That makes the standard testable against documents it was not written from.

효돈동's issued brief gives its 민원실 as 150.0 m². Nothing about that number
was used to write the formula, so reproducing it is evidence the whole table
can be generated rather than transcribed - which is the difference between a
system that needs a schedule typed in for every site and one that needs a
building type and a staff count.
"""

from django.test import SimpleTestCase

from design.maas.massv2.program import (
    GROSS_UP,
    Room,
    Schedule,
    blended,
    civic_centre_schedule,
    volume_shares,
)


class TheStandardReproducesTheIssuedBriefTests(SimpleTestCase):
    def test_hyodon_dong_counter_hall_comes_back_at_150_m2(self):
        """지침서 150.0 m², 상주 20명 · 민원인 200명 규모."""

        schedule = civic_centre_schedule(counter_staff=20, daily_visitors=80)
        counter = next(r for r in schedule.rooms if r.name == "종합민원실")

        self.assertAlmostEqual(counter.area_m2, 150.1, places=1)

    def test_paju_desk_areas_come_back_as_issued(self):
        """파주 법원읍: 직원 25명 180.0 · 자료실 12.4 · 전산실 11.7 · 휴게실 9.3."""

        schedule = civic_centre_schedule(staff=25, team_leaders=5)
        by_name = {room.name: room.total_m2 for room in schedule.rooms}

        self.assertAlmostEqual(by_name["직원실"], 180.0, places=1)
        self.assertAlmostEqual(by_name["자료실"], 12.4, places=1)
        self.assertAlmostEqual(by_name["전산실"], 11.7, places=1)
        self.assertAlmostEqual(by_name["휴게실"], 9.3, places=1)

    def test_a_bigger_counter_needs_a_bigger_hall(self):
        small = civic_centre_schedule(counter_staff=10)
        large = civic_centre_schedule(counter_staff=30)

        def counter(schedule):
            return next(r for r in schedule.rooms if r.name == "종합민원실").area_m2

        self.assertLess(counter(small), counter(large))

    def test_the_lavatory_rate_falls_as_the_building_fills(self):
        """0.43 under a hundred people, 0.40 to two hundred, 0.33 beyond."""

        def lavatory(visitors):
            schedule = civic_centre_schedule(daily_visitors=visitors)
            room = next(r for r in schedule.rooms if r.name == "화장실")
            return room.area_m2 / visitors

        self.assertAlmostEqual(lavatory(50), 0.43, places=2)
        self.assertAlmostEqual(lavatory(150), 0.40, places=2)
        self.assertAlmostEqual(lavatory(300), 0.33, places=2)


class TheBriefCarriesItsOwnHierarchyTests(SimpleTestCase):
    """What the form language had to legislate, a schedule simply has."""

    def test_a_hall_among_offices_is_the_dominant_volume(self):
        schedule = civic_centre_schedule(hall_m2=400.0, staff=10, team_leaders=2)

        self.assertGreater(schedule.dominance(), 0.2)
        self.assertEqual(len(schedule.of_kind("large_span")), 1)

    def test_the_large_room_is_never_divided_between_volumes(self):
        """A hall split across two volumes is not a hall."""

        schedule = Schedule("t", (
            Room("강당", 400.0, kind="large_span"),
            Room("사무실", 60.0, count=5),
        ))
        shares = volume_shares(schedule, pieces=3)

        self.assertAlmostEqual(shares[0], 400.0 / 700.0, places=3)
        self.assertAlmostEqual(sum(shares), 1.0, places=6)

    def test_gross_up_is_applied_once(self):
        schedule = Schedule("t", (Room("실", 100.0),))

        self.assertAlmostEqual(schedule.gross_m2, 100.0 * GROSS_UP, places=6)


class TheDialIsADialTests(SimpleTestCase):
    def test_zero_leaves_the_sentence_alone_and_one_hands_it_over(self):
        authored = (0.5, 0.3, 0.2)
        programme = (0.2, 0.4, 0.4)

        self.assertEqual(blended(authored, programme, weight=0.0), authored)
        self.assertEqual(blended(authored, programme, weight=1.0), programme)

    def test_halfway_sits_between_and_still_sums_to_one(self):
        mixed = blended((0.5, 0.3, 0.2), (0.2, 0.4, 0.4), weight=0.5)

        self.assertAlmostEqual(sum(mixed), 1.0, places=6)
        self.assertLess(mixed[0], 0.5)
        self.assertGreater(mixed[0], 0.2)
