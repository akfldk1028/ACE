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
  wall: '#dc2626',   // 진홍
  slope: '#ec4899',  // 핑크
};

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

  // Phase 2B — ground reference 결정 (3-state):
  //   "open_meteo" + 유효한 datum_elevation_m → §119 datum 절대 표고 (legally accurate)
  //   "failed" / null / undefined            → terrain.getHeight() fallback (LOCKED SPEC)
  //
  // NOTE: datum_elevation_m (Open-Meteo §119 가중평균)와 terrainH (Cesium globe.getHeight)는
  // 서로 다른 DEM 소스라 같은 좌표에서도 수 m 차이 가능. source='open_meteo'일 때
  // envelope이 §119 법적 datum에 정확히 앉는 대신, Cesium 지형 메쉬 위로 떠보이거나
  // 살짝 파묻힌 모습으로 보일 수 있음. ENABLE_DATUM_ELEVATION 프로덕션 토글 전 시각 검증 필수.
  const terrainH = sampleTerrainAt(
    viewer, Cesium, envelope.slanted_polygons?.[0]?.corners?.[0],
  );
  const groundH = (
    envelope.elevation_source === 'open_meteo'
    && typeof envelope.datum_elevation_m === 'number'
    && isFinite(envelope.datum_elevation_m)
  ) ? envelope.datum_elevation_m : terrainH;

  // (1) 북쪽 수직벽 — 바닥 → H=10m (직선→사선 올라가는 면)
  if (Array.isArray(envelope.walls)) {
    for (let wi = 0; wi < envelope.walls.length; wi++) {
      const wall = envelope.walls[wi];
      const positions = wall.positions;
      const maxH: number[] = wall.max_heights;
      const minH: number[] = wall.min_heights;
      if (!positions || positions.length < 2 || positions.length !== maxH.length) continue;

      const flat: number[] = [];
      for (const [lng, lat] of positions) flat.push(lng, lat);

      const id = `${SUNLIGHT_ENVELOPE_PREFIX}wall-${wi}`;
      viewer.entities.add({
        id,
        wall: {
          positions: Cesium.Cartesian3.fromDegreesArray(flat),
          minimumHeights: minH.map((h: number) => h + groundH),
          maximumHeights: maxH.map((h: number) => h + groundH),
          material: wallC.withAlpha(0.25),
          outline: true,
          outlineColor: wallC,
          outlineWidth: 3,
        },
      });
      addedIds.push(id);
    }
  }

  // (2) 경사 지붕 — H=10m → 50m (법규 사선, perPositionHeight)
  if (Array.isArray(envelope.slanted_polygons)) {
    for (let pi = 0; pi < envelope.slanted_polygons.length; pi++) {
      const poly = envelope.slanted_polygons[pi];
      const corners = poly.corners as number[][];
      if (!corners || corners.length < 3) continue;

      const roofFlat: number[] = [];
      for (const c of corners) roofFlat.push(c[0], c[1], c[2] + groundH);

      const id = `${SUNLIGHT_ENVELOPE_PREFIX}roof-${pi}`;
      viewer.entities.add({
        id,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArrayHeights(roofFlat),
          perPositionHeight: true,
          material: slopeC.withAlpha(0.28),
          outline: true,
          outlineColor: slopeC,
          outlineWidth: 3,
        },
      });
      addedIds.push(id);
    }
  }

  return addedIds;
}

/**
 * 첫 corner 위치에서 terrain 고도 sample.
 * 실패시 0 반환 (지형 데이터 없는 환경).
 */
function sampleTerrainAt(viewer: any, Cesium: any, corner: number[] | undefined): number {
  if (!corner || corner.length < 2) return 0;
  try {
    const carto = Cesium.Cartographic.fromDegrees(corner[0], corner[1]);
    const h = viewer.scene.globe.getHeight(carto);
    return typeof h === 'number' && isFinite(h) ? h : 0;
  } catch {
    return 0;
  }
}
