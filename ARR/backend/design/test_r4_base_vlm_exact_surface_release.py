from dataclasses import dataclass
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from design.maas.book_language.candidate_analysis import _Candidate
from design.maas.book_language.vlm_review import (
    _base_review_fingerprint,
    audit_book_base_stage_with_vlm,
)
from design.maas.program_massing import program_seed_sequences


@dataclass(frozen=True)
class _Source:
    metadata: dict


def _candidate(
    *,
    name: str,
    stage: str,
    final_hash: str,
    parent_hash: str = "",
    archived: bool = True,
    parent_fingerprint: str = "",
) -> _Candidate:
    lineage = {"stage": stage, "parent_key": "r4-parent"}
    if parent_hash:
        lineage["parent_geometry_hash"] = parent_hash
    if parent_fingerprint:
        lineage["parent_base_review_fingerprint"] = parent_fingerprint
    payload_hash = f"payload-{final_hash}"
    metadata = {
        "book_generation_lineage": lineage,
        "geometry_program_compilation": {
            "geometry_hash": f"preprojection-{name}",
        },
        "final_geometry_hash": final_hash,
        "final_surface_payload_hash": payload_hash,
        "program_gate_result": {
            "schema_version": "arr.maas.program_gate_result.v1",
            "hard_pass": False,
            "failed_gates": ("coherence",),
        },
        "program_review_authority": {
            "legal_archive_authority": archived,
            "hard_pass": False,
            "selection_eligible": False,
            "development_review_eligible": archived,
        },
        "authored_legal_projection_certificate": {
            "status": "verified",
            "hard_pass": True,
            "projected_surface_hash": final_hash,
            "projected_surface_payload_hash": payload_hash,
        },
    }
    return _Candidate(
        name,
        "base_operative" if stage == "base" else "combination",
        name,
        program_seed_sequences("neighborhood_living")[0],
        _Source(metadata),
        {"properties": {}},
        0.7,
    )


def _r4_failed_review_record(base: _Candidate) -> dict:
    audit = {
        "status": "fail",
        "hard_pass": False,
        "failures": ["gesture_clarity"],
        "response_id": "r4-small-vlm-response",
        "review_stage": "book_base_operative",
        "reviewed_exact_post_book_geometry": True,
        "critic_actions": ["clarify_primary_gesture"],
        "geometry_edits": [{"operator": "subtract"}],
    }
    return {
        "parent_key": "r4-parent",
        "base_review_fingerprint": _base_review_fingerprint(base),
        "hard_pass": False,
        "failures": ["gesture_clarity"],
        "response_id": audit["response_id"],
        "critic_actions": audit["critic_actions"],
        "geometry_edits": audit["geometry_edits"],
        "geometry_hash": base.source.metadata["final_geometry_hash"],
        "vlm_audit": audit,
    }


class R4BaseVlmExactSurfaceReleaseTests(TestCase):
    def test_r4_archived_exact_hash_and_actual_failed_review_release_typed_child(self):
        base = _candidate(
            name="r4-base", stage="base", final_hash="r4-final-surface"
        )
        child = _candidate(
            name="r4-child",
            stage="combination",
            final_hash="r4-child-surface",
            parent_hash="r4-final-surface",
        )
        record = _r4_failed_review_record(base)
        with (
            patch(
                "design.maas.book_language.vlm_review._book_base_parent_shortlist",
                return_value=([base], {"descendant_first_parent_resolution": True}),
            ),
            patch(
                "design.maas.book_language.vlm_review._audit_final_book_geometry_with_vlm",
                return_value=([], {"hard_pass_count": 0, "audit_records": [record]}),
            ),
        ):
            released, evidence = audit_book_base_stage_with_vlm(
                [base, child],
                building_type="neighborhood_living",
                output_dir=Path("unused"),
                visual_directive={},
            )

        self.assertEqual({item.principle_id for item in released}, {"r4-base", "r4-child"})
        released_child = next(item for item in released if item.principle_id == "r4-child")
        self.assertFalse(released_child.source.metadata["base_book_vlm_parent_audit"]["hard_pass"])
        self.assertEqual(
            released_child.source.metadata["base_book_vlm_parent_audit"]["response_id"],
            "r4-small-vlm-response",
        )
        self.assertEqual(evidence["released_descendant_count"], 1)

    def test_conflicting_exact_identity_or_missing_archive_refuses_release(self):
        base_a = _candidate(name="base-a", stage="base", final_hash="surface-a")
        base_b = _candidate(name="base-b", stage="base", final_hash="surface-b")
        conflict_child = _candidate(
            name="conflict-child",
            stage="combination",
            final_hash="child-conflict",
            parent_hash="surface-b",
            parent_fingerprint=_base_review_fingerprint(base_a),
        )
        missing_archive = _candidate(
            name="missing-archive",
            stage="base",
            final_hash="surface-missing",
            archived=False,
        )
        missing_child = _candidate(
            name="missing-child",
            stage="combination",
            final_hash="child-missing",
            parent_hash="surface-missing",
        )
        records = [_r4_failed_review_record(base_a), _r4_failed_review_record(base_b)]
        with (
            patch(
                "design.maas.book_language.vlm_review._book_base_parent_shortlist",
                return_value=([base_a, base_b], {}),
            ),
            patch(
                "design.maas.book_language.vlm_review._audit_final_book_geometry_with_vlm",
                return_value=([], {"hard_pass_count": 0, "audit_records": records}),
            ),
        ):
            released, evidence = audit_book_base_stage_with_vlm(
                [base_a, base_b, conflict_child, missing_archive, missing_child],
                building_type="neighborhood_living",
                output_dir=Path("unused"),
                visual_directive={},
            )

        self.assertNotIn("conflict-child", {item.principle_id for item in released})
        self.assertNotIn("missing-child", {item.principle_id for item in released})
        self.assertEqual(evidence["released_descendant_count"], 0)
