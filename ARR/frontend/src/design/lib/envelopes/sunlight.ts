/**
 * 정북 일조사선 envelope Cesium renderer (건축법 §61①, 시행령 §86①).
 *
 * ⚠️ LOCKED SPEC — DO NOT MODIFY without reading
 *     memory/arr/session14/envelope-locked-spec.md
 * session 14 (2026-04-21) 사용자 검증 결과. 과거 12회+ 반복 실패 후 확정.
 *
 * Contract (backend `land/services/envelopes/sunlight.py` 와 1:1):
 *   envelope = {
 *     walls:            [{positions, min_heights, max_heights, kind="north_vertical"}]
 *     slanted_polygons: [{corners: [[lng, lat, h]...], kind="slope"}]
 *     ...
 *   }
 *
 * 렌더 요소 (img_5 프로필과 일치):
 *   (1) 북쪽 수직벽 : 바닥 → H=10m (직선→사선 올라가는 면)
 *   (2) 경사 지붕   : H=10m → 50m (법규 사선)
 *
 * 렌더 안 하는 것 (사용자 img_18 피드백):
 *   - 사선에서 바닥으로 떨어지는 측면 벽
 *   - plateau 별도 polygon (경사 지붕이 H=10m에서 시작하므로 불필요)
 *   - daylight_diagonal_envelope (보라 채광사선, 정북일조와 시각 충돌)
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

import type { SunlightEnvelope } from '../../../land/lib/types';

export const SUNLIGHT_ENVELOPE_PREFIX = 'design-setback-sunlight-';

export interface SunlightColors {
  wall: string;  // 북쪽 수직벽 (진홍 권장)
  slope: string; // 경사 지붕 (핑크 권장)
}

export const DEFAULT_SUNLIGHT_COLORS: SunlightColors = {
  wall: '#22c55e',
  slope: '#22c55e',
};

function simplifyClosedRing<T>(ring: T[], maxPoints: number): T[] {
  if (ring.length <= maxPoints) return ring;
  const step = Math.ceil(ring.length / maxPoints);
  const simplified: T[] = [];
  for (let i = 0; i < ring.length; i += step) simplified.push(ring[i]);
  return simplified.length >= 3 ? simplified : ring.slice(0, Math.min(ring.length, maxPoints));
}

/**
 * Cesium viewer에 sunlight envelope 렌더링.
 *
 * @param viewer  Cesium viewer 인스턴스
 * @param Cesium  global Cesium namespace
 * @param envelope  backend response의 sunlight_envelope 객체
 * @param colors  렌더 색상 (선택)
 *
 * @returns 추가된 entity id 배열 (정리용)
 */
export function renderSunlightEnvelope(
  viewer: any,
  Cesium: any,
  envelope: SunlightEnvelope | null | undefined,
  colors: SunlightColors = DEFAULT_SUNLIGHT_COLORS,
): string[] {
  if (!envelope) return [];

  const wallC = Cesium.Color.fromCssColorString(colors.wall);
  const slopeC = Cesium.Color.fromCssColorString(colors.slope);
  const addedIds: string[] = [];

  // Step 5 (2026-05-11) — envelope base z = NGII §119 datum 절대값 우선.
  // backend `envelope.datum_elevation_m` (NGII 5m EGM2008) 가 있으면 그걸 사용 →
  // 매스/envelope/datum 평면 모두 단일 절대 평면 위에서 솟음 (시각 통일).
  // fallback: ring corner terrain 평균 (Step 3, NGII datum 없을 때).
  const corners = envelope.slanted_polygons?.[0]?.corners ?? [];
  const datumZ = envelope.datum_elevation_m;
  const groundH = (datumZ != null && isFinite(datumZ) && datumZ !== 0)
    ? datumZ
    : ringTerrainMean(viewer, Cesium, corners);

  // (1) 북쪽 수직벽 (H=0→10m).
  // 기본 clean view에서는 울타리처럼 보이는 wall 반복을 숨긴다.
  // 법규 디버그가 필요할 때만 URL에 `?walls=1` 또는 `?layers=all`로 켠다.
  const params = new URLSearchParams(window.location.search);
  const showWalls = params.get('walls') === '1' || params.get('layers') === 'all';
  if (showWalls && Array.isArray(envelope.walls)) {
    const wallStep = Math.max(1, Math.ceil(envelope.walls.length / 32));
    for (let i = 0; i < envelope.walls.length; i += wallStep) {
      const wall = envelope.walls[i];
      if (!wall?.positions || wall.positions.length < 2) continue;
      const c1 = wall.positions[0];
      const c2 = wall.positions[1];
      const min1 = wall.min_heights?.[0] ?? 0;
      const min2 = wall.min_heights?.[1] ?? min1;
      const max1 = wall.max_heights?.[0] ?? 10;
      const max2 = wall.max_heights?.[1] ?? max1;
      viewer.entities.add({
        id: `${SUNLIGHT_ENVELOPE_PREFIX}wall-${i}`,
        wall: {
          positions: Cesium.Cartesian3.fromDegreesArray([c1[0], c1[1], c2[0], c2[1]]),
          minimumHeights: [groundH + min1, groundH + min2],
          maximumHeights: [groundH + max1, groundH + max2],
          material: wallC.withAlpha(0.45),
          outline: true,
          outlineColor: wallC,
          outlineWidth: 3,
        },
      });
      addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}wall-${i}`);
    }
  }

  // Step 13 (2026-05-11) — plateau footprint 분리. 사용자 docs/img_44 요구:
  // plateau는 박스 윗면 전체가 아니라 정북 boundary ~ PLATEAU_END_M(5m) 띠만.
  // backend가 envelope.plateau_polygon으로 정확한 footprint 제공 → 그걸 사용.
  // backend가 못 제공하면 (정북 edge 없음 등) plateau 생략.
  // plateau polygon은 단면 프로파일에 포함해서 표현한다. 별도 채움면은
  // VWorld 지적/도로/레벨 마커를 가려 검토성이 떨어진다.

  // (2) 사선면은 기본 clean view에서 끈다.
  // 허용 볼륨 계산상 H<=10m 구간은 수평 plateau가 생길 수 있지만, VWorld에서
  // 넓은 면으로 보이면 사용자가 "정북일조는 수직벽→사선"이라는 단면 규칙을
  // 읽기 어렵다. 법규 debug가 필요할 때만 `?surface=1/detail`로 켠다.
  // backend 원본은 계산용 상세 geometry라 500+ corner가 될 수 있고,
  // 그대로 그리면 VWorld 위에서 contour/fence처럼 보여 사용자가 법규면을 읽기 어렵다.
  // 정밀 geometry 확인은 `?surface=detail` 또는 `?layers=all`로 켠다.
  const surfaceMode = params.get('surface');
  const showDetailedSurface = surfaceMode === 'detail' || params.get('layers') === 'all';
  const showSurface = surfaceMode === '1' || showDetailedSurface;
  if (showSurface && Array.isArray(envelope.slanted_polygons)) {
    for (let pi = 0; pi < envelope.slanted_polygons.length; pi++) {
      const poly = envelope.slanted_polygons[pi];
      const sourceCorners = poly.corners as number[][];
      const corners = showDetailedSurface ? sourceCorners : simplifyClosedRing(sourceCorners, 48);
      if (!corners || corners.length < 3) continue;

      const id = `${SUNLIGHT_ENVELOPE_PREFIX}roof-${pi}`;
      const roofFlat: number[] = [];
      for (const c of corners) roofFlat.push(c[0], c[1], c[2] + groundH);
      viewer.entities.add({
        id: `${id}-surface`,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArrayHeights(roofFlat),
          perPositionHeight: true,
          material: slopeC.withAlpha(showDetailedSurface ? 0.26 : 0.10),
          outline: false,
        },
      });
      addedIds.push(`${id}-surface`);

      const outlinePositions = corners.map((c) =>
        Cesium.Cartesian3.fromDegrees(c[0], c[1], groundH + c[2]),
      );
      outlinePositions.push(outlinePositions[0]);
      viewer.entities.add({
        id,
        polyline: {
          positions: outlinePositions,
          width: showDetailedSurface ? 5 : 3,
          material: slopeC.withAlpha(showDetailedSurface ? 0.9 : 0.64),
        },
      });
      addedIds.push(id);
    }
  }

  const showMesh = params.get('mesh') === '1' || params.get('layers') === 'all';
  if (showMesh && Array.isArray(envelope.envelope_layers)) {
    for (let i = 0; i < envelope.envelope_layers.length; i++) {
      const layer = envelope.envelope_layers[i];
      const ring = layer?.footprint_wgs;
      if (!ring || ring.length < 3) continue;
      const positions = ring.map((p) =>
        Cesium.Cartesian3.fromDegrees(p[0], p[1], groundH + layer.h_top),
      );
      positions.push(positions[0]);
      viewer.entities.add({
        id: `${SUNLIGHT_ENVELOPE_PREFIX}mesh-layer-${i}`,
        polyline: {
          positions,
          width: 3,
          material: slopeC.withAlpha(0.78),
        },
      });
      addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}mesh-layer-${i}`);
    }
  }

  const showProfileFill = params.get('profileFill') !== '0';
  // 정북일조는 매스 유무와 무관한 기본 법규 envelope다.
  // 넓은 surface는 debug로 숨기더라도, 수직 시작선 + 사선 단면선은 항상 보여야
  // 사용자가 "이 안에 매스가 들어갈 수 있는지" 판단할 수 있다.
  const showProfileLine = params.get('profile') !== '0';
  const detailedProfile = params.get('profile') === 'detail' || params.get('layers') === 'all';
  if ((showProfileFill || showProfileLine) && Array.isArray(envelope.profile_polylines)) {
    for (let i = 0; i < envelope.profile_polylines.length; i++) {
      const profile = envelope.profile_polylines[i];
      const points = profile?.points;
      if (!points || points.length < 2) continue;
      if (showProfileFill && points.length >= 3) {
        const ribbonWidthM = Math.max(1.2, Math.min(8, Number(params.get('profileWidth') ?? 2.8) || 2.8));
        const wallRibbon = buildProfileWallRibbon(Cesium, points, groundH, ribbonWidthM);
        if (wallRibbon) {
          viewer.entities.add({
            id: `${SUNLIGHT_ENVELOPE_PREFIX}profile-fill-wall-${i}`,
            wall: {
              positions: wallRibbon.positions,
              minimumHeights: wallRibbon.minimumHeights,
              maximumHeights: wallRibbon.maximumHeights,
              material: wallC.withAlpha(0.18),
              outline: true,
              outlineColor: wallC.withAlpha(0.72),
            },
          });
          addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}profile-fill-wall-${i}`);
        }

        const slopeRibbon = buildSlopedRibbon(Cesium, points, groundH, ribbonWidthM);
        if (slopeRibbon) {
          viewer.entities.add({
            id: `${SUNLIGHT_ENVELOPE_PREFIX}profile-fill-slope-${i}`,
            polygon: {
              hierarchy: new Cesium.PolygonHierarchy(slopeRibbon),
              perPositionHeight: true,
              material: slopeC.withAlpha(0.22),
              outline: false,
            },
          });
          addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}profile-fill-slope-${i}`);
        }
      }
      if (showProfileLine) {
        const linePoints = detailedProfile || points.length < 4
          ? points
          : [points[0], points[1], points[points.length - 1]];
        viewer.entities.add({
          id: `${SUNLIGHT_ENVELOPE_PREFIX}profile-${i}`,
          polyline: {
            positions: linePoints.map((p) => Cesium.Cartesian3.fromDegrees(p[0], p[1], groundH + p[2])),
            width: detailedProfile ? 7 : 6,
            material: new Cesium.PolylineGlowMaterialProperty({
              color: slopeC,
              glowPower: 0.16,
              taperPower: 0.9,
            }),
          },
        });
        addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}profile-${i}`);
        const labelPoint = linePoints[Math.max(1, Math.floor(linePoints.length / 2))];
        if (i === 0 && labelPoint) {
          viewer.entities.add({
            id: `${SUNLIGHT_ENVELOPE_PREFIX}profile-label`,
            position: Cesium.Cartesian3.fromDegrees(labelPoint[0], labelPoint[1], groundH + Math.max(12, labelPoint[2] + 2)),
            label: {
              text: `정북일조\n수직 10m + ${envelope.slope ?? 2}:1`,
              font: '700 12px ui-monospace, SFMono-Regular, Menlo, monospace',
              fillColor: Cesium.Color.WHITE,
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 3,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              backgroundColor: Cesium.Color.BLACK.withAlpha(0.46),
              backgroundPadding: new Cesium.Cartesian2(7, 4),
              showBackground: true,
              pixelOffset: new Cesium.Cartesian2(44, -30),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            },
          });
          addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}profile-label`);
        }
      }
    }
  }

  return addedIds;
}

type ProfilePoint = [number, number, number];

function toLocalMeters(origin: ProfilePoint, point: ProfilePoint) {
  const latRad = origin[1] * Math.PI / 180;
  return {
    x: (point[0] - origin[0]) * 111_320 * Math.cos(latRad),
    y: (point[1] - origin[1]) * 110_540,
  };
}

function offsetLngLat(point: ProfilePoint, nx: number, ny: number, offsetM: number): ProfilePoint {
  const latRad = point[1] * Math.PI / 180;
  return [
    point[0] + (nx * offsetM) / (111_320 * Math.cos(latRad)),
    point[1] + (ny * offsetM) / 110_540,
    point[2],
  ];
}

function profileNormal(start: ProfilePoint, end: ProfilePoint) {
  const delta = toLocalMeters(start, end);
  const len = Math.hypot(delta.x, delta.y);
  if (!isFinite(len) || len < 0.05) return null;
  return { nx: -delta.y / len, ny: delta.x / len };
}

function buildProfileWallRibbon(Cesium: any, points: number[][], groundH: number, widthM: number) {
  const p0 = points[0] as ProfilePoint;
  const p2 = (points[2] ?? points[1]) as ProfilePoint;
  const normal = profileNormal(p0, p2);
  if (!normal) return null;

  const a = offsetLngLat(p0, normal.nx, normal.ny, widthM / 2);
  const b = offsetLngLat(p2, normal.nx, normal.ny, widthM / 2);
  return {
    positions: Cesium.Cartesian3.fromDegreesArray([a[0], a[1], b[0], b[1]]),
    minimumHeights: [groundH + (p0[2] ?? 0), groundH + (p2[2] ?? 10)],
    maximumHeights: [groundH + 10, groundH + (p2[2] ?? 10)],
  };
}

function buildSlopedRibbon(Cesium: any, points: number[][], groundH: number, widthM: number) {
  const start = (points[2] ?? points[1]) as ProfilePoint;
  const end = points[points.length - 1] as ProfilePoint;
  const normal = profileNormal(start, end);
  if (!normal) return null;

  const half = widthM / 2;
  const a1 = offsetLngLat(start, normal.nx, normal.ny, half);
  const a2 = offsetLngLat(start, normal.nx, normal.ny, -half);
  const b2 = offsetLngLat(end, normal.nx, normal.ny, -half);
  const b1 = offsetLngLat(end, normal.nx, normal.ny, half);
  return [a1, b1, b2, a2].map((p) => Cesium.Cartesian3.fromDegrees(p[0], p[1], groundH + p[2]));
}

/**
 * Ring 모든 corner의 terrain 고도 평균 (Step 3 — datum 가중평균 시각).
 *
 * 모든 corner의 terrain.getHeight()를 sample해서 평균. parcel이 경사졌어도
 * envelope 베이스가 단일 평면 위에서 균일하게 솟도록 단일 z 값으로 통일.
 *
 * 실패한 sample은 평균에서 제외. 모두 실패면 0.
 */
function ringTerrainMean(viewer: any, Cesium: any, corners: number[][]): number {
  if (!corners || corners.length === 0) return 0;
  let sum = 0;
  let n = 0;
  for (const c of corners) {
    if (!c || c.length < 2) continue;
    try {
      const carto = Cesium.Cartographic.fromDegrees(c[0], c[1]);
      const h = viewer.scene.globe.getHeight(carto);
      if (typeof h === 'number' && isFinite(h)) {
        sum += h;
        n += 1;
      }
    } catch {
      // sample 실패한 corner skip
    }
  }
  return n > 0 ? sum / n : 0;
}
