from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.book_language import portfolio_benchmark
from design.maas.book_language import portfolio_replenishment


def _certified_base(
    index: int,
    *,
    geometry_hash: str | None = None,
    source_seed: str | None = None,
    program_hash: str | None = None,
    selectable: bool = True,
    development: bool = False,
):
    operative = ("lift", "carve", "bend", "shift", "branch")[index % 5]
    geometry_hash = geometry_hash or f"geometry-{index}"
    program_hash = program_hash or f"program-{index}"
    surface_hash = f"surface-{index}"
    lineage = candidate_generation.lineage_record(
        {
            "principle_id": f"book:operative:{operative}",
            "generation_stage": "base",
            "generation_stage_order": 1,
        },
        source_seed=source_seed or f"parent-seed-{index}",
        scope_label="3/8",
        orientation="long_axis",
        variant_index=index,
    )
    fingerprint = hashlib.sha256(json.dumps(
        {"geometry_hash": geometry_hash},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return SimpleNamespace(source=SimpleNamespace(metadata={
        "book_generation_lineage": lineage,
        "final_geometry_hash": geometry_hash,
        "final_program_hash": program_hash,
        "final_surface_payload_hash": surface_hash,
        "program_gate_result": {"hard_pass": selectable},
        "program_review_authority": {
            "legal_archive_authority": True,
            "selection_eligible": selectable,
            "development_review_eligible": development,
        },
        "base_book_vlm_audit": {
            "response_id": f"response-{index}",
            "review_stage": "book_base_operative",
            "reviewed_exact_post_book_geometry": True,
            "descendant_development_hard_pass": True,
            "geometry_hash": geometry_hash,
            "program_hash": program_hash,
            "base_review_fingerprint": fingerprint,
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


def _parent_seed(index: int, *, name: str | None = None, marker: str = ""):
    source = candidate_generation.program_seed_sequences(
        "neighborhood_living"
    )[0]
    program = candidate_generation.universal_form_program_pages(
        (index % 8,)
    )[0]
    seed_name = name or f"parent-seed-{index}"
    return replace(
        source,
        name=seed_name,
        notes=tuple(source.notes) + (
            "geometry_program_payload=" + json.dumps(
                program.to_dict(),
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
            f"geometry_program_source_seed={seed_name}",
            f"test_seed_marker={marker or index}",
        ),
    )


def test_carried_initial_certified_parents_release_later_descendants_without_new_bases(
    monkeypatch,
):
    initial = [_certified_base(index) for index in range(5)]
    seeds = [_parent_seed(index) for index in range(5)]
    snapshot = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        initial,
        parent_seeds=seeds,
    )
    descendant = SimpleNamespace(name="later-descendant")
    phases = []

    real_single_phase = candidate_generation._program_pool_single_phase

    def single_phase(*args, **kwargs):
        phase = kwargs.get("_generation_phase")
        phases.append(phase)
        if phase == "base":
            return [], {
                "_runtime_directed_seeds": (),
                "_runtime_parent_seeds": (),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        assert len(kwargs["_reviewed_base_registry"]) == 5
        assert len(kwargs["_reviewed_base_audits"]) == 5
        assert len(kwargs["_reviewed_base_lineages"]) == 5
        assert {
            seed.name for seed in kwargs["_parent_seeds_override"]
        } == {seed.name for seed in seeds}
        return real_single_phase(*args, **kwargs)

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        single_phase,
    )
    monkeypatch.setattr(
        candidate_generation,
        "_candidate_floor_context",
        lambda *_args, **_kwargs: {
            "hard_pass": True,
            "height_m": 14.0,
            "floors": 4,
            "legal_sections": (box(0, 0, 20, 20),) * 4,
            "upper_legal_section": box(0, 0, 20, 20),
            "floor_top_heights_m": (3.5, 7.0, 10.5, 14.0),
            "authority": "test_exact",
            "legal_floor_field_hash": "legal-field",
        },
    )
    pool, counts = candidate_generation._program_pool(
        box(0, 0, 20, 20),
        "neighborhood_living",
        14.0,
        4,
        base_review_callback=lambda pool: (pool, {
            "reviewed_parent_keys": [],
            "reviewed_parent_fingerprints": [],
        }),
        reviewed_base_parent_carry=snapshot,
    )

    assert phases == ["base", "descendant"]
    assert all(candidate not in snapshot for candidate in pool)
    assert counts["two_phase_base_vlm"][
        "descendant_parent_authorization"
    ]["input_count"] > 0
    assert counts["materialization_invocation_count"] > 0, {
        key: value for key, value in counts.items()
        if key in {
            "evaluated", "compiled", "clean", "program_passed",
            "materialization_invocation_count",
            "materialization_failure_counts",
            "terminal_materialization_failures",
            "descendant_parent_authorization",
            "capacity_stage_counts",
        }
    }
    assert counts["two_phase_base_vlm"]["carried_parent_count"] == 5


def test_certified_parent_snapshot_is_immutable_deduped_and_cycle_stable():
    parent = _certified_base(1)
    seed = _parent_seed(1)
    original = deepcopy(parent.source.metadata)

    first = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        [parent, deepcopy(parent)],
        parent_seeds=[seed, deepcopy(seed)],
    )
    second = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        carried=[*first, *first],
    )
    first[0].candidate.source.metadata["transient_consumer_write"] = True

    assert len(first) == 1
    assert len(second) == 1
    assert "transient_consumer_write" not in second[0].candidate.source.metadata
    assert parent.source.metadata == original


def test_certified_parent_snapshot_revokes_hash_conflict():
    valid = _certified_base(2)
    conflict = deepcopy(valid)
    conflict.source.metadata["final_geometry_hash"] = "changed-geometry"
    conflict.source.metadata["base_book_vlm_audit"][
        "geometry_hash"
    ] = "changed-geometry"
    conflict.source.metadata["base_book_vlm_audit"][
        "base_review_fingerprint"
    ] = hashlib.sha256(json.dumps(
        {"geometry_hash": "changed-geometry"},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    conflict.source.metadata["authored_legal_projection_certificate"][
        "projected_surface_hash"
    ] = "changed-geometry"

    snapshot = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        [valid, conflict],
        parent_seeds=[_parent_seed(2)],
    )

    assert snapshot == ()


def test_certified_parent_snapshot_preserves_development_contract_and_vlm_requirement():
    development = _certified_base(
        3,
        selectable=False,
        development=True,
    )
    unreviewed = _certified_base(
        4,
        selectable=False,
        development=True,
    )
    unreviewed.source.metadata["base_book_vlm_audit"]["response_id"] = ""

    snapshot = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        [development, unreviewed],
        parent_seeds=[_parent_seed(3), _parent_seed(4)],
    )

    assert len(snapshot) == 1
    assert snapshot[0].candidate.source.metadata["book_generation_lineage"] == (
        development.source.metadata["book_generation_lineage"]
    )
    assert snapshot[0].candidate.source.metadata["program_review_authority"][
        "selection_eligible"
    ] is False


def test_replenishment_live_state_carries_initial_and_prior_cycle_parent_snapshots():
    parents = [_certified_base(index) for index in range(5)]
    snapshot = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        parents,
        parent_seeds=[_parent_seed(index) for index in range(5)],
    )
    state = portfolio_benchmark._initial_replenishment_live_state(
        [],
        reviewed_final_vlm_fingerprints=set(),
        certified_reviewed_base_parents=snapshot,
    )
    observed = []

    def boundary(cycle_function, **kwargs):
        assert cycle_function == "cycle-function"
        carried = kwargs["certified_reviewed_base_parents"]
        observed.append(len(carried))
        return SimpleNamespace(
            live_qd_reserve=[],
            reviewed_final_vlm_fingerprints=set(),
            certified_reviewed_base_parents=(
                *carried,
                deepcopy(carried[0]),
            ),
        )

    _cycle, next_state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        boundary,
        "cycle-function",
        state=state,
    )
    _cycle, final_state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        boundary,
        "cycle-function",
        state=next_state,
    )

    assert observed == [5, 5]
    assert len(final_state.certified_reviewed_base_parents) == 5


def test_certified_parent_snapshot_rejects_conflicting_same_name_seed_program_binding():
    left = _certified_base(10, source_seed="shared-seed")
    right = _certified_base(
        11,
        source_seed="shared-seed",
        program_hash="different-program",
    )

    snapshot = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        [left, right],
        parent_seeds=[
            _parent_seed(10, name="shared-seed", marker="left"),
            _parent_seed(11, name="shared-seed", marker="right"),
        ],
    )

    assert snapshot == ()


def test_fresh_runtime_seed_conflict_revokes_carried_parent_before_descendant_phase(
    monkeypatch,
):
    parent = _certified_base(12, source_seed="shared-runtime-seed")
    carried_seed = _parent_seed(
        12,
        name="shared-runtime-seed",
        marker="carried",
    )
    conflicting_fresh_seed = _parent_seed(
        13,
        name="shared-runtime-seed",
        marker="fresh-conflict",
    )
    snapshot = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        [parent],
        parent_seeds=[carried_seed],
    )
    descendant_called = False

    def single_phase(*_args, **kwargs):
        nonlocal descendant_called
        if kwargs.get("_generation_phase") == "base":
            return [], {
                "_runtime_directed_seeds": (conflicting_fresh_seed,),
                "_runtime_parent_seeds": (conflicting_fresh_seed,),
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
    pool, counts = candidate_generation._program_pool(
        box(0, 0, 20, 20),
        "neighborhood_living",
        14.0,
        4,
        base_review_callback=lambda base_pool: (base_pool, {}),
        reviewed_base_parent_carry=snapshot,
    )

    assert pool == []
    assert descendant_called is False
    assert counts["two_phase_base_vlm"][
        "descendant_parent_authorization"
    ]["reason"] == "no_exact_canonical_reviewed_parent"


def test_certified_parent_snapshot_applies_deterministic_64_parent_cap():
    parents = [_certified_base(index) for index in range(70)]
    seeds = [_parent_seed(index) for index in range(70)]

    forward = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        parents,
        parent_seeds=seeds,
    )
    reverse = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
        list(reversed(parents)),
        parent_seeds=list(reversed(seeds)),
    )

    assert len(forward) == 64
    assert tuple(record.parent_key for record in forward) == tuple(
        record.parent_key for record in reverse
    )


def test_benchmark_two_cycle_state_unions_initial_and_fresh_parents_without_selectable_carry(
    monkeypatch,
    tmp_path,
):
    initial_parent = _certified_base(20)
    fresh_parent = _certified_base(21, selectable=False, development=True)
    initial_snapshot = (
        portfolio_replenishment.certified_reviewed_base_parent_snapshot(
            [initial_parent],
            parent_seeds=[_parent_seed(20)],
        )
    )
    fresh_snapshot = (
        portfolio_replenishment.certified_reviewed_base_parent_snapshot(
            [fresh_parent],
            parent_seeds=[_parent_seed(21)],
        )
    )
    descendants = {
        cycle: SimpleNamespace(source=SimpleNamespace(metadata={
            "shared_floor_contract": {"hard_pass": True},
            "book_generation_lineage": {
                "stage": "descendant",
                "parent_key": initial_snapshot[0].parent_key,
            },
            "program_gate_result": {"hard_pass": True},
        }))
        for cycle in (1, 2)
    }
    observed_carry_keys = []
    reviewed_fresh_counts = []

    def fake_program_pool(*_args, **kwargs):
        cycle = int(kwargs["parent_variant_indices"][0])
        carried = tuple(kwargs["reviewed_base_parent_carry"])
        observed_carry_keys.append(tuple(record.parent_key for record in carried))
        fresh = [fresh_parent] if cycle == 1 else []
        reviewed, base_gate = kwargs["base_review_callback"](fresh)
        reviewed_fresh_counts.append(len(reviewed))
        records = portfolio_replenishment.certified_reviewed_base_parent_snapshot(
            reviewed,
            parent_seeds=[_parent_seed(21)] if reviewed else [],
            carried=carried,
        )
        return [descendants[cycle]], {
            "_runtime_certified_reviewed_base_parents": records,
            "two_phase_base_vlm": {
                "active": True,
                "base_vlm_gate": base_gate,
            },
        }

    monkeypatch.setattr(portfolio_replenishment, "_program_pool", fake_program_pool)
    monkeypatch.setattr(
        portfolio_replenishment,
        "audit_book_base_stage_with_vlm",
        lambda pool, **_kwargs: (
            list(pool),
            {
                "status": "complete",
                "reviewed_parent_keys": [
                    candidate.source.metadata["book_generation_lineage"]["parent_key"]
                    for candidate in pool
                ],
                "reviewed_parent_fingerprints": [
                    candidate.source.metadata["base_book_vlm_audit"][
                        "base_review_fingerprint"
                    ]
                    for candidate in pool
                ],
            },
        ),
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_exclude_duplicate_program_hashes",
        lambda pool, _excluded: (list(pool), 0),
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_fingerprint",
        lambda candidate: (id(candidate),),
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_merge_live_qd_reserve",
        lambda prior, current: [*prior, *current],
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_solid_morphology_metrics",
        lambda _candidate: {"degenerate_sheet_like": False},
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "run_final_vlm_cycle",
        lambda review_pool, **_kwargs: SimpleNamespace(
            selection_pool=list(review_pool),
            repair_evidence={},
            final_vlm_gate={"status": "complete"},
        ),
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_repair_final_vlm_submission_fingerprints",
        lambda _cycle: set(),
    )

    state = portfolio_benchmark._initial_replenishment_live_state(
        [],
        reviewed_final_vlm_fingerprints=set(),
        certified_reviewed_base_parents=initial_snapshot,
    )

    def cycle_kwargs(cycle):
        return {
            "cycle_index": cycle,
            "parent_variant_index": cycle,
            "retained_selection_pool": [],
            "excluded_parent_keys": set(),
            "excluded_parent_fingerprints": set(),
            "excluded_program_hashes": set(),
            "generation_site": box(0, 0, 20, 20),
            "building_type": "neighborhood_living",
            "height": 14.0,
            "floors": 4,
            "generation_context": None,
            "typed_graph_mutations": [],
            "geometry_program_mutations": [],
            "synthesis_requests": [],
            "outcome_graph": None,
            "recursive_only": True,
            "target_count": 5,
            "exact_compile_limit": 12,
            "program_dimensional_context": {},
            "site_boundary_source": "test",
            "site_access_context": {},
            "site_access_geometry": {},
            "runtime_live_vlm": True,
            "live_vlm_selection_required": False,
            "base_capacity_contract": {},
            "trusted_legal_floor_field": {},
            "trusted_legal_floor_field_hash": "legal-field",
            "trusted_clear_span_floor_plan": {},
            "capacity_site": box(0, 0, 20, 20),
            "output_dir": tmp_path,
            "program_slug": "neighborhood",
            "visual_directive": {},
            "downstream_context": {},
            "hard_gate_summary": lambda _report, candidates: {
                "candidate_count": len(candidates),
            },
        }

    cycle1, state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        lambda function, **kwargs: function(**kwargs),
        portfolio_replenishment.run_replenishment_cycle,
        state=state,
        **cycle_kwargs(1),
    )
    cycle2, state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        lambda function, **kwargs: function(**kwargs),
        portfolio_replenishment.run_replenishment_cycle,
        state=state,
        **cycle_kwargs(2),
    )

    assert observed_carry_keys == [
        (initial_snapshot[0].parent_key,),
        tuple(sorted((initial_snapshot[0].parent_key, fresh_snapshot[0].parent_key))),
    ]
    assert reviewed_fresh_counts == [1, 0]
    assert len(state.certified_reviewed_base_parents) == 2
    assert cycle1.selection_pool == [descendants[1]]
    assert cycle2.selection_pool == [descendants[2]]
    assert all(
        candidate is not initial_parent and candidate is not fresh_parent
        for candidate in (*cycle1.selection_pool, *cycle2.selection_pool)
    )
