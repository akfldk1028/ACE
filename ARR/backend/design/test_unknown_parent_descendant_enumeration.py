import hashlib
import json
from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from shapely.geometry import box

from design.maas.book_language import candidate_generation


def _fingerprint(geometry_hash: str) -> str:
    return hashlib.sha256(json.dumps(
        {"geometry_hash": geometry_hash},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _lineage(
    *,
    source_seed="same-seed",
    scope="3/8",
    orientation="long_axis",
    variant_index=0,
):
    parent = candidate_generation.lineage_record(
        {
            "principle_id": "book:operative:shift",
            "generation_stage": "base",
            "generation_stage_order": 1,
            "kind": "operative",
            "execution_verbs": ("shift",),
            "implementation_elements": (),
        },
        source_seed=source_seed,
        scope_label=scope,
        orientation=orientation,
        variant_index=variant_index,
    )
    descendant = candidate_generation.lineage_record(
        {
            "principle_id": "book:combination:09:shift+shift",
            "lineage_base_operative_id": "book:operative:shift",
            "generation_stage": "descendant",
            "generation_stage_order": 2,
        },
        source_seed=source_seed,
        scope_label=scope,
        orientation=orientation,
        variant_index=variant_index,
    )
    descendant["parent_base_lineage"] = dict(parent)
    descendant["parent_key"] = parent["parent_key"]
    return descendant


def _authorization(lineage, *, geometry_hash="geometry-1"):
    parent_key = lineage["parent_key"]
    return (
        {parent_key: geometry_hash},
        {
            parent_key: {
                "geometry_hash": geometry_hash,
                "program_hash": "parent-program-1",
                "base_review_fingerprint": _fingerprint(geometry_hash),
                "response_id": "resp-parent-review",
            },
        },
    )


def _real_certified_base(*, selection_eligible=True):
    lineage = candidate_generation.lineage_record(
        {
            "principle_id": "book:operative:shift",
            "generation_stage": "base",
            "generation_stage_order": 1,
            "kind": "operative",
            "execution_verbs": ("shift",),
            "implementation_elements": (),
        },
        source_seed="same-seed",
        scope_label="3/8",
        orientation="long_axis",
        variant_index=0,
    )
    geometry_hash = "geometry-1"
    program_hash = "parent-program-1"
    surface_hash = "surface-1"
    return SimpleNamespace(source=SimpleNamespace(metadata={
        "book_generation_lineage": lineage,
        "final_geometry_hash": geometry_hash,
        "final_program_hash": program_hash,
        "final_surface_payload_hash": surface_hash,
        "program_gate_result": {"hard_pass": bool(selection_eligible)},
        "program_review_authority": {
            "legal_archive_authority": True,
            "selection_eligible": bool(selection_eligible),
            "development_review_eligible": not selection_eligible,
        },
        "base_book_vlm_audit": {
            "response_id": "resp-real-parent",
            "review_stage": "book_base_operative",
            "reviewed_exact_post_book_geometry": True,
            "descendant_development_hard_pass": True,
            "geometry_hash": geometry_hash,
            "program_hash": program_hash,
            "base_review_fingerprint": _fingerprint(geometry_hash),
            "candidate_morphology": {
                "phenotype": "prismatic",
                "body_phenotype": "prismatic",
                "section_phenotype": "none",
            },
        },
        "authored_legal_projection_certificate": {
            "schema_version": (
                "arr.maas.authored_legal_projection_certificate.v1"
            ),
            "status": "verified",
            "hard_pass": True,
            "input_authored_program_hash": program_hash,
            "projected_surface_hash": geometry_hash,
            "projected_surface_payload_hash": surface_hash,
        },
        "legal_capacity_authority": {"legal_hard_pass": True},
        "parking_hard_gate": {"hard_pass": True},
    }))


def _authorize(lineage, registry, audits):
    helper = getattr(
        candidate_generation,
        "_authorize_descendant_lineage_for_materialization",
        None,
    )
    assert callable(helper), "candidate-level authorization helper is missing"
    return helper(lineage, registry, audits)


def _base_lineage(operative, *, source_seed="same-seed", variant_index=0):
    return candidate_generation.lineage_record(
        {
            "principle_id": f"book:operative:{operative}",
            "generation_stage": "base",
            "generation_stage_order": 1,
            "kind": "operative",
            "execution_verbs": (operative,),
            "implementation_elements": (),
        },
        source_seed=source_seed,
        scope_label="1/4",
        orientation="vertical",
        variant_index=variant_index,
    )


def test_descendant_schedule_enumerates_canonical_children_per_reviewed_base():
    principles = tuple(
        candidate_generation.build_book_language_registry()["principles"]
    )
    reviewed = tuple(
        _base_lineage(operative, variant_index=index)
        for index, operative in enumerate(
            ("lift", "carve", "bend", "shift", "branch")
        )
    )

    seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )
    scheduled = candidate_generation._canonical_descendant_tuple_schedule(
        principles,
        reviewed,
        seed=seed,
        seed_index=0,
        selected_principle_ids=None,
        descendant_probe_count=3,
        variant_count=2,
        schedule_cap=12,
        rotation_offset=0,
    )

    represented = {
        principle["lineage_base_operative_id"]
        for _index, principle, _variant, _operations, _parent in scheduled
    }
    assert len(scheduled) <= 12
    assert len(represented) >= 3
    assert represented <= {
        f"book:operative:{operative}"
        for operative in ("lift", "carve", "bend", "shift", "branch")
    }
    assert "book:operative:expand" not in represented
    assert all(
        principle["principle_id"]
        != principle["lineage_base_operative_id"]
        for _index, principle, _variant, _operations, _parent in scheduled
    )


def test_replenishment_expand_parent_enumerates_its_canonical_children():
    principles = tuple(
        candidate_generation.build_book_language_registry()["principles"]
    )

    seed = candidate_generation.VerbSequence(
        name="replenishment-seed",
        label="replenishment seed",
        calls=(),
        notes=(),
    )
    scheduled = candidate_generation._canonical_descendant_tuple_schedule(
        principles,
        (_base_lineage("expand", source_seed="replenishment-seed"),),
        seed=seed,
        seed_index=0,
        selected_principle_ids=None,
        descendant_probe_count=3,
        variant_count=2,
        schedule_cap=3,
        rotation_offset=1,
    )

    assert scheduled
    assert len(scheduled) <= 3
    assert {
        principle["lineage_base_operative_id"]
        for _index, principle, _variant, _operations, _parent in scheduled
    } == {"book:operative:expand"}


def test_descendant_tuple_schedule_honors_selected_child_before_compose():
    principles = tuple(
        candidate_generation.build_book_language_registry()["principles"]
    )
    seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )

    scheduled = candidate_generation._canonical_descendant_tuple_schedule(
        principles,
        (_base_lineage("shift"),),
        seed=seed,
        seed_index=0,
        selected_principle_ids=frozenset({
            "book:combination:19:shift+notch",
        }),
        descendant_probe_count=3,
        variant_count=2,
        schedule_cap=8,
        rotation_offset=0,
        selected_candidate_keys=frozenset({
            "0:book:combination:19:shift+notch:10",
        }),
    )

    assert scheduled
    assert {
        principle["principle_id"]
        for _index, principle, _variant, _operations, _parent in scheduled
    } == {"book:combination:19:shift+notch"}
    assert {
        variant
        for _index, _principle, variant, _operations, _parent in scheduled
    } == {10}


def test_descendant_tuple_schedule_treats_zero_cap_as_unlimited():
    principles = tuple(
        candidate_generation.build_book_language_registry()["principles"]
    )
    seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )

    scheduled = candidate_generation._canonical_descendant_tuple_schedule(
        principles,
        (_base_lineage("shift"),),
        seed=seed,
        seed_index=0,
        selected_principle_ids=None,
        descendant_probe_count=2,
        variant_count=2,
        schedule_cap=0,
        rotation_offset=0,
    )

    assert len(scheduled) == 4


def test_descendant_tuple_schedule_applies_one_total_cap():
    principles = tuple(
        candidate_generation.build_book_language_registry()["principles"]
    )
    seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )

    scheduled = candidate_generation._canonical_descendant_tuple_schedule(
        principles,
        tuple(
            _base_lineage(operative, variant_index=index)
            for index, operative in enumerate(("bend", "shift", "branch"))
        ),
        seed=seed,
        seed_index=0,
        selected_principle_ids=None,
        descendant_probe_count=3,
        variant_count=3,
        schedule_cap=5,
        rotation_offset=0,
    )

    assert len(scheduled) == 5
    assert len({
        parent["base_operative_id"]
        for _index, _principle, _variant, _operations, parent in scheduled
    }) == 3


def test_descendant_tuple_schedule_rotates_parent_start_across_cycles():
    principles = tuple(
        candidate_generation.build_book_language_registry()["principles"]
    )
    seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )
    parents = tuple(
        _base_lineage(operative, variant_index=index)
        for index, operative in enumerate(("lift", "carve", "bend", "shift"))
    )

    first_parent_by_cycle = []
    for cycle_offset in range(4):
        scheduled = candidate_generation._canonical_descendant_tuple_schedule(
            principles,
            parents,
            seed=seed,
            seed_index=0,
            selected_principle_ids=None,
            descendant_probe_count=2,
            variant_count=2,
            schedule_cap=1,
            rotation_offset=cycle_offset,
        )
        first_parent_by_cycle.append(
            scheduled[0][4]["base_operative_id"]
        )

    assert set(first_parent_by_cycle) == {
        "book:operative:lift",
        "book:operative:carve",
        "book:operative:bend",
        "book:operative:shift",
    }


def test_program_pool_callback_materializes_reviewed_expand_descendants(
    monkeypatch,
):
    site = box(0, 0, 20, 20)
    kernel_source = candidate_generation.compile_sequence_to_source_mass(
        site,
        candidate_generation.program_seed_sequences(
            "neighborhood_living"
        )[0],
    )
    assert kernel_source is not None
    parent = _real_certified_base(selection_eligible=False)
    parent.source.metadata["book_generation_lineage"] = (
        candidate_generation.lineage_record(
            {
                "principle_id": "book:operative:expand",
                "generation_stage": "base",
                "generation_stage_order": 1,
                "kind": "operative",
                "execution_verbs": ("expand",),
                "implementation_elements": (),
            },
            source_seed="same-seed",
            scope_label="1/16",
            orientation="diagonal",
            variant_index=9,
        )
    )
    valid = parent.source.metadata["book_generation_lineage"]
    canonical_parent_key = (
        candidate_generation.canonical_lineage_parent_key(valid)
    )
    registry = candidate_generation._reviewed_archived_base_registry([parent])
    audits = candidate_generation._reviewed_base_development_audits(
        [parent],
        registry,
    )
    reviewed_lineages = [valid]
    for index, operative in enumerate(("lift", "carve", "bend", "branch"), start=1):
        lineage = candidate_generation.lineage_record(
            {
                "principle_id": f"book:operative:{operative}",
                "generation_stage": "base",
                "generation_stage_order": 1,
                "kind": "operative",
                "execution_verbs": (operative,),
                "implementation_elements": (),
            },
            source_seed="same-seed",
            scope_label="1/4",
            orientation="vertical",
            variant_index=index,
        )
        parent_key = candidate_generation.canonical_lineage_parent_key(lineage)
        geometry_hash = f"geometry-{operative}"
        reviewed_lineages.append(lineage)
        registry[parent_key] = geometry_hash
        audits[parent_key] = {
            "geometry_hash": geometry_hash,
            "program_hash": f"program-{operative}",
            "base_review_fingerprint": _fingerprint(geometry_hash),
        }
    assert parent.source.metadata["program_review_authority"] == {
        "legal_archive_authority": True,
        "selection_eligible": False,
        "development_review_eligible": True,
    }
    assert parent.source.metadata["base_book_vlm_audit"][
        "candidate_morphology"
    ]["phenotype"] == "prismatic"
    seed = candidate_generation.VerbSequence(
        name="same-seed",
        label="same seed",
        calls=(),
        notes=("geometry_program_directive=reviewed_base_descendants",),
    )
    principle = {
        "principle_id": "book:combination:18:expand+shift",
        "lineage_base_operative_id": "book:operative:expand",
        "generation_stage": "descendant",
        "generation_stage_order": 2,
        "kind": "combination",
        "execution_verbs": ("expand", "shift"),
        "implementation_elements": (),
    }
    base_principle = {
        "principle_id": "book:operative:expand",
        "lineage_base_operative_id": "book:operative:expand",
        "generation_stage": "base",
        "generation_stage_order": 1,
        "kind": "operative",
        "execution_verbs": ("expand",),
        "implementation_elements": (),
    }
    unmatched_principle = {
        "principle_id": "book:combination:unreviewed-shift",
        "lineage_base_operative_id": "book:operative:shift",
        "generation_stage": "descendant",
        "generation_stage_order": 2,
        "kind": "combination",
        "execution_verbs": ("shift", "shift"),
        "implementation_elements": (),
    }
    composed = []
    materialized = []
    authorization_inputs = []
    persisted_sources = []
    persist_lineage = (
        candidate_generation._source_with_book_generation_lineage
    )

    def capture_persisted_source(
        source,
        generation_lineage,
        *,
        parent_audit=None,
    ):
        persisted = persist_lineage(
            source,
            generation_lineage,
            parent_audit=parent_audit,
        )
        persisted_sources.append(persisted)
        return persisted

    monkeypatch.setattr(
        candidate_generation,
        "_source_with_book_generation_lineage",
        capture_persisted_source,
    )

    authorize = (
        candidate_generation
        ._authorize_descendant_lineage_for_materialization
    )

    def record_authorization(lineage, registry, reviewed_base_audits):
        if str(lineage.get("stage") or "") == "descendant":
            authorization_inputs.append(dict(lineage))
        return authorize(lineage, registry, reviewed_base_audits)

    monkeypatch.setattr(
        candidate_generation,
        "_authorize_descendant_lineage_for_materialization",
        record_authorization,
    )

    monkeypatch.setattr(
        candidate_generation,
        "program_seed_variants",
        lambda seed, **_kwargs: (seed,),
    )
    monkeypatch.setattr(
        candidate_generation,
        "build_book_language_registry",
        lambda: {
            "principles": (
                unmatched_principle,
                base_principle,
                principle,
            ),
        },
    )
    monkeypatch.setattr(
        candidate_generation,
        "staged_principle_schedule",
        lambda _principles, _seed_index, *, count: (
            (0, unmatched_principle),
        ),
    )
    monkeypatch.setattr(
        candidate_generation,
        "_recursive_principle_schedule_limit",
        lambda **_kwargs: 0,
    )
    monkeypatch.setattr(
        candidate_generation,
        "book_variation_indices",
        lambda _count: (0, 5),
    )
    monkeypatch.setattr(
        candidate_generation,
        "diagnostic_anchor_sentence_variants",
        lambda *_args, **_kwargs: ((), ()),
    )
    monkeypatch.setattr(
        candidate_generation,
        "book_probe_scope",
        lambda _seed, _base, variant, **_kwargs: (
            ("3/8", "long_axis")
            if variant == 0
            else ("1/1", "short_axis")
        ),
    )
    monkeypatch.setattr(
        candidate_generation,
        "diagnostic_anchor_scope",
        lambda _seed, *, default_label, default_orientation: (
            default_label,
            default_orientation,
        ),
    )
    monkeypatch.setattr(
        candidate_generation,
        "diagnostic_anchor_schedule_active",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        candidate_generation,
        "diagnostic_anchor_spec",
        lambda _seed: SimpleNamespace(variant_index=5),
    )
    monkeypatch.setattr(
        candidate_generation,
        "diagnostic_anchor_principles",
        lambda _seed, _by_id, scheduled: scheduled,
    )

    def compose(seed, _operations, **kwargs):
        composed.append((kwargs["base_volume_label"], kwargs["orientation"]))
        return candidate_generation.VerbSequence(
            name=f"{seed.name}__composed",
            label=seed.label,
            calls=(),
            notes=(),
        )

    @dataclass(frozen=True)
    class FakeSource:
        metadata: dict

    monkeypatch.setattr(
        candidate_generation,
        "compose_program_with_book_operations",
        compose,
    )
    monkeypatch.setattr(
        candidate_generation,
        "build_capacity_alternative",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        candidate_generation,
        "capacity_alternative_for_host",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        candidate_generation,
        "capacity_contract_for_alternative",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        candidate_generation,
        "_candidate_floor_context",
        lambda *_args, **_kwargs: {
            "hard_pass": True,
            "height_m": 14.0,
            "floors": 4,
            "legal_sections": (box(0, 0, 20, 20),) * 4,
            "floor_top_heights_m": (3.5, 7.0, 10.5, 14.0),
            "authority": "test_exact",
            "legal_floor_field_hash": "legal-field",
        },
    )
    monkeypatch.setattr(
        candidate_generation,
        "compile_sequence_to_source_mass",
        lambda *_args, **_kwargs: FakeSource(metadata={}),
    )
    monkeypatch.setattr(
        candidate_generation,
        "recursive_plan_coverage_floor",
        lambda *_args, **_kwargs: 0.0,
    )

    def materialize(_source, sequence, **_kwargs):
        materialized.append(sequence.name)
        return kernel_source

    monkeypatch.setattr(
        candidate_generation,
        "_materialize_directed_geometry",
        materialize,
    )
    monkeypatch.setattr(
        candidate_generation,
        "_clean_mass_gate",
        lambda _source: (
            False,
            {"failure_reasons": ("test_stop_after_persistence",)},
        ),
    )
    monkeypatch.setattr(
        candidate_generation,
        "gate_descendants_by_base",
        lambda candidates, **_kwargs: (list(candidates), {"hard_pass": True}),
    )

    real_single_phase = candidate_generation._program_pool_single_phase

    def run_phase(*args, **kwargs):
        if kwargs.get("_generation_phase") == "base":
            return [parent], {
                "_runtime_directed_seeds": (seed,),
                "_runtime_parent_seeds": (seed,),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        return real_single_phase(*args, **kwargs)

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        run_phase,
    )

    _pool, counts = candidate_generation._program_pool(
        site,
        "neighborhood_living",
        14.0,
        4,
        diagnostic_book_probe_count=2,
        base_review_callback=lambda pool: (
            list(pool),
            {"status": "complete", "active": True},
        ),
    )

    assert composed == [("1/1", "short_axis")], (
        counts,
        authorization_inputs,
    )
    assert materialized
    assert all("same-seed__composed" in name for name in materialized)
    assert len(persisted_sources) == 1
    for source in persisted_sources:
        persisted = source.metadata["book_generation_lineage"]
        assert persisted["stage"] == "descendant"
        assert persisted["parent_base_lineage"] == valid
        assert persisted["parent_geometry_hash"] == "geometry-1"
        assert source.metadata["base_book_vlm_parent_audit"] == audits[
            canonical_parent_key
        ]
    assert {
        source.metadata["book_generation_lineage"][
            "descendant_operation"
        ]["variant_index"]
        for source in persisted_sources
    } == {5}
    assert len(authorization_inputs) == 1
    for lineage in authorization_inputs:
        assert lineage["stage"] == "descendant"
        assert lineage["principle_id"] == (
            "book:combination:18:expand+shift"
        )
        assert lineage["parent_base_lineage"] == valid
        assert lineage["parent_key"] == canonical_parent_key
    assert {
        candidate_generation.canonical_lineage_parent_key(
            lineage["parent_base_lineage"]
        )
        for lineage in authorization_inputs
    } == {canonical_parent_key}
    assert {
        (
            lineage["descendant_operation"]["scope_label"],
            lineage["descendant_operation"]["orientation"],
            lineage["descendant_operation"]["variant_index"],
            lineage["descendant_operation"]["stage"],
            lineage["descendant_operation"]["principle_id"],
        )
        for lineage in authorization_inputs
    } == {
        (
            "1/1",
            "short_axis",
            5,
            "descendant",
            "book:combination:18:expand+shift",
        ),
    }
    assert counts["descendant_parent_authorization"] == {
        "schema_version": "arr.maas.descendant_parent_authorization.v1",
        "input_count": 1,
        "authorized_count": 1,
        "filtered_count": 0,
        "filtered_by_reason": {},
    }


def test_candidate_authorization_seam_rejects_before_composition(monkeypatch):
    valid = _lineage()
    unknown = _lineage(scope="1/1", orientation="short_axis")
    registry, audits = _authorization(valid)
    composed = []

    monkeypatch.setattr(
        candidate_generation,
        "compose_program_with_book_operations",
        lambda seed, operations, **kwargs: composed.append(
            (seed, operations, kwargs)
        ) or "composed",
    )
    seam = getattr(
        candidate_generation,
        "_authorize_and_compose_descendant_candidate",
        None,
    )
    assert callable(seam), "candidate authorization/composition seam is missing"

    rejected_lineage, rejected_composed, rejected_reason = seam(
        SimpleNamespace(name="same-seed"),
        ("operation",),
        generation_lineage=unknown,
        generation_phase="descendant",
        registry=registry,
        reviewed_base_audits=audits,
        name_suffix="combination_09_shift+shift",
        base_volume_label="1/1",
        orientation="short_axis",
    )
    assert rejected_lineage is None
    assert rejected_composed is None
    assert rejected_reason == "unknown_parent"
    assert composed == []

    bound_lineage, valid_composed, valid_reason = seam(
        SimpleNamespace(name="same-seed"),
        ("operation",),
        generation_lineage=valid,
        generation_phase="descendant",
        registry=registry,
        reviewed_base_audits=audits,
        name_suffix="combination_09_shift+shift",
        base_volume_label="3/8",
        orientation="long_axis",
    )
    assert valid_reason == "authorized"
    assert bound_lineage["parent_geometry_hash"] == "geometry-1"
    assert valid_composed == "composed"
    assert len(composed) == 1


def test_valid_selectable_parent_passes_real_registry_audit_key_chain():
    parent = _real_certified_base(selection_eligible=True)
    parent_key = parent.source.metadata["book_generation_lineage"]["parent_key"]

    registry = candidate_generation._reviewed_archived_base_registry([parent])
    audits = candidate_generation._reviewed_base_development_audits(
        [parent],
        registry,
    )
    keys = candidate_generation._exact_canonical_reviewed_parent_keys(
        [parent],
        registry,
        audits,
    )

    assert registry == {parent_key: "geometry-1"}
    assert audits[parent_key]["program_hash"] == "parent-program-1"
    assert audits[parent_key]["base_review_fingerprint"] == _fingerprint(
        "geometry-1"
    )
    assert keys == {parent_key}


@pytest.mark.parametrize(
    ("registry", "audits", "expected_reason"),
    [
        ({}, {}, "unknown_parent"),
        ({"key": None}, {}, "conflicting_registry_hash"),
        ({"key": "geometry-1"}, {}, "missing_reviewed_audit"),
    ],
)
def test_descendant_authorization_fails_closed_without_exact_parent(
    registry,
    audits,
    expected_reason,
):
    lineage = _lineage()
    if "key" in registry:
        registry = {lineage["parent_key"]: registry["key"]}

    authorized, reason = _authorize(lineage, registry, audits)

    assert authorized is None
    assert reason == expected_reason


def test_descendant_authorization_rejects_fingerprint_mismatch():
    lineage = _lineage()
    registry, audits = _authorization(lineage)
    audits[lineage["parent_key"]]["base_review_fingerprint"] = "stale"

    authorized, reason = _authorize(lineage, registry, audits)

    assert authorized is None
    assert reason == "reviewed_audit_fingerprint_mismatch"


def test_descendant_authorization_rejects_persisted_parent_key_disagreement():
    lineage = _lineage()
    registry, audits = _authorization(lineage)
    lineage["parent_key"] = "stale-persisted-parent-key"

    authorized, reason = _authorize(lineage, registry, audits)

    assert authorized is None
    assert reason == "lineage_parent_key_disagreement"


def test_empty_canonical_parent_records_skip_descendant_phase(monkeypatch):
    descendant_called = False
    noncanonical_base = SimpleNamespace(
        source=SimpleNamespace(metadata={
            "book_generation_lineage": {
                "stage": "base",
                "parent_key": "legacy-parent-only",
            },
        }),
    )

    def single_phase(*_args, **kwargs):
        nonlocal descendant_called
        if kwargs.get("_generation_phase") == "base":
            return [noncanonical_base], {
                "_runtime_directed_seeds": ("legacy-seed",),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        descendant_called = True
        return [], {}

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        single_phase,
    )
    monkeypatch.setattr(
        candidate_generation,
        "_reviewed_archived_base_registry",
        lambda _reviewed: {"legacy-parent-only": "geometry-1"},
    )
    monkeypatch.setattr(
        candidate_generation,
        "_reviewed_base_development_audits",
        lambda _reviewed, _registry: {
            "legacy-parent-only": {
                "geometry_hash": "geometry-1",
                "program_hash": "program-1",
                "base_review_fingerprint": _fingerprint("geometry-1"),
            },
        },
    )

    _pool, counts = candidate_generation._program_pool(
        object(),
        "neighborhood_living",
        14.0,
        4,
        base_review_callback=lambda pool: (list(pool), {"status": "complete"}),
    )

    assert descendant_called is False
    evidence = counts["two_phase_base_vlm"][
        "descendant_parent_authorization"
    ]
    assert evidence["phase_skipped"] is True
    assert evidence["reason"] == "no_exact_canonical_reviewed_parent"


def test_empty_registry_skips_descendant_phase(monkeypatch):
    descendant_called = False
    canonical_lineage = _lineage()
    canonical_lineage["stage"] = "base"
    base = SimpleNamespace(source=SimpleNamespace(metadata={
        "book_generation_lineage": canonical_lineage,
        "final_program_hash": "parent-program-1",
    }))

    def single_phase(*_args, **kwargs):
        nonlocal descendant_called
        if kwargs.get("_generation_phase") == "base":
            return [base], {
                "_runtime_directed_seeds": ("same-seed",),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        descendant_called = True
        return [], {}

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        single_phase,
    )
    monkeypatch.setattr(
        candidate_generation,
        "_reviewed_archived_base_registry",
        lambda _reviewed: {},
    )

    pool, counts = candidate_generation._program_pool(
        object(),
        "neighborhood_living",
        14.0,
        4,
        base_review_callback=lambda pool: (list(pool), {"status": "complete"}),
    )

    assert pool == [base]
    assert descendant_called is False
    assert counts["two_phase_base_vlm"][
        "descendant_parent_authorization"
    ]["phase_skipped"] is True


def test_program_pool_handoff_ignores_forged_later_registry_authority(monkeypatch):
    valid = _real_certified_base(selection_eligible=True)
    valid_lineage = valid.source.metadata["book_generation_lineage"]
    valid_lineage["record_marker"] = "valid"
    forged = _real_certified_base(selection_eligible=True)
    forged_lineage = json.loads(json.dumps(valid_lineage))
    forged_lineage["record_marker"] = "forged"
    forged.source.metadata["book_generation_lineage"] = forged_lineage
    forged.source.metadata["parking_hard_gate"] = {"hard_pass": False}
    captured_lineages = []
    parent_seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )

    def single_phase(*_args, **kwargs):
        if kwargs.get("_generation_phase") == "base":
            return [valid, forged], {
                "_runtime_directed_seeds": (parent_seed,),
                "_runtime_parent_seeds": (parent_seed,),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        captured_lineages.extend(kwargs.get("_reviewed_base_lineages") or ())
        return [], {
            "legal_mass_archive": {"records": []},
            "phase_durations_seconds": {},
            "descendant_parent_authorization": {
                "schema_version": "arr.maas.descendant_parent_authorization.v1",
                "input_count": 0,
                "authorized_count": 0,
                "filtered_count": 0,
                "filtered_by_reason": {},
            },
        }

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        single_phase,
    )

    candidate_generation._program_pool(
        object(),
        "neighborhood_living",
        14.0,
        4,
        base_review_callback=lambda pool: (list(pool), {"status": "complete"}),
    )

    assert [lineage["record_marker"] for lineage in captured_lineages] == [
        "valid"
    ]


@pytest.mark.parametrize("parent_variant_indices", [(0,), (2,)])
def test_program_pool_two_phase_handoff_authorizes_only_matching_parent(
    monkeypatch,
    parent_variant_indices,
):
    parent = _real_certified_base(selection_eligible=True)
    parent_lineage = parent.source.metadata["book_generation_lineage"]
    handoff = []
    parent_seed = candidate_generation.VerbSequence(
        name="same-seed", label="same seed", calls=(), notes=()
    )

    def single_phase(*_args, **kwargs):
        if kwargs.get("_generation_phase") == "base":
            assert kwargs.get("parent_variant_indices") == parent_variant_indices
            return [parent], {
                "_runtime_directed_seeds": (parent_seed,),
                "_runtime_parent_seeds": (parent_seed,),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        assert kwargs.get("parent_variant_indices") == parent_variant_indices
        lineages = tuple(kwargs.get("_reviewed_base_lineages") or ())
        registry = kwargs.get("_reviewed_base_registry") or {}
        audits = kwargs.get("_reviewed_base_audits") or {}
        assert lineages == (parent_lineage,)
        matching = candidate_generation.lineage_record(
            {
                "principle_id": "book:combination:09:shift+shift",
                "lineage_base_operative_id": "book:operative:shift",
                "generation_stage": "descendant",
                "generation_stage_order": 2,
                "kind": "combination",
                "execution_verbs": ("shift", "shift"),
                "implementation_elements": (),
            },
            source_seed="same-seed",
            scope_label="1/1",
            orientation="short_axis",
            variant_index=5,
        )
        matching["parent_base_lineage"] = json.loads(json.dumps(lineages[0]))
        matching["parent_key"] = candidate_generation.canonical_lineage_parent_key(
            lineages[0]
        )
        authorized, authorized_reason = (
            candidate_generation._authorize_descendant_lineage_for_materialization(
                matching,
                registry,
                audits,
            )
        )
        unmatched = candidate_generation.lineage_record(
            {
                "principle_id": "book:combination:unreviewed-expand",
                "lineage_base_operative_id": "book:operative:expand",
                "generation_stage": "descendant",
                "generation_stage_order": 2,
                "kind": "combination",
                "execution_verbs": ("expand", "shift"),
                "implementation_elements": (),
            },
            source_seed="same-seed",
            scope_label="1/1",
            orientation="short_axis",
            variant_index=5,
        )
        rejected, rejected_reason = (
            candidate_generation._authorize_descendant_lineage_for_materialization(
                unmatched,
                registry,
                audits,
            )
        )
        handoff.append((authorized_reason, rejected_reason))
        assert authorized is not None
        assert rejected is None
        return [], {
            "legal_mass_archive": {"records": []},
            "phase_durations_seconds": {},
            "descendant_parent_authorization": {
                "schema_version": "arr.maas.descendant_parent_authorization.v1",
                "input_count": 1,
                "authorized_count": 1,
                "filtered_count": 0,
                "filtered_by_reason": {},
            },
        }

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        single_phase,
    )

    candidate_generation._program_pool(
        object(),
        "neighborhood_living",
        14.0,
        4,
        parent_variant_indices=parent_variant_indices,
        base_review_callback=lambda pool: (list(pool), {"status": "complete"}),
    )

    assert handoff == [("authorized", "lineage_parent_key_disagreement")]
