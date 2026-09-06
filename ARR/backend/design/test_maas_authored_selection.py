"""Programme requirements bind; an unknown brief does not imply maximum density."""
import unittest
from dataclasses import replace

from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.form import MatrixForm, place
from design.maas.massv2.measure import measure_form
from design.maas.massv2.plausibility import Plausibility
from design.maas.massv2.select import Candidate, choose


def candidate(name, *, low=False, explicit=False, inferred=False, occupiable=True, brief=False):
    placements = [place('body', size=(30., 30., 7.2 if low else 14.4))]
    if low:
        placements.append(place('court', size=(10., 12., 20.), kind='subtractive'))
    extra = {'parti': {'growth': 'plan'} if explicit else {}}
    if inferred:
        extra['growth'] = 'plan'
    if brief:
        extra.update(programme_target=3600., far_capacity_m2=6000.)
    form = MatrixForm(name=name, placements=tuple(placements), primary_language='carved_body',
                      floor_height_m=3.6, extra=extra)
    source = compile_matrix_form(form, storey_height_m=3.6)
    assert source is not None
    return Candidate(form, source, measure_form(source),
        Plausibility(1., 12., 1., occupiable, () if occupiable else ('unsupported',)),
        'low|court' if low else 'high|body', .5,
        .15 if low else .6)


class AuthoredSelectionTests(unittest.TestCase):
    def test_unbriefed_low_density_remains_an_option_for_visual_review(self):
        low = candidate('garden', low=True, explicit=True)
        high = candidate('office')
        self.assertEqual({c.form.name for c in choose([low, high])}, {'garden', 'office'})

    def test_existing_all_underfilled_fallback_is_unchanged(self):
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                low = candidate('garden', low=True, explicit=explicit)
                self.assertEqual([c.form.name for c in choose([low])], ['garden'])

    def test_low_density_does_not_need_a_magic_growth_flag(self):
        for inferred in (False, True):
            with self.subTest(inferred=inferred):
                low = candidate('garden', low=True, inferred=inferred)
                self.assertEqual({c.form.name for c in choose([low, candidate('office')])}, {'garden', 'office'})

    def test_all_programme_misses_are_not_delivered_as_valid_options(self):
        self.assertEqual(choose([candidate('undersized', low=True, brief=True)]), [])

    def test_missing_area_measurement_does_not_erase_an_explicit_programme(self):
        item = candidate('unknown_measurement', brief=True)
        item = replace(item, form=replace(item.form, extra={**item.form.extra, 'far_capacity_m2': None}))
        self.assertEqual(choose([item, candidate('unbriefed')]), [])

    def test_explicit_plan_growth_does_not_bypass_physical_eligibility(self):
        low = candidate('unsupported', low=True, explicit=True, occupiable=False)
        self.assertEqual([c.form.name for c in choose([low, candidate('office')])], ['office'])

    def test_explicit_plan_growth_does_not_override_a_programme_area_schedule(self):
        low = candidate('undersized', low=True, explicit=True, brief=True)
        high = candidate('meets_programme', brief=True)
        self.assertEqual([c.form.name for c in choose([low, high])], ['meets_programme'])


if __name__ == '__main__':
    unittest.main()
