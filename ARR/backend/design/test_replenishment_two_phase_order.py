from pathlib import Path
import hashlib
import json
from types import SimpleNamespace

import pytest

from design.maas.book_language import candidate_generation
from design.maas.book_language import portfolio_replenishment as replenishment


def _run_cycle(*, runtime_live_vlm):
    return replenishment.run_replenishment_cycle(
        cycle_index=1,
        parent_variant_index=0,
        retained_selection_pool=[],
        excluded_parent_keys=set(),
        excluded_parent_fingerprints=set(),
        excluded_program_hashes=set(),
        generation_site=object(),
        building_type="neighborhood_living",
        height=14.0,
        floors=4,
        generation_context=object(),
        typed_graph_mutations=[],
        geometry_program_mutations=[],
        synthesis_requests=[],
        outcome_graph=None,
        recursive_only=True,
        target_count=5,
        exact_compile_limit=12,
        program_dimensional_context={},
        site_boundary_source="test",
        site_access_context={},
        site_access_geometry={},
        runtime_live_vlm=runtime_live_vlm,
        live_vlm_selection_required=False,
        base_capacity_contract={},
        trusted_legal_floor_field={},
        trusted_legal_floor_field_hash="legal-field-hash",
        trusted_clear_span_floor_plan={},
        capacity_site=object(),
        output_dir=Path("test-output"),
        program_slug="neighborhood",
        visual_directive={},
        downstream_context={},
        hard_gate_summary=lambda report, candidates: {
            "candidate_count": len(candidates),
            "report_present": report is not None,
        },
    )


def test_real_program_pool_reviews_base_before_descendant_generation(
    monkeypatch,
):
    events = []
    geometry_hash = "geometry-1"
    program_hash = "program-1"
    surface_hash = "surface-1"
    lineage = candidate_generation.lineage_record(
        {
            "principle_id": "book:operative:shift",
            "generation_stage": "base",
            "generation_stage_order": 1,
        },
        source_seed="ordered-parent-seed",
        scope_label="3/8",
        orientation="long_axis",
        variant_index=0,
    )
    parent_key = lineage["parent_key"]
    fingerprint = hashlib.sha256(json.dumps(
        {"geometry_hash": geometry_hash},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    base = SimpleNamespace(source=SimpleNamespace(metadata={
        "book_generation_lineage": lineage,
        "final_geometry_hash": geometry_hash,
        "final_program_hash": program_hash,
        "final_surface_payload_hash": surface_hash,
        "program_gate_result": {"hard_pass": True},
        "program_review_authority": {
            "legal_archive_authority": True,
            "selection_eligible": True,
            "development_review_eligible": False,
        },
        "base_book_vlm_audit": {
            "response_id": "resp-selectable-parent",
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
    parent_seed = candidate_generation.VerbSequence(
        name="ordered-parent-seed",
        label="ordered parent seed",
        calls=(),
        notes=(),
    )
    descendant = SimpleNamespace(name="descendant")

    def single_phase(*_args, **kwargs):
        phase = kwargs.get("_generation_phase")
        if phase == "base":
            events.append("base_generated")
            return [base], {
                "_runtime_directed_seeds": (parent_seed,),
                "_runtime_parent_seeds": (parent_seed,),
                "legal_mass_archive": {"records": []},
                "phase_durations_seconds": {},
            }
        assert phase == "descendant"
        assert kwargs["_directed_seeds_override"] == (parent_seed,)
        assert kwargs["_parent_seeds_override"] == (parent_seed,)
        assert kwargs["_reviewed_base_registry"] == {
            parent_key: geometry_hash
        }
        assert kwargs["_reviewed_base_audits"][parent_key][
            "base_review_fingerprint"
        ] == fingerprint
        events.append("descendant_generated")
        return [descendant], {
            "legal_mass_archive": {"records": []},
            "phase_durations_seconds": {},
        }

    def base_review(pool):
        assert pool == [base]
        events.append("base_reviewed")
        return list(pool), {
            "reviewed_parent_fingerprints": ["fingerprint-1"],
        }

    monkeypatch.setattr(
        candidate_generation,
        "_program_pool_single_phase",
        single_phase,
    )
    pool, counts = candidate_generation._program_pool(
        object(),
        "neighborhood_living",
        14.0,
        4,
        base_review_callback=base_review,
    )

    assert events == [
        "base_generated",
        "base_reviewed",
        "descendant_generated",
    ]
    assert pool == [base, descendant]
    assert counts["two_phase_base_vlm"]["active"] is True
    assert counts["two_phase_base_vlm"]["descendant_generation_count"] == 0


@pytest.mark.parametrize(
    "generation_counts",
    [
        {},
        {
            "two_phase_base_vlm": {
                "active": False,
                "base_vlm_gate": {"status": "complete"},
            },
        },
        {"two_phase_base_vlm": {"active": True}},
    ],
    ids=["absent", "inactive", "missing-gate"],
)
def test_live_replenishment_fails_closed_without_active_base_vlm_evidence(
    monkeypatch,
    generation_counts,
):
    calls = {"base_vlm": 0, "downstream": 0, "final_vlm": 0}

    monkeypatch.setattr(
        replenishment,
        "_program_pool",
        lambda *_args, **_kwargs: ([], generation_counts),
    )
    monkeypatch.setattr(
        replenishment,
        "audit_book_base_stage_with_vlm",
        lambda *_args, **_kwargs: calls.__setitem__(
            "base_vlm", calls["base_vlm"] + 1
        ),
    )
    monkeypatch.setattr(
        replenishment,
        "evaluate_accepted_sources_downstream",
        lambda *_args, **_kwargs: calls.__setitem__(
            "downstream", calls["downstream"] + 1
        ),
    )
    monkeypatch.setattr(
        replenishment,
        "run_final_vlm_cycle",
        lambda *_args, **_kwargs: calls.__setitem__(
            "final_vlm", calls["final_vlm"] + 1
        ),
    )

    with pytest.raises(
        ValueError,
        match="replenishment_two_phase_base_vlm_evidence_missing",
    ):
        _run_cycle(runtime_live_vlm=True)

    assert calls == {"base_vlm": 0, "downstream": 0, "final_vlm": 0}


def test_non_live_replenishment_accepts_absent_two_phase_evidence(
    monkeypatch,
):
    calls = {"base_vlm": 0, "downstream": 0, "final_vlm": 0}
    candidate = SimpleNamespace(
        source=SimpleNamespace(metadata={
            "shared_floor_contract": {"hard_pass": True},
        }),
    )

    def program_pool(*_args, **kwargs):
        assert kwargs["base_review_callback"] is None
        return [candidate], {}

    def downstream(candidates, **_kwargs):
        calls["downstream"] += 1
        assert candidates == [candidate]
        return {"rows": [{"combined_hard_pass": True}]}

    monkeypatch.setattr(replenishment, "_program_pool", program_pool)
    monkeypatch.setattr(
        replenishment,
        "_exclude_duplicate_program_hashes",
        lambda pool, _excluded: (list(pool), 0),
    )
    monkeypatch.setattr(
        replenishment,
        "_fingerprint",
        lambda _candidate: ("fake-non-live-candidate",),
    )
    monkeypatch.setattr(
        replenishment,
        "audit_book_base_stage_with_vlm",
        lambda *_args, **_kwargs: calls.__setitem__(
            "base_vlm", calls["base_vlm"] + 1
        ),
    )
    monkeypatch.setattr(
        replenishment,
        "evaluate_accepted_sources_downstream",
        downstream,
    )
    monkeypatch.setattr(
        replenishment,
        "_solid_morphology_metrics",
        lambda _candidate: {"degenerate_sheet_like": False},
    )
    monkeypatch.setattr(
        replenishment,
        "_bounded_visual_selection_pool",
        lambda pool: list(pool),
    )
    monkeypatch.setattr(
        replenishment,
        "run_final_vlm_cycle",
        lambda *_args, **_kwargs: calls.__setitem__(
            "final_vlm", calls["final_vlm"] + 1
        ),
    )

    result = _run_cycle(runtime_live_vlm=False)

    assert calls == {"base_vlm": 0, "downstream": 1, "final_vlm": 0}
    assert result.downstream_evaluation_pool == [candidate]
    assert result.selection_pool == [candidate]
    assert result.evidence["book_base_stage_vlm_gate"] == {
        "required": False,
        "status": "not_requested",
        "input_count": 1,
        "reviewed_parent_keys": [],
        "reviewed_parent_fingerprints": [],
    }


def test_replenishment_reviews_base_before_descendant_generation(monkeypatch):
    events = []
    base_gate = {
        "schema_version": "arr.maas.book_base_stage_vlm_gate.v2",
        "status": "complete",
        "reviewed_parent_keys": ["parent-1"],
        "reviewed_parent_fingerprints": ["fingerprint-1"],
    }
    candidate = SimpleNamespace(
        source=SimpleNamespace(metadata={
            "shared_floor_contract": {"hard_pass": True},
        }),
    )

    def fake_base_review(pool, **_kwargs):
        events.append("base_reviewed")
        return list(pool), dict(base_gate)

    def fake_program_pool(*_args, **kwargs):
        events.append("base_generated")
        callback = kwargs.get("base_review_callback")
        assert callable(callback), "replenishment omitted base_review_callback"
        reviewed, evidence = callback([candidate])
        assert reviewed == [candidate]
        assert evidence == base_gate
        events.append("descendant_generated")
        return [candidate], {
            "two_phase_base_vlm": {
                "active": True,
                "base_vlm_gate": evidence,
            },
        }

    monkeypatch.setattr(replenishment, "_program_pool", fake_program_pool)
    monkeypatch.setattr(
        replenishment,
        "audit_book_base_stage_with_vlm",
        fake_base_review,
    )
    monkeypatch.setattr(
        replenishment,
        "_exclude_duplicate_program_hashes",
        lambda pool, _excluded: (list(pool), 0),
    )
    monkeypatch.setattr(
        replenishment,
        "_fingerprint",
        lambda _candidate: ("fake-two-phase-candidate",),
    )
    monkeypatch.setattr(
        replenishment,
        "evaluate_accepted_sources_downstream",
        lambda candidates, **_kwargs: {
            "rows": [{
                "combined_hard_pass": True,
                "semantic_projection_hard_gate": {"hard_pass": True},
            } for _candidate in candidates],
        },
    )
    monkeypatch.setattr(
        replenishment,
        "_bind_final_visual_authority_for_review",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        replenishment,
        "_solid_morphology_metrics",
        lambda _candidate: {"degenerate_sheet_like": False},
    )
    monkeypatch.setattr(
        replenishment,
        "run_final_vlm_cycle",
        lambda review_pool, **_kwargs: SimpleNamespace(
            selection_pool=list(review_pool),
            repair_evidence={"repaired_candidate_count": 0},
            final_vlm_gate={"status": "complete"},
        ),
    )

    result = replenishment.run_replenishment_cycle(
        cycle_index=1,
        parent_variant_index=0,
        retained_selection_pool=[],
        excluded_parent_keys=set(),
        excluded_parent_fingerprints=set(),
        excluded_program_hashes=set(),
        generation_site=object(),
        building_type="neighborhood_living",
        height=14.0,
        floors=4,
        generation_context=object(),
        typed_graph_mutations=[],
        geometry_program_mutations=[],
        synthesis_requests=[],
        outcome_graph=None,
        recursive_only=True,
        target_count=5,
        exact_compile_limit=12,
        program_dimensional_context={},
        site_boundary_source="test",
        site_access_context={},
        site_access_geometry={},
        runtime_live_vlm=True,
        live_vlm_selection_required=False,
        base_capacity_contract={},
        trusted_legal_floor_field={},
        trusted_legal_floor_field_hash="legal-field-hash",
        trusted_clear_span_floor_plan={},
        capacity_site=object(),
        output_dir=Path("test-output"),
        program_slug="neighborhood",
        visual_directive={},
        downstream_context={},
        hard_gate_summary=lambda report, candidates: {
            "candidate_count": len(candidates),
            "report_present": report is not None,
        },
    )

    assert events == [
        "base_generated",
        "base_reviewed",
        "descendant_generated",
    ]
    assert result.evidence["book_base_stage_vlm_gate"] == base_gate
    assert result.reviewed_parent_keys == {"parent-1"}
    assert result.reviewed_parent_fingerprints == {"fingerprint-1"}
