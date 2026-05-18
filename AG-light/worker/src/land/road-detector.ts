/**
 * Road Detector — Vworld Data API 연속지적도에서 인접 도로 필지 탐지.
 *
 * 1. parcel BBOX + 20m 버퍼 → Data API GetFeature (geomFilter BOX)
 * 2. 지목="도" 필지 필터
 * 3. 공유변 추출 (parcel edge ↔ road polygon boundary)
 * 4. 도로폭 추정 (면적 / 공유변 길이)
 *
 * land-api.ts에서 분리: 토지정보 API(NED)와 지적도(Data)는 역할이 다름.
 */

import { type Coord, DEG_LON_M, DEG_LAT_M, toLocal, polygonArea } from "../geometry/geo-math";

// ── Types ───────────────────────────────────────────────

export interface RoadFrontage {
  sharedEdge: [number, number][];
  roadWidthM: number;
  landCategory: string;
}

export interface NeighborRoadsResult {
  success: boolean;
  roads: RoadFrontage[];
  error?: string;
}

// ── Main ────────────────────────────────────────────────

export async function fetchNeighborRoads(
  parcelCoords: number[][],
  vworldApiKey: string,
): Promise<NeighborRoadsResult> {
  if (!vworldApiKey) {
    return { success: false, roads: [], error: "VWORLD_API_KEY not configured" };
  }

  // BBOX with ~20m buffer (~0.0002°)
  const BUFFER_DEG = 0.0002;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const [lon, lat] of parcelCoords) {
    if (lon < minX) minX = lon;
    if (lat < minY) minY = lat;
    if (lon > maxX) maxX = lon;
    if (lat > maxY) maxY = lat;
  }
  minX -= BUFFER_DEG; minY -= BUFFER_DEG;
  maxX += BUFFER_DEG; maxY += BUFFER_DEG;

  const params = new URLSearchParams({
    service: "data",
    request: "GetFeature",
    data: "LP_PA_CBND_BUBUN",
    key: vworldApiKey,
    geomFilter: `BOX(${minX},${minY},${maxX},${maxY})`,
    format: "json",
    crs: "EPSG:4326",
    size: "100",
  });

  try {
    const resp = await fetch(`https://api.vworld.kr/req/data?${params}`, {
      signal: AbortSignal.timeout(15_000),
    });
    if (!resp.ok) {
      return { success: false, roads: [], error: `DataAPI: HTTP ${resp.status}` };
    }

    const raw = await resp.json() as { response?: { result?: { featureCollection?: WfsFeatureCollection } } };
    const data = raw.response?.result?.featureCollection;
    if (!data?.features || data.features.length === 0) {
      return { success: false, roads: [], error: "DataAPI: no features returned" };
    }

    // 지목 "도" (도로) 필터
    const roadFeatures = data.features.filter((f) => {
      const code = (f.properties?.lndcgrCode as string) ?? "";
      const name = (f.properties?.lndcgrCodeNm as string) ?? "";
      return code === "07" || name === "도" || name.includes("도로");
    });

    if (roadFeatures.length === 0) {
      return { success: true, roads: [] };
    }

    // 공유변 추출 + 도로폭 추정
    const roads: RoadFrontage[] = [];
    for (const rf of roadFeatures) {
      const roadCoords = extractPolygonCoords(rf.geometry);
      if (!roadCoords) continue;

      const shared = findSharedEdges(parcelCoords, roadCoords);
      if (shared.length === 0) continue;

      // 면적/도로폭: local 좌표로 변환 후 정확 계산
      const roadLocal: Coord[] = roadCoords.map(([lon, lat]) => toLocal(lon, lat));
      const roadArea = polygonArea(roadLocal);  // m²

      const sharedLenM = shared.reduce((sum, seg) => {
        const [a, b] = seg.map(([lon, lat]) => toLocal(lon, lat));
        return sum + Math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2);
      }, 0);

      // 도로폭 = 면적 / 공유변 길이 (직사각형 근사)
      const widthM = sharedLenM > 0.1 ? roadArea / sharedLenM : 6;

      // 각 세그먼트를 독립적으로 유지 (flat 안 함)
      for (const seg of shared) {
        roads.push({
          sharedEdge: seg,
          roadWidthM: Math.max(2, Math.min(widthM, 40)),
          landCategory: (rf.properties?.lndcgrCodeNm as string) ?? "도",
        });
      }
    }

    return { success: true, roads };
  } catch {
    return { success: false, roads: [], error: "DataAPI: connection failed" };
  }
}

// ── Helpers ─────────────────────────────────────────────

interface WfsFeatureCollection {
  features: Array<{
    geometry: { type: string; coordinates: unknown };
    properties?: Record<string, unknown>;
  }>;
}

function extractPolygonCoords(geom: { type: string; coordinates: unknown }): number[][] | null {
  if (geom.type === "Polygon") return (geom.coordinates as number[][][])?.[0] ?? null;
  if (geom.type === "MultiPolygon") return (geom.coordinates as number[][][][])?.[0]?.[0] ?? null;
  return null;
}

/** 두 폴리곤의 공유변 (tolerance ~1m ≈ 0.00001°). */
function findSharedEdges(parcel: number[][], road: number[][]): [number, number][][] {
  const TOL = 0.00001;
  const shared: [number, number][][] = [];

  for (let i = 0; i < parcel.length - 1; i++) {
    const p1 = parcel[i], p2 = parcel[i + 1];
    if (isPointNearPolyline(p1, road, TOL) && isPointNearPolyline(p2, road, TOL)) {
      shared.push([[p1[0], p1[1]], [p2[0], p2[1]]]);
    }
  }
  return shared;
}

function isPointNearPolyline(pt: number[], polyline: number[][], tol: number): boolean {
  for (let i = 0; i < polyline.length - 1; i++) {
    if (pointToSegDist(pt, polyline[i], polyline[i + 1]) < tol) return true;
  }
  return false;
}

function pointToSegDist(p: number[], a: number[], b: number[]): number {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const lenSq = dx * dx + dy * dy;
  if (lenSq < 1e-20) return Math.sqrt((p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2);
  let t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  return Math.sqrt((p[0] - (a[0] + t * dx)) ** 2 + (p[1] - (a[1] + t * dy)) ** 2);
}

