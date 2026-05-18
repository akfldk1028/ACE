/**
 * PNU Resolver — validates/parses 19-digit PNU codes, resolves addresses via Vworld API.
 * Port of: ARR/backend/land/services/pnu_resolver.py
 *
 * PNU structure (19 digits):
 *   [시도2][시군구3][읍면동3][리2][토지구분1][본번4][부번4]
 *   토지구분: 1=대, 2=임야
 */

const PNU_RE = /^\d{19}$/;

const VWORLD_GEOCODE_URL = "https://api.vworld.kr/req/address";

export function validatePnu(pnu: string): boolean {
  return PNU_RE.test(pnu);
}

export function parsePnu(pnu: string) {
  if (!validatePnu(pnu)) return null;

  const landTypeCode = pnu[10];
  return {
    pnu,
    sido: pnu.slice(0, 2),
    sigungu: pnu.slice(2, 5),
    eupmyeondong: pnu.slice(5, 8),
    ri: pnu.slice(8, 10),
    land_type: pnu.slice(10, 11),
    main_number: pnu.slice(11, 15),
    sub_number: pnu.slice(15, 19),
    land_type_name:
      landTypeCode === "1" ? "대" : landTypeCode === "2" ? "임야" : "기타",
  };
}

export type ResolveResult = {
  success: boolean;
  address: string;
  pnu: string | null;
  coordinates: { x: number; y: number } | null;
  geocoded_address?: string;
  error?: string;
};

export async function resolveAddress(
  address: string,
  vworldApiKey: string,
): Promise<ResolveResult> {
  if (!vworldApiKey) {
    return {
      success: false,
      error: "VWORLD_API_KEY not configured",
      address,
      pnu: null,
      coordinates: null,
    };
  }

  // Try PARCEL first, then ROAD
  for (const addrType of ["PARCEL", "ROAD"] as const) {
    const result = await vworldGeocode(address, addrType, vworldApiKey);
    if (result?.response?.status === "OK") {
      return parseGeocodeResult(result, address);
    }
  }

  return {
    success: false,
    error: `Vworld geocoding failed: no results for '${address}'`,
    address,
    pnu: null,
    coordinates: null,
  };
}

async function vworldGeocode(
  address: string,
  addrType: string,
  apiKey: string,
): Promise<VworldResponse | null> {
  const params = new URLSearchParams({
    service: "address",
    request: "getCoord",
    key: apiKey,
    address,
    type: addrType,
    format: "json",
    crs: "EPSG:4326",
    refine: "true",
  });

  try {
    const resp = await fetch(`${VWORLD_GEOCODE_URL}?${params}`, {
      headers: { "Referer": "http://localhost", "Origin": "http://localhost" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!resp.ok) return null;
    return (await resp.json()) as VworldResponse;
  } catch {
    return null;
  }
}

interface VworldResponse {
  response: {
    status: string;
    result?: { point: { x: string; y: string } };
    refined?: {
      text?: string;
      structure?: { level4LC?: string };
    };
  };
}

function parseGeocodeResult(
  data: VworldResponse,
  originalAddress: string,
): ResolveResult {
  try {
    const { response } = data;
    if (response.status !== "OK") {
      return {
        success: false,
        error: `Vworld status: ${response.status}`,
        address: originalAddress,
        pnu: null,
        coordinates: null,
      };
    }

    const point = response.result!.point;
    const x = parseFloat(point.x);
    const y = parseFloat(point.y);

    const level4lc = response.refined?.structure?.level4LC ?? "";
    const pnu = validatePnu(level4lc) ? level4lc : null;
    const geocodedText = response.refined?.text ?? "";

    return {
      success: true,
      address: originalAddress,
      pnu,
      coordinates: { x, y },
      geocoded_address: geocodedText,
    };
  } catch {
    return {
      success: false,
      error: "Failed to parse Vworld response",
      address: originalAddress,
      pnu: null,
      coordinates: null,
    };
  }
}
