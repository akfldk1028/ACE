"""MAP-Elites-style bounded archive for heavy compiled MASS candidates.

The archive keeps performance elites across architectural behavior cells rather
than retaining every compiled mesh. Rare plan and genotype anchors are protected
so memory reduction cannot silently erase triangular or other uncommon forms.
"""

from __future__ import annotations

from collections import defaultdict
import os
from typing import Any

from .candidate_analysis import (
    _Candidate,
    _capacity_alternative_key,
    _capacity_target_gate,
    _fingerprint,
    _geometry_program_family,
    _plan_family,
    _scope_key,
    _solid_morphology_metrics,
)


QD_SCHEMA = "arr.maas.map_elites_archive.v1"
QD_AXES = ("base_scope", "solid_phenotype", "capacity_alternative")


def _configured_integer(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(os.getenv(name, str(default)))))
    except (TypeError, ValueError):
        return default


def qd_archive_policy() -> dict[str, Any]:
    return {
        "schema_version": QD_SCHEMA,
        "algorithm": "MAP-Elites with rare-plan and genotype anchors",
        "descriptor_axes": list(QD_AXES),
        # A single elite preserved visual coverage but r187 demonstrated that
        # it can erase the compatibility reserve needed by the downstream
        # 20-member portfolio solver. Keep a runner-up per behavior cell so
        # legal/parking and pairwise-diversity constraints still have choices.
        "elites_per_cell": _configured_integer("MAAS_QD_ELITES_PER_CELL", 2, 1, 3),
        "max_archive_size": _configured_integer("MAAS_QD_ARCHIVE_MAX_SIZE", 192, 32, 512),
        "protect_plan_family_anchors": True,
        "protect_geometry_genotype_anchors": True,
    }


def behavior_descriptor(candidate: _Candidate) -> tuple[str, str, str]:
    morphology = _solid_morphology_metrics(candidate)
    return (
        _scope_key(candidate),
        str(morphology.get("phenotype") or "unclassified"),
        _capacity_alternative_key(candidate),
    )


def _performance_key(candidate: _Candidate) -> tuple[int, float]:
    measured_target_pass = _capacity_target_gate(candidate)
    return (int(measured_target_pass is True), float(candidate.score))


def map_elites_archive(pool: list[_Candidate]) -> list[_Candidate]:
    """Return a deterministic, bounded quality-diversity candidate archive."""
    policy = qd_archive_policy()
    elites_per_cell = int(policy["elites_per_cell"])
    maximum_size = int(policy["max_archive_size"])
    ordered = sorted(pool, key=_performance_key, reverse=True)
    cells: dict[tuple[str, str, str], list[_Candidate]] = defaultdict(list)
    for candidate in ordered:
        cell = cells[behavior_descriptor(candidate)]
        if len(cell) < elites_per_cell:
            cell.append(candidate)

    protected: list[_Candidate] = []
    seen_capacity_alternatives: set[str] = set()
    seen_principles: set[str] = set()
    seen_plan_families: set[str] = set()
    seen_genotypes: set[str] = set()
    for candidate in ordered:
        capacity_alternative = _capacity_alternative_key(candidate)
        principle_id = str(candidate.principle_id)
        plan_family = _plan_family(candidate)
        genotype = _geometry_program_family(candidate) or ""
        if capacity_alternative not in seen_capacity_alternatives:
            protected.append(candidate)
            seen_capacity_alternatives.add(capacity_alternative)
        if principle_id not in seen_principles:
            protected.append(candidate)
            seen_principles.add(principle_id)
        if plan_family and plan_family not in seen_plan_families:
            protected.append(candidate)
            seen_plan_families.add(plan_family)
        if genotype and genotype not in seen_genotypes:
            protected.append(candidate)
            seen_genotypes.add(genotype)

    retained: list[_Candidate] = []
    fingerprints: set[tuple[Any, ...]] = set()

    def admit(candidate: _Candidate) -> None:
        if len(retained) >= maximum_size:
            return
        fingerprint = _fingerprint(candidate)
        if fingerprint in fingerprints:
            return
        fingerprints.add(fingerprint)
        retained.append(candidate)

    for candidate in protected:
        admit(candidate)
    for descriptor in sorted(cells):
        for candidate in cells[descriptor]:
            admit(candidate)
    return retained


def qd_archive_evidence(pool: list[_Candidate]) -> dict[str, Any]:
    descriptors = {behavior_descriptor(candidate) for candidate in pool}
    return {
        **qd_archive_policy(),
        "retained_candidate_count": len(pool),
        "occupied_cell_count": len(descriptors),
        "plan_family_count": len({_plan_family(candidate) for candidate in pool}),
        "book_principle_count": len({str(candidate.principle_id) for candidate in pool}),
        "geometry_genotype_count": len({
            _geometry_program_family(candidate)
            for candidate in pool
            if _geometry_program_family(candidate)
        }),
    }


__all__ = [
    "QD_AXES",
    "QD_SCHEMA",
    "behavior_descriptor",
    "map_elites_archive",
    "qd_archive_evidence",
    "qd_archive_policy",
]
