from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from design.maas.book_language import candidate_generation


def _development_base(
    *,
    source_seed="development-parent-seed-1",
    geometry_hash="geometry-1",
    program_hash="program-1",
    surface_payload_hash="surface-1",
    response_id="resp-development-review",
    structural_hard_pass=True,
    statutory_hard_pass=True,
    parking_hard_pass=True,
    parking_compliance=None,
):
    lineage = candidate_generation.lineage_record(
        {
            "principle_id": "book:operative:shift",
            "generation_stage": "base",
            "generation_stage_order": 1,
        },
        source_seed=source_seed,
        scope_label="3/8",
        orientation="long_axis",
        variant_index=0,
    )
    fingerprint = hashlib.sha256(json.dumps(
        {"geometry_hash": geometry_hash},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    metadata = {
        "book_generation_lineage": lineage,
        "final_geometry_hash": geometry_hash,
        "final_program_hash": program_hash,
        "final_surface_payload_hash": surface_payload_hash,
        "program_gate_result": {"hard_pass": False},
        "program_review_authority": {
            "legal_archive_authority": True,
            "selection_eligible": False,
            "development_review_eligible": True,
        },
        "base_book_vlm_audit": {
            "response_id": response_id,
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
            "status": "verified" if structural_hard_pass else "rejected",
            "hard_pass": structural_hard_pass,
            "input_authored_program_hash": program_hash,
            "projected_surface_hash": geometry_hash,
            "projected_surface_payload_hash": surface_payload_hash,
        },
        "legal_capacity_authority": {
            "legal_hard_pass": statutory_hard_pass,
        },
        "shared_floor_contract": {"hard_pass": True},
        "parking_hard_gate": {"hard_pass": parking_hard_pass},
    }
    if parking_compliance is not None:
        metadata["parking_compliance"] = {
            "hard_pass": parking_compliance,
        }
    return SimpleNamespace(source=SimpleNamespace(metadata=metadata))


def test_development_reviewed_archived_base_releases_descendants(
    monkeypatch,
):
    events = []
    base = _development_base()
    parent_key = base.source.metadata["book_generation_lineage"]["parent_key"]
    parent_seed = candidate_generation.VerbSequence(
        name=base.source.metadata["book_generation_lineage"]["source_seed"],
        label="development parent seed",
        calls=(),
        notes=(),
    )
    descendant = SimpleNamespace(name="book-descendant")

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
        assert kwargs["_reviewed_base_registry"] == {
            parent_key: "geometry-1"
        }
        assert kwargs["_reviewed_base_audits"][parent_key][
            "response_id"
        ] == "resp-development-review"
        events.append("descendant_generated")
        return [descendant], {
            "legal_mass_archive": {"records": []},
            "phase_durations_seconds": {},
        }

    def base_review(pool):
        assert pool == [base]
        events.append("base_reviewed")
        return list(pool), {"status": "complete"}

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
    assert counts["two_phase_base_vlm"]["registered_unique_parent_count"] == 1
    assert base.source.metadata["program_review_authority"][
        "selection_eligible"
    ] is False
    assert base.source.metadata["program_gate_result"]["hard_pass"] is False


def test_unreviewed_development_base_is_not_registered():
    candidate = _development_base(response_id="")

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {}


def test_hash_conflicted_development_base_is_not_registered():
    first = _development_base(geometry_hash="geometry-1")
    second = _development_base(geometry_hash="geometry-2")

    parent_key = first.source.metadata["book_generation_lineage"]["parent_key"]
    assert candidate_generation._reviewed_archived_base_registry(
        [first, second]
    ) == {parent_key: None}


@pytest.mark.parametrize(
    "override",
    [
        {"structural_hard_pass": False},
        {"statutory_hard_pass": False},
    ],
    ids=["structural-invalid", "statutory-invalid"],
)
def test_invalid_authority_development_base_is_not_registered(override):
    candidate = _development_base(**override)

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {}


@pytest.mark.parametrize(
    ("audit_field", "copied_value"),
    [
        ("geometry_hash", "copied-geometry"),
        ("program_hash", "copied-program"),
        ("base_review_fingerprint", "copied-fingerprint"),
    ],
)
def test_copied_base_audit_identity_is_not_registered(
    audit_field,
    copied_value,
):
    candidate = _development_base()
    candidate.source.metadata["base_book_vlm_audit"][audit_field] = (
        copied_value
    )

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {}


@pytest.mark.parametrize(
    ("certificate_field", "copied_value"),
    [
        ("input_authored_program_hash", "copied-program"),
        ("projected_surface_hash", "copied-geometry"),
        ("projected_surface_payload_hash", "copied-surface"),
    ],
)
def test_stale_canonical_archive_binding_is_not_registered(
    certificate_field,
    copied_value,
):
    candidate = _development_base()
    candidate.source.metadata["authored_legal_projection_certificate"][
        certificate_field
    ] = copied_value

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {}


def test_explicit_parking_failure_is_not_registered():
    candidate = _development_base(parking_hard_pass=False)

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {}


def test_conflicting_parking_authorities_are_not_registered():
    candidate = _development_base(
        parking_hard_pass=True,
        parking_compliance=False,
    )

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {}


def test_absent_pre_downstream_parking_authority_is_accepted():
    candidate = _development_base()
    candidate.source.metadata.pop("parking_hard_gate")

    assert candidate_generation._reviewed_archived_base_registry(
        [candidate]
    ) == {
        candidate.source.metadata["book_generation_lineage"]["parent_key"]:
        "geometry-1"
    }


def test_development_base_is_parent_only_in_live_replenishment(monkeypatch):
    from pathlib import Path

    from design.maas.book_language import portfolio_replenishment

    development_base = _development_base()
    descendant = _development_base(source_seed="development-parent-seed-2")
    descendant.source.metadata["book_generation_lineage"]["stage"] = (
        "descendant"
    )
    descendant.source.metadata["program_gate_result"]["hard_pass"] = True
    descendant.source.metadata["program_review_authority"].update({
        "selection_eligible": True,
        "development_review_eligible": False,
    })
    seen = {"downstream": [], "final": []}

    monkeypatch.setattr(
        portfolio_replenishment,
        "_program_pool",
        lambda *_args, **_kwargs: (
            [development_base, descendant],
            {
                "two_phase_base_vlm": {
                    "active": True,
                    "base_vlm_gate": {"status": "complete"},
                },
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
        lambda candidate: (
            "fake-parent",
            str(
                (
                    candidate.source.metadata.get("book_generation_lineage")
                    or {}
                ).get("parent_key")
                or ""
            ),
        ),
    )

    def downstream(candidates, **_kwargs):
        seen["downstream"] = list(candidates)
        return {"rows": [{"combined_hard_pass": True} for _ in candidates]}

    monkeypatch.setattr(
        portfolio_replenishment,
        "evaluate_accepted_sources_downstream",
        downstream,
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_bind_final_visual_authority_for_review",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        portfolio_replenishment,
        "_solid_morphology_metrics",
        lambda _candidate: {"degenerate_sheet_like": False},
    )

    def final_cycle(review_pool, **_kwargs):
        seen["final"] = list(review_pool)
        return SimpleNamespace(
            selection_pool=list(review_pool),
            repair_evidence={},
            final_vlm_gate={},
        )

    monkeypatch.setattr(
        portfolio_replenishment,
        "run_final_vlm_cycle",
        final_cycle,
    )

    result = portfolio_replenishment.run_replenishment_cycle(
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
        hard_gate_summary=lambda _report, candidates: {
            "candidate_count": len(candidates),
        },
    )

    assert seen["downstream"] == [descendant]
    assert seen["final"] == [descendant]
    assert result.selection_pool == [descendant]
