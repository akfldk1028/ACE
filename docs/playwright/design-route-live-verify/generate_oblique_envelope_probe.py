#!/usr/bin/env python3
"""Generate a real-PNU visual harness for the generic oblique-envelope genotype.

This is an evaluation harness, not a production preset library.  Every card
uses the same ``taper`` graph operation and the same polygon-ring compiler;
only agent-editable normalized genotype parameters change.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "ARR" / "backend"
sys.path.insert(0, str(BACKEND))

import django  # noqa: E402
from shapely.geometry import Polygon, mapping  # noqa: E402

from design.maas.grammar.verb_sequence import VerbCall, VerbSequence  # noqa: E402
from design.maas.program_massing.search import _feature  # noqa: E402
from design.maas.source_geometry import compile_sequence_to_source_mass  # noqa: E402


PNU = "1168011800104170004"
SOURCE_PROBE = Path(__file__).with_name("maas-section-loft-genotype-probe-v1.json")
OUTPUT = Path(__file__).with_name("maas-oblique-envelope-genotype-probe-v1.json")


def polygon_controls(vertex_count: int, phase: float, bias: float) -> list[list[float]]:
    """Return a clean convex-ish plan field without storing a building outline."""
    points = []
    for index in range(vertex_count):
        angle = -math.pi / 2 + phase + index * math.tau / vertex_count
        radial = 0.40 + 0.035 * math.sin(index * 1.7 + bias)
        u = 0.5 + radial * math.cos(angle) * (1.0 + 0.10 * bias)
        v = 0.5 + radial * math.sin(angle) * (0.92 - 0.05 * bias)
        points.append([round(max(0.05, min(0.95, u)), 4), round(max(0.05, min(0.95, v)), 4)])
    return points


def authored_genotypes() -> list[tuple[str, dict]]:
    """Sample four behavior regions of one editable representation."""
    variants: list[tuple[str, dict]] = []
    regions = (
        ("wedge_monolith", 4, 0.48, 0.76, -0.16, 0.28, 0.92, 0.22, 0.25),
        ("diagonal_undercut", 4, 0.40, 0.70, -0.22, 0.92, 0.90, 0.04, 0.04),
        ("shifted_polygon_plate", 6, 0.70, 0.76, -0.08, 0.82, 0.86, 0.18, 0.12),
        ("leaning_ridge", 5, 0.58, 0.68, 0.12, 0.48, 0.96, -0.20, 0.24),
    )
    for region_index, region in enumerate(regions):
        label, base_vertices, base_sx, base_sy, base_shift, top_sx, top_sy, top_shift, height_amplitude = region
        for sample in range(5):
            count = max(3, min(8, base_vertices + ((sample + region_index) % 3) - 1))
            phase = 0.04 * sample + 0.09 * region_index
            bias = (sample - 2) * 0.12
            controls = polygon_controls(count, phase, bias)
            heights = [
                round(max(0.44, min(1.0, 0.94 + height_amplitude * math.sin(index * 1.3 + sample * 0.4 + region_index))), 4)
                for index in range(count)
            ]
            variants.append((f"{label}_{sample + 1:02d}", {
                "x_ratio": 0.88,
                "y_ratio": 0.86,
                "lower_floor_fraction": 0.28,
                "plan_control_points": controls,
                "top_height_controls": heights,
                "shoulder_fraction": round(0.22 + 0.055 * ((sample + region_index) % 5), 4),
                "base_scale_x_ratio": round(base_sx + 0.025 * (sample - 2), 4),
                "base_scale_y_ratio": round(base_sy + 0.018 * (2 - sample), 4),
                "base_shift_x_ratio": round(base_shift + 0.018 * (sample - 2), 4),
                "base_shift_y_ratio": round(0.025 * math.sin(sample + region_index), 4),
                "top_scale_x_ratio": round(top_sx + 0.028 * (sample - 2), 4),
                "top_scale_y_ratio": round(top_sy - 0.018 * (sample - 2), 4),
                "top_shift_x_ratio": round(top_shift - 0.018 * (sample - 2), 4),
                "top_shift_y_ratio": round(0.035 * math.cos(sample * 0.8 + region_index), 4),
                "design_field_source": "agent_genotype_visual_harness",
            }))
    return variants


def main() -> None:
    django.setup()
    source_payload = json.loads(SOURCE_PROBE.read_text(encoding="utf-8"))
    site_geometry = source_payload["boundary"]["geometry"]
    site = Polygon(site_geometry["coordinates"][0])
    features = []
    for index, (label, params) in enumerate(authored_genotypes(), start=1):
        sequence = VerbSequence(
            label,
            label,
            (VerbCall("base", {}), VerbCall("taper", params)),
            notes=("formal_principle=undercut_tapered_tower",),
        )
        source = compile_sequence_to_source_mass(site, sequence)
        if source is None:
            raise RuntimeError(f"oblique genotype did not compile: {label}")
        height = 18.0 + 1.2 * (index % 4)
        floors = max(3, round(height / 3.6))
        feature = _feature(
            source,
            sequence,
            building_type="neighborhood living",
            height=height,
            floors=floors,
            site_area=site.area,
        )
        proxy_area = sum(volume.footprint.area for volume in source.volumes)
        properties = feature["properties"]
        properties.update({
            "variant_id": f"oblique_{index:02d}",
            "mass_shape": label,
            "maas_concept": "agent polygon-ring field",
            "typology_family": "agent_oblique_envelope",
            "operator_family": "polygon_ring_loft",
            "maas_sequence_verbs": ["base", "taper"],
            "far": round(proxy_area * floors / site.area * 100.0, 2),
            "bcr": round(proxy_area / site.area * 100.0, 2),
            "parking_precheck": {
                "required_count": {"required_spaces": "probe"},
                "layout_candidate": {"status": "representation_probe", "provided_spaces": "-"},
            },
        })
        features.append(feature)

    payload = {
        "schema_version": "arr.maas.oblique-envelope-probe.v1",
        "pnu": PNU,
        "building_type": "근린생활시설 · oblique-envelope representation probe",
        "elapsed_ms": 0,
        "boundary": {"geometry": mapping(site)},
        "response": {"feature_collection": {"type": "FeatureCollection", "features": features}},
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "count": len(features)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
