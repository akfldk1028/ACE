/**
 * Zoning Mapper — maps zone names to BCR/FAR limits.
 * Port of: ARR/backend/land/services/zoning_mapper.py
 *
 * When multiple zones apply, the strictest (lowest) limits are used
 * per 국토계획법 제76-77조.
 */

import zoningData from "../data/zoning-limits.json";

export interface ZoneDefinition {
  zone_name: string;
  category: string;
  bcr_default: number;
  far_default: number;
  bcr_article: string;
  far_article: string;
  restriction_keywords: string[];
  height_limit_m: number | null;
  height_limit_article: string;
  sunlight_setback: {
    applies: boolean;
    rules: Array<{ condition: string; setback_m?: number; formula?: string }>;
    direction: string;
    article: string;
  };
  road_diagonal: {
    multiplier: number | null;
    note: string;
    article: string;
  };
  corner_cutoff: {
    required: boolean;
    min_road_width_m: number;
    article: string;
    note: string;
    default_cutoff_m?: number;
  };
  adjacent_setback_m: number;
  adjacent_setback_article: string;
  building_line_article: string;
  landscaping: {
    threshold_m2: number;
    min_pct: number;
    article: string;
  };
  parking_article: string;
}

const ZONES: Map<string, ZoneDefinition> = new Map(
  (zoningData.zones as ZoneDefinition[]).map((z) => [z.zone_name, z]),
);

export function getAllZones(): ZoneDefinition[] {
  return Array.from(ZONES.values());
}

export function lookup(zoneName: string): ZoneDefinition | undefined {
  return ZONES.get(zoneName);
}

export function resolveZoneLimits(zoneNames: string[]) {
  const matched: ZoneDefinition[] = [];
  const unmatched: string[] = [];

  for (const name of zoneNames) {
    const zone = ZONES.get(name);
    if (zone) matched.push(zone);
    else unmatched.push(name);
  }

  if (matched.length === 0) {
    return {
      bcr_limit: null as number | null,
      far_limit: null as number | null,
      zones: [] as ZoneDefinition[],
      matched: 0,
      unmatched,
    };
  }

  return {
    bcr_limit: Math.min(...matched.map((z) => z.bcr_default)),
    far_limit: Math.min(...matched.map((z) => z.far_default)),
    zones: matched,
    matched: matched.length,
    unmatched,
  };
}
