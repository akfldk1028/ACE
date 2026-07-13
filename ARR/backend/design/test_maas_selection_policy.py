"""Regression tests for MAAS review selection helpers."""

from django.test import TestCase

from design.maas.selection import (
    FinalMetricCallbacks,
    FinalReviewRefinementCallbacks,
    FormalDiversityCallbacks,
    IslandQuotaCallbacks,
    RecoveryRefinementCallbacks,
    ReviewSetConstraintCallbacks,
    SelectionState,
    enforce_formal_diversity_replacements,
    enforce_initial_recovery_replacements,
    enforce_island_quota_replacements,
    final_metric_snapshot,
    final_structural_quotas_ok_after,
    final_mass_stage_parking_pass,
    refine_final_review_set,
    review_set_constraints_ok,
)
from design.maas.selection_policy import SelectionState as ShimSelectionState
from design.maas.selection.integer_projection import ProjectionDescriptor, solve_final_integer_projection
from design.maas.selection.visual_similarity import pairwise_visual_similarity


def _feature(
    variant_id: str,
    *,
    shape: str,
    family: str = "courtyard",
    language: str = "courtyard_atrium",
    parking_status: str = "needs_mechanical_parking_review",
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "variant_id": variant_id,
            "mass_shape": shape,
            "height": 8.4,
            "mass_volumes": [
                {"bottom_height": 0.0, "top_height": 2.8, "role": "base"},
                {"bottom_height": 2.8, "top_height": 5.6, "role": "body"},
                {"bottom_height": 5.6, "top_height": 8.4, "role": "top"},
            ],
            "source_signature": {
                "family": family,
                "role_pattern": f"{family}|main|void",
                "parameter_default_ratio": 0.1,
                "surface_count": 24,
                "volume_count": 4,
            },
            "research_basis": {
                "mass_language": language,
                "quota_group": "subtractive" if family == "courtyard" else "generic",
                "role_pattern": f"{family}|main|void",
                "topology_tags": [family],
                "volume_count": 4,
            },
            "parking_precheck": {
                "layout_candidate": {
                    "status": parking_status,
                    "mass_stage_parking": {"status": parking_status},
                }
            },
        },
    }


class MaasSelectionPolicyTest(TestCase):
    def test_pairwise_visual_similarity_detects_same_precedent_geometry(self):
        common = dict(
            cost=0.1,
            family="stepback_tower",
            language="stepped_tower",
            formal_principle="slender_podium_tower",
            role_pattern="podium|tower",
            island="additive",
            height_band="8.40",
            direct_llm=True,
            vlm_scored=True,
            weak_llm=False,
            reference_ids=("archdaily_888821",),
            concept_vector=(0.8, 0.8, 0.9, 0.2, 0.9, 0.8),
            visual_vector=(30.0, 3.0, 8.4, 1.4, 1.0, 0.5, 0.5),
        )
        left = ProjectionDescriptor(feature=_feature("a", shape="llm_a"), **common)
        right_values = {**common, "family": "sloped_roof", "formal_principle": "folded_section"}
        right = ProjectionDescriptor(feature=_feature("b", shape="llm_b"), **right_values)
        self.assertEqual(pairwise_visual_similarity(left, right), 1.0)

    def test_pairwise_visual_similarity_preserves_shifted_plan(self):
        base = dict(
            cost=0.1, family="split", language="split_bridge",
            formal_principle="split_bridge_connector", island="hybrid",
            height_band="8.40", direct_llm=True, vlm_scored=True, weak_llm=False,
            reference_ids=(), concept_vector=(),
        )
        left = ProjectionDescriptor(
            feature=_feature("left", shape="llm_left"), role_pattern="left_role",
            visual_vector=(30.0, 3.0, 8.4, 1.4, 1.0, 0.25, 0.5), **base,
        )
        right = ProjectionDescriptor(
            feature=_feature("right", shape="llm_right"), role_pattern="right_role",
            visual_vector=(30.0, 3.0, 8.4, 1.4, 1.0, 0.75, 0.5), **base,
        )
        self.assertLess(pairwise_visual_similarity(left, right), 1.0)

    def test_pairwise_visual_similarity_rejects_same_language_isometric_silhouette(self):
        base = dict(
            cost=0.1, family="bend", language="bend_ribbon",
            formal_principle="torqued_stack", role_pattern="plate0|plate1|plate2",
            island="hybrid", height_band="5.60", direct_llm=False,
            vlm_scored=False, weak_llm=False, reference_ids=(), concept_vector=(),
        )
        left = ProjectionDescriptor(
            feature=_feature("bend_a", shape="agent_bend_a"),
            visual_vector=(33.0, 3.0, 5.6, 1.39, 1.0, 0.47, 0.61, 0.73, 0.57, 0.51),
            **base,
        )
        right = ProjectionDescriptor(
            feature=_feature("bend_b", shape="agent_bend_b"),
            visual_vector=(33.0, 3.0, 5.6, 1.18, 1.0, 0.48, 0.62, 0.72, 0.58, 0.51),
            **base,
        )
        self.assertEqual(pairwise_visual_similarity(left, right), 1.0)

    def test_integer_projection_enforces_global_formal_and_island_constraints(self):
        descriptors = []
        islands = ["additive", "subtractive", "hybrid", "sectional"]
        for index in range(24):
            feature = _feature(f"v{index}", shape=f"llm_shape_{index}", family=f"family_{index % 16}")
            descriptors.append(ProjectionDescriptor(
                feature=feature,
                cost=float(index) / 100.0,
                family=f"family_{index % 16}",
                language=f"language_{index}",
                formal_principle=f"formal_{index % 5}",
                role_pattern=f"role_{index}",
                island=islands[index % 4],
                height_band="5.60" if index % 2 else "8.40",
                direct_llm=True,
                vlm_scored=True,
                weak_llm=False,
            ))

        selected, trace = solve_final_integer_projection(descriptors)

        self.assertEqual(trace["status"], "optimal")
        self.assertEqual(len(selected), 20)
    def _callbacks(self) -> FinalReviewRefinementCallbacks:
        return FinalReviewRefinementCallbacks(
            design_review_quality_key=lambda feature: (float(feature["properties"].get("height") or 0.0),),
            has_review_source_geometry=lambda feature: True,
            is_agent_authored_candidate=lambda feature: False,
            is_clean_layered_anchor=lambda feature: False,
            is_direct_openai_llm_candidate=lambda feature: True,
            is_llm_authored_candidate=lambda feature: True,
            is_plain_capacity_anchor=lambda feature: False,
            is_reviewable_architectural_mass=lambda feature: True,
            research_mass_language=lambda feature: feature["properties"]["research_basis"]["mass_language"],
            source_family=lambda feature: feature["properties"]["source_signature"]["family"],
            source_signature=lambda feature: feature["properties"]["source_signature"],
        )

    def test_selection_policy_shim_reexports_package_state(self):
        self.assertIs(ShimSelectionState, SelectionState)

    def test_refine_final_review_set_accepts_empty_selection(self):
        refined = refine_final_review_set(
            [],
            legal_candidate_pool=[],
            final_limit=20,
            preferred_operator=None,
            callbacks=self._callbacks(),
        )

        self.assertEqual(refined, [])

    def test_selection_state_rejects_duplicate_shape_replacement(self):
        state = SelectionState(source_family=lambda feature: feature["properties"]["source_signature"]["family"])
        first = _feature("maas_01", shape="shape_a")
        second = _feature("maas_02", shape="shape_b")
        duplicate = _feature("maas_03", shape="shape_a")
        state.append_seen(first)
        state.append_seen(second)

        replaced = state.replace_relaxed(
            1,
            duplicate,
            mass_stage_parking_pass=final_mass_stage_parking_pass,
            enforce_unique_shape=True,
        )

        self.assertFalse(replaced)
        self.assertEqual(state.result[1]["properties"]["variant_id"], "maas_02")

    def test_selection_state_rejects_parking_fail_replacement(self):
        state = SelectionState(source_family=lambda feature: feature["properties"]["source_signature"]["family"])
        first = _feature("maas_01", shape="shape_a")
        candidate = _feature("maas_02", shape="shape_b", parking_status="fail")
        state.append_seen(first)

        replaced = state.replace_relaxed(
            0,
            candidate,
            mass_stage_parking_pass=final_mass_stage_parking_pass,
            enforce_unique_shape=True,
        )

        self.assertFalse(replaced)
        self.assertEqual(state.result[0]["properties"]["variant_id"], "maas_01")

    def test_review_constraints_reject_language_crowding(self):
        callbacks = ReviewSetConstraintCallbacks(
            architectural_order_gate=lambda feature: (True, ()),
            is_plain_review_mass=lambda feature: False,
            research_mass_language=lambda feature: feature["properties"]["research_basis"]["mass_language"],
            source_family=lambda feature: feature["properties"]["source_signature"]["family"],
            visible_volume_count=lambda feature: len(feature["properties"]["mass_volumes"]),
        )
        items = [
            _feature("maas_01", shape="shape_a", family="family_a", language="same_language"),
            _feature("maas_02", shape="shape_b", family="family_b", language="same_language"),
            _feature("maas_03", shape="shape_c", family="family_c", language="same_language"),
        ]

        ok = review_set_constraints_ok(
            items,
            max_weak_llm_review_masses=1,
            max_stepback_dominant=2,
            max_plain_review_masses=1,
            max_same_source_family=4,
            max_language_repeat=2,
            stepback_dominant_families={"stepback_tower"},
            review_geometry_ok=lambda feature: True,
            callbacks=callbacks,
        )

        self.assertFalse(ok)

    def test_review_constraints_reject_source_family_crowding(self):
        callbacks = ReviewSetConstraintCallbacks(
            architectural_order_gate=lambda feature: (True, ()),
            is_plain_review_mass=lambda feature: False,
            research_mass_language=lambda feature: feature["properties"]["research_basis"]["mass_language"],
            source_family=lambda feature: feature["properties"]["source_signature"]["family"],
            visible_volume_count=lambda feature: len(feature["properties"]["mass_volumes"]),
        )
        items = [
            _feature("maas_01", shape="shape_a", family="same_family", language="language_a"),
            _feature("maas_02", shape="shape_b", family="same_family", language="language_b"),
            _feature("maas_03", shape="shape_c", family="same_family", language="language_c"),
        ]

        ok = review_set_constraints_ok(
            items,
            max_weak_llm_review_masses=1,
            max_stepback_dominant=2,
            max_plain_review_masses=1,
            max_same_source_family=2,
            max_language_repeat=2,
            stepback_dominant_families={"stepback_tower"},
            review_geometry_ok=lambda feature: True,
            callbacks=callbacks,
        )

        self.assertFalse(ok)

    def test_review_constraints_reject_weak_llm_over_limit(self):
        callbacks = ReviewSetConstraintCallbacks(
            architectural_order_gate=lambda feature: (True, ()),
            is_plain_review_mass=lambda feature: False,
            research_mass_language=lambda feature: feature["properties"]["research_basis"]["mass_language"],
            source_family=lambda feature: feature["properties"]["source_signature"]["family"],
            visible_volume_count=lambda feature: len(feature["properties"]["mass_volumes"]),
        )
        weak_a = _feature("maas_01", shape="shape_a", family="family_a", language="language_a")
        weak_b = _feature("maas_02", shape="shape_b", family="family_b", language="language_b")
        weak_a["properties"]["llm_candidate_quality"] = {"status": "reject_final_review"}
        weak_b["properties"]["llm_candidate_quality"] = {"status": "reject_final_review"}

        ok = review_set_constraints_ok(
            [weak_a, weak_b],
            max_weak_llm_review_masses=1,
            max_stepback_dominant=2,
            max_plain_review_masses=1,
            max_same_source_family=4,
            max_language_repeat=2,
            stepback_dominant_families={"stepback_tower"},
            review_geometry_ok=lambda feature: True,
            callbacks=callbacks,
        )

        self.assertFalse(ok)

    def test_final_metric_snapshot_counts_review_set_structure(self):
        items = []
        groups = ["additive", "subtractive", "hybrid", "sectional"]
        for index in range(16):
            feature = _feature(
                f"maas_{index:02d}",
                shape=f"shape_{index}",
                family=f"family_{index}",
                language=f"language_{index}",
            )
            props = feature["properties"]
            props["quota_group"] = groups[index % len(groups)]
            props["source_signature"]["volume_count"] = 4
            props["source_signature"]["parameter_default_ratio"] = 0.2
            props["research_basis"]["role_pattern"] = f"role_{index}"
            props["llm_authored"] = True
            items.append(feature)

        callbacks = FinalMetricCallbacks(
            final_family=lambda feature: feature["properties"]["source_signature"]["family"],
            final_language=lambda feature: feature["properties"]["research_basis"]["mass_language"],
            final_parameter_default_ratio=lambda feature: feature["properties"]["source_signature"]["parameter_default_ratio"],
            final_role_pattern=lambda feature: feature["properties"]["research_basis"]["role_pattern"],
            final_volume_count=lambda feature: feature["properties"]["source_signature"]["volume_count"],
            height_bucket=lambda feature: str(feature["properties"]["height"]),
            is_agent_authored_candidate=lambda feature: True,
            is_llm_authored_candidate=lambda feature: feature["properties"].get("llm_authored") is True,
            repair_retention=lambda feature, **kwargs: 0.7,
            research_quota_group=lambda feature: feature["properties"]["quota_group"],
        )

        metrics = final_metric_snapshot(items, callbacks=callbacks)

        self.assertEqual(metrics["unique_families"], 16)
        self.assertEqual(metrics["unique_languages"], 16)
        self.assertEqual(metrics["additive"], 4)
        self.assertEqual(metrics["sectional"], 4)

    def test_final_structural_quotas_reject_language_repeat(self):
        items = []
        groups = ["additive", "subtractive", "hybrid", "sectional"]
        for index in range(16):
            feature = _feature(
                f"maas_{index:02d}",
                shape=f"shape_{index}",
                family=f"family_{index}",
                language="crowded_language" if index < 3 else f"language_{index}",
            )
            props = feature["properties"]
            props["quota_group"] = groups[index % len(groups)]
            props["source_signature"]["volume_count"] = 4
            props["source_signature"]["parameter_default_ratio"] = 0.2
            props["research_basis"]["role_pattern"] = f"role_{index}"
            items.append(feature)
        candidate = _feature("maas_candidate", shape="shape_candidate", family="family_candidate", language="language_candidate")
        candidate["properties"]["quota_group"] = "additive"
        candidate["properties"]["source_signature"]["volume_count"] = 4
        candidate["properties"]["source_signature"]["parameter_default_ratio"] = 0.2
        candidate["properties"]["research_basis"]["role_pattern"] = "role_candidate"

        callbacks = FinalMetricCallbacks(
            final_family=lambda feature: feature["properties"]["source_signature"]["family"],
            final_language=lambda feature: feature["properties"]["research_basis"]["mass_language"],
            final_parameter_default_ratio=lambda feature: feature["properties"]["source_signature"]["parameter_default_ratio"],
            final_role_pattern=lambda feature: feature["properties"]["research_basis"]["role_pattern"],
            final_volume_count=lambda feature: feature["properties"]["source_signature"]["volume_count"],
            height_bucket=lambda feature: str(feature["properties"]["height"]),
            is_agent_authored_candidate=lambda feature: True,
            is_llm_authored_candidate=lambda feature: True,
            repair_retention=lambda feature, **kwargs: 0.7,
            research_quota_group=lambda feature: feature["properties"]["quota_group"],
        )

        ok = final_structural_quotas_ok_after(items, 5, candidate, callbacks=callbacks)

        self.assertFalse(ok)

    def test_island_refinement_replaces_to_satisfy_missing_group(self):
        result = [
            _feature("maas_01", shape="shape_a", family="generic_a", language="language_a"),
            _feature("maas_02", shape="shape_b", family="generic_b", language="language_b"),
        ]
        for feature in result:
            feature["properties"]["research_basis"]["quota_group"] = "generic"
        candidate = _feature("maas_03", shape="shape_c", family="offset", language="offset_pair")
        candidate["properties"]["research_basis"]["quota_group"] = "additive"
        selected = result + [candidate]

        callbacks = IslandQuotaCallbacks(
            design_synthesis_rank=lambda feature: 1,
            formal_principle=lambda feature: "stacked_shifted_platforms",
            has_review_source_geometry=lambda feature: True,
            is_direct_openai_llm_candidate=lambda feature: True,
            repair_retention=lambda feature, **kwargs: 0.8,
            research_diversity_descriptor=lambda feature: feature["properties"]["research_basis"],
            research_quota_group=lambda feature: feature["properties"]["research_basis"]["quota_group"],
            research_role_pattern=lambda feature: feature["properties"]["research_basis"]["role_pattern"],
            source_signature=lambda feature: feature["properties"]["source_signature"],
            visible_volume_count=lambda feature: feature["properties"]["source_signature"]["volume_count"],
        )

        def replace_result(index, replacement):
            result[index] = replacement
            return True

        enforce_island_quota_replacements(
            result=result,
            selected=selected,
            island_targets={"additive": 1},
            callbacks=callbacks,
            candidate_ok=lambda feature: True,
            is_plain_capacity_anchor=lambda feature: False,
            replace_result=replace_result,
            final_limit=20,
        )

        self.assertIn(candidate, result)

    def test_formal_refinement_replaces_over_repeated_principle(self):
        result = [
            _feature("maas_01", shape="shape_a", family="family_a", language="language_a"),
            _feature("maas_02", shape="shape_b", family="family_b", language="language_b"),
        ]
        for feature in result:
            feature["properties"]["architectural_ambition_evidence"] = {
                "formal_principle": "torqued_stack",
                "vertical_strategy": "stacked",
                "silhouette_strength": 0.4,
                "sectional_diagram_clarity": 0.4,
            }
            feature["properties"]["maas_score"] = 0.2
        candidate = _feature("maas_03", shape="shape_c", family="family_c", language="language_c")
        candidate["properties"]["architectural_ambition_evidence"] = {
            "formal_principle": "carved_atrium",
            "vertical_strategy": "void_carved",
            "silhouette_strength": 0.9,
            "sectional_diagram_clarity": 0.9,
        }
        candidate["properties"]["maas_score"] = 0.9
        selected = result + [candidate]

        callbacks = FormalDiversityCallbacks(
            architectural_ambition=lambda feature: feature["properties"]["architectural_ambition_evidence"],
            design_review_quality_key=lambda feature: (float(feature["properties"].get("maas_score") or 0.0),),
            formal_principle=lambda feature: feature["properties"]["architectural_ambition_evidence"]["formal_principle"],
            is_agent_authored_candidate=lambda feature: True,
            is_direct_openai_llm_candidate=lambda feature: True,
            stair_like_risk=lambda feature: "low",
            vertical_strategy=lambda feature: feature["properties"]["architectural_ambition_evidence"]["vertical_strategy"],
        )

        def replace_result(index, replacement):
            result[index] = replacement
            return True

        enforce_formal_diversity_replacements(
            result=result,
            selected=selected,
            max_same_formal_principle=1,
            max_same_vertical_strategy=1,
            callbacks=callbacks,
            candidate_ok=lambda feature: True,
            is_plain_capacity_anchor=lambda feature: False,
            replace_result=replace_result,
            final_limit=20,
        )

        self.assertIn(candidate, result)

    def test_initial_recovery_replaces_severe_repair_loss(self):
        result = [
            _feature("maas_01", shape="shape_a", family="family_a", language="language_a"),
            _feature("maas_02", shape="shape_b", family="family_b", language="language_b"),
            _feature("maas_03", shape="shape_c", family="family_c", language="language_c"),
        ]
        for feature in result:
            feature["properties"]["repair_delta"] = {"area_retention": 0.4}
            feature["properties"]["source_volume_repair_delta"] = {"area_retention": 0.4}
            feature["properties"]["architectural_ambition_evidence"] = {"formal_principle": "torqued_stack"}
        candidate = _feature("maas_04", shape="shape_d", family="family_d", language="language_d")
        candidate["properties"]["repair_delta"] = {"area_retention": 0.8}
        candidate["properties"]["source_volume_repair_delta"] = {"area_retention": 0.8}
        candidate["properties"]["architectural_ambition_evidence"] = {"formal_principle": "carved_atrium"}
        selected = result + [candidate]

        callbacks = RecoveryRefinementCallbacks(
            design_review_quality_key=lambda feature: (float(feature["properties"].get("height") or 0.0),),
            formal_principle=lambda feature: feature["properties"]["architectural_ambition_evidence"]["formal_principle"],
            has_review_source_geometry=lambda feature: True,
            is_plain_capacity_anchor=lambda feature: False,
            is_reviewable_architectural_mass=lambda feature: True,
            repair_retention=lambda feature, **kwargs: feature["properties"]["repair_delta"]["area_retention"],
        )

        def replace_result(index, replacement):
            result[index] = replacement
            return True

        enforce_initial_recovery_replacements(
            result=result,
            selected=selected,
            callbacks=callbacks,
            replace_result=replace_result,
            final_limit=20,
            target_formal_principles={"carved_atrium"},
        )

        self.assertIn(candidate, result)
