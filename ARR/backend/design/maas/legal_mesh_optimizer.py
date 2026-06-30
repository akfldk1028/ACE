"""Legal MAAS variant generator for ARR mass GeoJSON.

Take one candidate mass, expand/mutate it with deterministic MAAS morphology
operators, then repair and rank the results by legal FAR/BCR utilization and
diversity. The hard rule is simple: never return a variant that fails the
available ARR legal constraints.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, box, mapping
from shapely.affinity import scale as shapely_scale, translate as shapely_translate
from shapely.ops import unary_union

from design.maas.diversity import (
    diversity_score,
    polygon_iou,
    sequence_distance,
    sequence_diversity_score,
    sequence_verbs,
    shape_signature,
)
from design.maas.design_quality import attach_design_quality_evidence
from design.maas.floor_groups import build_floor_groups
from design.maas.grammar import generate_grammar_variants, get_sequence_label
from design.maas.legal_envelope import (
    FloorPlateStack,
    build_floor_plate_stack,
    build_legal_envelope,
    failed_constraint_metrics,
)
from design.maas.morphology_operators import largest_polygon
from design.maas.parking_requirements import (
    apply_parking_requirement_to_props,
    load_parking_requirement_rules,
    resolve_candidate_parking_requirement,
)
from design.maas.parking_strategy import attach_parking_strategy
from design.maas.research_backends import d4descent_design_evidence
from design.maas.seed_library import generate_seed_variants, seed_library_metadata
from design.services.mass_evaluator import get_floor_height
from design.services.repair_operator import repair_design
from design.services.site_geometry import geojson_to_polygon, utm_to_wgs84, wgs84_to_utm


def _operator_family(operator: str) -> str:
    if operator.endswith("_layered"):
        operator = operator[:-8]
    if operator == "legal_layered_max":
        return "legal_layered"
    if operator.startswith("legal_buildable"):
        return "legal_buildable"
    if operator.startswith("bcr_fill"):
        return "bcr_fill"
    if operator.startswith("notch") or operator.startswith("court_open"):
        return "void_notch"
    if operator.startswith("slender_bar"):
        return "slender_bar"
    if operator.startswith("split_bridge"):
        return "split"
    if operator.startswith("branch_y"):
        return "branch"
    if operator.startswith("pinch_waist"):
        return "pinch"
    if operator.startswith("interlock_cross"):
        return "interlock"
    if operator.startswith("overlap_slabs"):
        return "overlap"
    if operator.startswith("parking_repair_diagonal_connector"):
        return "diagonal_connect"
    if operator.startswith("parking_repair_terrace_ribbon"):
        return "terrace_link"
    if operator.startswith("parking_repair_sloped_roof"):
        return "sloped_roof"
    if operator.startswith("parking_repair_split_bridge"):
        return "split"
    if operator.startswith("parking_repair_tapered_slab"):
        return "taper"
    if operator.startswith("parking_repair_single_bar"):
        return "slender_bar"
    if operator.startswith("parking_repair_grammar_split"):
        return "split"
    if operator.startswith("parking_repair_grammar_bar"):
        return "slender_bar"
    if operator.startswith("parking_repair_grammar_podium") or operator.startswith("parking_repair_grammar_sunlight"):
        return "stepback_tower"
    if operator.startswith("parking_repair_grammar_diagonal"):
        return "diagonal_connect"
    if operator.startswith("parking_repair_grammar_terrace") or operator.startswith("parking_repair_grammar_overlap_shift_terrace"):
        return "terrace_link"
    if operator.startswith("parking_repair_grammar_sloped"):
        return "sloped_roof"
    if operator.startswith("diagonal_connect"):
        return "diagonal_connect"
    if operator.startswith("terrace_link"):
        return "terrace_link"
    if operator.startswith("sloped_roof"):
        return "sloped_roof"
    if operator in {"courtyard_void"}:
        return "courtyard"
    if operator.startswith("tapered"):
        return "taper"
    if operator.startswith("grade_terrace"):
        return "grade"
    if operator in {"terrace_stepback", "shifted_tower", "lift_overlap_slabs"}:
        return "stepback_tower"
    if operator == "grammar_sunlight_multi_step":
        return "stepback_tower"
    if operator == "grammar_courtyard_lift_taper":
        return "courtyard"
    if operator == "grammar_split_lift_stepback":
        return "split"
    if operator == "grammar_bar_notch_grade":
        return "grade"
    if operator == "grammar_overlap_shift_terrace":
        return "overlap"
    if operator == "grammar_branch_pinch_taper":
        return "branch"
    if operator == "grammar_podium_tower_offset":
        return "stepback_tower"
    if operator == "grammar_cave_inset_puncture":
        return "void_notch"
    if operator == "grammar_interlock_step_taper":
        return "interlock"
    if operator == "grammar_diagonal_step_connector":
        return "diagonal_connect"
    if operator == "grammar_terrace_ribbon_stepback":
        return "terrace_link"
    if operator == "grammar_sloped_roof_envelope":
        return "sloped_roof"
    if operator.startswith("grammar_"):
        return operator
    if operator.startswith("inset"):
        return "inset"
    return operator


CONCEPT_ORDER = [
    "legal_layered",
    "void_notch",
    "courtyard",
    "slender_bar",
    "split",
    "branch",
    "pinch",
    "interlock",
    "overlap",
    "diagonal_connect",
    "terrace_link",
    "sloped_roof",
    "stepback_tower",
    "taper",
    "grade",
    "inset",
    "bcr_fill",
    "legal_buildable",
]

SECTION_CONCEPTS = {"stepback_tower", "taper", "grade", "diagonal_connect", "terrace_link", "sloped_roof"}
MIN_GRAMMAR_CONCEPTS = 3
MIN_SECTION_DESIGN_CONCEPTS = 4
SECTION_CONNECTOR_VERBS = {"diagonal_connect", "terrace_link", "sloped_roof_mass"}
SECTION_CONNECTOR_SHAPE_TOKENS = (
    "diagonal_connect",
    "terrace_link",
    "sloped_roof",
    "step_connector",
    "ribbon_stepback",
)
TYPOLOGY_FIRST_FAMILIES = [
    "legal_layered",
    "interlock",
    "overlap",
    "split",
    "courtyard",
    "void_notch",
    "branch",
    "pinch",
    "stepback_tower",
    "terrace_link",
    "diagonal_connect",
    "sloped_roof",
    "taper",
    "grade",
    "inset",
    "legal_buildable",
]

CONCEPT_LABELS = {
    "legal_layered": "법규엔벨로프",
    "legal_buildable": "최대건폐",
    "bcr_fill": "건폐확장",
    "void_notch": "코너/오픈코트",
    "courtyard": "중정형",
    "slender_bar": "바형",
    "split": "분절/브릿지",
    "branch": "브랜치형",
    "pinch": "핀치형",
    "interlock": "인터락",
    "overlap": "오버랩",
    "diagonal_connect": "사선연결",
    "terrace_link": "테라스연결",
    "sloped_roof": "사선지붕형",
    "stepback_tower": "포디움/타워",
    "taper": "테이퍼",
    "grade": "테라스",
    "inset": "인셋",
}


def _concept_label(operator: str) -> str:
    sequence_key = operator[:-8] if operator.endswith("_layered") else operator
    sequence_label = get_sequence_label(sequence_key)
    if sequence_label:
        return sequence_label
    return CONCEPT_LABELS.get(_operator_family(operator), _operator_family(operator))


def _is_section_connector(feature: dict[str, Any]) -> bool:
    props = feature.get("properties", {}) or {}
    mass_shape = str(props.get("mass_shape") or "")
    if any(token in mass_shape for token in SECTION_CONNECTOR_SHAPE_TOKENS):
        return True
    sequence = props.get("maas_verb_sequence")
    if not isinstance(sequence, list):
        model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
        sequence = model.get("verb_sequence")
    if not isinstance(sequence, list):
        return False
    return any(
        isinstance(call, dict) and call.get("verb") in SECTION_CONNECTOR_VERBS
        for call in sequence
    )


def _is_parking_repair_operator(operator: str) -> bool:
    return operator.startswith("parking_repair_")


def _is_typology_first_candidate(feature: dict[str, Any]) -> bool:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    operator = str(props.get("mass_shape") or "")
    if _is_parking_repair_operator(operator):
        return False
    return _operator_family(operator) in set(TYPOLOGY_FIRST_FAMILIES)


def _polygon_min_dimension(poly) -> float:
    try:
        minx, miny, maxx, maxy = poly.bounds
        return float(min(maxx - minx, maxy - miny))
    except Exception:
        return 0.0


def _upper_typology_is_viable(footprint_utm, upper_footprint_utm) -> bool:
    if upper_footprint_utm is None or upper_footprint_utm.is_empty:
        return False
    lower_area = float(getattr(footprint_utm, "area", 0.0) or 0.0)
    upper_area = float(getattr(upper_footprint_utm, "area", 0.0) or 0.0)
    if lower_area <= 0.0:
        return False
    if upper_area < max(20.0, lower_area * 0.25):
        return False
    if _polygon_min_dimension(upper_footprint_utm) < 3.0:
        return False
    return True


def _feature_plan_min_dimension(feature: dict[str, Any]) -> float:
    try:
        geom = wgs84_to_utm(geojson_to_polygon(feature.get("geometry")))
        return _polygon_min_dimension(geom)
    except Exception:
        return 0.0


def _feature_height_to_min_dimension(feature: dict[str, Any]) -> float:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    height = float(props.get("height") or 0.0)
    min_dim = _feature_plan_min_dimension(feature)
    if min_dim <= 0.0:
        return 999.0
    return height / min_dim


def _is_reviewable_architectural_mass(feature: dict[str, Any]) -> bool:
    """Gate the 20-card review sheet to real massing candidates.

    Parking-repair slivers and very thin towers are still useful diagnostic
    evidence, but they should not be presented as architectural mass options.
    """
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    operator = str(props.get("mass_shape") or "")
    if _is_parking_repair_operator(operator):
        return False
    precheck = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
    layout = precheck.get("layout_candidate") if isinstance(precheck.get("layout_candidate"), dict) else {}
    if layout.get("status") == "fail":
        return False
    if _feature_plan_min_dimension(feature) < 4.2:
        return False
    if _feature_height_to_min_dimension(feature) > 6.2:
        return False
    return True


def _is_plain_capacity_anchor(feature: dict[str, Any]) -> bool:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    family = _operator_family(str(props.get("mass_shape") or ""))
    return family in {"bcr_fill", "legal_buildable"}


def _is_grammar_candidate(feature: dict[str, Any]) -> bool:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    return str(props.get("mass_shape") or "").startswith("grammar_")


def _visible_volume_count(feature: dict[str, Any]) -> int:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    volumes = props.get("mass_volumes")
    if isinstance(volumes, list):
        return len(volumes)
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
    model_volumes = model.get("volumes")
    return len(model_volumes) if isinstance(model_volumes, list) else 0


def _design_synthesis_rank(feature: dict[str, Any]) -> int:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    materialized = props.get("section_profile_materialized")
    if isinstance(materialized, dict) and materialized.get("design_synthesis"):
        return 3
    if _is_section_connector(feature):
        return 2
    family = _operator_family(str(props.get("mass_shape") or ""))
    if family in SECTION_CONCEPTS:
        return 1
    return 0


def _design_review_quality_key(feature: dict[str, Any]) -> tuple[float, float, float, float, float, float, float, float]:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    return (
        1.0 if _is_grammar_candidate(feature) else 0.0,
        float(min(_visible_volume_count(feature), 6)) / 6.0,
        float(_design_synthesis_rank(feature)),
        -1.0 if _is_plain_capacity_anchor(feature) else 0.0,
        float(props.get("design_quality_score") or 0.0),
        float(props.get("diversity_score") or 0.0),
        float(props.get("maas_score") or 0.0),
        _feature_plan_min_dimension(feature),
    )


def _has_resolved_parking_requirement(feature: dict[str, Any]) -> bool:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    precheck = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
    required = precheck.get("required_count") if isinstance(precheck.get("required_count"), dict) else {}
    return isinstance(required.get("required_spaces"), int)


def _preserve_visible_section_connector(
    selected: list[dict[str, Any]],
    *,
    final_limit: int,
    preferred_operator: str | None = None,
) -> list[dict[str, Any]]:
    if preferred_operator or final_limit <= 1:
        return selected
    visible = selected[:final_limit]
    if any(_is_section_connector(feature) for feature in visible):
        return selected
    connector = next((feature for feature in selected if _is_section_connector(feature)), None)
    if connector is None:
        return selected
    has_parking_gate = any(_has_resolved_parking_requirement(feature) for feature in selected)
    if has_parking_gate and _parking_priority_key(connector) < _parking_priority_key(visible[-1]):
        return selected
    return visible[:-1] + [connector] + [
        feature for feature in selected[final_limit:]
        if feature is not connector
    ]


def _final_design_balanced_selection(
    selected: list[dict[str, Any]],
    *,
    final_limit: int,
    preferred_operator: str | None = None,
) -> list[dict[str, Any]]:
    """Keep the review set architectural, not just score/parking sorted.

    The user-facing 20-card evidence sheet is used for design review. A raw
    score sort tends to show many legal stepback variants and parking-repair
    shrink variants first, which hides the actual grammar families. Keep a
    compact parking signal, then reserve one representative for each spatial
    family before backfilling.
    """
    if preferred_operator or final_limit <= 1:
        return selected[:final_limit]

    result: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_shapes: set[str] = set()

    def add(feature: dict[str, Any], *, allow_duplicate_shape: bool = False) -> bool:
        marker = id(feature)
        if marker in seen_ids or len(result) >= final_limit:
            return False
        shape = str((feature.get("properties") or {}).get("mass_shape") or "")
        if shape in seen_shapes and not allow_duplicate_shape:
            return False
        result.append(feature)
        seen_ids.add(marker)
        if shape:
            seen_shapes.add(shape)
        return True

    def layout_status(feature: dict[str, Any]) -> str:
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        precheck = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
        layout = precheck.get("layout_candidate") if isinstance(precheck.get("layout_candidate"), dict) else {}
        return str(layout.get("status") or "")

    # The review sheet should start with architectural evidence, not six
    # mechanical high-FAR variants or low-FAR parking repairs. Keep one legal
    # max anchor, then one real typology representative per family.
    legal_anchor = next(
        (
            feature for feature in selected
            if str((feature.get("properties") or {}).get("mass_shape") or "") == "legal_layered_max"
        ),
        None,
    )
    if legal_anchor is not None:
        add(legal_anchor)

    by_family: dict[str, list[dict[str, Any]]] = {}
    for feature in selected:
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        family = _operator_family(str(props.get("mass_shape") or ""))
        by_family.setdefault(family, []).append(feature)

    for family in TYPOLOGY_FIRST_FAMILIES:
        if family in {"legal_buildable", "bcr_fill"}:
            continue
        options = sorted(
            [
                feature for feature in by_family.get(family, [])
                if _is_typology_first_candidate(feature)
                and _is_reviewable_architectural_mass(feature)
                and not _is_plain_capacity_anchor(feature)
            ],
            key=lambda feature: (
                1 if layout_status(feature) != "needs_mechanical_parking_review" else 0,
                *_design_review_quality_key(feature),
            ),
            reverse=True,
        )
        for feature in options:
            if add(feature):
                break

    grammar_candidates = [
        feature for feature in selected
        if str((feature.get("properties") or {}).get("mass_shape") or "").startswith("grammar_")
        and _is_typology_first_candidate(feature)
        and _is_reviewable_architectural_mass(feature)
    ]
    grammar_candidates.sort(
        key=lambda feature: (
            1 if _is_section_connector(feature) else 0,
            *_design_review_quality_key(feature),
        ),
        reverse=True,
    )
    for feature in grammar_candidates:
        add(feature)
        if len(result) >= final_limit:
            break

    reviewable_backfill = [
        feature for feature in selected
        if _is_reviewable_architectural_mass(feature)
        and not _is_parking_repair_operator(str((feature.get("properties") or {}).get("mass_shape") or ""))
        and not _is_plain_capacity_anchor(feature)
    ]
    reviewable_backfill.sort(key=_design_review_quality_key, reverse=True)
    for feature in reviewable_backfill:
        add(feature, allow_duplicate_shape=True)
        if len(result) >= final_limit:
            break

    # Capacity-only boxes remain valid calculation anchors, but they are a poor
    # design-review surface. Use them only if the legal pool cannot fill the
    # requested evidence sheet with reviewable architectural masses.
    if len(result) < final_limit:
        capacity_backfill = [
            feature for feature in selected
            if _is_reviewable_architectural_mass(feature)
            and not _is_parking_repair_operator(str((feature.get("properties") or {}).get("mass_shape") or ""))
        ]
        capacity_backfill.sort(key=_design_review_quality_key, reverse=True)
        for feature in capacity_backfill:
            add(feature, allow_duplicate_shape=True)
            if len(result) >= final_limit:
                break

    return result[:final_limit]


def _volume_profile(feature: dict[str, Any]) -> tuple[tuple[float, float, float], ...]:
    props = feature.get("properties", {}) or {}
    volumes = props.get("mass_volumes") or props.get("maas_model", {}).get("volumes") or []
    profile: list[tuple[float, float, float]] = []
    for volume in volumes:
        try:
            geom = wgs84_to_utm(geojson_to_polygon(volume.get("geometry")))
            profile.append((
                round(float(volume.get("bottom_height") or 0.0), 1),
                round(float(volume.get("top_height") or 0.0), 1),
                round(float(geom.area), 1),
            ))
        except Exception:
            continue
    if profile:
        return tuple(profile)
    try:
        geom = wgs84_to_utm(geojson_to_polygon(feature.get("geometry")))
        return ((0.0, round(float(props.get("height") or 0.0), 1), round(float(geom.area), 1)),)
    except Exception:
        return ()


def _shape_signature_3d(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties", {}) or {}
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
    floor_plates = props.get("floor_plates") or model.get("floor_plates") or []
    plate_areas = [
        round(float(plate.get("area") or plate.get("area_m2") or 0.0), 2)
        for plate in floor_plates
        if isinstance(plate, dict)
    ]
    return {
        "height_m": props.get("height"),
        "num_floors": props.get("num_floors"),
        "volume_count": len(_volume_profile(feature)),
        "volume_profile": [
            {"bottom_height": bottom, "top_height": top, "area_m2": area}
            for bottom, top, area in _volume_profile(feature)
        ],
        "floor_plate_count": len(plate_areas),
        "floor_plate_area_profile": plate_areas,
    }


def _diversity_class(feature: dict[str, Any]) -> str:
    props = feature.get("properties", {}) or {}
    footprint_diversity = float(props.get("diversity_score") or 0.0)
    signature = props.get("shape_signature_3d") if isinstance(props.get("shape_signature_3d"), dict) else {}
    volume_count = int(signature.get("volume_count") or 0)
    floor_plate_count = int(signature.get("floor_plate_count") or 0)
    if footprint_diversity >= 0.2:
        return "plan_diverse"
    if volume_count > 1 or floor_plate_count > 0:
        return "section_diverse"
    return "near_duplicate"


def _attach_3d_diversity(feature: dict[str, Any]) -> None:
    props = feature.setdefault("properties", {})
    signature = _shape_signature_3d(feature)
    props["shape_signature_3d"] = signature
    props["candidate_diversity"] = {
        "class": _diversity_class(feature),
        "footprint_diversity_score": props.get("diversity_score"),
        "source_iou": props.get("source_iou"),
        "shape_signature_3d": signature,
    }


def _attach_design_quality(feature: dict[str, Any], footprint_utm) -> None:
    attach_design_quality_evidence(
        feature,
        footprint_utm=footprint_utm,
        optimizer_backend=d4descent_design_evidence(),
    )


def _stack_has_meaningful_top(stack: FloorPlateStack) -> bool:
    if not stack.floor_plates:
        return False
    top_area = float(stack.floor_plates[-1].get("area") or 0.0)
    ground_area = float(stack.footprint.area or 0.0)
    return top_area >= max(8.0, ground_area * 0.08)


def _should_use_floor_plate_stack(operator: str, preferred_operator: str | None = None) -> bool:
    """Use the expensive legal stack only for genuinely vertical/sectional forms.

    Plan-shape operators such as notch, courtyard, bar, branch, pinch, interlock
    and overlap lose their architectural identity if every candidate is rebuilt
    as the same envelope-derived floor plate stack. Those should keep their
    repaired footprint and be checked by the normal legal repair/metric pass.
    """
    if operator == preferred_operator:
        return True
    if operator == "grammar_sunlight_multi_step":
        return True
    if operator.startswith("grammar_"):
        return False
    return _operator_family(operator) in {"legal_layered"}


def _capacity_score(props: dict[str, Any]) -> float:
    far = float(props.get("far_utilization") or 0.0)
    bcr = float(props.get("bcr_utilization") or 0.0)
    return far * 0.62 + bcr * 0.38


def _normalized_feature_vector(feature: dict[str, Any]) -> tuple[float, ...]:
    props = feature.get("properties", {}) or {}
    signature = props.get("shape_signature") if isinstance(props.get("shape_signature"), dict) else {}
    signature_3d = props.get("shape_signature_3d") if isinstance(props.get("shape_signature_3d"), dict) else {}
    return (
        float(props.get("bcr") or 0.0) / 100.0,
        float(props.get("far") or 0.0) / 300.0,
        float(props.get("height") or 0.0) / 60.0,
        float(signature.get("compactness") or 0.0) / 100.0,
        float(signature_3d.get("volume_count") or 0.0) / 6.0,
        float(signature_3d.get("floor_plate_count") or 0.0) / 20.0,
    )


def _feature_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    """MAAS-style alt distance: geometry, 3D metrics, and verb sequence."""
    try:
        geom_distance = 1.0 - polygon_iou(geojson_to_polygon(a["geometry"]), geojson_to_polygon(b["geometry"]))
    except Exception:
        geom_distance = 0.0
    av = _normalized_feature_vector(a)
    bv = _normalized_feature_vector(b)
    metric_distance = sum(abs(x - y) for x, y in zip(av, bv)) / max(1, len(av))
    seq_distance = sequence_distance(
        sequence_verbs((a.get("properties") or {}).get("maas_verb_sequence")),
        sequence_verbs((b.get("properties") or {}).get("maas_verb_sequence")),
    )
    concept_distance = 0.0 if _operator_family((a.get("properties") or {}).get("mass_shape", "")) == _operator_family((b.get("properties") or {}).get("mass_shape", "")) else 1.0
    return round(
        geom_distance * 0.30
        + metric_distance * 0.25
        + seq_distance * 0.35
        + concept_distance * 0.10,
        4,
    )


def _kmedoid_representatives(
    candidates: list[dict[str, Any]],
    *,
    k: int,
    anchors: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Pick diverse representatives using the clone/MAAS diversity-kmedoids pattern.

    The clone uses mesh complexity + convexity + verb Jaccard. ARR does not
    depend on STL meshes at runtime, so the same idea is applied to legal
    GeoJSON features: footprint IoU, normalized mass metrics, and MAAS verb
    sequence distance.
    """
    if k <= 0 or not candidates:
        return []
    anchors = anchors or []
    picked: list[dict[str, Any]] = []
    distance_cache: dict[tuple[int, int], float] = {}

    def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
        key = tuple(sorted((id(a), id(b))))
        if key not in distance_cache:
            distance_cache[key] = _feature_distance(a, b)
        return distance_cache[key]

    def min_distance_to_selection(feature: dict[str, Any]) -> float:
        selected = anchors + picked
        if not selected:
            return 1.0
        return min(distance(feature, item) for item in selected)

    first = max(
        candidates,
        key=lambda feature: (
            min_distance_to_selection(feature),
            _capacity_score(feature.get("properties", {}) or {}),
        ),
    )
    picked.append(first)

    while len(picked) < min(k, len(candidates)):
        remaining = [feature for feature in candidates if feature not in picked]
        if not remaining:
            break
        picked.append(max(
            remaining,
            key=lambda feature: (
                min_distance_to_selection(feature),
                _capacity_score(feature.get("properties", {}) or {}),
            ),
        ))

    return picked


def _maas_verb_sequence(operator: str) -> list[dict[str, Any]]:
    """Architectural-language tags adapted from the MAAS verb grammar repo."""
    base = [{"verb": "base", "params": {"proportion": "1/1"}}]
    op = operator[:-8] if operator.endswith("_layered") else operator
    recipes: dict[str, list[dict[str, Any]]] = {
        "legal_layered_max": [{"verb": "taper", "params": {"top_ratio": 0.72}}],
        "legal_buildable_max": [{"verb": "taper", "params": {"top_ratio": 0.72}}],
        "notch_north_west": [{"verb": "notch", "params": {"corner": "-x+y"}}],
        "notch_north_east": [{"verb": "notch", "params": {"corner": "+x+y"}}],
        "notch_south_west": [{"verb": "notch", "params": {"corner": "-x-y"}}],
        "notch_south_east": [{"verb": "notch", "params": {"corner": "+x-y"}}],
        "court_open_north": [{"verb": "cave", "params": {"face": "+y"}}],
        "court_open_south": [{"verb": "cave", "params": {"face": "-y"}}],
        "court_open_east": [{"verb": "cave", "params": {"face": "+x"}}],
        "court_open_west": [{"verb": "cave", "params": {"face": "-x"}}],
        "courtyard_void": [{"verb": "puncture", "params": {"axis": "z"}}],
        "split_bridge_x": [{"verb": "split", "params": {"axis": "x"}}],
        "split_bridge_y": [{"verb": "split", "params": {"axis": "y"}}],
        "branch_y_soft": [{"verb": "branch", "params": {"angle": 28.0}}],
        "branch_y_wide": [{"verb": "branch", "params": {"angle": 42.0}}],
        "pinch_waist_x": [{"verb": "pinch", "params": {"axis": "x"}}],
        "pinch_waist_y": [{"verb": "pinch", "params": {"axis": "y"}}],
        "interlock_cross_soft": [{"verb": "interlock", "params": {"cross_axis": "z"}}, {"verb": "rotate_part", "params": {"axis": "z", "angle": 28.0}}],
        "interlock_cross_diagonal": [{"verb": "interlock", "params": {"cross_axis": "z"}}, {"verb": "rotate_part", "params": {"axis": "z", "angle": -34.0}}],
        "overlap_slabs_x": [{"verb": "overlap", "params": {"offset_vec": [0.5, 0.2, 0.0]}}],
        "overlap_slabs_y": [{"verb": "overlap", "params": {"offset_vec": [0.2, 0.5, 0.0]}}],
        "terrace_stepback": [{"verb": "grade", "params": {"axis": "+z"}}, {"verb": "taper", "params": {"top_ratio": 0.68}}],
        "shifted_tower": [{"verb": "lift", "params": {"other": "6/8"}}, {"verb": "shift", "params": {"axis": "x"}}],
        "tapered_slab": [{"verb": "taper", "params": {"top_ratio": 0.58}}],
        "grade_terrace_north": [{"verb": "grade", "params": {"axis": "+y"}}],
        "lift_overlap_slabs": [{"verb": "overlap", "params": {"offset_vec": [0.4, 0.2, 0.0]}}, {"verb": "lift", "params": {"other": "6/8"}}],
        "diagonal_connect_step_x": [{"verb": "diagonal_connect", "params": {"axis": "x", "upper_ratio": 0.72, "distance_ratio": 0.12}}],
        "diagonal_connect_step_y": [{"verb": "diagonal_connect", "params": {"axis": "y", "upper_ratio": 0.72, "distance_ratio": 0.12}}],
        "terrace_link_north": [{"verb": "terrace_link", "params": {"side": "north", "upper_ratio": 0.84}}],
        "sloped_roof_mass": [{"verb": "sloped_roof_mass", "params": {"upper_ratio": 0.90, "x_ratio": 0.70, "y_ratio": 0.92}}],
        "parking_repair_single_bar": [
            {"verb": "compress", "params": {"axis": "y", "factor": 0.72}},
            {"verb": "taper", "params": {"top_ratio": 0.86}},
        ],
        "parking_repair_tapered_slab": [
            {"verb": "lift", "params": {"upper_ratio": 0.72, "lower_floor_fraction": 0.30}},
            {"verb": "taper", "params": {"x_ratio": 0.72, "y_ratio": 0.80}},
        ],
        "parking_repair_split_bridge": [
            {"verb": "split", "params": {"axis": "x", "gap_ratio": 0.18, "bridge_ratio": 0.20}},
            {"verb": "lift", "params": {"upper_ratio": 0.76, "lower_floor_fraction": 0.32}},
            {"verb": "taper", "params": {"x_ratio": 0.82, "y_ratio": 0.86}},
        ],
        "parking_repair_diagonal_connector": [
            {"verb": "lift", "params": {"upper_ratio": 0.78, "lower_floor_fraction": 0.24}},
            {"verb": "diagonal_connect", "params": {"axis": "x", "upper_ratio": 0.86, "distance_ratio": 0.12, "lower_floor_fraction": 0.24}},
            {"verb": "taper", "params": {"x_ratio": 0.86, "y_ratio": 0.92}},
        ],
        "parking_repair_terrace_ribbon": [
            {"verb": "lift", "params": {"upper_ratio": 0.82, "lower_floor_fraction": 0.22}},
            {"verb": "terrace_link", "params": {"side": "north", "upper_ratio": 0.88, "width_ratio": 0.62, "depth_ratio": 0.20, "lower_floor_fraction": 0.22}},
            {"verb": "shift", "params": {"axis": "y", "distance_ratio": -0.04}},
        ],
        "parking_repair_sloped_roof_mass": [
            {"verb": "sloped_roof_mass", "params": {"upper_ratio": 0.90, "x_ratio": 0.70, "y_ratio": 0.92, "lower_floor_fraction": 0.28}},
            {"verb": "taper", "params": {"x_ratio": 0.88, "y_ratio": 0.94}},
        ],
    }
    if op.startswith("slender_bar"):
        return base + [{"verb": "compress", "params": {"axis": "x" if op.endswith(("east", "west")) else "y", "factor": 0.54}}]
    if op.startswith("bcr_fill"):
        return base + [{"verb": "expand", "params": {"face": "+x"}}, {"verb": "expand", "params": {"face": "+y"}}]
    if op.startswith("inset"):
        return base + [{"verb": "compress", "params": {"axis": "x", "factor": 0.92}}, {"verb": "compress", "params": {"axis": "y", "factor": 0.92}}]
    return base + recipes.get(op, [{"verb": op, "params": {}}])


def _compact_visual_volumes(floor_plates: list[dict[str, Any]], operator: str) -> list[dict[str, Any]]:
    """Build the MAAS volume representation from legal floor plates.

    The volume geometry is not a separate render-only artifact. It is the
    user-facing MAAS mass, and it is derived from floor plates that have already
    been clipped by the legal envelope. Using each band's top plate keeps the
    full volume inside the same legal envelope.
    """
    if not floor_plates:
        return []
    n = len(floor_plates)
    family = _operator_family(operator)
    areas = [float(plate.get("area") or 0.0) for plate in floor_plates]
    max_area = max(areas) if areas else 0.0
    min_area = min(areas) if areas else 0.0
    has_layered_envelope_steps = (
        family == "legal_layered"
        and n >= 3
        and max_area > 0.0
        and (max_area - min_area) / max_area >= 0.08
    )
    wants_stepped_display = (
        has_layered_envelope_steps
        or "step" in operator
        or "terrace" in operator
        or "grade" in operator
        or "diagonal_connect" in operator
        or "sloped_roof" in operator
        or family in {"stepback_tower", "grade"}
    )
    if has_layered_envelope_steps:
        cuts = [(index, index) for index in range(n)]
    elif wants_stepped_display and n >= 4:
        raw_cuts = [
            (0, max(0, n // 4 - 1)),
            (max(0, n // 4), max(0, n // 2 - 1)),
            (max(0, n // 2), max(0, (n * 3) // 4 - 1)),
            (max(0, (n * 3) // 4), n - 1),
        ]
        cuts = []
        for start, end in raw_cuts:
            if start <= end and (not cuts or cuts[-1] != (start, end)):
                cuts.append((start, end))
    elif n <= 2:
        cuts = [(0, n - 1)]
    elif family in {"legal_layered", "stepback_tower", "taper", "grade"}:
        cuts = [(0, max(0, n // 3)), (max(0, n // 3 + 1), n - 1)]
    else:
        cuts = [(0, max(0, n // 2)), (max(0, n // 2 + 1), n - 1)]

    volumes: list[dict[str, Any]] = []
    previous_top = 0.0
    for band_index, (start, end) in enumerate(cuts):
        if start > end or end >= n:
            continue
        top_plate = floor_plates[end]
        top_height = float(top_plate.get("top_height") or 0.0)
        if top_height <= previous_top:
            continue
        volumes.append({
            "band": band_index,
            "bottom_height": round(previous_top, 2),
            "top_height": round(top_height, 2),
            "geometry": top_plate.get("geometry"),
            "role": "morphology_volume",
        })
        previous_top = top_height
    return volumes


def _maas_model(
    *,
    operator: str,
    floor_plates: list[dict[str, Any]],
    props: dict[str, Any],
    site_area_m2: float,
) -> dict[str, Any]:
    """Single integrated object for agents/frontend: morphology + legal audit."""
    return {
        "algorithm": "maas_legal_envelope",
        "operator": operator,
        "verb_sequence": _maas_verb_sequence(operator),
        "volumes": _compact_visual_volumes(floor_plates, operator),
        "floor_plates": floor_plates,
        "floor_groups": build_floor_groups(
            floor_plates,
            site_area_m2=site_area_m2,
            building_type=str(props.get("building_type") or ""),
        ),
        "legal_metrics": {
            "far": props.get("far"),
            "bcr": props.get("bcr"),
            "height": props.get("height"),
            "num_floors": props.get("num_floors"),
            "footprint_area": props.get("footprint_area"),
            "floor_area": props.get("floor_area"),
            "min_setback": props.get("min_setback"),
            "open_pct": props.get("open_pct"),
        },
    }


def _section_profile_from_sequence(
    *,
    operator: str,
    sequence: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    props: dict[str, Any],
) -> dict[str, Any] | None:
    """Expose section-design intent separately from legal volume accounting.

    FAR/BCR and legality still use volumes/floor plates. This profile is the
    canonical design/raster-render hint derived from the MAAS verb sequence, so
    diagonal/terrace/sloped candidates do not collapse visually into identical
    stacked boxes.
    """
    calls = [call for call in sequence or [] if isinstance(call, dict)]
    for call in calls:
        verb = str(call.get("verb") or "")
        params = call.get("params") if isinstance(call.get("params"), dict) else {}
        if verb == "diagonal_connect":
            return {
                "kind": "diagonal_connector",
                "source": "maas_verb_sequence",
                "operator": operator,
                "axis": params.get("axis", "x"),
                "upper_ratio": float(params.get("upper_ratio", 0.72)),
                "distance_ratio": float(params.get("distance_ratio", 0.10)),
                "lower_floor_fraction": float(params.get("lower_floor_fraction", props.get("step_floor", 0.40) or 0.40)),
                "render_hint": "draw_inclined_connector_between_lower_and_upper_masses",
            }
        if verb == "terrace_link":
            return {
                "kind": "terrace_ribbon",
                "source": "maas_verb_sequence",
                "operator": operator,
                "side": params.get("side", "north"),
                "upper_ratio": float(params.get("upper_ratio", 0.84)),
                "width_ratio": float(params.get("width_ratio", 0.62)),
                "depth_ratio": float(params.get("depth_ratio", 0.20)),
                "render_hint": "draw_continuous_terrace_bands_not_isolated_boxes",
            }
        if verb == "sloped_roof_mass":
            return {
                "kind": "sloped_roof",
                "source": "maas_verb_sequence",
                "operator": operator,
                "upper_ratio": float(params.get("upper_ratio", 0.90)),
                "x_ratio": float(params.get("x_ratio", 0.70)),
                "y_ratio": float(params.get("y_ratio", 0.92)),
                "render_hint": "draw_sloped_envelope_plane_over_mass",
            }
    family = _operator_family(operator)
    if family in {"diagonal_connect", "terrace_link", "sloped_roof"}:
        profile_kind = {
            "diagonal_connect": "diagonal_connector",
            "terrace_link": "terrace_ribbon",
            "sloped_roof": "sloped_roof",
        }[family]
        return {
            "kind": profile_kind,
            "source": "operator_family",
            "operator": operator,
            "render_hint": "derive_section_profile_from_operator_family",
        }
    return None


def _attach_section_profile(feature: dict[str, Any]) -> None:
    props = feature.setdefault("properties", {})
    sequence = props.get("maas_verb_sequence")
    profile = _section_profile_from_sequence(
        operator=str(props.get("mass_shape") or ""),
        sequence=sequence,
        props=props,
    )
    if profile is None:
        return
    props["section_profile"] = profile
    model = props.get("maas_model")
    if isinstance(model, dict):
        model["section_profile"] = profile


def _largest_polygon_or_none(geometry) -> Any | None:
    if geometry is None or geometry.is_empty:
        return None
    if geometry.geom_type == "Polygon":
        return geometry if geometry.area >= 1.0 else None
    if geometry.geom_type == "MultiPolygon":
        try:
            poly = largest_polygon(geometry)
            return poly if poly.area >= 1.0 else None
        except Exception:
            return None
    polygons = [
        item for item in getattr(geometry, "geoms", [])
        if getattr(item, "geom_type", None) == "Polygon" and item.area >= 1.0
    ]
    if not polygons:
        return None
    return max(polygons, key=lambda item: item.area)


def _section_materialized_polygon(base_utm, *, profile: dict[str, Any], progress: float, bounds: tuple[float, float, float, float]):
    minx, miny, maxx, maxy = bounds
    span_x = maxx - minx
    span_y = maxy - miny
    kind = str(profile.get("kind") or "")

    if kind == "sloped_roof":
        x_ratio = max(0.42, 1.0 - (1.0 - float(profile.get("x_ratio") or 0.70)) * progress)
        y_ratio = max(0.58, 1.0 - (1.0 - float(profile.get("y_ratio") or 0.92)) * progress)
        shifted = shapely_translate(
            shapely_scale(base_utm, xfact=x_ratio, yfact=y_ratio, origin="centroid"),
            yoff=-span_y * 0.045 * progress,
        )
        return shifted.intersection(base_utm)

    if kind == "terrace_ribbon":
        side = str(profile.get("side") or "north")
        y_shift = -span_y * 0.085 * progress if side != "south" else span_y * 0.085 * progress
        x_shift = span_x * 0.025 * progress
        shaped = shapely_translate(
            shapely_scale(base_utm, xfact=max(0.78, 1.0 - 0.06 * progress), yfact=1.0, origin="centroid"),
            xoff=x_shift,
            yoff=y_shift,
        )
        return shaped.intersection(base_utm)

    if kind in {"diagonal_connector", "diagonal_connect"}:
        axis = str(profile.get("axis") or "x")
        distance = float(profile.get("distance_ratio") or 0.10)
        x_shift = span_x * distance * progress if axis == "x" else span_x * 0.035 * progress
        y_shift = span_y * distance * progress if axis == "y" else span_y * 0.055 * progress
        shaped = shapely_translate(
            shapely_scale(base_utm, xfact=max(0.76, 1.0 - 0.14 * progress), yfact=max(0.76, 1.0 - 0.14 * progress), origin="centroid"),
            xoff=x_shift,
            yoff=y_shift,
        )
        return shaped.intersection(base_utm)

    return base_utm


def _surface_point_wgs84(point: tuple[float, float, float]) -> list[float]:
    lng, lat = utm_to_wgs84(box(point[0], point[1], point[0] + 0.01, point[1] + 0.01)).centroid.coords[0]
    return [round(lng, 8), round(lat, 8), round(float(point[2]), 2)]


def _surface_from_bounds(
    *,
    role: str,
    kind: str,
    bounds: tuple[float, float, float, float],
    high_m: float,
    low_m: float,
    inset_ratio: float = 0.06,
) -> dict[str, Any]:
    minx, miny, maxx, maxy = bounds
    dx = (maxx - minx) * inset_ratio
    dy = (maxy - miny) * inset_ratio
    return {
        "role": role,
        "kind": kind,
        "surface_type": "quad",
        "vertices_wgs84_h": [
            _surface_point_wgs84((minx + dx, miny + dy, high_m)),
            _surface_point_wgs84((maxx - dx, miny + dy, high_m)),
            _surface_point_wgs84((maxx - dx, maxy - dy, low_m)),
            _surface_point_wgs84((minx + dx, maxy - dy, low_m)),
        ],
    }


def _surface_from_polygon(
    *,
    role: str,
    kind: str,
    polygon_utm,
    height_m: float,
) -> dict[str, Any] | None:
    poly = _largest_polygon_or_none(polygon_utm)
    if poly is None:
        return None
    coords = list(poly.exterior.coords)
    if len(coords) < 4:
        return None
    # Keep source surfaces compact for evidence/rendering.
    sampled = coords[:-1]
    if len(sampled) > 8:
        step = max(1, len(sampled) // 8)
        sampled = sampled[::step][:8]
    return {
        "role": role,
        "kind": kind,
        "surface_type": "polygon",
        "vertices_wgs84_h": [
            _surface_point_wgs84((float(x), float(y), height_m))
            for x, y in sampled
        ],
    }


def _sloped_surface_from_polygon(
    *,
    role: str,
    kind: str,
    polygon_utm,
    high_m: float,
    low_m: float,
) -> dict[str, Any] | None:
    poly = _largest_polygon_or_none(polygon_utm)
    if poly is None:
        return None
    coords = [(float(x), float(y)) for x, y in list(poly.exterior.coords)[:-1]]
    if len(coords) < 3:
        return None
    if len(coords) > 8:
        step = max(1, len(coords) // 8)
        coords = coords[::step][:8]
    miny = min(y for _, y in coords)
    maxy = max(y for _, y in coords)
    span = max(maxy - miny, 1e-6)
    vertices = []
    for x, y in coords:
        ratio = (y - miny) / span
        height = high_m + (low_m - high_m) * ratio
        vertices.append(_surface_point_wgs84((x, y, height)))
    return {
        "role": role,
        "kind": kind,
        "surface_type": "polygon",
        "vertices_wgs84_h": vertices,
    }


def _surface_between_polygons(
    *,
    role: str,
    kind: str,
    lower_utm,
    upper_utm,
    lower_height_m: float,
    upper_height_m: float,
    width_ratio: float = 0.18,
) -> dict[str, Any] | None:
    lower = _largest_polygon_or_none(lower_utm)
    upper = _largest_polygon_or_none(upper_utm)
    if lower is None or upper is None:
        return None
    lx, ly = lower.centroid.x, lower.centroid.y
    ux, uy = upper.centroid.x, upper.centroid.y
    dx = ux - lx
    dy = uy - ly
    length = (dx * dx + dy * dy) ** 0.5
    minx = min(lower.bounds[0], upper.bounds[0])
    miny = min(lower.bounds[1], upper.bounds[1])
    maxx = max(lower.bounds[2], upper.bounds[2])
    maxy = max(lower.bounds[3], upper.bounds[3])
    span = max(maxx - minx, maxy - miny, 1.0)
    width = max(1.0, span * width_ratio)
    if length <= 0.1:
        nx, ny = 0.0, width
    else:
        nx = -dy / length * width
        ny = dx / length * width
    vertices = [
        (lx + nx, ly + ny, lower_height_m),
        (lx - nx, ly - ny, lower_height_m),
        (ux - nx, uy - ny, upper_height_m),
        (ux + nx, uy + ny, upper_height_m),
    ]
    return {
        "role": role,
        "kind": kind,
        "surface_type": "quad",
        "vertices_wgs84_h": [_surface_point_wgs84(point) for point in vertices],
    }


def _surface_between_bounds_face(
    *,
    role: str,
    kind: str,
    lower_utm,
    upper_utm,
    lower_height_m: float,
    upper_height_m: float,
    face: str,
    inset_ratio: float = 0.04,
) -> dict[str, Any] | None:
    lower = _largest_polygon_or_none(lower_utm)
    upper = _largest_polygon_or_none(upper_utm)
    if lower is None or upper is None:
        return None
    def face_points(poly, target_face: str) -> tuple[tuple[float, float], tuple[float, float]] | None:
        coords = [(float(x), float(y)) for x, y in list(poly.exterior.coords)[:-1]]
        if len(coords) < 2:
            return None
        if target_face in {"north", "south"}:
            reverse = target_face == "north"
            ordered = sorted(coords, key=lambda point: point[1], reverse=reverse)
            candidates = ordered[:max(2, min(len(ordered), len(ordered) // 3 + 1))]
            left = min(candidates, key=lambda point: point[0])
            right = max(candidates, key=lambda point: point[0])
            if left == right:
                return None
            return (left, right) if target_face == "north" else (right, left)
        reverse = target_face == "east"
        ordered = sorted(coords, key=lambda point: point[0], reverse=reverse)
        candidates = ordered[:max(2, min(len(ordered), len(ordered) // 3 + 1))]
        low = min(candidates, key=lambda point: point[1])
        high = max(candidates, key=lambda point: point[1])
        if low == high:
            return None
        return (high, low) if target_face == "east" else (low, high)

    lower_edge = face_points(lower, face)
    upper_edge = face_points(upper, face)
    if lower_edge is None or upper_edge is None:
        return None
    lower_a, lower_b = lower_edge
    upper_a, upper_b = upper_edge
    vertices = [
        (lower_a[0], lower_a[1], lower_height_m),
        (lower_b[0], lower_b[1], lower_height_m),
        (upper_b[0], upper_b[1], upper_height_m),
        (upper_a[0], upper_a[1], upper_height_m),
    ]
    return {
        "role": role,
        "kind": kind,
        "surface_type": "quad",
        "vertices_wgs84_h": [_surface_point_wgs84(point) for point in vertices],
    }


def _build_section_source_surfaces(
    *,
    kind: str,
    profile: dict[str, Any],
    materialized: list[dict[str, Any]],
    materialized_utms: list[Any],
) -> list[dict[str, Any]]:
    if not materialized or not materialized_utms:
        return []
    minx = min(geom.bounds[0] for geom in materialized_utms)
    miny = min(geom.bounds[1] for geom in materialized_utms)
    maxx = max(geom.bounds[2] for geom in materialized_utms)
    maxy = max(geom.bounds[3] for geom in materialized_utms)
    top = max(float(volume.get("top_height") or 0.0) for volume in materialized)
    low = max(
        min(float(volume.get("top_height") or top) for volume in materialized),
        top * 0.58,
    )
    surfaces: list[dict[str, Any]] = []
    if kind == "sloped_roof":
        roof = _sloped_surface_from_polygon(
            role="section_surface_sloped_roof_plane",
            kind=kind,
            polygon_utm=materialized_utms[-1],
            high_m=top + 0.15,
            low_m=low + 0.15,
        )
        if roof:
            surfaces.append(roof)
    elif kind == "terrace_ribbon":
        for index in range(1, len(materialized_utms)):
            surface = _surface_between_polygons(
                role=f"section_surface_terrace_ribbon_link_{index}",
                kind=kind,
                lower_utm=materialized_utms[index - 1],
                upper_utm=materialized_utms[index],
                lower_height_m=float(materialized[index - 1].get("top_height") or 0.0) + 0.08,
                upper_height_m=float(materialized[index].get("top_height") or top) + 0.08,
                width_ratio=0.06,
            )
            if surface:
                surfaces.append(surface)
        for index, geom in enumerate(materialized_utms[1:], start=1):
            height = float(materialized[min(index, len(materialized) - 1)].get("top_height") or top)
            surface = _surface_from_polygon(
                role=f"section_surface_terrace_band_{index}",
                kind=kind,
                polygon_utm=geom.boundary.buffer(max(0.4, min(maxx - minx, maxy - miny) * 0.035)).intersection(geom),
                height_m=height + 0.1,
            )
            if surface:
                surfaces.append(surface)
    elif kind in {"diagonal_connector", "diagonal_connect"}:
        surface = _surface_between_polygons(
            role="section_surface_diagonal_connector_skin",
            kind=kind,
            lower_utm=materialized_utms[0],
            upper_utm=materialized_utms[-1],
            lower_height_m=float(materialized[0].get("top_height") or 0.0) + 0.12,
            upper_height_m=top + 0.12,
            width_ratio=0.08,
        )
        if surface:
            surfaces.append(surface)
        bridge = next(
            (
                (volume, geom)
                for volume, geom in zip(materialized, materialized_utms)
                if str(volume.get("role") or "").endswith("diagonal_connector_bridge")
            ),
            None,
        )
        if bridge:
            volume, geom = bridge
            surface = _surface_from_polygon(
                role="section_surface_diagonal_connector_deck",
                kind=kind,
                polygon_utm=geom,
                height_m=float(volume.get("top_height") or top) + 0.12,
            )
            if surface:
                surfaces.append(surface)
    return surfaces


def _materialize_section_profile_volumes(feature: dict[str, Any]) -> None:
    """Convert section profile intent into conservative source volume geometry.

    Legal accounting remains based on the original floor plates. The returned
    `mass_volumes` are still clipped inside each legal band, but their source
    geometry now expresses sloped, terrace, and diagonal design intent instead
    of relying on a separate pink overlay.
    """
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    profile = props.get("section_profile")
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
    if not isinstance(profile, dict):
        profile = model.get("section_profile") if isinstance(model.get("section_profile"), dict) else None
    if not isinstance(profile, dict):
        return
    kind = str(profile.get("kind") or "")
    if kind not in {"sloped_roof", "terrace_ribbon", "diagonal_connector", "diagonal_connect"}:
        return
    existing = props.get("section_profile_materialized")
    if isinstance(existing, dict) and existing.get("kind") == kind:
        return
    volumes = model.get("volumes") if isinstance(model.get("volumes"), list) else props.get("mass_volumes")
    if not isinstance(volumes, list) or len(volumes) < 2:
        return

    parsed: list[tuple[dict[str, Any], Any]] = []
    for volume in volumes:
        if not isinstance(volume, dict) or not isinstance(volume.get("geometry"), dict):
            continue
        try:
            geom = _largest_polygon_or_none(wgs84_to_utm(geojson_to_polygon(volume["geometry"])))
        except Exception:
            geom = None
        if geom is not None:
            parsed.append((volume, geom))
    if len(parsed) < 2:
        return

    minx = min(geom.bounds[0] for _, geom in parsed)
    miny = min(geom.bounds[1] for _, geom in parsed)
    maxx = max(geom.bounds[2] for _, geom in parsed)
    maxy = max(geom.bounds[3] for _, geom in parsed)
    count = max(1, len(parsed) - 1)
    materialized: list[dict[str, Any]] = []
    materialized_utms: list[Any] = []
    for index, (volume, geom) in enumerate(parsed):
        progress = index / count
        shaped = _section_materialized_polygon(geom, profile=profile, progress=progress, bounds=(minx, miny, maxx, maxy))
        shaped = _largest_polygon_or_none(shaped)
        if shaped is None:
            shaped = geom
        materialized_utms.append(shaped)
        next_volume = {
            **volume,
            "geometry": mapping(utm_to_wgs84(shaped)),
            "role": f"section_source_{kind}",
            "source_geometry": {
                "basis": "section_profile_materialized_inside_legal_floor_plate",
                "profile_kind": kind,
                "legal_accounting": "floor_plates_remain_conservative_source_for_far_bcr_height",
            },
        }
        materialized.append(next_volume)

    if kind in {"diagonal_connector", "diagonal_connect"} and len(materialized_utms) >= 2:
        lower = materialized_utms[0]
        upper = materialized_utms[-1]
        line = LineString([lower.centroid, upper.centroid])
        if line.length > 0.5:
            width = max(1.2, min(maxx - minx, maxy - miny) * 0.12)
            allowed = unary_union([geom for _, geom in parsed])
            connector = _largest_polygon_or_none(line.buffer(width, cap_style=2).intersection(allowed))
            if connector is not None:
                bottom_height = float(materialized[0].get("top_height") or materialized[0].get("bottom_height") or 0.0)
                top_height = float(materialized[-1].get("top_height") or bottom_height)
                if top_height > bottom_height + 0.5:
                    materialized.append({
                        "band": "diagonal_connector",
                        "bottom_height": round(bottom_height, 2),
                        "top_height": round(top_height, 2),
                        "geometry": mapping(utm_to_wgs84(connector)),
                        "role": "section_source_diagonal_connector_bridge",
                        "source_geometry": {
                            "basis": "maas_verb_sequence_diagonal_connect",
                            "profile_kind": kind,
                            "legal_accounting": "display_connector_inside_union_of_legal_floor_plates",
                        },
                    })
                    materialized_utms.append(connector)

    if len(materialized) != len(parsed):
        if not (kind in {"diagonal_connector", "diagonal_connect"} and len(materialized) == len(parsed) + 1):
            return
    section_surfaces = _build_section_source_surfaces(
        kind=kind,
        profile=profile,
        materialized=materialized,
        materialized_utms=materialized_utms,
    )
    props["mass_volumes"] = materialized
    props["section_source_surfaces"] = section_surfaces
    props["section_profile_materialized"] = {
        "status": "materialized_inside_legal_floor_plates",
        "kind": kind,
        "design_synthesis": True,
        "volume_count": len(materialized),
        "surface_count": len(section_surfaces),
        "legal_accounting": "floor_plates",
        "basis": "maas_section_synthesis_v1",
    }
    if isinstance(model, dict):
        model["volumes"] = materialized
        model["section_source_surfaces"] = section_surfaces
        model["section_profile_materialized"] = props["section_profile_materialized"]


def _interpolated_upper_volumes(feature: dict[str, Any], *, steps: int = 4) -> list[dict[str, Any]]:
    props = feature.get("properties", {}) or {}
    if props.get("lower_height") is None or props.get("upper_geometry") is None:
        return []
    try:
        lower_height = float(props.get("lower_height") or 0.0)
        total_height = float(props.get("height") or lower_height)
        lower = _largest_polygon_or_none(wgs84_to_utm(geojson_to_polygon(feature.get("geometry"))))
        upper = _largest_polygon_or_none(wgs84_to_utm(geojson_to_polygon(props.get("upper_geometry"))))
    except Exception:
        return []
    if lower is None or upper is None or total_height <= lower_height <= 0:
        return []

    usable_steps = max(2, min(5, steps))
    upper_area_ratio = max(0.05, min(1.0, float(upper.area) / max(float(lower.area), 1e-9)))
    lower_centroid = lower.centroid
    upper_centroid = upper.centroid
    stage_height = (total_height - lower_height) / usable_steps
    volumes: list[dict[str, Any]] = [{
        "band": 0,
        "bottom_height": 0.0,
        "top_height": round(lower_height, 2),
        "geometry": feature.get("geometry"),
        "role": "morphology_volume",
    }]
    previous_top = lower_height
    for index in range(usable_steps):
        progress = (index + 1) / usable_steps
        if index == usable_steps - 1:
            shaped = upper
        else:
            area_ratio = 1.0 + (upper_area_ratio - 1.0) * progress
            factor = area_ratio ** 0.5
            shaped = shapely_scale(lower, xfact=factor, yfact=factor, origin="centroid")
            shaped = shapely_translate(
                shaped,
                xoff=(upper_centroid.x - lower_centroid.x) * progress,
                yoff=(upper_centroid.y - lower_centroid.y) * progress,
            )
            shaped = _largest_polygon_or_none(shaped.intersection(lower).union(upper).intersection(lower))
            if shaped is None:
                shaped = upper
        top_height = total_height if index == usable_steps - 1 else lower_height + stage_height * (index + 1)
        if top_height <= previous_top:
            continue
        volumes.append({
            "band": index + 1,
            "bottom_height": round(previous_top, 2),
            "top_height": round(top_height, 2),
            "geometry": mapping(utm_to_wgs84(shaped)),
            "role": "morphology_volume_interpolated",
        })
        previous_top = top_height
    return volumes


def _single_volume_model(operator: str, feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties", {}) or {}
    volumes = [{
        "band": 0,
        "bottom_height": 0.0,
        "top_height": props.get("height") or 0.0,
        "geometry": feature.get("geometry"),
        "role": "morphology_volume",
    }]
    interpolated = _interpolated_upper_volumes(feature)
    if interpolated:
        volumes = interpolated
    return {
        "algorithm": "maas_legal_envelope",
        "operator": operator,
        "verb_sequence": _maas_verb_sequence(operator),
        "volumes": volumes,
        "floor_plates": [],
        "legal_metrics": {
            "far": props.get("far"),
            "bcr": props.get("bcr"),
            "height": props.get("height"),
            "num_floors": props.get("num_floors"),
            "footprint_area": props.get("footprint_area"),
            "floor_area": props.get("floor_area"),
            "min_setback": props.get("min_setback"),
            "open_pct": props.get("open_pct"),
        },
    }


def _apply_variant_verb_sequence(feature: dict[str, Any], variant) -> None:
    sequence = getattr(variant, "verb_sequence", ()) or ()
    if not sequence:
        return
    props = feature.get("properties", {}) or {}
    sequence_list = [dict(item) for item in sequence]
    props["maas_verb_sequence"] = sequence_list
    model = props.get("maas_model")
    if isinstance(model, dict):
        model["verb_sequence"] = sequence_list
        model["grammar_sequence"] = variant.operator
        model["grammar_label"] = _concept_label(variant.operator)
    _attach_section_profile(feature)
    _materialize_section_profile_volumes(feature)


def _select_diverse_features(
    features: list[dict[str, Any]],
    max_variants: int,
    preferred_operator: str | None = None,
) -> list[dict[str, Any]]:
    """Pick the best legal candidate per spatial concept, then fill by score.

    MAAS is useful here only if the user sees different architectural
    strategies, not eighteen tiny variations of the same sunlight stepback.
    The first pass therefore reserves one slot for each concept family.
    """
    limit = max(1, max_variants)
    if len(features) <= 1:
        return features

    by_score = sorted(features, key=lambda f: f["properties"].get("maas_score", 0), reverse=True)
    selected: list[dict[str, Any]] = []

    # Keep an explicit user/agent-preferred operator first; otherwise keep the
    # legal capacity anchor first. Family coverage is applied after that.
    anchor = None
    if preferred_operator:
        anchor = next((f for f in by_score if f["properties"].get("mass_shape") == preferred_operator), None)
    if anchor is None:
        anchor = next((f for f in by_score if f["properties"].get("mass_shape") == "legal_layered_max"), None)
    if anchor is not None:
        selected.append(anchor)

    def is_near_duplicate(feature: dict[str, Any]) -> bool:
        if preferred_operator and feature["properties"].get("mass_shape") == preferred_operator:
            return False
        try:
            family = _operator_family(feature["properties"].get("mass_shape", ""))
            candidate = geojson_to_polygon(feature["geometry"])
            candidate_profile = _volume_profile(feature)
            candidate_is_connector = _is_section_connector(feature)
            candidate_verbs = sequence_verbs(feature["properties"].get("maas_verb_sequence"))
            for existing in selected:
                existing_family = _operator_family(existing["properties"].get("mass_shape", ""))
                existing_is_connector = _is_section_connector(existing)
                iou = polygon_iou(candidate, geojson_to_polygon(existing["geometry"]))
                existing_verbs = sequence_verbs(existing["properties"].get("maas_verb_sequence"))
                if iou >= 0.98 and candidate_profile == _volume_profile(existing):
                    return True
                if iou >= 0.94 and candidate_verbs == existing_verbs:
                    return True
                if family in {"bcr_fill", "legal_buildable"} and iou >= 0.96:
                    return True
                # A podium/tower or taper can legitimately share the same
                # ground footprint with another concept while differing in
                # section. Treat only same-family high-IoU footprints as
                # duplicates; cross-family vertical typologies must survive.
                if family != existing_family:
                    continue
                if iou >= 0.96:
                    return True
            return False
        except Exception:
            return False

    by_family: dict[str, list[dict[str, Any]]] = {}
    for feature in by_score:
        family = _operator_family(feature["properties"].get("mass_shape", ""))
        by_family.setdefault(family, []).append(feature)

    if limit >= 8:
        capped_by_score = by_score[: max(limit + 12, 32)]
        medoid_pool = [
            feature for feature in capped_by_score
            if feature not in selected and not is_near_duplicate(feature)
        ]
        medoid_pool = medoid_pool[: max(limit + 8, 28)]
        medoids = _kmedoid_representatives(
            medoid_pool,
            k=limit - len(selected),
            anchors=selected,
        )
        selected.extend(medoids)
        min_section_design = min(MIN_SECTION_DESIGN_CONCEPTS, max(1, limit // 5))
        section_design_count = sum(1 for feature in selected if _is_section_connector(feature))
        if section_design_count < min_section_design:
            section_candidates = [
                feature for feature in by_score
                if feature not in selected and _is_section_connector(feature)
            ]
            for feature in section_candidates:
                if section_design_count >= min_section_design:
                    break
                candidate_verbs = sequence_verbs(feature["properties"].get("maas_verb_sequence"))
                selected_section_verbs = [
                    sequence_verbs(item["properties"].get("maas_verb_sequence"))
                    for item in selected
                    if _is_section_connector(item)
                ]
                if candidate_verbs in selected_section_verbs:
                    continue
                if len(selected) >= limit:
                    replace_index = min(
                        range(len(selected)),
                        key=lambda i: (
                            1 if _is_section_connector(selected[i]) else 0,
                            sequence_diversity_score(
                                sequence_verbs(selected[i]["properties"].get("maas_verb_sequence")),
                                [
                                    sequence_verbs(other["properties"].get("maas_verb_sequence"))
                                    for j, other in enumerate(selected)
                                    if j != i
                                ],
                            ),
                            _capacity_score(selected[i]["properties"]),
                        ),
                    )
                    selected.pop(replace_index)
                selected.append(feature)
                section_design_count += 1
        required_section_families = [
            "diagonal_connect",
            "terrace_link",
            "sloped_roof",
            "stepback_tower",
        ]
        for family in required_section_families:
            if any(_operator_family(item["properties"].get("mass_shape", "")) == family for item in selected):
                continue
            options = [
                feature for feature in by_family.get(family, [])
                if feature not in selected and not is_near_duplicate(feature)
            ]
            if not options:
                continue
            options.sort(
                key=lambda feature: (
                    _design_synthesis_rank(feature),
                    sequence_diversity_score(
                        sequence_verbs(feature["properties"].get("maas_verb_sequence")),
                        [
                            sequence_verbs(item["properties"].get("maas_verb_sequence"))
                            for item in selected
                        ],
                    ),
                    float(feature["properties"].get("diversity_score") or 0.0),
                    float(feature["properties"].get("maas_score") or 0.0),
                ),
                reverse=True,
            )
            if len(selected) < limit:
                selected.append(options[0])
                continue
            replace_index = min(
                range(len(selected)),
                key=lambda i: (
                    1 if str(selected[i]["properties"].get("mass_shape", "")) == "legal_layered_max" else 0,
                    1 if _operator_family(selected[i]["properties"].get("mass_shape", "")) in required_section_families else 0,
                    1 if _is_section_connector(selected[i]) else 0,
                    float(selected[i]["properties"].get("diversity_score") or 0.0),
                    float(selected[i]["properties"].get("maas_score") or 0.0),
                ),
            )
            selected[replace_index] = options[0]
        required_plan_families = [
            "interlock",
            "overlap",
            "split",
            "branch",
            "pinch",
            "courtyard",
            "void_notch",
            "slender_bar",
        ]
        for family in required_plan_families:
            if any(_operator_family(item["properties"].get("mass_shape", "")) == family for item in selected):
                continue
            options = [
                feature for feature in by_family.get(family, [])
                if feature not in selected and not is_near_duplicate(feature)
            ]
            if not options:
                continue
            options.sort(
                key=lambda feature: (
                    1 if _is_grammar_candidate(feature) else 0,
                    _visible_volume_count(feature),
                    float(feature["properties"].get("diversity_score") or 0.0),
                    float(feature["properties"].get("maas_score") or 0.0),
                ),
                reverse=True,
            )
            if len(selected) < limit:
                selected.append(options[0])
                continue
            replace_index = min(
                range(len(selected)),
                key=lambda i: (
                    1 if _is_section_connector(selected[i]) else 0,
                    1 if _operator_family(selected[i]["properties"].get("mass_shape", "")) in required_plan_families else 0,
                    float(selected[i]["properties"].get("diversity_score") or 0.0),
                    float(selected[i]["properties"].get("maas_score") or 0.0),
                ),
            )
            selected[replace_index] = options[0]
        for feature in by_score:
            if len(selected) >= limit:
                break
            if feature in selected or is_near_duplicate(feature):
                continue
            selected.append(feature)
        return selected[:limit]

    # Keep at least one sectional/stepback strategy when the parcel can support
    # it. The user still needs a legal terrace/step mass as an option; the
    # diversity pass below only prevents that family from dominating the list.
    if limit > len(selected) and not preferred_operator:
        has_section = any(
            _operator_family(s["properties"].get("mass_shape", "")) in SECTION_CONCEPTS
            for s in selected
        )
        if not has_section:
            section_candidates = [
                f for family in ("stepback_tower", "grade", "taper")
                for f in by_family.get(family, [])
            ]
            for feature in section_candidates:
                if feature in selected or is_near_duplicate(feature):
                    continue
                selected.append(feature)
                break

    # A stepped mass alone is not enough for MAAS design exploration. Preserve
    # at least one section connector option so the user can compare step-only
    # forms against diagonal/terrace/sloped linking masses in the default run.
    if limit > len(selected) and not preferred_operator:
        has_connector = any(_is_section_connector(feature) for feature in selected)
        if not has_connector:
            connector_candidates = [f for f in by_score if _is_section_connector(f)]
            for feature in connector_candidates:
                if feature in selected or is_near_duplicate(feature):
                    continue
                selected.append(feature)
                break

    ordered_families = CONCEPT_ORDER + [
        family for family in by_family
        if family not in CONCEPT_ORDER
    ]

    for family in ordered_families:
        if len(selected) >= limit:
            break
        if any(_operator_family(s["properties"].get("mass_shape", "")) == family for s in selected):
            continue
        for feature in by_family.get(family, []):
            if feature in selected or is_near_duplicate(feature):
                continue
            selected.append(feature)
            break

    if limit > len(selected) and not preferred_operator:
        grammar_candidates = [
            f for f in by_score
            if str(f["properties"].get("mass_shape", "")).startswith("grammar_")
        ]
        for feature in grammar_candidates:
            if len(selected) >= limit:
                break
            grammar_count = sum(
                1 for s in selected
                if str(s["properties"].get("mass_shape", "")).startswith("grammar_")
            )
            if grammar_count >= min(MIN_GRAMMAR_CONCEPTS, limit):
                break
            if feature in selected or is_near_duplicate(feature):
                continue
            selected.append(feature)

    # Only backfill same-family variants when the parcel yielded too few
    # concepts. For normal parcels, stop at one representative per spatial
    # concept so the UI does not become a list of near-identical stepbacks.
    min_required = limit
    while len(selected) < min_required:
        remaining = [f for f in by_score if f not in selected and not is_near_duplicate(f)]
        if not remaining:
            break
        selected_polys = [geojson_to_polygon(f["geometry"]) for f in selected]
        selected_sequences = [
            sequence_verbs(f["properties"].get("maas_verb_sequence"))
            for f in selected
        ]
        best = max(
            remaining,
            key=lambda f: (
                _capacity_score(f["properties"]) * 0.45
                + diversity_score(geojson_to_polygon(f["geometry"]), selected_polys, None) * 0.25
                + sequence_diversity_score(
                    sequence_verbs(f["properties"].get("maas_verb_sequence")),
                    selected_sequences,
                ) * 0.30
            ),
        )
        selected.append(best)

    if preferred_operator:
        return selected
    return selected[:limit]


def _mass_feature(
    *,
    operator: str,
    footprint_utm,
    upper_footprint_utm,
    num_floors: int,
    lower_floor_fraction: float | None,
    site_utm,
    site_area_m2: float,
    building_type: str,
    notes: tuple[str, ...],
    diversity: float,
    source_iou: float,
) -> dict[str, Any]:
    floor_height = get_floor_height(building_type)
    height = num_floors * floor_height
    footprint_area = footprint_utm.area
    open_pct = max(0.0, 100.0 - (footprint_area / site_area_m2 * 100)) if site_area_m2 > 0 else 0.0

    lower_floors = num_floors
    upper_floors = 0
    lower_height = None
    if upper_footprint_utm is not None and num_floors >= 2:
        fraction = lower_floor_fraction if lower_floor_fraction is not None else 0.5
        lower_floors = max(1, min(num_floors - 1, int(round(num_floors * fraction))))
        upper_floors = num_floors - lower_floors
        lower_height = lower_floors * floor_height
        floor_area = footprint_area * lower_floors + upper_footprint_utm.area * upper_floors
    else:
        floor_area = footprint_area * num_floors

    props = {
        "algorithm": "maas_legal_envelope",
        "mass_shape": operator,
        "operator_family": _operator_family(operator),
        "typology_family": _operator_family(operator),
        "typology_source": "typology_first",
        "maas_concept": _concept_label(operator),
        "height": round(height, 2),
        "num_floors": num_floors,
        "floor_height": floor_height,
        "footprint_area": round(footprint_area, 2),
        "floor_area": round(floor_area, 2),
        "bcr": round(footprint_area / site_area_m2 * 100, 2) if site_area_m2 > 0 else 0,
        "far": round(floor_area / site_area_m2 * 100, 2) if site_area_m2 > 0 else 0,
        "min_setback": round(float(footprint_utm.distance(site_utm.boundary)), 2),
        "open_pct": round(open_pct, 2),
        "diversity_score": diversity,
        "source_iou": source_iou,
        "shape_signature": shape_signature(footprint_utm),
        "notes": list(notes),
    }
    if lower_height is not None and upper_footprint_utm is not None:
        props["lower_height"] = round(lower_height, 2)
        props["step_floor"] = lower_floors
        props["upper_geometry"] = mapping(utm_to_wgs84(upper_footprint_utm))
        props["typology_bands"] = [
            {
                "role": "lower",
                "from_floor": 1,
                "to_floor": lower_floors,
                "geometry": mapping(utm_to_wgs84(footprint_utm)),
            },
            {
                "role": "upper",
                "from_floor": lower_floors + 1,
                "to_floor": num_floors,
                "geometry": mapping(utm_to_wgs84(upper_footprint_utm)),
            },
        ]
    else:
        props["typology_bands"] = [
            {
                "role": "single",
                "from_floor": 1,
                "to_floor": num_floors,
                "geometry": mapping(utm_to_wgs84(footprint_utm)),
            }
        ]

    feature = {
        "type": "Feature",
        "geometry": mapping(utm_to_wgs84(footprint_utm)),
        "properties": props,
    }
    model = _single_volume_model(operator, feature)
    props["maas_model"] = model
    props["mass_volumes"] = model["volumes"]
    props["maas_verb_sequence"] = model["verb_sequence"]
    props["maas_sequence_verbs"] = sequence_verbs(model["verb_sequence"])
    _attach_section_profile(feature)
    _materialize_section_profile_volumes(feature)
    attach_parking_strategy(
        props,
        site_area_m2=site_area_m2,
        building_type=building_type,
        footprint_utm=footprint_utm,
        site_utm=site_utm,
    )
    _attach_3d_diversity(feature)
    return feature


def _floor_plate_feature(
    *,
    stack: FloorPlateStack,
    site_utm,
    site_area_m2: float,
    building_type: str,
    diversity: float,
    source_iou: float,
) -> dict[str, Any]:
    floor_height = get_floor_height(building_type)
    footprint_area = stack.footprint.area
    open_pct = max(0.0, 100.0 - (footprint_area / site_area_m2 * 100)) if site_area_m2 > 0 else 0.0
    props = {
        "algorithm": "maas_legal_envelope",
        "mass_shape": stack.operator,
        "operator_family": _operator_family(stack.operator),
        "typology_family": _operator_family(stack.operator),
        "typology_source": "legal_floor_plate_anchor",
        "maas_concept": _concept_label(stack.operator),
        "building_type": building_type,
        "height": round(stack.height_m, 2),
        "num_floors": stack.num_floors,
        "floor_height": floor_height,
        "footprint_area": round(footprint_area, 2),
        "floor_area": round(stack.total_floor_area_m2, 2),
        "bcr": round(footprint_area / site_area_m2 * 100, 2) if site_area_m2 > 0 else 0,
        "far": round(stack.total_floor_area_m2 / site_area_m2 * 100, 2) if site_area_m2 > 0 else 0,
        "min_setback": round(float(stack.footprint.distance(site_utm.boundary)), 2),
        "open_pct": round(open_pct, 2),
        "diversity_score": diversity,
        "source_iou": source_iou,
        "shape_signature": shape_signature(stack.footprint),
        "notes": list(stack.notes),
    }
    model = _maas_model(
        operator=stack.operator,
        floor_plates=stack.floor_plates,
        props=props,
        site_area_m2=site_area_m2,
    )
    props["maas_model"] = model
    # Compatibility fields for existing UI/tests. The canonical source is
    # properties.maas_model, so agents should read that first.
    props["floor_plates"] = model["floor_plates"]
    props["floor_groups"] = model["floor_groups"]
    props["mass_volumes"] = model["volumes"]
    props["maas_verb_sequence"] = model["verb_sequence"]
    props["maas_sequence_verbs"] = sequence_verbs(model["verb_sequence"])
    attach_parking_strategy(
        props,
        site_area_m2=site_area_m2,
        building_type=building_type,
        footprint_utm=stack.footprint,
        site_utm=site_utm,
    )
    feature = {
        "type": "Feature",
        "geometry": mapping(utm_to_wgs84(stack.footprint)),
        "properties": props,
    }
    _attach_section_profile(feature)
    _materialize_section_profile_volumes(feature)
    _attach_3d_diversity(feature)
    return feature


def generate_legal_mass_variants(
    *,
    mass_geojson: dict[str, Any],
    site_polygon_geojson: dict[str, Any],
    constraints: list[dict[str, Any]] | None = None,
    building_type: str = "공동주택",
    max_variants: int = 6,
    sunlight_envelope: dict[str, Any] | None = None,
    setback_geometries: dict[str, Any] | None = None,
    include_interactive_seed: bool = False,
    preferred_operator: str | None = None,
    pnu: str | None = None,
    parking_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return legal, diverse variants derived from a selected mass GeoJSON."""
    if mass_geojson.get("type") != "Feature":
        raise ValueError("mass_geojson must be a GeoJSON Feature")

    source_wgs = largest_polygon(geojson_to_polygon(mass_geojson.get("geometry")))
    source_utm = wgs84_to_utm(source_wgs)
    site_wgs = geojson_to_polygon(site_polygon_geojson)
    site_utm = wgs84_to_utm(site_wgs)
    site_area_m2 = site_utm.area

    envelope = build_legal_envelope(
        site_utm=site_utm,
        constraints=constraints,
        building_type=building_type,
        sunlight_envelope=sunlight_envelope,
        setback_geometries=setback_geometries,
    )
    limits = envelope.limits
    max_seed_floors = envelope.max_seed_floors

    repaired_source, repaired_floors, source_actions = repair_design(
        source_utm, site_utm, max_seed_floors, limits,
        sunlight_envelope=sunlight_envelope,
    )
    if repaired_source is None:
        raise ValueError("source mass cannot be repaired into the site/legal envelope")

    selected = []
    selected_polygons = []
    rejected = []

    layered_stack = build_floor_plate_stack(envelope, sunlight_envelope)
    if layered_stack is not None:
        source_iou = round(1.0 - diversity_score(layered_stack.footprint, [], repaired_source), 4)
        diversity = diversity_score(layered_stack.footprint, selected_polygons, repaired_source)
        feature = _floor_plate_feature(
            stack=layered_stack,
            site_utm=site_utm,
            site_area_m2=site_area_m2,
            building_type=building_type,
            diversity=diversity,
            source_iou=source_iou,
        )
        props = feature["properties"]
        failed_metrics = failed_constraint_metrics(props, envelope)
        if failed_metrics:
            rejected.append({
                "operator": layered_stack.operator,
                "reason": "legal_metric_failed_after_layering",
                "failed_metrics": failed_metrics,
            })
        else:
            far_utilization = min(1.0, props["far"] / envelope.far_limit) if envelope.far_limit > 0 else 0.0
            bcr_utilization = min(1.0, props["bcr"] / envelope.bcr_limit) if envelope.bcr_limit > 0 else 0.0
            props["far_utilization"] = round(far_utilization, 4)
            props["bcr_utilization"] = round(bcr_utilization, 4)
            props["maas_score"] = round(far_utilization * 0.52 + bcr_utilization * 0.30 + diversity * 0.18, 4)
            _attach_design_quality(feature, layered_stack.footprint)
            selected.append(feature)
            selected_polygons.append(layered_stack.footprint)

    variants = generate_seed_variants(
        repaired_source,
        envelope,
        include_interactive_seed=include_interactive_seed,
    )

    for variant in variants:
        repaired_fp, floors, actions = repair_design(
            variant.footprint,
            site_utm,
            max_seed_floors,
            limits,
            sunlight_envelope=sunlight_envelope,
        )
        if repaired_fp is None:
            rejected.append({"operator": variant.operator, "reason": "repair_failed"})
            continue

        upper = variant.upper_footprint
        if upper is not None:
            upper = upper.intersection(repaired_fp)
            if upper.is_empty or upper.area < 1.0:
                upper = None
            elif not _upper_typology_is_viable(repaired_fp, upper):
                rejected.append({
                    "operator": variant.operator,
                    "reason": "upper_typology_too_small_for_architectural_mass",
                    "upper_area_m2": round(float(upper.area), 2),
                    "lower_area_m2": round(float(repaired_fp.area), 2),
                })
                continue

        source_iou = round(1.0 - diversity_score(repaired_fp, [], repaired_source), 4)
        diversity = diversity_score(repaired_fp, selected_polygons, repaired_source)
        variant_stack = None
        if _should_use_floor_plate_stack(variant.operator, preferred_operator):
            variant_stack = build_floor_plate_stack(
                envelope,
                sunlight_envelope,
                operator=variant.operator if variant.operator == preferred_operator else f"{variant.operator}_layered",
                ground_footprint=repaired_fp,
                upper_footprint=upper,
                lower_floor_fraction=variant.lower_floor_fraction,
            )
        if (
            variant_stack is not None
            and variant_stack.total_floor_area_m2 >= repaired_fp.area
            and _stack_has_meaningful_top(variant_stack)
        ):
            feature = _floor_plate_feature(
                stack=variant_stack,
                site_utm=site_utm,
                site_area_m2=site_area_m2,
                building_type=building_type,
                diversity=diversity,
                source_iou=source_iou,
            )
            feature["properties"]["notes"].extend(list(variant.notes + tuple(actions)))
            _apply_variant_verb_sequence(feature, variant)
        else:
            feature = _mass_feature(
                operator=variant.operator,
                footprint_utm=repaired_fp,
                upper_footprint_utm=upper,
                num_floors=floors,
                lower_floor_fraction=variant.lower_floor_fraction,
                site_utm=site_utm,
                site_area_m2=site_area_m2,
                building_type=building_type,
                notes=variant.notes + tuple(actions),
                diversity=diversity,
                source_iou=source_iou,
            )
            _apply_variant_verb_sequence(feature, variant)
        props = feature["properties"]
        if (
            variant.operator == "grammar_sunlight_multi_step"
            and len(props.get("mass_volumes") or []) < 3
        ):
            rejected.append({
                "operator": variant.operator,
                "reason": "not_enough_floor_bands_for_multi_step",
            })
            continue
        failed_metrics = failed_constraint_metrics(props, envelope)
        if failed_metrics:
            rejected.append({
                "operator": variant.operator,
                "reason": "legal_metric_failed_after_repair",
                "failed_metrics": failed_metrics,
            })
            continue

        far_utilization = min(1.0, props["far"] / envelope.far_limit) if envelope.far_limit > 0 else 0.0
        bcr_utilization = min(1.0, props["bcr"] / envelope.bcr_limit) if envelope.bcr_limit > 0 else 0.0
        props["far_utilization"] = round(far_utilization, 4)
        props["bcr_utilization"] = round(bcr_utilization, 4)
        props["maas_score"] = round(far_utilization * 0.45 + bcr_utilization * 0.35 + diversity * 0.20, 4)
        _attach_design_quality(feature, repaired_fp)
        selected.append(feature)
        selected_polygons.append(repaired_fp)

    selected.sort(key=lambda f: f["properties"].get("maas_score", 0), reverse=True)
    legal_candidate_pool = list(selected)
    if preferred_operator:
        preferred_index = next(
            (
                i for i, feature in enumerate(selected)
                if feature["properties"].get("mass_shape") == preferred_operator
            ),
            None,
        )
        if preferred_index is not None:
            selected.insert(0, selected.pop(preferred_index))
    selected = _select_diverse_features(selected, max(1, max_variants), preferred_operator=preferred_operator)
    parking_scan_features = list(selected)
    if not preferred_operator:
        parking_scan_features.extend(
            feature for feature in legal_candidate_pool[:24]
            if feature not in parking_scan_features
        )
    _attach_parking_requirements(
        parking_scan_features,
        pnu=pnu,
        building_type=building_type,
        site_utm=site_utm,
        site_area_m2=site_area_m2,
        parking_options=parking_options,
    )
    parking_viable_extras = [
        feature for feature in parking_scan_features
        if feature not in selected and _parking_priority_key(feature)[0] > 0
    ]
    parking_viable_extras.sort(key=_parking_priority_key, reverse=True)
    for feature in parking_viable_extras[:3]:
        selected.append(feature)
    parking_repairs = _parking_repair_candidates(
        selected,
        envelope=envelope,
        site_utm=site_utm,
        site_area_m2=site_area_m2,
        building_type=building_type,
        parking_options=parking_options,
    )
    if parking_repairs:
        _attach_parking_requirements(
            parking_repairs,
            pnu=pnu,
            building_type=building_type,
            site_utm=site_utm,
            site_area_m2=site_area_m2,
            parking_options=parking_options,
        )
        _sync_parking_repair_metadata(parking_repairs)
        selected.extend(parking_repairs)
    parking_visible = [
        feature for feature in selected
        if _parking_priority_key(feature)[1] > 0
    ]
    parking_visible.sort(key=_parking_priority_key, reverse=True)
    review_candidates = [
        feature for feature in selected
        if feature not in parking_visible
    ]
    review_candidates.sort(key=_review_diversity_priority_key, reverse=True)
    selected = parking_visible + review_candidates
    if preferred_operator:
        preferred_index = next(
            (
                i for i, feature in enumerate(selected)
                if feature["properties"].get("mass_shape") == preferred_operator
            ),
            None,
        )
        if preferred_index is not None:
            selected.insert(0, selected.pop(preferred_index))
    final_limit = max(1, max_variants)
    selected = _preserve_visible_section_connector(
        selected,
        final_limit=final_limit,
        preferred_operator=preferred_operator,
    )
    selected = _final_design_balanced_selection(
        selected,
        final_limit=final_limit,
        preferred_operator=preferred_operator,
    )
    for i, feature in enumerate(selected, start=1):
        feature["properties"]["variant_id"] = f"maas_{i:02d}"

    return {
        "mode": "maas_legal_variants",
        "algorithm": "maas_legal_envelope",
        "count": len(selected),
        "seed_library": seed_library_metadata(),
        "source_repair_actions": source_actions,
        "constraints": {
            "bcr_limit": envelope.bcr_limit,
            "far_limit": envelope.far_limit,
            "height_limit": envelope.height_limit,
            "max_seed_floors": envelope.max_seed_floors,
            "has_buildable_footprint": envelope.buildable_footprint is not None,
            "has_floor_plate_stack": layered_stack is not None,
        },
        "feature_collection": {
            "type": "FeatureCollection",
            "features": selected,
        },
        "rejected": rejected,
        "notes": [
            "Legal envelope is the primary generator boundary.",
            "Layered MAAS candidates clip every floor plate by the legal envelope before FAR/BCR scoring.",
            "Selected ARR/legacy mass is treated as a seed for diversity, not as the capacity source.",
            "Each variant is repaired and checked against BCR/FAR/height/sunlight before return.",
            "Variants are ranked by legal FAR/BCR utilization plus geometric diversity.",
        ],
    }


def _attach_parking_requirements(
    features: list[dict[str, Any]],
    *,
    pnu: str | None,
    building_type: str,
    site_utm,
    site_area_m2: float,
    parking_options: dict[str, Any] | None,
) -> None:
    options = parking_options or {}
    road_context = options.get("road_context") if isinstance(options.get("road_context"), dict) else None
    loaded_rules = load_parking_requirement_rules(options=options) if pnu else None
    rules = loaded_rules.get("rules") if isinstance(loaded_rules, dict) and loaded_rules.get("status") == "loaded" else None
    graph_unavailable = loaded_rules if isinstance(loaded_rules, dict) and loaded_rules.get("status") != "loaded" else None
    for feature in features:
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        if graph_unavailable:
            requirement = {
                "status": graph_unavailable.get("status"),
                "required_spaces": None,
                "accessible": {
                    "status": graph_unavailable.get("status"),
                    "accessible_min": None,
                    "accessible_max": None,
                },
                "reason": graph_unavailable.get("reason"),
            }
        else:
            feature_options = _parking_options_for_feature(options, props, building_type)
            requirement = resolve_candidate_parking_requirement(
                pnu=pnu,
                building_type=building_type,
                facility_area_m2=_float_or_none(props.get("floor_area")),
                options=feature_options,
                rules=rules,
            )
        apply_parking_requirement_to_props(props, requirement)
        try:
            footprint_utm = largest_polygon(wgs84_to_utm(geojson_to_polygon(feature.get("geometry"))))
        except Exception:
            footprint_utm = None
        attach_parking_strategy(
            props,
            site_area_m2=site_area_m2,
            building_type=building_type,
            footprint_utm=footprint_utm,
            site_utm=site_utm,
            road_context=road_context,
        )


def _parking_repair_candidates(
    features: list[dict[str, Any]],
    *,
    envelope,
    site_utm,
    site_area_m2: float,
    building_type: str,
    parking_options: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    options = parking_options or {}
    road_context = options.get("road_context") if isinstance(options.get("road_context"), dict) else None
    repaired: list[dict[str, Any]] = []
    seen_signatures: set[tuple[float, float, float]] = set()
    for feature in features:
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        precheck = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
        layout = precheck.get("layout_candidate") if isinstance(precheck.get("layout_candidate"), dict) else {}
        required_count = precheck.get("required_count") if isinstance(precheck.get("required_count"), dict) else {}
        required = _int_or_none(required_count.get("required_spaces"))
        if required is None or required <= 0:
            required = _int_or_none(layout.get("required_spaces"))
        if required is None or required <= 0:
            required = _int_or_none(props.get("required_parking_spaces"))
        if required is None or required <= 0:
            continue
        if layout.get("status") == "pass" and int(layout.get("provided_spaces") or 0) >= required:
            continue
        try:
            footprint_utm = largest_polygon(wgs84_to_utm(geojson_to_polygon(feature.get("geometry"))))
        except Exception:
            continue
        repair = _find_parking_repair_footprint(
            footprint_utm,
            site_utm=site_utm,
            required_spaces=required,
            road_context=road_context,
            floors=int(float(props.get("num_floors") or 1)),
            building_type=building_type,
        )
        if repair is None:
            continue
        repaired_fp, repair_layout, repair_meta = repair
        repaired_fp = _strict_setback_footprint(repaired_fp, site_utm=site_utm, envelope=envelope)
        if repaired_fp.is_empty or repaired_fp.area < 8.0:
            continue
        signature = (
            round(float(repaired_fp.area), 1),
            round(float(repaired_fp.centroid.x), 1),
            round(float(repaired_fp.centroid.y), 1),
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        floors = int(float(props.get("num_floors") or 1))
        source_score = float(props.get("maas_score") or 0.0)
        source_iou = round(1.0 - diversity_score(repaired_fp, [], footprint_utm), 4)
        diversity = float(props.get("diversity_score") or 0.0)
        candidate = _mass_feature(
            operator="parking_repair_shrink",
            footprint_utm=repaired_fp,
            upper_footprint_utm=None,
            num_floors=max(1, floors),
            lower_floor_fraction=None,
            site_utm=site_utm,
            site_area_m2=site_area_m2,
            building_type=building_type,
            notes=(
                "parking_repair: reshape/translate footprint to fit required small-lot parking",
                f"parking_repair_method={repair_meta.get('method')}",
                f"parking_repair_scale=({repair_meta.get('scale_x')},{repair_meta.get('scale_y')})",
                f"parking_repair_offset_m=({repair_meta.get('dx')},{repair_meta.get('dy')})",
                f"parking_repair_layout_status={repair_layout.get('status')}",
            ),
            diversity=diversity,
            source_iou=source_iou,
        )
        cprops = candidate["properties"]
        if failed_constraint_metrics(cprops, envelope):
            continue
        cprops["maas_score"] = round(max(0.0, source_score - 0.18), 4)
        _attach_design_quality(candidate, repaired_fp)
        cprops["parking_repair"] = {
            "source_variant_id": props.get("variant_id"),
            "source_mass_shape": props.get("mass_shape"),
            "method": repair_meta.get("method"),
            "scale_factor": repair_meta.get("scale_factor"),
            "scale": {"x": repair_meta.get("scale_x"), "y": repair_meta.get("scale_y")},
            "offset_m": {"x": repair_meta.get("dx"), "y": repair_meta.get("dy")},
            "area_retention": repair_meta.get("area_retention"),
            "target_required_spaces": repair_meta.get("candidate_required_spaces", required),
            "preview_layout_status": repair_layout.get("status"),
            "preview_layout_mode": repair_layout.get("placement_mode"),
            "preview_adjacency": repair_layout.get("adjacency"),
            "authority_review": repair_layout.get("status") != "pass",
        }
        repaired.append(candidate)
        for section_candidate in _parking_preserving_section_candidates(
            repaired_fp,
            source_feature=feature,
            repair_layout=repair_layout,
            repair_meta=repair_meta,
            envelope=envelope,
            site_utm=site_utm,
            site_area_m2=site_area_m2,
            building_type=building_type,
            floors=floors,
            source_score=source_score,
            diversity=diversity,
            source_iou=source_iou,
        ):
            repaired.append(section_candidate)
        if floors >= 2 and footprint_utm.area > repaired_fp.area * 1.2:
            lifted_candidate = _mass_feature(
                operator="parking_repair_ground_void",
                footprint_utm=repaired_fp,
                upper_footprint_utm=footprint_utm,
                num_floors=max(2, floors),
                lower_floor_fraction=1.0 / max(2, floors),
                site_utm=site_utm,
                site_area_m2=site_area_m2,
                building_type=building_type,
                notes=(
                    "parking_repair: keep upper mass while reducing ground footprint for parking",
                    f"parking_repair_method={repair_meta.get('method')}",
                    f"parking_repair_scale=({repair_meta.get('scale_x')},{repair_meta.get('scale_y')})",
                    f"parking_repair_offset_m=({repair_meta.get('dx')},{repair_meta.get('dy')})",
                    f"parking_repair_layout_status={repair_layout.get('status')}",
                ),
                diversity=diversity,
                source_iou=source_iou,
            )
            lifted_props = lifted_candidate["properties"]
            if failed_constraint_metrics(lifted_props, envelope):
                continue
            lifted_props["maas_score"] = round(max(0.0, source_score - 0.08), 4)
            _attach_design_quality(lifted_candidate, repaired_fp)
            lifted_props["parking_repair"] = {
                **cprops["parking_repair"],
                "method": "ground_void_upper_mass",
                "base_method": repair_meta.get("method"),
                "upper_mass_retained": True,
                "upper_source_mass_shape": props.get("mass_shape"),
                "upper_floor_start": lifted_props.get("step_floor"),
            }
            repaired.append(lifted_candidate)
        break
    return repaired


def _strict_setback_footprint(footprint_utm, *, site_utm, envelope):
    min_setback = _strict_setback_limit_m(envelope)
    if min_setback <= 0:
        return footprint_utm
    if float(footprint_utm.distance(site_utm.boundary)) >= min_setback + 0.01:
        return footprint_utm
    strict_area = site_utm.buffer(-(min_setback + 0.02))
    if strict_area.is_empty:
        return footprint_utm
    adjusted = largest_polygon(footprint_utm.intersection(strict_area))
    return adjusted if not adjusted.is_empty else footprint_utm


def _strict_setback_limit_m(envelope) -> float:
    value = 0.0
    constraints = getattr(envelope, "constraint_values", {}) or {}
    for name in ("setback", "building_line_setback"):
        requirement, limit = constraints.get(name, ("", 0.0))
        if requirement == "Greater than":
            try:
                value = max(value, float(limit))
            except (TypeError, ValueError):
                pass
    return value


def _parking_preserving_section_candidates(
    parking_footprint_utm,
    *,
    source_feature: dict[str, Any],
    repair_layout: dict[str, Any],
    repair_meta: dict[str, Any],
    envelope,
    site_utm,
    site_area_m2: float,
    building_type: str,
    floors: int,
    source_score: float,
    diversity: float,
    source_iou: float,
) -> list[dict[str, Any]]:
    """Create section-diverse masses while keeping the proven parking footprint."""
    source_props = source_feature.get("properties") if isinstance(source_feature.get("properties"), dict) else {}
    upper_limit = getattr(envelope, "buildable_footprint", None)
    if upper_limit is None or upper_limit.is_empty:
        upper_limit = site_utm
    grammar_variants = [
        variant for variant in generate_grammar_variants(parking_footprint_utm)
        if variant.upper_footprint is not None
        or any(
            token in variant.operator
            for token in ("diagonal", "terrace", "sloped", "split", "bar", "podium", "overlap")
        )
    ]
    created: list[dict[str, Any]] = []
    seen: set[tuple[float, float, float]] = set()
    for variant in grammar_variants:
        operator = f"parking_repair_{variant.operator}"
        upper_source = variant.upper_footprint if variant.upper_footprint is not None else variant.footprint
        upper = _largest_polygon_or_none(upper_source.intersection(upper_limit).intersection(site_utm))
        if upper is None:
            continue
        if upper.is_empty or upper.area < 8.0:
            continue
        if not site_utm.buffer(1e-7).covers(upper):
            continue
        signature = (
            round(float(upper.area), 1),
            round(float(upper.centroid.x), 1),
            round(float(upper.centroid.y), 1),
        )
        if signature in seen:
            continue
        seen.add(signature)
        candidate = _mass_feature(
            operator=operator,
            footprint_utm=parking_footprint_utm,
            upper_footprint_utm=upper,
            num_floors=max(3, floors),
            lower_floor_fraction=variant.lower_floor_fraction,
            site_utm=site_utm,
            site_area_m2=site_area_m2,
            building_type=building_type,
            notes=(
                "parking_repair: preserve verified ground parking footprint while varying upper mass",
                f"parking_repair_method={repair_meta.get('method')}",
                f"parking_repair_layout_status={repair_layout.get('status')}",
                f"parking_preserve_operator={operator}",
                "parking_preserve_source=maas_grammar_sequence_library",
                *tuple(str(note) for note in variant.notes),
            ),
            diversity=diversity,
            source_iou=source_iou,
        )
        props = candidate["properties"]
        if failed_constraint_metrics(props, envelope):
            continue
        sequence_len = len(getattr(variant, "verb_sequence", ()) or ())
        score_penalty = min(0.14, 0.04 + max(0, sequence_len - 2) * 0.015)
        props["maas_score"] = round(max(0.0, source_score - score_penalty), 4)
        _apply_variant_verb_sequence(candidate, variant)
        _attach_design_quality(candidate, parking_footprint_utm)
        props["parking_repair"] = {
            "source_variant_id": source_props.get("variant_id"),
            "source_mass_shape": source_props.get("mass_shape"),
            "method": operator,
            "base_method": repair_meta.get("method"),
            "scale_factor": repair_meta.get("scale_factor"),
            "scale": {"x": repair_meta.get("scale_x"), "y": repair_meta.get("scale_y")},
            "offset_m": {"x": repair_meta.get("dx"), "y": repair_meta.get("dy")},
            "area_retention": repair_meta.get("area_retention"),
            "target_required_spaces": repair_meta.get("candidate_required_spaces"),
            "preview_layout_status": repair_layout.get("status"),
            "preview_layout_mode": repair_layout.get("placement_mode"),
            "preview_adjacency": repair_layout.get("adjacency"),
            "parking_footprint_preserved": True,
            "authority_review": repair_layout.get("status") != "pass",
        }
        created.append(candidate)
    return created


def _sync_parking_repair_metadata(features: list[dict[str, Any]]) -> None:
    for feature in features:
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        repair = props.get("parking_repair") if isinstance(props.get("parking_repair"), dict) else None
        precheck = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
        requirement = precheck.get("required_count") if isinstance(precheck.get("required_count"), dict) else {}
        layout = precheck.get("layout_candidate") if isinstance(precheck.get("layout_candidate"), dict) else {}
        if repair is None:
            continue
        final_required = _int_or_none(requirement.get("required_spaces"))
        final_provided = _int_or_none(layout.get("provided_spaces"))
        repair["final_required_spaces"] = final_required
        repair["final_provided_spaces"] = final_provided
        repair["final_layout_status"] = layout.get("status")
        repair["final_layout_mode"] = layout.get("placement_mode")
        repair["final_adjacency"] = layout.get("adjacency")
        repair["authority_review"] = bool(
            layout.get("turning_clearance", {}).get("authority_review")
            if isinstance(layout.get("turning_clearance"), dict)
            else layout.get("status") != "pass"
        )


def _find_parking_repair_footprint(
    footprint_utm,
    *,
    site_utm,
    required_spaces: int,
    road_context: dict[str, Any] | None,
    floors: int,
    building_type: str,
) -> tuple[Any, dict[str, Any], dict[str, Any]] | None:
    from design.maas.parking_layout import generate_parking_layout_candidate
    from design.maas.parking_strategy import _parking_drive_envelope, _parking_envelope

    best: tuple[tuple[Any, ...], Any, dict[str, Any], dict[str, Any]] | None = None
    source_area = float(footprint_utm.area or 0.0)
    for candidate_fp, meta in _iter_parking_repair_footprints(footprint_utm):
        if candidate_fp.is_empty or candidate_fp.area < 8.0:
            continue
        if not site_utm.buffer(1e-7).covers(candidate_fp):
            continue
        envelope = _parking_envelope(
            "ground_surface",
            footprint_utm=candidate_fp,
            site_utm=site_utm,
        )
        drive_envelope = _parking_drive_envelope(
            "ground_surface",
            footprint_utm=candidate_fp,
            site_utm=site_utm,
        )
        candidate_required = _estimate_candidate_repair_required_spaces(
            candidate_fp,
            floors=floors,
            building_type=building_type,
            fallback_required_spaces=required_spaces,
        )
        layout = generate_parking_layout_candidate(
            envelope,
            drive_envelope=drive_envelope,
            required_spaces=candidate_required,
            strategy="ground_surface",
            road_context=road_context,
        )
        provided = int(layout.get("provided_spaces") or 0)
        if provided < candidate_required:
            continue
        adjacency = layout.get("adjacency") if isinstance(layout.get("adjacency"), dict) else {}
        status = str(layout.get("status") or "")
        area_retention = float(candidate_fp.area / source_area) if source_area > 0 else 0.0
        meta = {
            **meta,
            "area_retention": round(area_retention, 4),
            "candidate_required_spaces": candidate_required,
        }
        score = (
            3 if status == "pass" else 2 if status in {"needs_drive_connectivity_review", "needs_swept_path_review"} else 0,
            1 if adjacency.get("row_contiguous_ok") else 0,
            1 if adjacency.get("contiguous_ok") else 0,
            round(area_retention, 4),
            1 if meta.get("method") in {"edge_notch", "axis_compress"} else 0,
            -float(meta.get("movement_m") or 0.0),
        )
        if best is None or score > best[0]:
            best = (score, candidate_fp, layout, meta)
    if best is None:
        return None
    _score, candidate_fp, layout, meta = best
    return candidate_fp, layout, meta


def _estimate_candidate_repair_required_spaces(
    footprint_utm,
    *,
    floors: int,
    building_type: str,
    fallback_required_spaces: int,
) -> int:
    if not _is_common_housing(building_type):
        return fallback_required_spaces
    floor_count = max(1, floors)
    footprint_area = float(getattr(footprint_utm, "area", 0.0) or 0.0)
    if footprint_area <= 0:
        return fallback_required_spaces
    exclusive_area_per_unit = footprint_area * 0.75
    total_exclusive_area = exclusive_area_per_unit * floor_count
    area_ratio_spaces = total_exclusive_area / 75.0
    if exclusive_area_per_unit <= 30.0:
        min_per_unit = 0.5
    elif exclusive_area_per_unit <= 60.0:
        min_per_unit = 0.8
    else:
        min_per_unit = 1.0
    household_min_spaces = floor_count * min_per_unit
    return max(1, int(__import__("math").ceil(max(area_ratio_spaces, household_min_spaces))))


def _iter_parking_repair_footprints(footprint_utm) -> list[tuple[Any, dict[str, Any]]]:
    candidates: list[tuple[Any, dict[str, Any]]] = []
    offsets = (0.0, -4.0, 4.0, -8.0, 8.0)

    def add_scaled(method: str, sx: float, sy: float) -> None:
        scaled = shapely_scale(footprint_utm, xfact=sx, yfact=sy, origin="centroid")
        for dx in offsets:
            for dy in offsets:
                moved = shapely_translate(scaled, xoff=dx, yoff=dy)
                candidates.append((moved, {
                    "method": method,
                    "scale_factor": round(min(sx, sy), 4),
                    "scale_x": sx,
                    "scale_y": sy,
                    "dx": dx,
                    "dy": dy,
                    "movement_m": abs(dx) + abs(dy),
                }))

    for factor in (0.74, 0.66, 0.58, 0.50):
        add_scaled("uniform_shrink", factor, factor)
    for factor in (0.82, 0.74, 0.66, 0.58):
        add_scaled("axis_compress", factor, 1.0)
        add_scaled("axis_compress", 1.0, factor)

    minx, miny, maxx, maxy = footprint_utm.bounds
    span_x = maxx - minx
    span_y = maxy - miny
    strip_specs = [
        ("west", minx, miny, minx + width, maxy)
        for width in (2.0, 3.5, 5.0, 6.5, 8.0)
        if width < span_x
    ] + [
        ("east", maxx - width, miny, maxx, maxy)
        for width in (2.0, 3.5, 5.0, 6.5, 8.0)
        if width < span_x
    ] + [
        ("south", minx, miny, maxx, miny + depth)
        for depth in (2.0, 3.5, 5.0, 6.5, 8.0)
        if depth < span_y
    ] + [
        ("north", minx, maxy - depth, maxx, maxy)
        for depth in (2.0, 3.5, 5.0, 6.5, 8.0)
        if depth < span_y
    ]
    for edge, a, b, c, d in strip_specs:
        cut = box(a, b, c, d)
        diff = footprint_utm.difference(cut)
        repaired = largest_polygon(diff)
        if repaired.is_empty:
            continue
        for dx in (0.0, -4.0, 4.0):
            for dy in (0.0, -4.0, 4.0):
                moved = shapely_translate(repaired, xoff=dx, yoff=dy)
                candidates.append((moved, {
                    "method": "edge_notch",
                    "edge": edge,
                    "scale_factor": None,
                    "scale_x": 1.0,
                    "scale_y": 1.0,
                    "dx": dx,
                    "dy": dy,
                    "movement_m": abs(dx) + abs(dy),
                }))
    return candidates


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _parking_options_for_feature(options: dict[str, Any], props: dict[str, Any], building_type: str) -> dict[str, Any]:
    result = dict(options)
    if result.get("housing_unit_schedule") or not _is_common_housing(building_type):
        return result
    schedule = _estimate_housing_unit_schedule(props)
    if schedule:
        result["housing_unit_schedule"] = schedule
        result.setdefault("jurisdiction_type", "special_city")
    return result


def _is_common_housing(building_type: str) -> bool:
    text = building_type or ""
    return any(token in text for token in ("공동주택", "아파트", "연립", "다세대"))


def _estimate_housing_unit_schedule(props: dict[str, Any]) -> list[dict[str, Any]]:
    plates = props.get("floor_plates")
    if not isinstance(plates, list) or not plates:
        model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
        plates = model.get("floor_plates") if isinstance(model.get("floor_plates"), list) else []
    if not isinstance(plates, list) or not plates:
        footprint_area = _float_or_none(props.get("footprint_area"))
        floor_area = _float_or_none(props.get("floor_area"))
        floors = int(_float_or_none(props.get("num_floors")) or 0)
        if floors > 0 and floor_area and floor_area > 0:
            average_floor_area = floor_area / floors
            plates = [{"floor": floor, "area_m2": average_floor_area} for floor in range(1, floors + 1)]
        elif footprint_area and footprint_area > 0 and floors > 0:
            plates = [{"floor": floor, "area_m2": footprint_area} for floor in range(1, floors + 1)]
    schedule: list[dict[str, Any]] = []
    exclusive_ratio = 0.75
    for plate in plates:
        if not isinstance(plate, dict):
            continue
        area = _float_or_none(plate.get("area") or plate.get("area_m2"))
        floor = int(_float_or_none(plate.get("floor")) or len(schedule) + 1)
        if area is None or area <= 0:
            continue
        schedule.append({
            "unit_type": f"F{floor:02d}",
            "count": 1,
            "exclusive_area_m2": round(area * exclusive_ratio, 2),
            "gross_floor_plate_area_m2": round(area, 2),
            "exclusive_area_ratio": exclusive_ratio,
            "source": "mass_stage_estimate",
        })
    return schedule


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parking_priority_key(feature: dict[str, Any]) -> tuple[int, int, int, float, float, float]:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    precheck = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
    layout = precheck.get("layout_candidate") if isinstance(precheck.get("layout_candidate"), dict) else {}
    required = layout.get("required_spaces")
    provided = layout.get("provided_spaces")
    unmet = layout.get("unmet_spaces")
    status = layout.get("status")
    mass_stage = layout.get("mass_stage_parking") if isinstance(layout.get("mass_stage_parking"), dict) else {}
    if isinstance(required, int) and required > 0 and isinstance(provided, int):
        satisfied = int(provided >= required and (not isinstance(unmet, int) or unmet == 0))
    else:
        satisfied = 0
    status_rank = (
        3 if status == "pass" and isinstance(required, int) and required > 0
        else 2 if mass_stage.get("status") == "pass"
        else 1 if status in {
            "needs_drive_connectivity_review",
            "needs_aisle_review",
            "needs_swept_path_review",
            "needs_mechanical_parking_review",
        }
        else 0
    )
    repair = props.get("parking_repair") if isinstance(props.get("parking_repair"), dict) else None
    repair_rank = 0 if repair else 1
    floor_area = float(props.get("floor_area") or 0.0)
    footprint_area = float(props.get("footprint_area") or 0.0)
    return (
        satisfied,
        status_rank,
        repair_rank,
        float(props.get("maas_score") or 0.0),
        floor_area,
        footprint_area,
    )


def _review_diversity_priority_key(feature: dict[str, Any]) -> tuple[int, float, float, float]:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    diversity = props.get("candidate_diversity") if isinstance(props.get("candidate_diversity"), dict) else {}
    class_rank = {
        "plan_diverse": 3,
        "near_duplicate": 2,
        "section_diverse": 1,
    }.get(diversity.get("class"), 0)
    return (
        class_rank,
        float(props.get("diversity_score") or 0.0),
        float(props.get("maas_score") or 0.0),
        float(props.get("floor_area") or 0.0),
    )


__all__ = ["generate_legal_mass_variants"]
