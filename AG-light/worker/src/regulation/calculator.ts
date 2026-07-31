/**
 * Regulation Calculator — computes 11 building regulations from zone data.
 * Port of: ARR/backend/land/services/regulation_calculator.py
 *
 * When multiple zones apply, the strictest values are used.
 * LLM extraction is deferred to Phase 2.
 */

import { lookup, type ZoneDefinition } from "../land/zoning-mapper";
import { applyOrdinanceOverrides } from "./ordinance";

export interface RegulationResult {
  bcr_pct: number | null;
  bcr_article: string;
  far_pct: number | null;
  far_article: string;
  height_limit_m: number | null;
  height_article: string;
  sunlight_applies: boolean;
  sunlight_rules: Array<{ condition: string; setback_m?: number; formula?: string }>;
  sunlight_article: string;
  corner_cutoff_required: boolean;
  corner_cutoff_m: number | null;
  corner_cutoff_article: string;
  road_diagonal_multiplier: number | null;
  road_diagonal_rule: string;
  road_diagonal_article: string;
  building_line_setback_m: number | null;
  building_line_article: string;
  adjacent_setback_m: number | null;
  adjacent_setback_article: string;
  parking_rule: string;
  parking_article: string;
  landscaping_threshold_m2: number | null;
  landscaping_min_pct: number | null;
  landscaping_article: string;
  building_designation_applies: boolean;
  building_designation_setback_m: number | null;
  building_designation_article: string;
  building_designation_source: string;
  sunlight_source: string;
  adjacent_setback_source: string;
  zone_category: string;
  matched_zones: string[];
  unmatched_zones: string[];
}

const EMPTY: RegulationResult = {
  bcr_pct: null, bcr_article: "",
  far_pct: null, far_article: "",
  height_limit_m: null, height_article: "",
  sunlight_applies: false, sunlight_rules: [], sunlight_article: "",
  corner_cutoff_required: false, corner_cutoff_m: null, corner_cutoff_article: "",
  road_diagonal_multiplier: null, road_diagonal_rule: "", road_diagonal_article: "",
  building_line_setback_m: null, building_line_article: "",
  adjacent_setback_m: null, adjacent_setback_article: "",
  parking_rule: "", parking_article: "",
  landscaping_threshold_m2: null, landscaping_min_pct: null, landscaping_article: "",
  building_designation_applies: false, building_designation_setback_m: null,
  building_designation_article: "", building_designation_source: "",
  sunlight_source: "", adjacent_setback_source: "",
  zone_category: "", matched_zones: [], unmatched_zones: [],
};

export function calculateAll(
  zoneNames: string[],
  _landInfo: Record<string, unknown> | null,
  sigunguCode: string,
): RegulationResult {
  let zonesData = zoneNames
    .map((z) => lookup(z))
    .filter((z): z is ZoneDefinition => z !== undefined);

  if (zonesData.length === 0) {
    return { ...EMPTY, unmatched_zones: [...zoneNames] };
  }

  // Apply ordinance overrides (e.g., 강남구 조례)
  if (sigunguCode) {
    zonesData = applyOrdinanceOverrides(
      zonesData as unknown as Record<string, unknown>[],
      sigunguCode,
    ) as unknown as ZoneDefinition[];
  }

  return {
    ...resolveBcrFar(zonesData),
    ...resolveHeight(zonesData),
    ...resolveSunlight(zonesData),
    ...resolveCornerCutoff(zonesData),
    ...resolveRoadDiagonal(zonesData),
    ...resolveBuildingLine(zonesData),
    ...resolveAdjacentSetback(zonesData),
    ...resolveParking(zonesData),
    ...resolveLandscaping(zonesData),
    ...resolveBuildingDesignation(zoneNames),
    zone_category: zonesData[0].category,
    matched_zones: zonesData.map((z) => z.zone_name),
    unmatched_zones: zoneNames.filter(
      (n) => !zonesData.some((z) => z.zone_name === n),
    ),
  };
}

// ── Helpers ──

function uniqueArticles(zones: ZoneDefinition[], key: keyof ZoneDefinition | ((z: ZoneDefinition) => string)): string {
  const getter = typeof key === "function" ? key : (z: ZoneDefinition) => z[key] as string;
  const seen = new Set<string>();
  const result: string[] = [];
  for (const z of zones) {
    const v = getter(z);
    if (v && !seen.has(v)) { seen.add(v); result.push(v); }
  }
  return result.join("; ");
}

function resolveBcrFar(zones: ZoneDefinition[]) {
  return {
    bcr_pct: Math.min(...zones.map((z) => z.bcr_default)),
    bcr_article: uniqueArticles(zones, "bcr_article"),
    far_pct: Math.min(...zones.map((z) => z.far_default)),
    far_article: uniqueArticles(zones, "far_article"),
  };
}

function resolveHeight(zones: ZoneDefinition[]) {
  const heights = zones
    .map((z) => z.height_limit_m)
    .filter((h): h is number => h !== null);
  return {
    height_limit_m: heights.length > 0 ? Math.min(...heights) : null,
    height_article: uniqueArticles(zones, "height_limit_article"),
  };
}

function resolveSunlight(zones: ZoneDefinition[]) {
  const applicable = zones.find((z) => z.sunlight_setback?.applies);
  if (!applicable) {
    return {
      sunlight_applies: false,
      sunlight_rules: [] as Array<{ condition: string; setback_m?: number; formula?: string }>,
      sunlight_article: uniqueArticles(zones, (z) => z.sunlight_setback?.article ?? ""),
      sunlight_source: "",
    };
  }
  return {
    sunlight_applies: true,
    sunlight_rules: applicable.sunlight_setback.rules,
    sunlight_article: applicable.sunlight_setback.article,
    sunlight_source: "static_json",
  };
}

function resolveCornerCutoff(zones: ZoneDefinition[]) {
  const required = zones.some((z) => z.corner_cutoff?.required);
  const cutoffs = zones
    .map((z) => (z.corner_cutoff as { default_cutoff_m?: number })?.default_cutoff_m)
    .filter((v): v is number => v != null);
  return {
    corner_cutoff_required: required,
    corner_cutoff_m: cutoffs.length > 0 ? Math.max(...cutoffs) : null,
    corner_cutoff_article: uniqueArticles(zones, (z) => z.corner_cutoff?.article ?? ""),
  };
}

function resolveRoadDiagonal(zones: ZoneDefinition[]) {
  const multipliers = zones
    .map((z) => z.road_diagonal?.multiplier)
    .filter((v): v is number => v != null);
  const notes = zones
    .map((z) => z.road_diagonal?.note)
    .filter((v): v is string => !!v);
  return {
    road_diagonal_multiplier: multipliers.length > 0 ? Math.min(...multipliers) : null,
    road_diagonal_rule: notes[0] ?? "",
    road_diagonal_article: uniqueArticles(zones, (z) => z.road_diagonal?.article ?? ""),
  };
}

function resolveBuildingLine(zones: ZoneDefinition[]) {
  return {
    building_line_setback_m: null as number | null,
    building_line_article: uniqueArticles(zones, "building_line_article"),
  };
}

function resolveAdjacentSetback(zones: ZoneDefinition[]) {
  const setbacks = zones
    .map((z) => z.adjacent_setback_m)
    .filter((v): v is number => v != null);
  return {
    adjacent_setback_m: setbacks.length > 0 ? Math.max(...setbacks) : null,
    adjacent_setback_article: uniqueArticles(zones, "adjacent_setback_article"),
    adjacent_setback_source: "static_json",
  };
}

function resolveParking(zones: ZoneDefinition[]) {
  return {
    parking_rule: "용도별 주차대수 산정 (주차장법 시행령 별표1)",
    parking_article: uniqueArticles(zones, "parking_article"),
  };
}

function resolveLandscaping(zones: ZoneDefinition[]) {
  const thresholds = zones
    .map((z) => z.landscaping?.threshold_m2)
    .filter((v): v is number => v != null);
  const pcts = zones
    .map((z) => z.landscaping?.min_pct)
    .filter((v): v is number => v != null);
  const articles = new Set(
    zones.map((z) => z.landscaping?.article).filter(Boolean),
  );
  return {
    landscaping_threshold_m2: thresholds.length > 0 ? Math.min(...thresholds) : null,
    landscaping_min_pct: pcts.length > 0 ? Math.max(...pcts) : null,
    landscaping_article: [...articles].join("; "),
  };
}

function resolveBuildingDesignation(allZoneNames: string[]) {
  const isDistrictPlan = allZoneNames.some((z) => z.includes("지구단위계획"));
  return {
    building_designation_applies: isDistrictPlan,
    building_designation_setback_m: isDistrictPlan ? 2.0 : null,
    building_designation_article: isDistrictPlan
      ? "국토계획법 §49-52, 건축법 §46-47"
      : "",
    building_designation_source: isDistrictPlan ? "static_default" : "",
  };
}
