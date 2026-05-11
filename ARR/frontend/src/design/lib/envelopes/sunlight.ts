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

  // Step 5 (2026-05-11) — envelope base z = NGII §119 datum 절대값 우선.
  // backend `envelope.datum_elevation_m` (NGII 5m EGM2008) 가 있으면 그걸 사용 →
  // 매스/envelope/datum 평면 모두 단일 절대 평면 위에서 솟음 (시각 통일).
  // fallback: ring corner terrain 평균 (Step 3, NGII datum 없을 때).
  const corners = envelope.slanted_polygons?.[0]?.corners ?? [];
  const datumZ = envelope.datum_elevation_m;
  const groundH = (datumZ != null && isFinite(datumZ) && datumZ !== 0)
    ? datumZ
    : ringTerrainMean(viewer, Cesium, corners);

  // Step 6 (2026-05-11) — 다이어그램(이재인 §86 그림) 부합:
  // (A) 9m 이하 부분: parcel inner ring 위 수직 박스 (H=0→10m, 모든 면 수직)
  // (B) 9m 초과 부분: 사선 polygon (corners H ≥ 10, 정북 → 정남 사선)
  // 이전: 북쪽 단일 벽만 + 사선이 지면까지. 사용자 지적: "전부 이 다이어그램 모습".
  const slopeCorners = envelope.slanted_polygons?.[0]?.corners ?? [];
  if (slopeCorners.length >= 3) {
    const baseFlat: number[] = [];
    for (const c of slopeCorners) baseFlat.push(c[0], c[1]);
    viewer.entities.add({
      id: `${SUNLIGHT_ENVELOPE_PREFIX}base-box`,
      polygon: {
        hierarchy: Cesium.Cartesian3.fromDegreesArray(baseFlat),
        height: groundH,
        extrudedHeight: groundH + 10,    // 9m → 10m (2023.9.12 §86 개정)
        material: wallC.withAlpha(0.30),
        outline: true,
        outlineColor: wallC,
        outlineWidth: 3,
      },
    });
    addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}base-box`);
  }

  // (2) 사선면 prism — 사선 측면 walls (Step 6, 다이어그램 부합):
  //   - 박스 윗면 (H=10m) → corner H_max (사선 끝)
  //   - 정북 edge (H1≈H2≈10): wall 0 높이 skip
  //   - 정남 edge: 거의 수직 wall (H_max → H_max)
  //   - 동/서 edge: 사선 wall (10 → H_max)
  // 그 위 사선 폴리곤 (perPositionHeight) — 윗면.
  if (Array.isArray(envelope.slanted_polygons)) {
    for (let pi = 0; pi < envelope.slanted_polygons.length; pi++) {
      const poly = envelope.slanted_polygons[pi];
      const corners = poly.corners as number[][];
      if (!corners || corners.length < 3) continue;

      // 측면 wall — corner i → i+1, 박스 윗면(10) → corner z
      for (let i = 0; i < corners.length; i++) {
        const c1 = corners[i];
        const c2 = corners[(i + 1) % corners.length];
        const h1 = c1[2], h2 = c2[2];
        if (h1 <= 10.5 && h2 <= 10.5) continue;  // 정북 edge 박스 위 평탄
        viewer.entities.add({
          id: `${SUNLIGHT_ENVELOPE_PREFIX}slope-side-${pi}-${i}`,
          wall: {
            positions: Cesium.Cartesian3.fromDegreesArray([c1[0], c1[1], c2[0], c2[1]]),
            minimumHeights: [groundH + 10, groundH + 10],
            maximumHeights: [groundH + h1, groundH + h2],
            material: slopeC.withAlpha(0.40),
            outline: true,
            outlineColor: slopeC,
            outlineWidth: 2,
          },
        });
        addedIds.push(`${SUNLIGHT_ENVELOPE_PREFIX}slope-side-${pi}-${i}`);
      }

      // 윗면 사선 폴리곤
      const roofFlat: number[] = [];
      for (const c of corners) roofFlat.push(c[0], c[1], c[2] + groundH);

      const id = `${SUNLIGHT_ENVELOPE_PREFIX}roof-${pi}`;
      viewer.entities.add({
        id,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArrayHeights(roofFlat),
          perPositionHeight: true,
          material: slopeC.withAlpha(0.40),
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
