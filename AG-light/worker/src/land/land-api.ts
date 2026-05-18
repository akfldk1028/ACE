/**
 * Land API — fetches land info from Vworld Data APIs.
 * Port of: ARR/backend/land/services/land_api.py
 *
 * 3 APIs (all use same VWORLD_API_KEY):
 * - getLandUseAttr: 토지이용계획 → 용도지역 names
 * - ladfrlList: 토지임야대장 → 면적(m2), 지목
 * - getIndvdLandPriceAttr: 개별공시지가 → 원/m2
 */

import { lookup } from "./zoning-mapper";

const VWORLD_DATA_BASE = "https://api.vworld.kr/ned/data";

export interface LandUseResult {
  success: boolean;
  pnu: string;
  zones: string[];
  land_area_m2: number | null;
  official_land_price: number | null;
  land_use_situation: string;
  source: "vworld" | "stub";
  errors?: string[];
  message?: string;
}

export async function getLandUseInfo(
  pnu: string,
  vworldApiKey: string,
): Promise<LandUseResult> {
  if (!vworldApiKey) {
    return {
      success: true,
      pnu,
      zones: [],
      land_area_m2: null,
      official_land_price: null,
      land_use_situation: "",
      source: "stub",
      message: "VWORLD_API_KEY not configured. Provide zones manually.",
    };
  }

  const errors: string[] = [];

  // Call 3 APIs in parallel — partial failure OK
  const [landUse, ladfrl, price] = await Promise.allSettled([
    fetchLandUseAttr(pnu, vworldApiKey),
    fetchLadfrl(pnu, vworldApiKey),
    fetchLandPrice(pnu, vworldApiKey),
  ]);

  const zones =
    landUse.status === "fulfilled" && landUse.value.success
      ? landUse.value.zones
      : (landUse.status === "fulfilled" && landUse.value.error
          ? (errors.push(landUse.value.error), [])
          : (errors.push("getLandUseAttr: failed"), []));

  let land_area_m2: number | null = null;
  let land_use_situation = "";
  if (ladfrl.status === "fulfilled" && ladfrl.value.success) {
    land_area_m2 = ladfrl.value.land_area_m2;
    land_use_situation = ladfrl.value.land_use_situation;
  } else if (ladfrl.status === "fulfilled" && ladfrl.value.error) {
    errors.push(ladfrl.value.error);
  } else {
    errors.push("ladfrlList: failed");
  }

  let official_land_price: number | null = null;
  if (price.status === "fulfilled" && price.value.success) {
    official_land_price = price.value.official_land_price;
  } else if (price.status === "fulfilled" && price.value.error) {
    errors.push(price.value.error);
  } else {
    errors.push("getIndvdLandPriceAttr: failed");
  }

  const anySuccess =
    (landUse.status === "fulfilled" && landUse.value.success) ||
    (ladfrl.status === "fulfilled" && ladfrl.value.success) ||
    (price.status === "fulfilled" && price.value.success);

  const result: LandUseResult = {
    success: anySuccess,
    pnu,
    zones,
    land_area_m2,
    official_land_price,
    land_use_situation,
    source: anySuccess ? "vworld" : "stub",
  };
  if (errors.length > 0) result.errors = errors;
  if (!anySuccess) result.message = "All Vworld API calls failed. " + errors.join("; ");

  return result;
}

// ── getLandUseAttr ──────────────────────────────────────

interface LandUseAttrResult {
  success: boolean;
  zones: string[];
  error?: string;
}

async function fetchLandUseAttr(
  pnu: string,
  apiKey: string,
): Promise<LandUseAttrResult> {
  const params = new URLSearchParams({
    key: apiKey,
    pnu,
    format: "json",
    numOfRows: "50",
    pageNo: "1",
  });

  try {
    const resp = await fetch(`${VWORLD_DATA_BASE}/getLandUseAttr?${params}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!resp.ok) {
      return { success: false, zones: [], error: `getLandUseAttr: HTTP ${resp.status}` };
    }

    const data = await resp.json() as Record<string, unknown>;
    const landUses = (data.landUses ?? {}) as Record<string, unknown>;
    let items = landUses.field as Record<string, unknown>[] | Record<string, unknown> | undefined;

    if (items && !Array.isArray(items)) items = [items];
    if (!items || (items as unknown[]).length === 0) {
      return { success: false, zones: [], error: "getLandUseAttr: no data for this PNU" };
    }

    const zones: string[] = [];
    const seen = new Set<string>();

    for (const item of items as Record<string, unknown>[]) {
      // 포함(fully inside) or 저촉(partially overlapping) → applicable
      // 접함(adjacent) → skip
      // None/missing → include as defensive default
      const cnflcAtNm = item.cnflcAtNm as string | undefined;
      if (cnflcAtNm != null && cnflcAtNm !== "포함" && cnflcAtNm !== "저촉") {
        continue;
      }

      const name = ((item.prposAreaDstrcCodeNm as string) ?? "").trim();
      if (!name) continue;

      const normalized = normalizeZoneName(name);
      if (!seen.has(normalized)) {
        zones.push(normalized);
        seen.add(normalized);
      }
    }

    return { success: true, zones };
  } catch {
    return { success: false, zones: [], error: "getLandUseAttr: connection failed" };
  }
}

// ── ladfrlList ──────────────────────────────────────────

interface LadfrlResult {
  success: boolean;
  land_area_m2: number | null;
  land_use_situation: string;
  error?: string;
}

async function fetchLadfrl(
  pnu: string,
  apiKey: string,
): Promise<LadfrlResult> {
  const params = new URLSearchParams({
    key: apiKey,
    pnu,
    format: "json",
    numOfRows: "1",
    pageNo: "1",
  });

  try {
    const resp = await fetch(`${VWORLD_DATA_BASE}/ladfrlList?${params}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!resp.ok) {
      return { success: false, land_area_m2: null, land_use_situation: "", error: `ladfrlList: HTTP ${resp.status}` };
    }

    const data = await resp.json() as Record<string, unknown>;
    const wrapper = (data.ladfrlVOList ?? {}) as Record<string, unknown>;
    let items = wrapper.ladfrlVOList as Record<string, unknown>[] | Record<string, unknown> | undefined;

    if (items && !Array.isArray(items)) items = [items];
    if (!items || (items as unknown[]).length === 0) {
      return { success: false, land_area_m2: null, land_use_situation: "", error: "ladfrlList: no data for this PNU" };
    }

    const item = (items as Record<string, unknown>[])[0];
    const areaStr = (item.lndpclAr as string) ?? "";
    const area = areaStr ? parseFloat(areaStr) : null;
    const jimok = ((item.lndcgrCodeNm as string) ?? "").trim();

    return { success: true, land_area_m2: area, land_use_situation: jimok };
  } catch {
    return { success: false, land_area_m2: null, land_use_situation: "", error: "ladfrlList: connection failed" };
  }
}

// ── getIndvdLandPriceAttr ───────────────────────────────

interface LandPriceResult {
  success: boolean;
  official_land_price: number | null;
  error?: string;
}

async function fetchLandPrice(
  pnu: string,
  apiKey: string,
): Promise<LandPriceResult> {
  const currentYear = new Date().getFullYear();
  const yearsToTry = [String(currentYear), String(currentYear - 1)];

  for (const year of yearsToTry) {
    const result = await fetchLandPriceForYear(pnu, apiKey, year);
    if (result.success) return result;
  }

  return { success: false, official_land_price: null, error: "getIndvdLandPriceAttr: no data" };
}

async function fetchLandPriceForYear(
  pnu: string,
  apiKey: string,
  stdrYear: string,
): Promise<LandPriceResult> {
  const params = new URLSearchParams({
    key: apiKey,
    pnu,
    format: "json",
    numOfRows: "1",
    pageNo: "1",
    stdrYear,
  });

  try {
    const resp = await fetch(`${VWORLD_DATA_BASE}/getIndvdLandPriceAttr?${params}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!resp.ok) {
      return { success: false, official_land_price: null, error: `getIndvdLandPriceAttr: HTTP ${resp.status}` };
    }

    const data = await resp.json() as Record<string, unknown>;
    const prices = (data.indvdLandPrices ?? {}) as Record<string, unknown>;
    let items = prices.field as Record<string, unknown>[] | Record<string, unknown> | undefined;

    if (items && !Array.isArray(items)) items = [items];
    if (!items || (items as unknown[]).length === 0) {
      return { success: false, official_land_price: null, error: `no price data for ${stdrYear}` };
    }

    const priceStr = ((items as Record<string, unknown>[])[0].pblntfPclnd as string) ?? "";
    const price = priceStr ? Math.floor(parseFloat(priceStr)) : null;

    return { success: true, official_land_price: price };
  } catch {
    return { success: false, official_land_price: null, error: "getIndvdLandPriceAttr: connection failed" };
  }
}

// ── Vworld Data API: 필지 폴리곤 조회 ───────────────────

export interface ParcelGeometryResult {
  success: boolean;
  geometry: { type: string; coordinates: unknown } | null;
  error?: string;
}

/**
 * PNU로 필지 경계 폴리곤 조회 (Vworld 2D Data API).
 * LP_PA_CBND_BUBUN 레이어에서 PNU 일치 필지 조회.
 */
export async function fetchParcelGeometry(
  pnu: string,
  vworldApiKey: string,
): Promise<ParcelGeometryResult> {
  if (!vworldApiKey) {
    return { success: false, geometry: null, error: "VWORLD_API_KEY not configured" };
  }

  const params = new URLSearchParams({
    service: "data",
    request: "GetFeature",
    data: "LP_PA_CBND_BUBUN",
    key: vworldApiKey,
    attrFilter: `pnu:=:${pnu}`,
    format: "json",
    crs: "EPSG:4326",
    size: "1",
  });

  try {
    const resp = await fetch(`https://api.vworld.kr/req/data?${params}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!resp.ok) {
      return { success: false, geometry: null, error: `ParcelGeometry: HTTP ${resp.status}` };
    }

    const data = await resp.json() as {
      response?: { status?: string; result?: { featureCollection?: { features?: Array<{ geometry: { type: string; coordinates: unknown } }> } } };
    };

    const features = data.response?.result?.featureCollection?.features;
    if (!features || features.length === 0) {
      return { success: false, geometry: null, error: "ParcelGeometry: no features" };
    }

    const geom = features[0].geometry;
    // MultiPolygon → Polygon (첫 번째만)
    if (geom.type === "MultiPolygon") {
      const coords = geom.coordinates as number[][][][];
      if (coords.length > 0) {
        return { success: true, geometry: { type: "Polygon", coordinates: coords[0] } };
      }
    }

    return { success: true, geometry: geom };
  } catch {
    return { success: false, geometry: null, error: "ParcelGeometry: connection failed" };
  }
}

// ── Helpers ─────────────────────────────────────────────

function normalizeZoneName(name: string): string {
  if (name.endsWith("지역") || name.endsWith("지구") || name.endsWith("구역") || name.endsWith("권역")) {
    return name;
  }
  const candidate = name + "지역";
  if (lookup(candidate) !== undefined) {
    return candidate;
  }
  return name;
}
