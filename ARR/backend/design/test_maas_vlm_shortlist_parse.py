"""How a jury verdict is read - the binding between a tile and its score.

The parser under test replaced a single non-greedy regex over the whole
verdict file. That regex let a juror who opened a TILE block and omitted its
WEIGHTED line take the NEXT tile's number: two tiles carried one score, one
tile carried another drawing's score, and the round published both silently.
judge.sh could not see it either - it counts TILE lines, and in that failure
the count is correct and only the binding is wrong. These cases pin the four
ways the binding can break, and pin that a refusal names the file and the
tile so the round can be rejudged rather than guessed at.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SHORTLIST = BACKEND_ROOT / "tmp_mass_check" / "_massv2" / "tools" / "vlm_shortlist.py"


def _load_shortlist():
    spec = importlib.util.spec_from_file_location("maas_vlm_shortlist_test", SHORTLIST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SHORTLIST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _block(tile: str, weighted: str | None) -> str:
    lines = [
        f"TILE {tile}",
        "CONCEPT 3 | A bar and a tower, read as one move.",
        "FEASIBILITY 3 | Orthodox volumes, civic budget.",
        "SITE 3 | Addresses the open side.",
        "EDITABILITY 3 | Takes floors without losing the parti.",
    ]
    if weighted is not None:
        lines.append(f"WEIGHTED {weighted}")
    return "\n".join(lines) + "\n\n"


class VlmVerdictParseTests(SimpleTestCase):
    KEY = {"t01", "t02", "t03"}

    def _read(self, text: str, name: str = "r2.txt"):
        module = _load_shortlist()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(text, encoding="utf-8")
            return module, path, module.read_verdict(path, self.KEY)

    def _refusal(self, text: str, name: str = "r2.txt") -> str:
        module = _load_shortlist()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(module.VerdictError) as caught:
                module.read_verdict(path, self.KEY)
        return str(caught.exception)

    def test_a_well_formed_verdict_binds_each_score_to_its_own_tile(self):
        text = (_block("t01", "2.70") + _block("t02", "3.15") + _block("t03", "4.00")
                + "RANKING: t03, t02, t01\n"
                + "VERDICT: t03 is the only advance.\n")
        _module, _path, seen = self._read(text)

        self.assertEqual(seen, {"t01": 2.70, "t02": 3.15, "t03": 4.00})

    def test_windows_utf8_bom_preserves_the_first_tiles_score(self):
        text = '\ufeff' + _block('t01', '2.70') + _block('t02', '3.15')
        _module, _path, seen = self._read(text)
        self.assertEqual(seen, {'t01': 2.70, 't02': 3.15})

    def test_a_block_with_no_weighted_refuses_instead_of_taking_the_next_score(self):
        # The defect itself: t02 has no WEIGHTED, so the old regex handed it
        # t03's 4.00 and t03 kept it too. Nothing downstream could tell.
        text = _block("t01", "2.70") + _block("t02", None) + _block("t03", "4.00")

        message = self._refusal(text, name="r3.txt")

        self.assertIn("r3.txt", message)
        self.assertIn("t02", message)
        self.assertIn("WEIGHTED", message)

    def test_a_tile_scored_twice_with_two_numbers_refuses(self):
        text = _block("t01", "2.70") + _block("t02", "3.15") + _block("t02", "4.55")

        message = self._refusal(text)

        self.assertIn("r2.txt", message)
        self.assertIn("t02", message)

    def test_a_juror_restating_its_own_table_is_not_a_contradiction(self):
        # ovs17-en r3 wrote a seven-row summary under its seven blocks with
        # the same numbers. That is a restatement, not a second verdict, and
        # refusing it would make an already seated round unrescorable.
        text = (_block("t01", "2.70") + _block("t02", "3.15") + _block("t03", "4.00")
                + "TILE t01 A3 F3 C3 E3 WEIGHTED 2.70\n"
                + "TILE t02 A4 F3 C3 E3 WEIGHTED 3.15\n"
                + "TILE t03 A4 F4 C4 E4 WEIGHTED 4.00\n")
        _module, _path, seen = self._read(text)

        self.assertEqual(seen, {"t01": 2.70, "t02": 3.15, "t03": 4.00})

    def test_a_score_outside_the_rubrics_range_refuses(self):
        text = _block("t01", "2.70") + _block("t02", "7.40") + _block("t03", "4.00")

        message = self._refusal(text)

        self.assertIn("r2.txt", message)
        self.assertIn("t02", message)

    def test_a_weighted_that_is_not_a_number_refuses(self):
        text = _block("t01", "2.70") + _block("t02", "n/a") + _block("t03", "4.00")

        message = self._refusal(text)

        self.assertIn("r2.txt", message)
        self.assertIn("t02", message)

    def test_a_tile_the_key_does_not_hold_refuses(self):
        # A juror pointed at a stale stage scores tiles this round never made.
        text = _block("t01", "2.70") + _block("t09", "3.15")

        message = self._refusal(text)

        self.assertIn("r2.txt", message)
        self.assertIn("t09", message)
