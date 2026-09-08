"""A coarse family cannot certify two executable spatial propositions as duplicates."""
from copy import deepcopy
from pathlib import Path
import sys

from django.test import SimpleTestCase
from shapely.geometry import box
from design.maas.massv2.execute import execute
from design.maas.massv2.grammar import parti_from_record
from design.maas.massv2.family import family_key
from design.maas.massv2.select import composition_signature

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
from validate_authored import _repeated_families


class AuthorSourceDistinctionTests(SimpleTestCase):
    def source(self, name, verb, profile='square', **params):
        return {'name': name, 'primary_language': 'solid_body', 'floor_height_m': 3.,
                'ops': [{'op': 'extrude', 'height': 1., 'profile': profile, 'storeys': 4},
                        {'op': verb, **params}]}

    def signature(self, record):
        form = execute(parti_from_record(record), buildable=box(0, 0, 40, 30),
                       axis=(1, 0), height_m=12, storey_height_m=3)
        self.assertIsNotNone(form)
        return composition_signature(form)

    def test_bend_and_twist_reach_distinct_actual_forms_despite_equal_family(self):
        bent = self.source('bent', 'bend', degrees=42, segments=6)
        turning = self.source('turning', 'twist', profile='hexagon', degrees=75)
        self.assertEqual(family_key(bent), family_key(turning))
        self.assertNotEqual(self.signature(bent), self.signature(turning))
        self.assertEqual(_repeated_families([bent, turning]), [])

    def test_same_verb_with_distinct_profile_and_roof_sections_is_not_a_duplicate(self):
        square = self.source('square', 'crown', form='dome', sag=.3)
        hexagon = self.source('hexagon', 'crown', profile='hexagon', form='dome', sag=.3)
        saddle = self.source('saddle', 'crown', form='saddle', sag=.3)
        self.assertEqual(family_key(square), family_key(hexagon))
        self.assertEqual(family_key(square), family_key(saddle))
        self.assertEqual(len({self.signature(r) for r in (square, hexagon, saddle)}), 3)
        self.assertEqual(_repeated_families([square, hexagon, saddle]), [])

    def test_renaming_rewording_and_reordering_json_keys_do_not_create_a_source(self):
        source = self.source('first', 'bend', degrees=42, segments=6)
        alias = deepcopy(source)
        alias['name'] = 'new title'
        alias['formal_principle'] = 'New prose cannot create another executable proposition.'
        alias['ops'][1] = {'why': 'Different explanation', 'segments': 6., 'degrees': 42., 'op': 'bend'}
        self.assertEqual(self.signature(source), self.signature(alias))
        faults = _repeated_families([source, alias])
        self.assertEqual(len(faults), 1)
        self.assertIn('first', faults[0])

    def test_actual_floor_contract_remains_distinct(self):
        first = self.source('first', 'bend', degrees=42, segments=6)
        second = deepcopy(first)
        second.update(name='different-height', floor_height_m=4.)
        self.assertEqual(_repeated_families([first, second]), [])
