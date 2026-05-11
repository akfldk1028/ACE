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

  // Step 3 (2026-05-08) — envelope base z = ring 모든 corner terrain 평균 (단일 평면).
  // 이전: 첫 corner 1점 sample → 경사진 parcel에선 envelope 베이스가 한쪽 지면에 박혀
  //       다른 쪽이 떠 보이고 사선이 한쪽으로 비스듬히 솟는 비대칭 발생 (img_28~30).
  // 변경: 모든 corner terrain 평균 → §119② 가중평균 수평면(datum)에 해당.
  //       모든 corner에 같은 groundH가 더해져 envelope이 단일 평면 위에서 균일하게 솟음.
  // backend `envelope.datum_elevation_m` 은 §119 법적 H=0 절대값(EGM2008, Open-Meteo) —
  // Cesium globe(EGM96 가능) 과 좌표 단위 차이로 시각엔 안 씀. DatumInfoCard 표시만.
  const corners = envelope.slanted_polygons?.[0]?.corners ?? [];
  const groundH = ringTerrainMean(viewer, Cesium, corners);

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
          material: wallC.withAlpha(0.55),  // 0.25 → 0.55: 인접 건물 가림 줄임
          outline: true,
          outlineColor: wallC,
          outlineWidth: 4,
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
