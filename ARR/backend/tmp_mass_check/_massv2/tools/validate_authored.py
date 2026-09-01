"""Check authored sentences against the grammar before the pipeline sees them.

A generator plus a sound verifier is the part of LLM-Modulo that pays; the
critique loop is the part that does not. So this refuses, it does not advise.
"""

import inspect
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# The verb list drifted from the executor twice: once an authoring agent hit
# a `tie` floor the executor no longer had, and once this file refused seven
# real words (gable, vault, canopy, lodge, nest, branch, mansard) and the
# whole stack-method parameter set - a hand-copied enumeration is exactly
# what the one-owner rule exists to prevent. So the owner answers directly:
# verbs come from `execute._VERBS`, and each verb's parameters are read out
# of its own source (`op.params.get("...")`). The old hand table survives
# only as a union for helpers this scan cannot see into.
_HAND_PARAMS = {
    "extrude":   {"height"},
    "split":     {"ratio", "along", "first", "second", "contrast", "gap"},
    "stack":     {"n", "contrast", "align", "height", "grow"},
    "aggregate": {"n", "spread", "height", "tie"},
    "loop":      {"bar", "height", "step"},
    "shear":     {"ratio", "toward"},
    "taper":     {"ratio"},
    "lift":      {"clearance"},
    "carve":     {"size", "at", "reach"},
    "notch":     {"size", "at"},
    "puncture":  {"size", "n"},
    "rotate":    {"degrees"}, "skew": {"degrees", "toward"},
    "twist":     {"degrees"}, "shift": {"ratio", "toward"},
    "offset":    {"ratio", "toward"}, "expand": {"ratio", "toward"},
    "compress":  {"ratio", "toward"}, "inflate": {"ratio"},
}
# Read by the frame, the parser or the grid on ANY op: target, regulating
# pivot, plan family, declared stature (the grid stamps `storeys` as
# declared stature whatever the verb - the declared-storeys exemption).
_UNIVERSAL = {"on", "about", "profile", "storeys"}


def _derived_verbs() -> dict:
    from design.maas.massv2.execute import _VERBS
    table = {}
    for verb, fn in _VERBS.items():
        try:
            source = inspect.getsource(fn)
        except (OSError, TypeError):
            source = ""
        params = set(re.findall(r'params\.get\(\s*"([a-z_]+)"', source))
        table[verb] = params | _HAND_PARAMS.get(verb, set()) | _UNIVERSAL
    return table


VERBS = _derived_verbs()
PROFILES = {"square", "oval", "stadium", "hexagon", "chamfered", "faceted",
            "trapezoidal", "triangular", "kite", "concave_l"}
LANGUAGES = {"solid_body", "carved_body", "open_figure", "porous_field"}
RANGES = {
    "height": (0.1, 1.0), "ratio": (0.15, 0.95), "n": (2, 6),
    "contrast": (1.2, 2.5), "spread": (1.2, 2.5), "bar": (0.15, 0.5),
    # 0 is legal and means "no binding plate at all" - Moriyama and the
    # Inujima Art Houses have none, and the executor allows it since the
    # field cap was lifted. The validator was still refusing it.
    "tie": (0.0, 0.4), "step": (0.4, 1.0),
    "size": (0.1, 0.7), "reach": (0.0, 1.0), "clearance": (0.1, 0.4),
    "degrees": (-90.0, 90.0),
    # `gap` is a multiplier of JOINT_CLEARANCE_M (0.76 m) and the executor
    # does not clamp it. 9 is 6.8 m, which is a courtyard between two bodies
    # rather than a construction tolerance - the void the critics said the
    # corpus never produces. Bounded only where the parts would leave the site.
    "gap": (0.0, 12.0),
}

# Where a parameter name means different things to different verbs. `ratio` is
# a share for `split` and a multiplier for `expand`, so one global range refused
# a legal `expand: 1.6`. Checked before RANGES.
PER_VERB_RANGES = {
    ("expand", "ratio"): (1.0, 1.6),
    ("inflate", "ratio"): (1.0, 1.6),
    ("compress", "ratio"): (0.6, 1.0),
    ("stack", "contrast"): (1.2, 3.5),
    ("split", "contrast"): (1.2, 3.5),
    ("aggregate", "spread"): (1.05, 2.5),
}

# Verbs that bring volumes into being. Everything else transforms or cuts what
# is already standing, so a sentence that opens with one of those has nothing to
# act on and produces no mass at all - the diff check reports an empty list
# rather than a silent word, which is easy to miss.
MAKING_VERBS = {"extrude", "stack", "loop", "aggregate"}

REQUIRED = ("name", "primary_language", "secondary_language", "formal_principle",
            "dominant_gesture", "reference_basis", "ops")


def check(path: Path) -> tuple[list, Counter, Counter]:
    faults: list[str] = []
    verbs: Counter = Counter()
    profiles: Counter = Counter()
    data = json.loads(path.read_text(encoding="utf-8"))
    schemes = data.get("schemes")
    if not isinstance(schemes, list) or not schemes:
        return [f"{path.name}: no schemes"], verbs, profiles

    for scheme in schemes:
        name = scheme.get("name", "?")
        for field in REQUIRED:
            if not scheme.get(field):
                faults.append(f"{name}: missing {field}")
        if scheme.get("primary_language") not in LANGUAGES:
            faults.append(f"{name}: primary_language {scheme.get('primary_language')!r} "
                          f"not one of {sorted(LANGUAGES)}")
        ops = scheme.get("ops") or []
        if ops and str(ops[0].get("op")) not in MAKING_VERBS:
            faults.append(f"{name}: opens with {ops[0].get('op')!r}, which needs a "
                          f"volume to act on - start with one of {sorted(MAKING_VERBS)}")
        if not 2 <= len(ops) <= 6:
            faults.append(f"{name}: {len(ops)} ops, wanted 2..6")

        # what names exist for a later verb to aim at
        available: set[str] = set()
        for index, op in enumerate(ops):
            verb = op.get("op")
            if verb not in VERBS:
                faults.append(f"{name} op{index}: unknown verb {verb!r}")
                continue
            verbs[verb] += 1
            unknown = set(op) - VERBS[verb] - {"op", "why"}
            if unknown:
                faults.append(f"{name} op{index} ({verb}): unknown params {sorted(unknown)}")
            if not str(op.get("why") or "").strip():
                faults.append(f"{name} op{index} ({verb}): no why")
            for key, (lo, hi) in RANGES.items():
                if key in op and isinstance(op[key], (int, float)):
                    lo, hi = PER_VERB_RANGES.get((verb, key), (lo, hi))
                    if (verb, key) == ("aggregate", "spread") and \
                            str(op.get("method") or "") == "stack":
                        # The stack branch uses spread as its size fan and
                        # 1.0 (no fan) is legal there; the 1.05 floor is the
                        # pack branch's spacing rule.
                        lo = 1.0
                    if not lo <= op[key] <= hi:
                        faults.append(f"{name} op{index} ({verb}): {key}={op[key]} "
                                      f"outside {lo}..{hi}")
            if "profile" in op:
                if op["profile"] not in PROFILES:
                    faults.append(f"{name} op{index}: profile {op['profile']!r} unknown")
                else:
                    profiles[op["profile"]] += 1
            # an `on` that names nothing is a silent verb by construction
            target = str(op.get("on") or "").strip()
            if target and not any(known.startswith(target) or target.startswith(known)
                                  for known in available):
                faults.append(f"{name} op{index} ({verb}): on={target!r} names nothing "
                              f"standing (available: {sorted(available) or 'nothing yet'})")
            if verb == "split":
                available.update({str(op.get("first") or "part_a"),
                                  str(op.get("second") or "part_b")})
            elif verb == "extrude":
                available.add("body")
            elif verb == "stack":
                available.update(f"tier_{i}" for i in range(int(op.get("n", 3))))
            elif verb == "aggregate":
                available.update(f"object_{i}" for i in range(int(op.get("n", 4))))
                available.add("field_plate")
            elif verb == "loop":
                available.update({"bar_n", "bar_s", "bar_e", "bar_w"})
            elif verb == "lift":
                available.add("support")
    return faults, verbs, profiles


def main() -> None:
    total_faults = 0
    verbs: Counter = Counter()
    profiles: Counter = Counter()
    count = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"MISSING  {path}")
            total_faults += 1
            continue
        faults, v, p = check(path)
        verbs += v
        profiles += p
        count += len(json.loads(path.read_text(encoding="utf-8")).get("schemes", []))
        status = "OK" if not faults else f"{len(faults)} FAULTS"
        print(f"\n=== {path.name}: {status}")
        for fault in faults[:40]:
            print("   ", fault)
        total_faults += len(faults)
    print(f"\nsentences {count}   faults {total_faults}")
    print("verbs   ", dict(verbs.most_common()))
    print("profiles", dict(profiles.most_common()))
    carve = verbs.get("carve", 0)
    if count:
        print(f"carve per sentence: {carve/count:.2f}   (기존 코퍼스 0.97)")
    sys.exit(1 if total_faults else 0)


main()
