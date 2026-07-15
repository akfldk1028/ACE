#!/usr/bin/env python3
"""Generate visual evidence for the generic sectional-monolith genotype."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from shapely.geometry import box, mapping


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "ARR" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from design.maas.grammar.verb_sequence import VerbCall, VerbSequence  # noqa: E402
from design.maas.program_massing.search import _feature  # noqa: E402
from design.maas.source_geometry.compiler import compile_sequence_to_source_mass  # noqa: E402


CASES = (
    ("wedge_gate", [[0.08, 0.0], [0.92, 0.0], [0.60, 1.0], [0.22, 0.72]], [[0.56, 0.0], [0.80, 0.0], [0.69, 0.32]], 0.72, -0.04),
    ("diagonal_undercut", [[0.06, 0.0], [0.94, 0.0], [0.94, 1.0], [0.06, 1.0]], [[0.44, 0.0], [0.94, 0.0], [0.94, 0.42]], 0.66, 0.10),
    ("elevated_mega_void", [[0.06, 0.0], [0.94, 0.0], [0.94, 1.0], [0.06, 1.0]], [[0.16, 0.34], [0.76, 0.34], [0.76, 0.73], [0.16, 0.73]], 0.82, -0.06),
    ("leaning_court", [[0.08, 0.0], [0.88, 0.0], [0.96, 0.82], [0.68, 1.0], [0.12, 0.84]], [[0.27, 0.28], [0.73, 0.36], [0.67, 0.68], [0.31, 0.62]], 0.58, 0.12),
    ("split_ground_portal", [[0.05, 0.0], [0.95, 0.0], [0.82, 1.0], [0.18, 1.0]], [[0.30, 0.0], [0.70, 0.0], [0.62, 0.46], [0.38, 0.46]], 0.76, 0.0),
    ("cantilever_window", [[0.08, 0.0], [0.88, 0.0], [0.96, 0.70], [0.72, 1.0], [0.16, 0.88]], [[0.12, 0.24], [0.62, 0.24], [0.74, 0.62], [0.24, 0.70]], 0.48, -0.15),
)


def main() -> None:
    site = box(0, 0, 60, 40)
    features = []
    for index, (name, outer, void, depth, shift) in enumerate(CASES, start=1):
        params = {
            "axis": "x" if index % 2 else "y",
            "length": 0.86,
            "size": 0.72,
            "upper_ratio": 0.82,
            "lower_floor_fraction": 0.45,
            "section_depth_ratio": depth,
            "section_depth_shift_ratio": shift,
            "section_outer_control_points": outer,
            "section_void_control_points": void,
            "design_field_source": "capability_probe_agent_controls",
        }
        sequence = VerbSequence(
            f"sectional_{index:02d}_{name}",
            name.replace("_", " "),
            (VerbCall("base", {}), VerbCall("extrude", params)),
            notes=(
                "formal_principle=sectional_monolith_cut",
                "mass_language=sectional_monolith",
                "primary_language=section_solid_void",
            ),
        )
        source = compile_sequence_to_source_mass(site, sequence)
        if source is None:
            raise RuntimeError(f"failed to compile {name}")
        feature = _feature(source, sequence, building_type="neighborhood facility capability probe", height=24.0, floors=6, site_area=2400.0)
        feature["properties"].update({
            "maas_concept": name.replace("_", " "),
            "typology_family": "sectional_monolith",
            "far": round(sum(volume.footprint.area * max(0.0, volume.top_fraction - volume.bottom_fraction) for volume in source.volumes) * 6 / 2400 * 100, 1),
            "bcr": round(source.footprint.area / 2400 * 100, 1),
        })
        features.append(feature)
    payload = {
        "pnu": "SECTION-GENOTYPE-PROBE",
        "building_type": "근린생활시설 · section solid/void capability",
        "elapsed_ms": 0,
        "boundary": {"geometry": mapping(site)},
        "response": {"feature_collection": {"type": "FeatureCollection", "features": features}},
    }
    output = Path(__file__).with_name("maas-sectional-monolith-probe-latest.json")
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
