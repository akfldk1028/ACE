"""The composition family of a sentence, computed instead of eyeballed.

Three times in one day a board was curated by hand because near-identical
partis stacked up - six plinth-and-turned-tower schemes side by side, from
three authors who were told to be different. Personas do not partition a
model's distribution; a key does. This module owns the question "are these
two sentences the same building?" at the level a jury reads - physical
principle, not detail - so staging, boards and the cell selector can prefer
one-per-family without anyone looking.

Born as a workspace tool beside the board curator; moved here the day the
audit showed the delivered thirty-two picks were fifteen families, one of
them seated six times - the selector deduped by sentence NAME, and a family
is exactly what a set of names has in common.

The key is (opener, move families, stature band): which word stands the
volume up, which *kinds* of moves act on it (not their parameters), and
whether the body is low, mid or tall. plinth_turned_tower, grid_realigned
_tower and plinth_slender_turned all collapse to (extrude, relational, low)
- which is exactly what both judges said of them.
"""

FAMILY_OF_VERB = {
    # what kind of statement a verb is, at the level a jury reads
    "nest": "relational", "lodge": "relational", "overlap": "relational",
    "interlock": "relational", "merge": "relational", "extract": "relational",
    "gable": "section", "butterfly": "section", "mansard": "section",
    "vault": "section", "fold": "section", "grade": "section",
    "split": "cut", "carve": "cut", "notch": "cut", "puncture": "cut",
    "inscribe": "cut", "fracture": "cut", "intersect": "cut",
    "cantilever": "banding", "shear": "banding", "twist": "banding",
    "taper": "banding", "bend": "banding", "pinch": "banding",
    "canopy": "plate",
    "lift": "piloti",
    "branch": "field", "embed": "relational",
}
OPENERS = ("extrude", "loop", "aggregate", "stack")
QUIET = {"compress", "expand", "inflate", "shift", "offset", "rotate",
         "skew", "align", "realign", "approach"}


def family_key(scheme: dict) -> tuple:
    """(opener, frozenset of move families, stature band) for one sentence."""

    ops = scheme.get("ops") or ()
    opener = "?"
    height = 0.0
    for op in ops:
        word = str(op.get("op") or op.get("verb") or "")
        if word in OPENERS:
            opener = word
            if word == "aggregate" and str(op.get("method") or "") == "stack":
                opener = "aggregate_stack"
            height = max(height, float(op.get("height") or 0.0))
            break
    moves = {
        FAMILY_OF_VERB[str(op.get("op") or op.get("verb") or "")]
        for op in ops
        if str(op.get("op") or op.get("verb") or "") in FAMILY_OF_VERB
    }
    # One dominant move names the family. A marquee added to a plinth-and-
    # turned-tower does not make it a different building - the judges read
    # the strongest statement, so the key does too.
    for dominant in ("relational", "section", "cut", "banding",
                     "piloti", "plate", "field"):
        if dominant in moves:
            moves = {dominant}
            break
    stature = "low" if height < 0.42 else ("mid" if height < 0.72 else "tall")
    return (opener, frozenset(moves), stature)


def family_tag(scheme: dict) -> str:
    """The key as one printable word, for ledgers and selector maps."""

    opener, moves, stature = family_key(scheme)
    return f"{opener}/{next(iter(moves), '-')}/{stature}"


def one_per_family(entries, *, key_of, score_of):
    """The best entry per family, order preserved by descending score."""

    best: dict = {}
    for item in entries:
        k = key_of(item)
        if k not in best or score_of(item) > score_of(best[k]):
            best[k] = item
    return sorted(best.values(), key=score_of, reverse=True)
