"""Stack family describes actual occupied level organization, not only its verb."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

from design.maas.massv2.family import family_key

sys.path.insert(0, str(Path(__file__).parent.parent/'tmp_mass_check/_massv2/tools'))
from validate_authored import _repeated_families


def stack(name, levels):
    return {'name':name, 'ops':[{'op':'aggregate','method':'stack','n':4,
            'levels':levels,'storeys':1,'height':1,'tie':0,'spread':1.08,'turn':24}]}


class StackFamilyTests(unittest.TestCase):
    def test_four_single_levels_and_two_paired_levels_are_distinct(self):
        tower, paired = stack('four occupied levels',4), stack('paired strata',2)
        self.assertNotEqual(family_key(tower),family_key(paired))
        self.assertEqual(_repeated_families([tower,paired]),[])

    def test_cosmetic_name_and_rotation_do_not_fake_a_different_organization(self):
        original = stack('first',4)
        duplicate = deepcopy(original)
        duplicate['name'] = 'new author label'
        duplicate['ops'][0]['turn'] = 18
        self.assertEqual(family_key(original),family_key(duplicate))
        self.assertEqual(len(_repeated_families([original,duplicate])),1)

    def test_executor_clamped_levels_have_one_family(self):
        self.assertEqual(family_key(stack('four',4)),family_key(stack('oversized level request',40)))
