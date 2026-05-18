import { Hono } from "hono";
import type { Env } from "../index";
import { resolveAddress, parsePnu, validatePnu, resolveZoneLimits, getAllZones, getLandUseInfo, fetchParcelGeometry, fetchNeighborRoads, type LandUseResult } from "../land";
import { calculateAll, calculateExtended, enhanceWithLlm, type RegulationResult } from "../regulation";
import { computeSetbackLines, type RoadFrontageInput } from "../geometry";
import { searchForZones } from "../law";

export const landRoutes = new Hono<{ Bindings: Env }>();

/**
 * POST /land/analyze
 * Body: { input: string, input_type?: "pnu"|"address", zones?: string[], include_law?: boolean }
 *
 * Response keys match Django ARR backend for compatibility.
 */
landRoutes.post("/analyze", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const { input, zones, include_law = true } = body as Record<string, unknown>;

  if (!input || typeof input !== "string") {
    return c.json({ error: '"input" (string) is required' }, 400);
  }

  // Validate zones
  const manualZones: string[] = [];
  if (zones !== undefined) {
    if (!Array.isArray(zones) || !zones.every((z) => typeof z === "string")) {
      return c.json({ error: '"zones" must be an array of strings' }, 400);
    }
    manualZones.push(...zones);
  }

  let inputType = (body as Record<string, unknown>).input_type as string | undefined;
  let pnuData: ReturnType<typeof parsePnu> = null;

  // Auto-detect input type
  if (!inputType) {
    inputType = validatePnu(input) ? "pnu" : "address";
  }

  // Resolve PNU
  if (inputType === "pnu") {
    pnuData = parsePnu(input);
    if (!pnuData) {
      return c.json({ error: "Invalid PNU format (19 digits required)" }, 400);
    }
  } else {
    const resolved = await resolveAddress(input, c.env.VWORLD_API_KEY);
    if (!resolved.success) {
      return c.json({ error: resolved.error, address: input }, 400);
    }
    if (resolved.pnu) {
      pnuData = parsePnu(resolved.pnu);
    }
  }

  // Auto-resolve zones from Vworld Data API when manualZones is empty
  let resolvedZones = manualZones;
  let landInfo: LandUseResult | null = null;

  if (resolvedZones.length === 0 && pnuData?.pnu) {
    landInfo = await getLandUseInfo(pnuData.pnu, c.env.VWORLD_API_KEY);
    if (landInfo.success && landInfo.zones.length > 0) {
      resolvedZones = landInfo.zones;
    }
  }

  // Zone regulation
  const zoneResult = resolveZoneLimits(resolvedZones);

  // Full regulation calculation (core 11)
  // sigunguCode = 시도(2) + 시군구(3) = 5자리 (e.g., "11680" = 서울 강남구)
  const sigunguCode = pnuData ? (pnuData.sido + pnuData.sigungu) : "";
  const regulations = calculateAll(
    resolvedZones,
    landInfo as Record<string, unknown> | null,
    sigunguCode,
  );

  // Extended regulations (31)
  const extendedRegulations = calculateExtended(
    resolvedZones,
    landInfo as Record<string, unknown> | null,
  );

  // LLM enhancement (3-tier: static JSON → ordinance → LLM override)
  if (c.env.OPENAI_API_KEY && c.env.JINA_API_KEY && resolvedZones.length > 0) {
    await enhanceWithLlm(regulations, resolvedZones, c.env);
  }

  // Law articles (optional)
  let lawArticles = { articles: [] as unknown[], total_count: 0, errors: [] as string[] };
  if (include_law && resolvedZones.length > 0) {
    lawArticles = await searchForZones(resolvedZones, c.env);
  }

  // Build restrictions summary (human-readable)
  const restrictions: string[] = [];
  if (regulations.bcr_pct != null) {
    restrictions.push(`건폐율 상한: ${regulations.bcr_pct}%`);
  }
  if (regulations.far_pct != null) {
    restrictions.push(`용적률 상한: ${regulations.far_pct}%`);
  }
  if (regulations.height_limit_m != null) {
    restrictions.push(`높이제한: ${regulations.height_limit_m}m`);
  }
  if (regulations.sunlight_applies) {
    restrictions.push("정북일조 사선제한 적용");
  }

  // Setback geometry — auto-fetch parcel polygon if not provided
  let parcelGeojson = (body as Record<string, unknown>).parcel_geojson as
    | { type: string; coordinates: unknown }
    | undefined;
  let setbackLines = null;
  let roadFrontages: RoadFrontageInput[] | undefined;

  // Auto-fetch parcel polygon from Vworld Data API
  if (!parcelGeojson && pnuData?.pnu) {
    const parcelResult = await fetchParcelGeometry(pnuData.pnu, c.env.VWORLD_API_KEY);
    if (parcelResult.success && parcelResult.geometry) {
      parcelGeojson = parcelResult.geometry;
    }
  }

  if (parcelGeojson) {
    // Auto-fetch neighboring road parcels
    const parcelCoords = (parcelGeojson.coordinates as number[][][])?.[0];
    if (parcelCoords) {
      const neighborResult = await fetchNeighborRoads(parcelCoords, c.env.VWORLD_API_KEY);
      if (neighborResult.success && neighborResult.roads.length > 0) {
        roadFrontages = neighborResult.roads.map((r) => ({
          sharedEdge: r.sharedEdge.map((p) => [p[0], p[1]]) as number[][],
          roadWidthM: r.roadWidthM,
        }));
      }
    }

    setbackLines = computeSetbackLines(parcelGeojson, regulations, roadFrontages);
  }

  // Response keys match Django ARR backend
  return c.json({
    pnu: pnuData,
    regulations,
    extended_regulations: extendedRegulations,
    zone_info: {
      zones: resolvedZones,
      bcr_limit: zoneResult.bcr_limit,
      far_limit: zoneResult.far_limit,
      matched: zoneResult.matched,
      unmatched: zoneResult.unmatched,
    },
    land_info: landInfo,
    law_articles: lawArticles,
    restrictions,
    parcel_geojson: parcelGeojson,
    setback_lines: setbackLines,
  });
});

/**
 * POST /land/setback
 * Body: { parcel_geojson: GeoJSON Polygon, regulations: RegulationResult }
 *
 * Standalone setback computation (when regulations are already known).
 */
landRoutes.post("/setback", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const { parcel_geojson, regulations: regs, road_frontages } = body as Record<string, unknown>;
  if (!parcel_geojson || typeof parcel_geojson !== "object") {
    return c.json({ error: '"parcel_geojson" (GeoJSON Polygon) is required' }, 400);
  }
  if (!regs || typeof regs !== "object") {
    return c.json({ error: '"regulations" object is required' }, 400);
  }

  const result = computeSetbackLines(
    parcel_geojson as { type: string; coordinates: unknown },
    regs as Record<string, unknown>,
    road_frontages as RoadFrontageInput[] | undefined,
  );
  return c.json(result);
});

/**
 * POST /land/resolve
 * Body: { input: string, input_type?: "pnu"|"address" }
 *
 * Handles both PNU validation and address resolution (matches Django).
 */
landRoutes.post("/resolve", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const { input } = body as Record<string, unknown>;
  if (!input || typeof input !== "string") {
    return c.json({ error: '"input" (string) is required' }, 400);
  }

  const inputType = (body as Record<string, unknown>).input_type as string | undefined;

  if (inputType === "pnu" || (!inputType && validatePnu(input))) {
    const parsed = parsePnu(input);
    if (!parsed) {
      return c.json({ success: false, error: "Invalid PNU format", input, pnu: null });
    }
    return c.json({ success: true, pnu: parsed.pnu, parsed, input });
  }

  const result = await resolveAddress(input, c.env.VWORLD_API_KEY);
  return c.json(result);
});

/**
 * GET /land/zones
 */
landRoutes.get("/zones", (c) => {
  const zones = getAllZones();
  return c.json({ zones, count: zones.length });
});

