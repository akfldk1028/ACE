/**
 * Geometry Math — 2D 기하 원시함수 (한국 flat-earth 투영 포함).
 *
 * setback-geometry, road-detector 등에서 공유.
 * Shapely/Turf 없이 순수 수학으로 구현.
 */

export type Coord = [number, number];

// ── Flat-earth projection (Korea, lat ~37°) ─────────────
// 한국 위도 33~38° 범위에서 오차 < 0.1%

export const DEG_LAT_M = 110_574;
const COS_37 = Math.cos(37 * Math.PI / 180);
export const DEG_LON_M = 111_320 * COS_37;

export function toLocal(lon: number, lat: number): Coord {
  return [lon * DEG_LON_M, lat * DEG_LAT_M];
}

export function toWgs(x: number, y: number): Coord {
  return [x / DEG_LON_M, y / DEG_LAT_M];
}

// ── Scalar ──────────────────────────────────────────────

/** Squared distance between two points. */
export function dist2(a: Coord, b: Coord): number {
  return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
}

export function edgeLength(coords: Coord[]): number {
  let total = 0;
  for (let i = 0; i < coords.length - 1; i++) {
    total += Math.sqrt(dist2(coords[i], coords[i + 1]));
  }
  return total;
}

// ── Polygon ─────────────────────────────────────────────

export function polygonCentroid(coords: Coord[]): Coord {
  let cx = 0, cy = 0;
  const n = coords.length - 1; // exclude closing point
  for (let i = 0; i < n; i++) {
    cx += coords[i][0];
    cy += coords[i][1];
  }
  return [cx / n, cy / n];
}

export function polygonArea(coords: Coord[]): number {
  let area = 0;
  const n = coords.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += coords[i][0] * coords[j][1];
    area -= coords[j][0] * coords[i][1];
  }
  return Math.abs(area) / 2;
}

export function polygonBounds(coords: Coord[]): {
  minX: number; minY: number; maxX: number; maxY: number;
  width: number; height: number;
} {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const [x, y] of coords) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY };
}

// ── Normal ──────────────────────────────────────────────

export function inwardNormal(edge: Coord[], centroid: Coord): { nx: number; ny: number } {
  const dx = edge[1][0] - edge[0][0];
  const dy = edge[1][1] - edge[0][1];
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 0.01) return { nx: 0, ny: 0 };

  let nx = -dy / len;
  let ny = dx / len;

  const midX = (edge[0][0] + edge[1][0]) / 2;
  const midY = (edge[0][1] + edge[1][1]) / 2;
  const toCx = centroid[0] - midX;
  const toCy = centroid[1] - midY;
  if (nx * toCx + ny * toCy < 0) { nx = -nx; ny = -ny; }

  return { nx, ny };
}

export function outwardNormal(edge: Coord[], centroid: Coord): { nx: number; ny: number } {
  const { nx, ny } = inwardNormal(edge, centroid);
  return { nx: -nx, ny: -ny };
}

// ── Intersection ────────────────────────────────────────

export function segmentIntersection(p1: Coord, p2: Coord, p3: Coord, p4: Coord): Coord | null {
  const d1x = p2[0] - p1[0], d1y = p2[1] - p1[1];
  const d2x = p4[0] - p3[0], d2y = p4[1] - p3[1];
  const denom = d1x * d2y - d1y * d2x;
  if (Math.abs(denom) < 1e-10) return null;

  const t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / denom;
  const u = ((p3[0] - p1[0]) * d1y - (p3[1] - p1[1]) * d1x) / denom;

  if (t >= 0 && t <= 1 && u >= 0 && u <= 1) {
    return [p1[0] + t * d1x, p1[1] + t * d1y];
  }
  return null;
}

/** Unbounded line-line intersection (no t/u clamping). */
export function lineLineIntersection(p1: Coord, p2: Coord, p3: Coord, p4: Coord): Coord | null {
  const d1x = p2[0] - p1[0], d1y = p2[1] - p1[1];
  const d2x = p4[0] - p3[0], d2y = p4[1] - p3[1];
  const denom = d1x * d2y - d1y * d2x;
  if (Math.abs(denom) < 1e-10) return null;

  const t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / denom;
  return [p1[0] + t * d1x, p1[1] + t * d1y];
}

// ── Point-in-Polygon ────────────────────────────────────

export function pointInPolygon(point: Coord, polygon: Coord[]): boolean {
  let inside = false;
  const [px, py] = point;
  const n = polygon.length;

  for (let i = 0, j = n - 1; i < n; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  return inside;
}

// ── Line Clipping ───────────────────────────────────────

/** Clip a line to a polygon — returns interior portion. */
export function clipLineToPolygon(line: Coord[], polygon: Coord[]): Coord[] | null {
  const result: Coord[] = [];

  for (let i = 0; i < line.length; i++) {
    if (pointInPolygon(line[i], polygon)) {
      result.push(line[i]);
    } else if (i > 0 && pointInPolygon(line[i - 1], polygon)) {
      const inter = linePolygonIntersection(line[i - 1], line[i], polygon);
      if (inter) result.push(inter);
    } else if (i < line.length - 1 && pointInPolygon(line[i + 1], polygon)) {
      const inter = linePolygonIntersection(line[i], line[i + 1], polygon);
      if (inter) result.push(inter);
    }
  }

  return result.length >= 2 ? result : null;
}

function linePolygonIntersection(p1: Coord, p2: Coord, polygon: Coord[]): Coord | null {
  let closest: Coord | null = null;
  let minDist = Infinity;

  for (let i = 0; i < polygon.length - 1; i++) {
    const inter = segmentIntersection(p1, p2, polygon[i], polygon[i + 1]);
    if (inter) {
      const d = dist2(p1, inter);
      if (d < minDist) { minDist = d; closest = inter; }
    }
  }
  return closest;
}

// ── Polygon Buffer ──────────────────────────────────────

/** Inward polygon buffer via edge offset + consecutive intersection. */
export function bufferPolygonInward(coords: Coord[], distance: number): Coord[] | null {
  if (coords.length < 4) return null;

  const centroid = polygonCentroid(coords);
  const n = coords.length - 1;

  const offsetEdges: { p1: Coord; p2: Coord }[] = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const edge: Coord[] = [coords[i], coords[j]];
    const { nx, ny } = inwardNormal(edge, centroid);
    offsetEdges.push({
      p1: [coords[i][0] + nx * distance, coords[i][1] + ny * distance],
      p2: [coords[j][0] + nx * distance, coords[j][1] + ny * distance],
    });
  }

  const result: Coord[] = [];
  for (let i = 0; i < offsetEdges.length; i++) {
    const j = (i + 1) % offsetEdges.length;
    const inter = lineLineIntersection(
      offsetEdges[i].p1, offsetEdges[i].p2,
      offsetEdges[j].p1, offsetEdges[j].p2,
    );
    result.push(inter ?? offsetEdges[i].p2);
  }

  if (result.length < 3) return null;
  result.push(result[0]);
  return result;
}

// ── Point-to-Segment Distance ───────────────────────────

export function pointToSegDist(p: Coord, a: Coord, b: Coord): number {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const lenSq = dx * dx + dy * dy;
  if (lenSq < 0.0001) return Math.sqrt(dist2(p, a));
  let t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  return Math.sqrt((p[0] - (a[0] + t * dx)) ** 2 + (p[1] - (a[1] + t * dy)) ** 2);
}
