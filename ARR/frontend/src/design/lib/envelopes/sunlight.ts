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

  // (2) 사선면은 기본 clean view에서 대표 면으로 단순화해 표시한다.
  // backend 원본은 계산용 상세 geometry라 500+ corner가 될 수 있고,
  // 그대로 그리면 VWorld 위에서 contour/fence처럼 보여 사용자가 법규면을 읽기 어렵다.
  // 숨김은 `?surface=0`, 정밀 geometry 확인은 `?surface=detail` 또는 `?layers=all`로 켠다.
  const surfaceMode = params.get('surface');
  const showDetailedSurface = surfaceMode === 'detail' || params.get('layers') === 'all';
  const showSurface = surfaceMode !== '0';
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

  const showProfileFill = params.get('profileFill') === '1' || params.get('layers') === 'all';
  const showProfileLine = params.get('profile') === '1' || params.get('layers') === 'all';
  if ((showProfileFill || showProfileLine) && Array.isArray(envelope.profile_polylines)) {
    for (let i = 0; i < envelope.profile_polylines.length; i++) {
      const profile = envelope.profile_polylines[i];
      const points = profile?.points;
      if (!points || points.length < 2) continue;
      if (showProfileFill && points.length >= 3) {
        viewer.entities.add({
          id: `${SUNLIGHT_ENVELOPE_PREFIX}profile-fill-${i}`,
          polygon: {
            hierarchy: new Cesium.PolygonHierarchy(
              points.map((p) => Cesium.Cartesian3.fromDegrees(p[0], p[1], groundH + p[2])),
            ),
            perPositionHeight: true,
            material: slopeC.withAlpha(0.20),
            outline: false,
          },
        });
        addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}profile-fill-${i}`);
      }
      if (showProfileLine) {
        viewer.entities.add({
          id: `${SUNLIGHT_ENVELOPE_PREFIX}profile-${i}`,
          polyline: {
            positions: points.map((p) => Cesium.Cartesian3.fromDegrees(p[0], p[1], groundH + p[2])),
            width: 6,
            material: slopeC,
          },
        });
        addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}profile-${i}`);
      }
    }
  }

  return addedIds;
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
