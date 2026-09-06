import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


class AuthorBriefTests(TestCase):
    def test_new_era_can_author_before_a_board_key_exists(self):
        path = Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools/make_brief.py'
        spec = importlib.util.spec_from_file_location('mass_brief_test', path)
        brief = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(brief)
        with TemporaryDirectory() as directory, patch.object(brief, 'ROOT', Path(directory)):
            result = brief.board_section('O')
        self.assertIn('No judged and baked seats exist in the current era yet.', result)
