/**
 * Setback Geometry — 필지 polygon + 규제 수치 → 규제선 GeoJSON 생성.
 * Port of: ARR/backend/land/services/setback_geometry.py
 *
 * 건축법 규제선 8종:
 * 1. buildable_area      건축가능영역 (인접이격 buffer)
 * 2. north_setback       정북 일조사선 4단계 (§86①)
 * 3. adjacent_setback    인접대지 이격선 (§58)
 * 4. road_setback        건축선 후퇴 — 도로폭 차등 (§46-47)
 * 5. corner_cutoff       가각전제 (령§31)
 * 6. building_designation_line 건축지정선/한계선 (§49-52)
 * 7. sunlight_envelope   3D 일조사선 경사면
 * 8. daylight_diagonal_envelope 채광사선제한 3D (§86③)
 *
 * 기하 원시함수는 geo-math.ts에 분리.
 */

import {
  type Coord,
  toLocal, toWgs,
  edgeLength, dist2,
  polygonCentroid, polygonArea, polygonBounds,
  inwardNormal, outwardNormal,
  clipLineToPolygon, bufferPolygonInward, pointToSegDist,
} from "./geo-math";

// ── Types ───────────────────────────────────────────────

type Edge = { line: Coord[]; azimuth: number };

interface GeoJSONGeometry {
  type: string;
  coordinates: unknown;
}

interface GeoJSONFeature {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: GeoJSONGeometry;
}

export interface SetbackResult {
  buildable_area: GeoJSONGeometry | null;
  north_setback: { type: "FeatureCollection"; features: GeoJSONFeature[] } | null;
  adjacent_setback: GeoJSONGeometry | null;
  road_setback: GeoJSONGeometry | null;
  corner_cutoff: GeoJSONGeometry | null;
  sunlight_envelope: {
    walls: Array<{ positions: number[][]; min_heights: number[]; max_heights: number[] }>;
    slope: number; base_setback_m: number; base_height_m: number; max_depth_m: number;
  } | null;
  building_designation_line: GeoJSONGeometry | null;
  daylight_diagonal_envelope: {
    walls: Array<{ positions: number[][]; min_heights: number[]; max_heights: number[] }>;
    multiplier: number; max_depth_m: number;
  } | null;
}

interface Regulations {
  adjacent_setback_m?: number | null;
  building_line_setback_m?: number | null;
  sunlight_applies?: boolean;
  sunlight_rules?: Array<{ condition?: string; setback_m?: number; formula?: string }>;
  corner_cutoff_required?: boolean;
  corner_cutoff_m?: number | null;
  building_designation_applies?: boolean;
  building_designation_setback_m?: number | null;
  daylight_diagonal_multiplier?: number | null;
}

/** 도로 인접 정보 (Vworld WFS 또는 외부 제공) */
export interface RoadFrontageInput {
  sharedEdge: number[][];
  roadWidthM: number;
}

/** 도로폭→건축선 후퇴 (§46) */
function roadSetbackByWidth(roadWidthM: number): number {
  if (roadWidthM >= 4) return 0;
  return (4 - roadWidthM) / 2;
}

// ── Edge Classification ─────────────────────────────────

type ClassifiedEdges = {
  north: Coord[][]; road: Coord[][]; adjacent: Coord[][];
  roadWidths: number[];
};

interface RoadMatch { isRoad: boolean; widthM: number }

function classifyEdgesWithRoads(
  edges: Edge[],
  centroid: Coord,
  roadData?: { edge: Coord[]; widthM: number }[],
): ClassifiedEdges {
  const classified: ClassifiedEdges = { north: [], road: [], adjacent: [], roadWidths: [] };
  if (edges.length === 0) return classified;

  const matches = roadData && roadData.length > 0
    ? matchEdgesToRoads(edges, roadData)
    : heuristicRoadDetection(edges);

  for (let idx = 0; idx < edges.length; idx++) {
    const edge = edges[idx];
    const { nx, ny } = outwardNormal(edge.line, centroid);
    if (nx === 0 && ny === 0) continue;

    const normalAz = (Math.atan2(nx, ny) * 180 / Math.PI + 360) % 360;
    const isNorthFacing = normalAz >= 300 || normalAz <= 60;
    const rm = matches[idx];

    if (rm.isRoad) {
      classified.road.push(edge.line);
      classified.roadWidths.push(rm.widthM);
      if (isNorthFacing) classified.north.push(edge.line);
    } else if (isNorthFacing) {
      classified.north.push(edge.line);
    } else {
      classified.adjacent.push(edge.line);
    }
  }
  return classified;
}

function matchEdgesToRoads(edges: Edge[], roadData: { edge: Coord[]; widthM: number }[]): RoadMatch[] {
  return edges.map((e) => {
    const mid: Coord = [(e.line[0][0] + e.line[1][0]) / 2, (e.line[0][1] + e.line[1][1]) / 2];
    for (const rd of roadData) {
      for (let i = 0; i < rd.edge.length - 1; i++) {
        if (pointToSegDist(mid, rd.edge[i], rd.edge[i + 1]) < 2.0) {
          return { isRoad: true, widthM: rd.widthM };
        }
      }
    }
    return { isRoad: false, widthM: 0 };
  });
}

function heuristicRoadDetection(edges: Edge[]): RoadMatch[] {
  const maxLen = Math.max(...edges.map((e) => edgeLength(e.line)));
  return edges.map((e) => ({ isRoad: edgeLength(e.line) >= maxLen * 0.70, widthM: 0 }));
}

// ── Main ────────────────────────────────────────────────

export function computeSetbackLines(
  parcelGeojson: GeoJSONGeometry,
  regulations: Regulations,
  roadFrontages?: RoadFrontageInput[],
): SetbackResult {
  const empty: SetbackResult = {
    buildable_area: null, north_setback: null, adjacent_setback: null,
    road_setback: null, corner_cutoff: null, sunlight_envelope: null,
    building_designation_line: null, daylight_diagonal_envelope: null,
  };

  if (!parcelGeojson || parcelGeojson.type !== "Polygon") return empty;
  const coords = (parcelGeojson.coordinates as number[][][])?.[0];
  if (!coords || coords.length < 4) return empty;

  const localCoords: Coord[] = coords.map(([lon, lat]) => toLocal(lon, lat));
  const adjacentM = regulations.adjacent_setback_m ?? 0.5;
  const sunlightApplies = regulations.sunlight_applies ?? false;
  const sunlightRules = regulations.sunlight_rules ?? [];

  const result = { ...empty };
  result.buildable_area = computeBuildableArea(localCoords, adjacentM);

  const edges = extractEdges(localCoords);
  if (edges.length === 0) return result;

  const centroid = polygonCentroid(localCoords);
  const localRoads = roadFrontages?.map((rf) => ({
    edge: rf.sharedEdge.map(([lon, lat]) => toLocal(lon, lat)) as Coord[],
    widthM: rf.roadWidthM,
  }));
  const classified = classifyEdgesWithRoads(edges, centroid, localRoads);

  // 정북일조 (2D + 3D)
  if (sunlightApplies && classified.north.length > 0) {
    result.north_setback = computeSunlightLines(classified.north, localCoords, centroid);
    result.sunlight_envelope = computeSunlightEnvelope(classified.north, localCoords, centroid);
  }

  // 인접대지 이격
  if (classified.adjacent.length > 0 && adjacentM > 0) {
    result.adjacent_setback = offsetEdgesInward(classified.adjacent, centroid, adjacentM);
  }

  // 도로변 건축선 후퇴 (도로폭 차등)
  if (classified.road.length > 0) {
    result.road_setback = computeRoadSetback(classified, centroid, regulations);
  }

  // 가각전제
  const cornerCutoffM = regulations.corner_cutoff_m ?? null;
  if (regulations.corner_cutoff_required && classified.road.length >= 2) {
    const hasNarrow = classified.roadWidths.some((w) => w < 8);
    if (hasNarrow || cornerCutoffM != null) {
      result.corner_cutoff = computeCornerCutoff(classified.road, cornerCutoffM);
    }
  }

  // 건축지정선
  const designSetback = regulations.building_designation_setback_m;
  if (regulations.building_designation_applies && classified.road.length > 0 && designSetback && designSetback > 0) {
    result.building_designation_line = offsetEdgesInward(classified.road, centroid, designSetback);
  }

  // 채광사선 3D
  const daylightMult = regulations.daylight_diagonal_multiplier;
  if (daylightMult && classified.adjacent.length > 0) {
    result.daylight_diagonal_envelope = computeDaylightEnvelope(classified.adjacent, localCoords, centroid, daylightMult);
  }

  return result;
}

// ── Edge Extraction ─────────────────────────────────────

function extractEdges(localCoords: Coord[]): Edge[] {
  const edges: Edge[] = [];
  for (let i = 0; i < localCoords.length - 1; i++) {
    const p1 = localCoords[i], p2 = localCoords[i + 1];
    const dx = p2[0] - p1[0], dy = p2[1] - p1[1];
    const length = Math.sqrt(dx * dx + dy * dy);
    if (length < 0.1) continue;
    edges.push({ line: [p1, p2], azimuth: (Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360 });
  }
  return edges;
}

// ── Buildable Area ──────────────────────────────────────

function computeBuildableArea(localCoords: Coord[], setbackM: number): GeoJSONGeometry | null {
  if (polygonArea(localCoords) < 1) return null;
  const buffered = bufferPolygonInward(localCoords, setbackM);
  if (!buffered || buffered.length < 4 || polygonArea(buffered) < 1) return null;
  return { type: "Polygon", coordinates: [buffered.map(([x, y]) => toWgs(x, y))] };
}

// ── Sunlight (정북일조 2D) ──────────────────────────────

function computeSunlightLines(
  northEdges: Coord[][], polygon: Coord[], centroid: Coord,
): SetbackResult["north_setback"] {
  const steps: [number, number, string][] = [
    [10, 1.5, "H=10m → 1.5m"], [20, 10, "H=20m → 10m"],
    [30, 15, "H=30m → 15m"], [40, 20, "H=40m → 20m"],
  ];
  const features: GeoJSONFeature[] = [];

  for (const [heightM, offsetM, label] of steps) {
    const lines: Coord[][] = [];
    for (const edge of northEdges) {
      const { nx, ny } = inwardNormal(edge, centroid);
      if (nx === 0 && ny === 0) continue;
      const offset: Coord[] = edge.map(([x, y]) => [x + nx * offsetM, y + ny * offsetM]);
      const clipped = clipLineToPolygon(offset, polygon);
      if (clipped && clipped.length >= 2) lines.push(clipped);
    }
    if (lines.length === 0) continue;
    const wgs = lines.map((l) => l.map(([x, y]) => toWgs(x, y)));
    features.push({
      type: "Feature",
      properties: { height_m: heightM, offset_m: offsetM, label },
      geometry: wgs.length === 1
        ? { type: "LineString", coordinates: wgs[0] }
        : { type: "MultiLineString", coordinates: wgs },
    });
  }
  return features.length > 0 ? { type: "FeatureCollection", features } : null;
}

// ── Sunlight Envelope (3D) ──────────────────────────────

function computeSunlightEnvelope(
  northEdges: Coord[][], polygon: Coord[], centroid: Coord,
): SetbackResult["sunlight_envelope"] {
  const baseSetback = 1.5, baseHeight = 10, slope = 2;
  const bounds = polygonBounds(polygon);
  const maxDepth = Math.min(Math.max(bounds.width, bounds.height) * 0.4, 30);
  const walls: Array<{ positions: number[][]; min_heights: number[]; max_heights: number[] }> = [];

  for (const edge of northEdges) {
    const { nx, ny } = inwardNormal(edge, centroid);
    if (nx === 0 && ny === 0) continue;

    // Wall 1: vertical (0→1.5m, height 0→10m)
    const w1p: number[][] = [], w1min: number[] = [], w1max: number[] = [];
    for (const [x, y] of edge) { w1p.push(toWgs(x, y)); w1min.push(0); w1max.push(0); }
    for (const [x, y] of edge) { w1p.push(toWgs(x + nx * baseSetback, y + ny * baseSetback)); w1min.push(0); w1max.push(baseHeight); }
    walls.push({ positions: w1p, min_heights: w1min, max_heights: w1max });

    // Wall 2: slope (1.5m→maxDepth)
    const w2p: number[][] = [], w2min: number[] = [], w2max: number[] = [];
    for (const dist of [baseSetback, 10, 20, 35, maxDepth]) {
      const h = Math.max(slope * dist, baseHeight);
      for (const [x, y] of edge) { w2p.push(toWgs(x + nx * dist, y + ny * dist)); w2min.push(0); w2max.push(h); }
    }
    walls.push({ positions: w2p, min_heights: w2min, max_heights: w2max });
  }

  return walls.length > 0 ? { walls, slope, base_setback_m: baseSetback, base_height_m: baseHeight, max_depth_m: maxDepth } : null;
}

// ── Edge Offset (공통: 인접/도로/지정선) ────────────────

function offsetEdgesInward(edges: Coord[][], centroid: Coord, distance: number): GeoJSONGeometry | null {
  const lines: Coord[][] = [];
  for (const edge of edges) {
    const { nx, ny } = inwardNormal(edge, centroid);
    if (nx === 0 && ny === 0) continue;
    const offset: Coord[] = edge.map(([x, y]) => [x + nx * distance, y + ny * distance]);
    if (edgeLength(offset) > 0.1) lines.push(offset);
  }
  if (lines.length === 0) return null;
  const wgs = lines.map((l) => l.map(([x, y]) => toWgs(x, y)));
  return wgs.length === 1
    ? { type: "LineString", coordinates: wgs[0] }
    : { type: "MultiLineString", coordinates: wgs };
}

// ── Road Setback (도로폭 차등) ──────────────────────────

function computeRoadSetback(classified: ClassifiedEdges, centroid: Coord, regulations: Regulations): GeoJSONGeometry | null {
  const lines: Coord[][] = [];
  for (let i = 0; i < classified.road.length; i++) {
    const edge = classified.road[i];
    const width = classified.roadWidths[i];
    const setbackM = width > 0 ? roadSetbackByWidth(width) : (regulations.building_line_setback_m ?? 1.0);
    if (setbackM <= 0) continue;
    const { nx, ny } = inwardNormal(edge, centroid);
    if (nx === 0 && ny === 0) continue;
    const offset: Coord[] = edge.map(([x, y]) => [x + nx * setbackM, y + ny * setbackM]);
    if (edgeLength(offset) > 0.1) lines.push(offset);
  }
  if (lines.length === 0) return null;
  const wgs = lines.map((l) => l.map(([x, y]) => toWgs(x, y)));
  return wgs.length === 1 ? { type: "LineString", coordinates: wgs[0] } : { type: "MultiLineString", coordinates: wgs };
}

// ── Corner Cutoff (가각전제) ────────────────────────────

function computeCornerCutoff(roadEdges: Coord[][], cutoffM: number | null): GeoJSONGeometry | null {
  if (roadEdges.length < 2) return null;
  const triangles: Coord[][] = [];

  for (let i = 0; i < roadEdges.length; i++) {
    for (let j = i + 1; j < roadEdges.length; j++) {
      const shared = findSharedVertex(roadEdges[i], roadEdges[j]);
      if (!shared) continue;
      const actual = cutoffM ?? cornerCutoffByAngle(roadEdges[i], roadEdges[j], shared);
      if (actual <= 0) continue;
      const ptA = pointAlongEdge(roadEdges[i], shared, actual);
      const ptB = pointAlongEdge(roadEdges[j], shared, actual);
      if (ptA && ptB) triangles.push([shared, ptA, ptB, shared]);
    }
  }

  if (triangles.length === 0) return null;
  const wgs = triangles.map((t) => t.map(([x, y]) => toWgs(x, y)));
  return wgs.length === 1
    ? { type: "Polygon", coordinates: [wgs[0]] }
    : { type: "MultiPolygon", coordinates: wgs.map((t) => [t]) };
}

function cornerCutoffByAngle(a: Coord[], b: Coord[], shared: Coord): number {
  const va = vecAway(a, shared), vb = vecAway(b, shared);
  const la = Math.sqrt(va[0] ** 2 + va[1] ** 2), lb = Math.sqrt(vb[0] ** 2 + vb[1] ** 2);
  if (la < 0.01 || lb < 0.01) return 3;
  const cos = Math.max(-1, Math.min(1, (va[0] * vb[0] + va[1] * vb[1]) / (la * lb)));
  const deg = Math.acos(cos) * 180 / Math.PI;
  if (deg >= 120) return 0;
  if (deg >= 90) return 2;
  return 3;
}

function vecAway(edge: Coord[], shared: Coord): Coord {
  const far = dist2(edge[0], shared) < dist2(edge[edge.length - 1], shared) ? edge[edge.length - 1] : edge[0];
  return [far[0] - shared[0], far[1] - shared[1]];
}

function findSharedVertex(a: Coord[], b: Coord[], tol = 0.5): Coord | null {
  for (const pa of a) for (const pb of b) {
    if (Math.sqrt(dist2(pa, pb)) < tol) return [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2];
  }
  return null;
}

function pointAlongEdge(edge: Coord[], startPt: Coord, distance: number): Coord | null {
  let coords = [...edge];
  if (dist2(coords[coords.length - 1], startPt) < dist2(coords[0], startPt)) coords = coords.reverse();
  let rem = distance;
  for (let i = 0; i < coords.length - 1; i++) {
    const segLen = Math.sqrt(dist2(coords[i], coords[i + 1]));
    if (segLen < 0.001) continue;
    if (rem <= segLen) {
      const r = rem / segLen;
      return [coords[i][0] + r * (coords[i + 1][0] - coords[i][0]), coords[i][1] + r * (coords[i + 1][1] - coords[i][1])];
    }
    rem -= segLen;
  }
  return null;
}

// ── Daylight Diagonal Envelope (채광사선 3D) ────────────

function computeDaylightEnvelope(
  adjacentEdges: Coord[][], polygon: Coord[], centroid: Coord, multiplier: number,
): SetbackResult["daylight_diagonal_envelope"] {
  const bounds = polygonBounds(polygon);
  const maxDepth = Math.min(Math.min(bounds.width, bounds.height) * 0.5, 30);
  if (maxDepth < 3) return null;

  const depthPairs: [number, number][] = [[0, maxDepth * 0.4], [maxDepth * 0.4, maxDepth]];
  const walls: Array<{ positions: number[][]; min_heights: number[]; max_heights: number[] }> = [];

  for (const edge of adjacentEdges) {
    const { nx, ny } = inwardNormal(edge, centroid);
    if (nx === 0 && ny === 0) continue;

    for (const [dS, dE] of depthPairs) {
      const pos: number[][] = [], minH: number[] = [], maxH: number[] = [];
      for (const [x, y] of edge) { pos.push(toWgs(x + nx * dS, y + ny * dS)); minH.push(0); maxH.push(dS * multiplier); }
      for (const [x, y] of [...edge].reverse()) { pos.push(toWgs(x + nx * dE, y + ny * dE)); minH.push(0); maxH.push(dE * multiplier); }
      walls.push({ positions: pos, min_heights: minH, max_heights: maxH });
    }
  }

  return walls.length > 0 ? { walls, multiplier, max_depth_m: maxDepth } : null;
}
