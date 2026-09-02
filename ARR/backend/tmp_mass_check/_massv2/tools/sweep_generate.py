"""Generate grammar-valid sentences at base-volume scale.

The authored corpus explores the language a few sentences at a time; the
combinatorial space of (opener x profile x modifier verbs x params) is tens
of thousands. This generator samples that space wide - seeded, reproducible -
and keeps ONLY what the living validator accepts, so correctness is owned by
the validator (which derives verbs/params from the executor), not by tables
here. The whole point is the funnel: generate wide, let the gates and cells
and juries pick the good ones.

Sweep books are written OUTSIDE inputs/ on purpose: the corpus glob
(inputs/gen-*.json) is the authored canon, and a thousand generated sentences
must not join it. Winners get promoted by hand into inputs/gen-sweep-picks
after a jury - the same door every sentence walks through.

    python tools/sweep_generate.py <count> <out.json> [seed]
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]

# Openers and their body parameters. Heights stay clear of the stature
# thresholds' knife edges; storeys spread across the site's plausible band.
_PROFILES = ("square", "oval", "stadium", "chamfered", "trapezoidal",
             "kite", "hexagon", "faceted", "triangular", "concave_l")
_OPENERS = (
    ("extrude", lambda r: {"profile": r.choice(_PROFILES),
                           "height": round(r.choice((0.25, 0.3, 0.5, 0.6, 0.8, 0.85)), 2),
                           "storeys": r.choice((2, 3, 4, 5, 6))}),
    ("loop", lambda r: {"bar": round(r.uniform(0.2, 0.3), 2),
                        "height": round(r.choice((0.25, 0.3, 0.5)), 2),
                        "storeys": r.choice((1, 2, 3))}),
    ("aggregate", lambda r: {"n": r.choice((2, 3, 4, 5, 6)),
                             "spread": round(r.uniform(1.1, 1.5), 2),
                             "height": round(r.choice((0.3, 0.5, 0.6)), 2),
                             "storeys": r.choice((2, 3)),
                             "tie": r.choice((0, 0, 0.2))}),
    ("stack", lambda r: {"n": r.choice((3, 4, 5)),
                         "contrast": round(r.uniform(1.25, 2.0), 2),
                         "height": round(r.choice((0.6, 0.8, 0.9)), 2)}),
)

# Modifier verbs with safe param recipes (values inside their ranges, away
# from gate thresholds). Enum params are small hand tables - any bad combo
# is caught by the in-process validator below, which is the actual owner.
_AIM = ("open", "back", "cross")
_MODS = (
    ("compress", lambda r: {"ratio": round(r.uniform(0.6, 0.75), 2), "toward": "cross"}),
    ("gable", lambda r: {"pitch": round(r.uniform(0.6, 1.1), 2), "along": "long"}),
    ("vault", lambda r: {"rise": round(r.uniform(0.5, 1.0), 2)}),
    ("fold", lambda r: {"folds": r.choice((2, 3)), "pitch": round(r.uniform(0.35, 0.6), 2)}),
    ("butterfly", lambda r: {"pitch": round(r.uniform(0.5, 0.8), 2),
                             "at": round(r.uniform(0.3, 0.45), 2)}),
    ("mansard", lambda r: {"pitch": round(r.uniform(0.6, 1.0), 2)}),
    ("grade", lambda r: {"mode": "smooth", "run": round(r.uniform(0.5, 0.8), 2),
                         "toward": "open"}),
    ("lift", lambda r: {"clearance": round(r.uniform(0.3, 0.4), 2)}),
    ("carve", lambda r: {"depth": round(r.uniform(0.25, 0.45), 2), "toward": r.choice(_AIM)}),
    ("split", lambda r: {"ratio": round(r.uniform(0.3, 0.55), 2)}),
    ("taper", lambda r: {"ratio": round(r.uniform(0.55, 0.8), 2)}),
    ("twist", lambda r: {"turn": r.choice((12, 18, 24, 30))}),
    ("shear", lambda r: {"run": round(r.uniform(0.15, 0.3), 2), "toward": r.choice(_AIM)}),
    ("notch", lambda r: {"depth": round(r.uniform(0.2, 0.4), 2), "toward": r.choice(_AIM)}),
    ("puncture", lambda r: {"n": r.choice((1, 2, 3))}),
    ("inscribe", lambda r: {"share": round(r.uniform(0.15, 0.3), 2)}),
    ("nest", lambda r: {"size": round(r.uniform(0.35, 0.5), 2),
                        "proud": round(r.uniform(0.4, 0.7), 2),
                        "turn": r.choice((-30, -20, 15, 20, 30))}),
    ("cantilever", lambda r: {"reach": round(r.uniform(0.2, 0.3), 2), "toward": "open"}),
    ("canopy", lambda r: {"reach": round(r.uniform(0.2, 0.3), 2), "at": 1.0,
                          "toward": "open"}),
    ("pinch", lambda r: {"ratio": round(r.uniform(0.55, 0.7), 2)}),
    ("bend", lambda r: {"turn": r.choice((15, 20, 30))}),
    ("expand", lambda r: {"ratio": round(r.uniform(1.15, 1.35), 2)}),
)

_WHY = ("swept from the grammar - the funnel, not this sentence, argues; "
        "gates and juries decide what survives")


def _sentence(r: random.Random, index: int) -> dict:
    opener, oparams = r.choice(_OPENERS)
    ops = [{"op": opener, **oparams(r), "why": _WHY}]
    for _ in range(r.choice((1, 1, 2, 2, 3))):
        verb, vparams = r.choice(_MODS)
        if any(o["op"] == verb for o in ops):
            continue
        ops.append({"op": verb, **vparams(r), "why": _WHY})
    return {
        "name": f"sweep_{index:04d}_{opener}_{'_'.join(o['op'] for o in ops[1:]) or 'pure'}",
        "primary_language": "solid_body" if opener != "loop" else "open_figure",
        "secondary_language": "generated sweep candidate - see name for the verbs",
        "formal_principle": "스윕 후보 — 문법이 말할 수 있는 조합 하나를 게이트 앞에 세운다.",
        "dominant_gesture": ops[-1]["op"],
        "reference_basis": "grammar sweep",
        "floor_height_m": 3.4,
        "ops": ops,
    }


def main() -> int:
    count = int(sys.argv[1])
    out = Path(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20260902
    r = random.Random(seed)

    # The validator is the correctness owner: generate, filter by its
    # check() (which derives verbs/params from the executor source), repeat.
    import validate_authored as va

    out.parent.mkdir(parents=True, exist_ok=True)
    probe = out.parent / "_sweep_probe.json"
    kept: list[dict] = []
    tried = 0
    while len(kept) < count and tried < count * 8:
        tried += 1
        record = _sentence(r, tried)
        probe.write_text(json.dumps({"schemes": [record]}, ensure_ascii=False),
                         encoding="utf-8")
        faults, _verbs, _profiles = va.check(probe)
        if faults:
            continue
        kept.append(record)
    probe.unlink(missing_ok=True)

    out.write_text(json.dumps({"schemes": kept}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"kept {len(kept)} / tried {tried} (seed {seed}) -> {out}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
