"""Causal scheduling for the BOOK 30/20/9/10 language corpus."""

from __future__ import annotations

from typing import Any


def staged_principle_schedule(
    principles: tuple[dict[str, Any], ...],
    seed_index: int,
    *,
    count: int,
) -> tuple[tuple[int, dict[str, Any]], ...]:
    """Return base parents first and only then their recorded descendants."""
    if not principles:
        return ()
    wanted = max(6, min(len(principles), int(count)))
    indexed = tuple(enumerate(principles))
    bases = tuple(
        item for item in indexed
        if str(item[1].get("generation_stage") or item[1].get("kind"))
        in {"base", "base_operative"}
    )
    if not bases:
        return indexed[:wanted]

    descendants_by_base: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for item in indexed:
        base_id = str(item[1].get("lineage_base_operative_id") or "")
        if base_id and str(item[1].get("principle_id") or "") != base_id:
            descendants_by_base.setdefault(base_id, []).append(item)
    rich_bases = tuple(
        item for item in bases
        if str(item[1].get("principle_id") or "") in descendants_by_base
    )

    root_target = min(len(bases), max(1, wanted // 2))
    rich_target = min(len(rich_bases), max(1, root_target - 2))
    chosen_bases: list[tuple[int, dict[str, Any]]] = []

    def rotating(source, amount: int, offset: int):
        result = []
        if not source or amount <= 0:
            return result
        cursor = offset % len(source)
        visited = 0
        while len(result) < amount and visited < len(source) * 2:
            item = source[cursor]
            if item not in chosen_bases and item not in result:
                result.append(item)
            cursor = (cursor + 7) % len(source)
            visited += 1
        return result

    chosen_bases.extend(rotating(rich_bases, rich_target, int(seed_index) * 5))
    chosen_bases.extend(rotating(
        bases,
        root_target - len(chosen_bases),
        int(seed_index) * 11,
    ))
    scheduled: list[tuple[int, dict[str, Any]]] = list(chosen_bases)
    child_depth = 0
    while len(scheduled) < wanted:
        added = False
        for _base_index, base in chosen_bases:
            children = descendants_by_base.get(str(base.get("principle_id") or ""), ())
            if not children:
                continue
            child = children[(child_depth + int(seed_index)) % len(children)]
            if child not in scheduled:
                scheduled.append(child)
                added = True
                if len(scheduled) >= wanted:
                    break
        if not added:
            break
        child_depth += 1
    if len(scheduled) < wanted:
        scheduled.extend(rotating(
            bases,
            wanted - len(scheduled),
            int(seed_index) * 13 + 1,
        ))
    return tuple(scheduled[:wanted])


def lineage_record(
    principle: dict[str, Any],
    *,
    source_seed: str,
    scope_label: str,
    orientation: str,
    variant_index: int,
) -> dict[str, Any]:
    """Build the stable parent key shared by a base and its descendants."""
    base_id = str(
        principle.get("lineage_base_operative_id")
        or principle.get("principle_id")
        or ""
    )
    parent_key = "|".join((
        source_seed,
        base_id,
        scope_label,
        orientation,
        f"v{int(variant_index)}",
    ))
    return {
        "schema_version": "arr.maas.book_generation_lineage.v1",
        "stage": str(principle.get("generation_stage") or principle.get("kind") or "base"),
        "stage_order": int(principle.get("generation_stage_order") or 1),
        "principle_id": str(principle.get("principle_id") or ""),
        "principle_label": str(principle.get("label") or ""),
        "principle_kind": str(principle.get("kind") or ""),
        "execution_verbs": list(principle.get("execution_verbs") or ()),
        "implementation_elements": list(principle.get("implementation_elements") or ()),
        "base_operative_id": base_id,
        "parent_principle_id": principle.get("lineage_parent_principle_id"),
        "parent_key": parent_key,
        "source_seed": source_seed,
        "scope_label": scope_label,
        "orientation": orientation,
        "variant_index": int(variant_index),
    }


def gate_descendants_by_base(candidates: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    """Keep descendants only when their exact base parent is in the pool."""
    def family(candidate: Any) -> str:
        raw_program = candidate.source.metadata.get("geometry_program") or {}
        metadata = raw_program.get("metadata") if isinstance(raw_program, dict) else {}
        return str(
            (metadata or {}).get("family")
            or candidate.source.metadata.get("family")
            or "unclassified"
        )

    base_keys = {
        str((candidate.source.metadata.get("book_generation_lineage") or {}).get("parent_key") or "")
        for candidate in candidates
        if str((candidate.source.metadata.get("book_generation_lineage") or {}).get("stage") or "") == "base"
    }
    retained = []
    rejected = 0
    family_counts: dict[str, dict[str, int]] = {}
    for candidate in candidates:
        lineage = candidate.source.metadata.get("book_generation_lineage") or {}
        stage = str(lineage.get("stage") or "")
        candidate_family = family(candidate)
        counts = family_counts.setdefault(candidate_family, {
            "input_base_count": 0,
            "input_descendant_count": 0,
            "retained_base_count": 0,
            "retained_descendant_count": 0,
            "rejected_descendant_without_viable_base_count": 0,
        })
        counts["input_base_count" if stage == "base" else "input_descendant_count"] += 1
        if stage == "base" or str(lineage.get("parent_key") or "") in base_keys:
            retained.append(candidate)
            counts["retained_base_count" if stage == "base" else "retained_descendant_count"] += 1
        else:
            rejected += 1
            counts["rejected_descendant_without_viable_base_count"] += 1
    return retained, {
        "schema_version": "arr.maas.book_lineage_gate.v1",
        "input_count": len(candidates),
        "base_parent_count": len(base_keys),
        "retained_count": len(retained),
        "descendant_without_viable_base_count": rejected,
        "by_geometry_family": dict(sorted(family_counts.items())),
        "hard_pass": rejected == 0,
    }


__all__ = ["gate_descendants_by_base", "lineage_record", "staged_principle_schedule"]
