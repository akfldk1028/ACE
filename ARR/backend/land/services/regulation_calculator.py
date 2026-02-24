"""
Regulation Calculator - computes all 10 building regulations from zone data.

Given zone names, resolves BCR, FAR, height limit, sunlight setback,
road diagonal, corner cutoff, building line, adjacent setback, parking,
and landscaping regulations. When multiple zones apply, the strictest values are used.
"""

import logging

from land.services import zoning_mapper

logger = logging.getLogger(__name__)


def calculate_all(zone_names: list[str], land_info: dict | None = None) -> dict:
    """
    Compute all 10 regulations from zone names.

    Args:
        zone_names: list of exact zone names (e.g. ["제1종일반주거지역"])
        land_info: optional dict with land_area_m2, etc.

    Returns dict with keys matching LandAnalysisResult fields.
    """
    zones_data = [
        zoning_mapper.lookup(z) for z in zone_names
        if zoning_mapper.lookup(z) is not None
    ]

    if not zones_data:
        return _empty_result()

    result = {}
    result.update(_resolve_bcr_far(zones_data))
    result.update(_resolve_height(zones_data))
    result.update(_resolve_sunlight(zones_data))
    result.update(_resolve_corner_cutoff(zones_data))
    result.update(_resolve_road_diagonal(zones_data))
    result.update(_resolve_building_line(zones_data))
    result.update(_resolve_adjacent_setback(zones_data))
    result.update(_resolve_parking(zones_data))
    result.update(_resolve_landscaping(zones_data, land_info))
    result["zone_category"] = zones_data[0].get("category", "")
    result["matched_zones"] = [z["zone_name"] for z in zones_data]
    result["unmatched_zones"] = [
        z for z in zone_names if z not in result["matched_zones"]
    ]

    return result


def _empty_result() -> dict:
    return {
        "bcr_pct": None, "bcr_article": "",
        "far_pct": None, "far_article": "",
        "height_limit_m": None, "height_article": "",
        "sunlight_applies": False, "sunlight_rules": [], "sunlight_article": "",
        "corner_cutoff_required": False, "corner_cutoff_article": "",
        "road_diagonal_multiplier": None, "road_diagonal_rule": "",
        "road_diagonal_article": "",
        "building_line_setback_m": None, "building_line_article": "",
        "adjacent_setback_m": None, "adjacent_setback_article": "",
        "parking_rule": "", "parking_article": "",
        "landscaping_threshold_m2": None, "landscaping_min_pct": None,
        "landscaping_article": "",
        "zone_category": "",
        "matched_zones": [],
        "unmatched_zones": [],
    }


def _resolve_bcr_far(zones_data: list[dict]) -> dict:
    """BCR/FAR: use strictest (lowest) across zones."""
    bcr = min(z["bcr_default"] for z in zones_data)
    far = min(z["far_default"] for z in zones_data)

    bcr_articles = list({z["bcr_article"] for z in zones_data})
    far_articles = list({z["far_article"] for z in zones_data})

    return {
        "bcr_pct": bcr,
        "bcr_article": "; ".join(bcr_articles),
        "far_pct": far,
        "far_article": "; ".join(far_articles),
    }


def _resolve_height(zones_data: list[dict]) -> dict:
    """Height limit: use strictest (lowest non-null)."""
    heights = [z["height_limit_m"] for z in zones_data if z.get("height_limit_m") is not None]
    articles = list({z.get("height_limit_article", "") for z in zones_data if z.get("height_limit_article")})

    return {
        "height_limit_m": min(heights) if heights else None,
        "height_article": "; ".join(articles) if articles else "",
    }


def _resolve_sunlight(zones_data: list[dict]) -> dict:
    """Sunlight setback: applies if ANY zone requires it."""
    applies = any(
        z.get("sunlight_setback", {}).get("applies", False)
        for z in zones_data
    )

    if not applies:
        articles = list({
            z.get("sunlight_setback", {}).get("article", "")
            for z in zones_data
            if z.get("sunlight_setback", {}).get("article")
        })
        return {
            "sunlight_applies": False,
            "sunlight_rules": [],
            "sunlight_article": "; ".join(articles) if articles else "",
        }

    # Use rules from the first zone that applies
    for z in zones_data:
        ss = z.get("sunlight_setback", {})
        if ss.get("applies"):
            return {
                "sunlight_applies": True,
                "sunlight_rules": ss.get("rules", []),
                "sunlight_article": ss.get("article", ""),
            }

    return {"sunlight_applies": False, "sunlight_rules": [], "sunlight_article": ""}


def _resolve_corner_cutoff(zones_data: list[dict]) -> dict:
    """Corner cutoff: required if ANY zone requires it."""
    required = any(
        z.get("corner_cutoff", {}).get("required", False)
        for z in zones_data
    )
    articles = list({
        z.get("corner_cutoff", {}).get("article", "")
        for z in zones_data
        if z.get("corner_cutoff", {}).get("article")
    })

    return {
        "corner_cutoff_required": required,
        "corner_cutoff_article": "; ".join(articles) if articles else "",
    }


def _resolve_road_diagonal(zones_data: list[dict]) -> dict:
    """Road diagonal: use strictest (lowest multiplier)."""
    multipliers = [
        z.get("road_diagonal", {}).get("multiplier")
        for z in zones_data
        if z.get("road_diagonal", {}).get("multiplier") is not None
    ]
    notes = [
        z.get("road_diagonal", {}).get("note", "")
        for z in zones_data
        if z.get("road_diagonal", {}).get("note")
    ]
    articles = list({
        z.get("road_diagonal", {}).get("article", "")
        for z in zones_data
        if z.get("road_diagonal", {}).get("article")
    })

    return {
        "road_diagonal_multiplier": min(multipliers) if multipliers else None,
        "road_diagonal_rule": notes[0] if notes else "",
        "road_diagonal_article": "; ".join(articles) if articles else "",
    }


def _resolve_building_line(zones_data: list[dict]) -> dict:
    """Building line: rule text only (site-specific calculation in Phase 3+)."""
    articles = list({
        z.get("building_line_article", "")
        for z in zones_data
        if z.get("building_line_article")
    })

    return {
        "building_line_setback_m": None,
        "building_line_article": "; ".join(articles) if articles else "",
    }


def _resolve_adjacent_setback(zones_data: list[dict]) -> dict:
    """Adjacent setback: use strictest (largest setback)."""
    setbacks = [
        z.get("adjacent_setback_m")
        for z in zones_data
        if z.get("adjacent_setback_m") is not None
    ]
    articles = list({
        z.get("adjacent_setback_article", "")
        for z in zones_data
        if z.get("adjacent_setback_article")
    })

    return {
        "adjacent_setback_m": max(setbacks) if setbacks else None,
        "adjacent_setback_article": "; ".join(articles) if articles else "",
    }


def _resolve_parking(zones_data: list[dict]) -> dict:
    """Parking: rule text only (usage-dependent, not zone-dependent)."""
    articles = list({
        z.get("parking_article", "")
        for z in zones_data
        if z.get("parking_article")
    })

    return {
        "parking_rule": "용도별 주차대수 산정 (주차장법 시행령 별표1)",
        "parking_article": "; ".join(articles) if articles else "",
    }


def _resolve_landscaping(zones_data: list[dict], land_info: dict | None = None) -> dict:
    """Landscaping: use strictest (highest min_pct)."""
    thresholds = []
    pcts = []
    articles_set = set()

    for z in zones_data:
        ls = z.get("landscaping", {})
        if ls.get("threshold_m2") is not None:
            thresholds.append(ls["threshold_m2"])
        if ls.get("min_pct") is not None:
            pcts.append(ls["min_pct"])
        if ls.get("article"):
            articles_set.add(ls["article"])

    return {
        "landscaping_threshold_m2": min(thresholds) if thresholds else None,
        "landscaping_min_pct": max(pcts) if pcts else None,
        "landscaping_article": "; ".join(articles_set) if articles_set else "",
    }
