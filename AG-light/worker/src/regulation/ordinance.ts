/**
 * Ordinance Override — 지자체 조례에 의한 규제 수치 override.
 * Port of: ARR/backend/land/services/regulation_calculator.py (_apply_ordinance_overrides)
 *
 * In Workers, static JSON files per sigungu are embedded inline.
 * Future: KV storage or /law/ordinance + LLM extraction.
 */

// ── Known ordinance overrides (embedded) ────────────────

interface OrdinanceOverride {
  sigungu_code: string;
  sigungu_name: string;
  overrides: Record<string, Record<string, unknown>>;
}

const ORDINANCE_DB: Record<string, OrdinanceOverride> = {
  "11680": {
    sigungu_code: "11680",
    sigungu_name: "강남구",
    overrides: {
      "제3종일반주거지역": {
        adjacent_setback_m: 1.0,
        corner_cutoff: { default_cutoff_m: 4 },
      },
    },
  },
};

// ── Public API ──────────────────────────────────────────

/**
 * Apply ordinance overrides to zone regulation data.
 * 1-level merge: zone_data에 override 값 덮어쓰기.
 * Returns new object (no mutation).
 */
export function applyOrdinanceOverrides<T extends Record<string, unknown>>(
  zonesData: T[],
  sigunguCode: string,
): T[] {
  const ordinance = ORDINANCE_DB[sigunguCode];
  if (!ordinance) return zonesData;

  const overrides = ordinance.overrides;
  if (!overrides || Object.keys(overrides).length === 0) return zonesData;

  return zonesData.map((z) => {
    const zoneName = z.zone_name as string | undefined;
    if (!zoneName || !(zoneName in overrides)) return z;

    const merged = { ...z };
    const zoneOverrides = overrides[zoneName];
    for (const [key, val] of Object.entries(zoneOverrides)) {
      const target = merged as Record<string, unknown>;
      if (
        val !== null &&
        typeof val === "object" &&
        !Array.isArray(val) &&
        target[key] !== null &&
        typeof target[key] === "object" &&
        !Array.isArray(target[key])
      ) {
        target[key] = { ...(target[key] as Record<string, unknown>), ...val };
      } else {
        target[key] = val;
      }
    }
    return merged;
  });
}

/**
 * Get ordinance info for a sigungu code.
 */
export function getOrdinanceInfo(sigunguCode: string): OrdinanceOverride | null {
  return ORDINANCE_DB[sigunguCode] ?? null;
}
