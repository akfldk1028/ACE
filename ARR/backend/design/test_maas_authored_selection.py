"""A deliberately low authored scheme reaches visual review without bypassing gates."""
import unittest

from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.form import MatrixForm, place
from design.maas.massv2.measure import measure_form
from design.maas.massv2.plausibility import Plausibility
from design.maas.massv2.select import Candidate, choose, MINIMUM_DELIVERED_SHARE


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
        MINIMUM_DELIVERED_SHARE / 2 if low else .6)


class AuthoredSelectionTests(unittest.TestCase):
    def test_explicit_plan_growth_retains_the_only_legal_occupant_of_a_low_cell(self):
        low = candidate('garden', low=True, explicit=True)
        high = candidate('office')
        self.assertEqual({c.form.name for c in choose([low, high])}, {'garden', 'office'})

    def test_inferred_or_missing_growth_keeps_existing_unbriefed_density_policy(self):
        for inferred in (False, True):
            with self.subTest(inferred=inferred):
                low = candidate('garden', low=True, inferred=inferred)
                self.assertEqual([c.form.name for c in choose([low, candidate('office')])], ['office'])

    def test_explicit_plan_growth_does_not_bypass_physical_eligibility(self):
        low = candidate('unsupported', low=True, explicit=True, occupiable=False)
        self.assertEqual([c.form.name for c in choose([low, candidate('office')])], ['office'])

    def test_explicit_plan_growth_does_not_override_a_programme_area_schedule(self):
        low = candidate('undersized', low=True, explicit=True, brief=True)
        high = candidate('meets_programme', brief=True)
        self.assertEqual([c.form.name for c in choose([low, high])], ['meets_programme'])


if __name__ == '__main__':
    unittest.main()
