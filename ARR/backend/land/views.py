"""
Land Regulation Analysis API v2

Analyzes land parcels for 10 building regulations (BCR, FAR, height, sunlight,
corner cutoff, road diagonal, building line, adjacent setback, parking, landscaping)
with legal article references.
"""

import json
import logging
import time

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from land.models import LandQuery, LandAnalysisResult
from land.services import pnu_resolver, zoning_mapper, land_api, law_enricher
from land.services import regulation_calculator

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    """
    POST /land/analyze/

    Main analysis endpoint. Accepts PNU, address, or raw zone list.
    Returns 10 building regulations with legal article references.

    Body: {
        "input": "1168011200101280003" | "서울시 강남구 ...",
        "input_type": "pnu" | "address" | "raw",
        "zones": ["제1종일반주거지역"],     # required if input_type=raw, optional override
        "include_law": true                 # default true, fetch law articles
    }
    """
    try:
        body = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    raw_input = body.get("input", "")
    input_type = body.get("input_type", "pnu")
    manual_zones = body.get("zones", [])
    include_law = body.get("include_law", True)

    # Input validation
    if not isinstance(raw_input, str):
        return JsonResponse({"error": '"input" must be a string'}, status=400)
    if len(raw_input) > 500:
        return JsonResponse({"error": '"input" too long (max 500)'}, status=400)
    if not isinstance(manual_zones, list) or not all(isinstance(z, str) for z in manual_zones):
        return JsonResponse({"error": '"zones" must be a list of strings'}, status=400)

    if not raw_input and not manual_zones:
        return JsonResponse(
            {"error": 'Either "input" or "zones" is required'},
            status=400,
        )

    if input_type not in ("pnu", "address", "raw"):
        return JsonResponse(
            {"error": f'Invalid input_type: {input_type}. Use pnu/address/raw'},
            status=400,
        )

    start = time.time()
    errors = []
    pnu_info = None
    land_info = None
    zone_names = list(manual_zones)

    # Step 1: Resolve PNU
    if input_type == "pnu" and raw_input:
        if not pnu_resolver.validate_pnu(raw_input):
            return JsonResponse(
                {"error": f"Invalid PNU format (expected 19 digits): {raw_input}"},
                status=400,
            )
        pnu_info = pnu_resolver.parse_pnu(raw_input)
    elif input_type == "address" and raw_input:
        result = pnu_resolver.resolve_address(raw_input)
        if not result["success"]:
            errors.append(result["error"])
        else:
            pnu_info = pnu_resolver.parse_pnu(result["pnu"])

    # Step 2: Fetch land use info from data.go.kr (stub)
    if pnu_info:
        land_info = land_api.get_land_use_info(pnu_info["pnu"])
        if land_info["success"] and land_info["zones"]:
            if not zone_names:
                zone_names = land_info["zones"]

    # Step 3: No zones → warning
    if not zone_names:
        elapsed_ms = (time.time() - start) * 1000
        _log_query(input_type, raw_input, pnu_info, None, land_info, 0, elapsed_ms,
                    error="No zones provided or resolved")
        return JsonResponse({
            "pnu": pnu_info,
            "regulations": None,
            "zone_info": None,
            "land_info": land_info,
            "law_articles": None,
            "restrictions": [],
            "warning": "No zoning zones provided or resolved. "
                       "Pass 'zones' array or wait for data.go.kr API integration.",
        })

    # Step 4: Calculate all 10 regulations
    reg = regulation_calculator.calculate_all(zone_names, land_info)

    # Step 5: Fetch law articles
    law_articles = None
    if include_law:
        law_articles = law_enricher.search_for_zones(zone_names)
        if law_articles["errors"]:
            errors.extend(law_articles["errors"])

    # Step 6: Save LandAnalysisResult
    analysis_result = _save_analysis_result(pnu_info, zone_names, reg, law_articles, land_info)

    # Step 7: Build restrictions summary
    restrictions = _build_restrictions(reg, zone_names)

    elapsed_ms = (time.time() - start) * 1000

    _log_query(
        input_type, raw_input, pnu_info, reg,
        land_info, law_articles["total_count"] if law_articles else 0,
        elapsed_ms, error="; ".join(errors) if errors else "",
        analysis_result=analysis_result,
    )

    # Build zone info from zoning_mapper for backward compat
    zone_info = zoning_mapper.resolve_limits(zone_names)

    response = {
        "pnu": pnu_info,
        "regulations": _format_regulations(reg),
        "zone_info": zone_info,
        "land_info": land_info,
        "law_articles": law_articles,
        "restrictions": restrictions,
    }
    if errors:
        response["errors"] = errors

    return JsonResponse(response)


@csrf_exempt
@require_http_methods(["POST"])
def resolve(request):
    """
    POST /land/resolve/

    Resolve address to PNU or validate/parse PNU.

    Body: {"input": "...", "input_type": "pnu" | "address"}
    """
    try:
        body = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    raw_input = body.get("input", "")
    input_type = body.get("input_type", "pnu")

    if not raw_input:
        return JsonResponse({"error": '"input" is required'}, status=400)

    if input_type == "pnu":
        if not pnu_resolver.validate_pnu(raw_input):
            return JsonResponse({"error": "Invalid PNU format", "valid": False}, status=400)
        return JsonResponse({
            "valid": True,
            "parsed": pnu_resolver.parse_pnu(raw_input),
        })
    elif input_type == "address":
        result = pnu_resolver.resolve_address(raw_input)
        return JsonResponse(result)
    else:
        return JsonResponse({"error": f"Unknown input_type: {input_type}"}, status=400)


@require_http_methods(["GET"])
def zones(request):
    """
    GET /land/zones/

    Return all zoning zone definitions with BCR/FAR limits.
    """
    all_zones = zoning_mapper.get_all_zones()
    return JsonResponse({"zones": all_zones, "count": len(all_zones)})


@require_http_methods(["GET"])
def stats(request):
    """
    GET /land/stats/

    Return query statistics from LandQuery audit log.
    """
    from django.db.models import Avg, Count

    logs = LandQuery.objects.all()
    total = logs.count()
    avg_time = logs.aggregate(avg=Avg("response_time_ms"))["avg"] or 0
    by_type = (
        logs.values("input_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    error_count = logs.exclude(error="").count()

    return JsonResponse({
        "total_queries": total,
        "avg_response_time_ms": round(avg_time, 2),
        "by_input_type": list(by_type),
        "error_count": error_count,
    })


def _format_regulations(reg: dict) -> dict:
    """Format regulation_calculator output into API response structure."""
    return {
        "bcr": {
            "limit_pct": reg.get("bcr_pct"),
            "article": reg.get("bcr_article", ""),
        },
        "far": {
            "limit_pct": reg.get("far_pct"),
            "article": reg.get("far_article", ""),
        },
        "height": {
            "limit_m": reg.get("height_limit_m"),
            "rule": "가로구역별 높이제한 적용",
            "article": reg.get("height_article", ""),
        },
        "sunlight_setback": {
            "applies": reg.get("sunlight_applies", False),
            "direction": "정북방향" if reg.get("sunlight_applies") else None,
            "rules": reg.get("sunlight_rules", []),
            "article": reg.get("sunlight_article", ""),
        },
        "corner_cutoff": {
            "required": reg.get("corner_cutoff_required", False),
            "rule": "6m+ 도로 교차시 적용" if reg.get("corner_cutoff_required") else None,
            "article": reg.get("corner_cutoff_article", ""),
        },
        "road_diagonal": {
            "multiplier": reg.get("road_diagonal_multiplier"),
            "rule": reg.get("road_diagonal_rule", ""),
            "article": reg.get("road_diagonal_article", ""),
        },
        "building_line": {
            "setback_m": reg.get("building_line_setback_m"),
            "rule": "도로경계선 후퇴 (조례에 따름)",
            "article": reg.get("building_line_article", ""),
        },
        "adjacent_setback": {
            "min_m": reg.get("adjacent_setback_m"),
            "article": reg.get("adjacent_setback_article", ""),
        },
        "parking": {
            "rule": reg.get("parking_rule", ""),
            "article": reg.get("parking_article", ""),
        },
        "landscaping": {
            "threshold_m2": reg.get("landscaping_threshold_m2"),
            "min_pct": reg.get("landscaping_min_pct"),
            "article": reg.get("landscaping_article", ""),
        },
    }


def _build_restrictions(reg: dict, zone_names: list[str]) -> list[str]:
    """Build a human-readable list of key restrictions."""
    restrictions = []

    bcr = reg.get("bcr_pct")
    far = reg.get("far_pct")

    if bcr is not None:
        restrictions.append(f"건폐율 상한: {bcr}%")
    if far is not None:
        restrictions.append(f"용적률 상한: {far}%")

    if reg.get("sunlight_applies"):
        restrictions.append("일조사선: 정북방향 H/2 이격")

    if reg.get("road_diagonal_multiplier") is not None:
        restrictions.append(
            f"도로사선: 전면도로폭 × {reg['road_diagonal_multiplier']}"
        )

    if reg.get("corner_cutoff_required"):
        restrictions.append("가각전제: 6m+ 도로 교차시 적용")

    if reg.get("adjacent_setback_m") is not None:
        restrictions.append(f"인접대지 이격: {reg['adjacent_setback_m']}m 이상")

    if reg.get("landscaping_min_pct") is not None:
        restrictions.append(f"조경: 대지면적의 {reg['landscaping_min_pct']}% 이상")

    if len(zone_names) > 1:
        restrictions.append(
            f"복수 용도지역 적용 ({len(zone_names)}개) - 최엄격 기준 적용 (국토계획법 제76-77조)"
        )

    cat = reg.get("zone_category", "")
    if "녹지" in cat:
        restrictions.append("건축물 용도 제한 (녹지지역)")
    elif "공업" in cat:
        restrictions.append("환경오염 관련 규제 주의 (공업지역)")

    if reg.get("unmatched_zones"):
        restrictions.append(
            f"미인식 용도지역: {', '.join(reg['unmatched_zones'])} (수동 확인 필요)"
        )

    return restrictions


def _save_analysis_result(pnu_info, zone_names, reg, law_articles, land_info):
    """Save LandAnalysisResult (non-fatal on failure)."""
    try:
        return LandAnalysisResult.objects.create(
            pnu=pnu_info["pnu"] if pnu_info else "",
            address=pnu_info.get("address", "") if pnu_info else "",
            coordinate_x=pnu_info.get("coordinate_x") if pnu_info else None,
            coordinate_y=pnu_info.get("coordinate_y") if pnu_info else None,
            zones=zone_names,
            zone_category=reg.get("zone_category", ""),
            land_area_m2=land_info.get("land_area_m2") if land_info else None,
            official_land_price=land_info.get("official_land_price") if land_info else None,
            bcr_pct=reg.get("bcr_pct"),
            bcr_article=reg.get("bcr_article", ""),
            far_pct=reg.get("far_pct"),
            far_article=reg.get("far_article", ""),
            height_limit_m=reg.get("height_limit_m"),
            height_article=reg.get("height_article", ""),
            sunlight_applies=reg.get("sunlight_applies", False),
            sunlight_rules=reg.get("sunlight_rules", []),
            sunlight_article=reg.get("sunlight_article", ""),
            corner_cutoff_required=reg.get("corner_cutoff_required", False),
            corner_cutoff_article=reg.get("corner_cutoff_article", ""),
            road_diagonal_multiplier=reg.get("road_diagonal_multiplier"),
            road_diagonal_rule=reg.get("road_diagonal_rule", ""),
            road_diagonal_article=reg.get("road_diagonal_article", ""),
            building_line_setback_m=reg.get("building_line_setback_m"),
            building_line_article=reg.get("building_line_article", ""),
            adjacent_setback_m=reg.get("adjacent_setback_m"),
            adjacent_setback_article=reg.get("adjacent_setback_article", ""),
            parking_rule=reg.get("parking_rule", ""),
            parking_article=reg.get("parking_article", ""),
            landscaping_threshold_m2=reg.get("landscaping_threshold_m2"),
            landscaping_min_pct=reg.get("landscaping_min_pct"),
            landscaping_article=reg.get("landscaping_article", ""),
            law_articles_json=law_articles.get("articles", []) if law_articles else [],
            law_article_count=law_articles.get("total_count", 0) if law_articles else 0,
            data_source="static",
        )
    except Exception as e:
        logger.warning(f"LandAnalysisResult save failed (non-fatal): {e}")
        return None


def _log_query(input_type, raw_input, pnu_info, reg, land_info,
               law_count, elapsed_ms, error="", analysis_result=None):
    """Save audit log (non-fatal on failure)."""
    try:
        LandQuery.objects.create(
            input_type=input_type,
            raw_input=raw_input[:500],
            resolved_pnu=pnu_info["pnu"] if pnu_info else "",
            zoning_zones=reg.get("matched_zones", []) if reg else [],
            building_coverage_limit=reg.get("bcr_pct") if reg else None,
            floor_area_limit=reg.get("far_pct") if reg else None,
            land_area_m2=land_info.get("land_area_m2") if land_info else None,
            official_land_price=land_info.get("official_land_price") if land_info else None,
            law_article_count=law_count,
            analysis_result=analysis_result,
            response_time_ms=round(elapsed_ms, 2),
            error=error,
        )
    except Exception as e:
        logger.warning(f"LandQuery save failed (non-fatal): {e}")
