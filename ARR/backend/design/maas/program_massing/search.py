"""Bounded generate-evaluate-select loop for program component assemblies."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.ir import SourceMass

from .assembly import component_mutation_limits, load_component_assemblies
from .creative import attach_creative_mass_evidence, creative_seed_sequences
from .scoring import attach_program_massing_evidence
from .sequences import program_seed_sequences


@dataclass(frozen=True)
class ProgramElite:
    sequence: VerbSequence
    source: SourceMass
    feature: dict[str, Any]
    score: float
    generation: int


def search_program_elites(
    base: Polygon,
    *,
    building_type: str,
    height: float,
    floors: int,
    generations: int = 4,
    offspring_per_seed: int = 12,
    random_seed: int = 417,
    target_count: int | None = None,
) -> tuple[tuple[ProgramElite, ...], dict[str, Any]]:
    rng = random.Random(random_seed)
    elites: list[ProgramElite] = []
    archive_pool: list[ProgramElite] = []
    evaluated = rejected = 0
    for seed in program_seed_sequences(building_type):
        parent_overrides: dict[str, float] = {}
        best: ProgramElite | None = None
        for generation in range(max(1, generations)):
            candidates = [parent_overrides]
            candidates.extend(_mutated_overrides(seed, parent_overrides, rng) for _ in range(max(1, offspring_per_seed)))
            generation_elites: list[ProgramElite] = []
            for index, overrides in enumerate(candidates):
                candidate = _with_overrides(seed, overrides, generation, index)
                source = compile_sequence_to_source_mass(base, candidate)
                evaluated += 1
                if source is None:
                    rejected += 1
                    continue
                feature = _feature(source, candidate, building_type=building_type, height=height, floors=floors, site_area=float(base.area))
                evidence = attach_program_massing_evidence(feature, building_type=building_type)
                spatial = feature["properties"]["program_spatial_evidence"]
                if not evidence["hard_pass"] or float(spatial["architectural_score"]) < 0.88:
                    rejected += 1
                    continue
                score = float(evidence["program_fit_score"]) * 0.55 + float(spatial["architectural_score"]) * 0.45
                generation_elites.append(ProgramElite(candidate, source, feature, round(score, 6), generation))
            if generation_elites:
                archive_pool.extend(generation_elites)
                generation_elites.sort(key=lambda item: (item.score, item.source.signature()["coherence_evidence"].get("score", 0.0)), reverse=True)
                best = generation_elites[0]
                parent_overrides = _extract_overrides(best.sequence)
        if best is not None:
            elites.append(best)
    if target_count is not None:
        elites = _select_diverse_archive(archive_pool, target_count=max(1, target_count))
    return tuple(elites), {
        "schema_version": "arr.maas.program_search_report.v1",
        "generations": max(1, generations),
        "offspring_per_seed": max(1, offspring_per_seed),
        "evaluated_count": evaluated,
        "rejected_count": rejected,
        "elite_count": len(elites),
        "archive_pool_count": len(archive_pool),
        "target_count": target_count,
        "random_seed": random_seed,
    }


def search_creative_elites(
    base: Polygon,
    *,
    height: float = 18.0,
    floors: int = 6,
    generations: int = 5,
    offspring_per_seed: int = 16,
    random_seed: int = 417,
    target_count: int = 20,
) -> tuple[tuple[ProgramElite, ...], dict[str, Any]]:
    """Search a program-neutral form archive before law and parking projection."""
    rng = random.Random(random_seed)
    archive_pool: list[ProgramElite] = []
    evaluated = rejected = 0
    for seed in creative_seed_sequences():
        parent_overrides: dict[str, float] = {}
        for generation in range(max(1, generations)):
            candidates = [parent_overrides]
            candidates.extend(_mutated_overrides(seed, parent_overrides, rng) for _ in range(max(1, offspring_per_seed)))
            generation_elites: list[ProgramElite] = []
            for index, overrides in enumerate(candidates):
                candidate = _with_overrides(seed, overrides, generation, index, stage="creative")
                source = compile_sequence_to_source_mass(base, candidate)
                evaluated += 1
                if source is None:
                    rejected += 1
                    continue
                feature = _feature(
                    source,
                    candidate,
                    building_type="creative mass exploration",
                    height=height,
                    floors=floors,
                    site_area=float(base.area),
                )
                evidence = attach_creative_mass_evidence(feature, site_area_m2=float(base.area))
                if not evidence["hard_pass"]:
                    rejected += 1
                    continue
                score = float(evidence["creative_score"])
                generation_elites.append(ProgramElite(candidate, source, feature, round(score, 6), generation))
            if generation_elites:
                archive_pool.extend(generation_elites)
                generation_elites.sort(key=lambda item: item.score, reverse=True)
                parent_overrides = _extract_overrides(generation_elites[0].sequence)
    elites = _select_diverse_archive(archive_pool, target_count=max(1, target_count))
    geometric_language_count = _geometric_language_count(list(elites))
    return tuple(elites), {
        "schema_version": "arr.maas.creative_search_report.v1",
        "stage": "creative_form_exploration",
        "program_conditioned": False,
        "legal_parking_checked": False,
        "generations": max(1, generations),
        "offspring_per_seed": max(1, offspring_per_seed),
        "evaluated_count": evaluated,
        "rejected_count": rejected,
        "elite_count": len(elites),
        "geometric_language_count": geometric_language_count,
        "archive_pool_count": len(archive_pool),
        "target_count": target_count,
        "random_seed": random_seed,
    }


def _select_diverse_archive(pool: list[ProgramElite], *, target_count: int) -> list[ProgramElite]:
    unique: dict[tuple[Any, ...], ProgramElite] = {}
    for item in pool:
        fingerprint = _geometry_fingerprint(item)
        current = unique.get(fingerprint)
        if current is None or item.score > current.score:
            unique[fingerprint] = item
    candidates = [item for item in unique.values() if item.score >= 0.75]
    if len(candidates) < target_count:
        candidates = list(unique.values())
    topology_count = max(1, len({_topology(item) for item in candidates}))
    topology_cap = max(1, (target_count + topology_count - 1) // topology_count)
    representatives: dict[str, ProgramElite] = {}
    for item in candidates:
        key = _topology(item)
        current = representatives.get(key)
        if current is None or item.score > current.score:
            representatives[key] = item
    selected = sorted(representatives.values(), key=lambda item: item.score, reverse=True)[:target_count]
    topology_usage = {_topology(item): 1 for item in selected}
    for item in selected:
        candidates.remove(item)
    while candidates and len(selected) < target_count:
        eligible = [item for item in candidates if topology_usage.get(_topology(item), 0) < topology_cap]
        if not eligible:
            break
        def selection_key(item: ProgramElite) -> tuple[float, float]:
            novelty = 1.0 if not selected else min(_descriptor_distance(item, other) for other in selected)
            return item.score * 0.68 + novelty * 0.32, item.score
        winner = max(eligible, key=selection_key)
        selected.append(winner)
        topology_usage[_topology(winner)] = topology_usage.get(_topology(winner), 0) + 1
        candidates.remove(winner)
    return selected


def _topology(item: ProgramElite) -> str:
    return item.sequence.name.split("__search_", 1)[0]


def _geometry_fingerprint(item: ProgramElite) -> tuple[Any, ...]:
    return tuple(sorted((
        volume.role,
        *(round(value, 1) for value in volume.footprint.bounds),
        round(volume.bottom_fraction, 2),
        round(volume.top_fraction, 2),
    ) for volume in item.source.volumes))


def _descriptor_distance(left: ProgramElite, right: ProgramElite) -> float:
    def vector(item: ProgramElite) -> tuple[float, ...]:
        props = item.feature["properties"]
        evidence = props.get("creative_mass_evidence") or props.get("program_spatial_evidence") or {}
        signature = item.source.signature()
        union = unary_union([volume.footprint for volume in item.source.volumes])
        envelope = union.minimum_rotated_rectangle
        envelope_area = max(float(envelope.area), 1e-9)
        compactness = min(1.0, float(union.area) / envelope_area)
        minx, miny, maxx, maxy = union.bounds
        aspect = min(maxx - minx, maxy - miny) / max(max(maxx - minx, maxy - miny), 1e-9)
        height_bands = sorted({round(volume.top_fraction, 2) for volume in item.source.volumes})
        return (
            float(evidence["dominant_component_ratio"]),
            float(evidence["site_coverage_ratio"]),
            min(1.0, float(evidence["height_level_count"]) / 4.0),
            min(1.0, float(signature["surface_count"]) / 48.0),
            compactness,
            aspect,
            min(1.0, len(item.source.volumes) / 5.0),
            sum(height_bands) / max(len(height_bands), 1),
        )
    a, b = vector(left), vector(right)
    left_plan = unary_union([volume.footprint for volume in left.source.volumes])
    right_plan = unary_union([volume.footprint for volume in right.source.volumes])
    plan_union = left_plan.union(right_plan)
    plan_distance = float(left_plan.symmetric_difference(right_plan).area) / max(float(plan_union.area), 1e-9)
    scalar_distance = min(1.0, sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5 / 1.35)
    return min(1.0, plan_distance * 0.62 + scalar_distance * 0.38)


def _geometric_language_count(items: list[ProgramElite], *, threshold: float = 0.16) -> int:
    """Count visibly distinct geometry groups, independent of topology labels."""
    representatives: list[ProgramElite] = []
    for item in sorted(items, key=lambda candidate: candidate.score, reverse=True):
        if all(_descriptor_distance(item, other) >= threshold for other in representatives):
            representatives.append(item)
    return len(representatives)


def _mutated_overrides(seed: VerbSequence, parent: dict[str, float], rng: random.Random) -> dict[str, float]:
    payload = load_component_assemblies()
    templates = payload.get("templates") or {}
    template_name = seed.name.replace("creative_", "program_housing_", 1) if seed.name.startswith("creative_") else seed.name
    template = templates.get(template_name)
    if template is None:
        return _mutated_graph_parameters(seed, parent, rng)
    limits = component_mutation_limits(seed.name)
    coord_delta = limits.get("coordinate_delta", 0.03)
    height_delta = limits.get("height_delta", 0.05)
    rotation_delta = limits.get("rotation_delta", 0.0)
    result: dict[str, float] = {}
    for index, component in enumerate(template.get("components") or []):
        if component.get("polygon") or component.get("path"):
            points = component.get("polygon") or component.get("path")
            for vertex_index, point in enumerate(points):
                for axis, baseline in zip(("x", "y"), point):
                    key = f"component_{index}_vertex_{vertex_index}_{axis}"
                    center = parent.get(key, float(baseline))
                    result[key] = round(max(0.0, min(1.0, center + rng.uniform(-coord_delta, coord_delta))), 4)
            if component.get("path"):
                key = f"component_{index}_width_ratio"
                center = parent.get(key, float(component.get("width_ratio", 0.08)))
                result[key] = round(max(0.025, min(0.22, center + rng.uniform(-coord_delta * 0.45, coord_delta * 0.45))), 4)
        else:
            for axis, baseline in enumerate(component["bounds"]):
                key = f"component_{index}_bound_{axis}"
                center = parent.get(key, float(baseline))
                result[key] = round(max(0.0, min(1.0, center + rng.uniform(-coord_delta, coord_delta))), 4)
        for axis, baseline in enumerate(component["height"]):
            key = f"component_{index}_height_{axis}"
            center = parent.get(key, float(baseline))
            result[key] = round(max(0.0, min(1.0, center + rng.uniform(-height_delta, height_delta))), 4)
        if rotation_delta > 0 or component.get("rotation_deg"):
            key = f"component_{index}_rotation"
            center = parent.get(key, float(component.get("rotation_deg", 0.0)))
            result[key] = round(max(-35.0, min(35.0, center + rng.uniform(-rotation_delta, rotation_delta))), 3)
    return result


def _mutated_graph_parameters(seed: VerbSequence, parent: dict[str, float], rng: random.Random) -> dict[str, float]:
    """Mutate parameters on every MassDSL call while preserving its graph topology."""
    result: dict[str, float] = {}
    for call_index, operation in enumerate(seed.calls[1:], start=1):
        for name, baseline_value in operation.params.items():
            if isinstance(baseline_value, bool) or not isinstance(baseline_value, (int, float)):
                continue
            key = f"call_{call_index}__{name}"
            center = parent.get(key, float(baseline_value))
            if name == "angle":
                value = max(-70.0, min(70.0, center + rng.uniform(-9.0, 9.0)))
            elif name == "n":
                value = float(max(2, min(5, round(center + rng.choice((-1, 0, 1))))))
            elif name in {"shift", "distance_ratio"}:
                value = max(-0.30, min(0.30, center + rng.uniform(-0.055, 0.055)))
            elif name == "gap":
                value = max(0.015, min(0.14, center + rng.uniform(-0.018, 0.018)))
            elif "ratio" in name or name in {"factor", "inner_scale", "guest_scale", "length", "size"}:
                value = max(0.10, min(0.96, center + rng.uniform(-0.075, 0.075)))
            else:
                value = center + rng.uniform(-0.06, 0.06)
            result[key] = round(value, 4)
    return result


def _with_overrides(seed: VerbSequence, overrides: dict[str, float], generation: int, index: int, *, stage: str = "program") -> VerbSequence:
    calls = list(seed.calls)
    component_overrides = {key: value for key, value in overrides.items() if key.startswith("component_")}
    if component_overrides:
        last = calls[-1]
        calls[-1] = VerbCall(last.verb, {**last.params, **component_overrides})
    for call_index, operation in enumerate(calls):
        prefix = f"call_{call_index}__"
        changes = {key[len(prefix):]: value for key, value in overrides.items() if key.startswith(prefix)}
        if changes:
            calls[call_index] = VerbCall(operation.verb, {**operation.params, **changes})
    return VerbSequence(
        name=f"{seed.name}__search_g{generation}_{index}",
        label=seed.label,
        calls=tuple(calls),
        notes=seed.notes + (f"{stage}_component_search=bounded_generate_evaluate_select",),
    )


def _extract_overrides(sequence: VerbSequence) -> dict[str, float]:
    result = {key: float(value) for key, value in sequence.calls[-1].params.items() if key.startswith("component_")}
    for call_index, operation in enumerate(sequence.calls):
        for key, value in operation.params.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            result[f"call_{call_index}__{key}"] = float(value)
    return result


def _feature(source: SourceMass, sequence: VerbSequence, *, building_type: str, height: float, floors: int, site_area: float) -> dict[str, Any]:
    origin = source.footprint.centroid
    source_surfaces = []
    for surface in source.surfaces:
        record = surface.signature()
        record["vertices_world_m"] = [
            [round(float(origin.x) + x, 3), round(float(origin.y) + y, 3), round(height * z, 3)]
            for x, y, z in surface.vertices_m
        ]
        source_surfaces.append(record)
    return {
        "type": "Feature",
        "geometry": mapping(source.footprint),
        "properties": {
            "variant_id": sequence.name,
            "mass_shape": source.name,
            "building_type": building_type,
            "height": height,
            "num_floors": floors,
            "benchmark_site_area_m2": site_area,
            "mass_volumes": [{
                "geometry": mapping(volume.footprint),
                "bottom_height": round(height * volume.bottom_fraction, 3),
                "top_height": round(height * volume.top_fraction, 3),
                "role": volume.role,
            } for volume in source.volumes],
            "source_surfaces": source_surfaces,
            "source_signature": source.signature(),
            "maas_model": {},
        },
    }


__all__ = ["ProgramElite", "search_creative_elites", "search_program_elites"]
