"""Check authored sentences against the grammar before the pipeline sees them.

A generator plus a sound verifier is the part of LLM-Modulo that pays; the
critique loop is the part that does not. So this refuses, it does not advise.
"""

import json
import sys
from collections import Counter
from pathlib import Path

VERBS = {
    "extrude":   {"height", "profile"},
    "split":     {"ratio", "along", "first", "second", "contrast", "gap", "on", "profile"},
    "stack":     {"n", "contrast", "align", "height", "grow", "on", "profile"},
    "aggregate": {"n", "spread", "height", "tie", "on", "profile"},
    "loop":      {"bar", "height", "on", "profile"},
    "shear":     {"ratio", "toward", "on"},
    "taper":     {"ratio", "on"},
    "lift":      {"clearance", "on"},
    "carve":     {"size", "at", "reach", "on"},
}
PROFILES = {"square", "oval", "stadium", "hexagon", "chamfered", "faceted",
            "trapezoidal", "triangular", "kite", "concave_l"}
LANGUAGES = {"solid_body", "carved_body", "open_figure", "porous_field"}
RANGES = {
    "height": (0.1, 1.0), "ratio": (0.15, 0.95), "n": (2, 6),
    "contrast": (1.2, 2.5), "spread": (1.2, 2.5), "bar": (0.15, 0.5),
    "tie": (0.08, 0.4),
    "size": (0.1, 0.7), "reach": (0.0, 1.0), "clearance": (0.05, 0.4),
    "gap": (0.0, 4.0),
}
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
