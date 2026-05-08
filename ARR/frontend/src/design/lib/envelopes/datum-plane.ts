/**
 * §119 datum 평면 시각화 (Cesium 3D).
 *
 * "지도에도 대지 레벨이 떠야 한다" 의도 반영. 사용자에게 §119 H=0 절대 표고를
 * 시각적으로 보여주는 보조 entity.
 *
 * **Phase 2D-3 LOCKED SPEC 보호**: envelope/setback 시각은 terrainH 통일 그대로.
 * 이 모듈은 추가 시각만 함. 기존 entity 변경 없음.
 *
 * Render:
 *   1. parcel ring 위 datum_m 높이의 반투명 노란 평면 (지면에서 떠 있음)
 *   2. parcel centroid에 텍스트 라벨 "H₀ = 38.42m"
 *
 * datum_m이 0/null/미계산이면 렌더 X (LOCKED SPEC fallback 동일).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export const DATUM_PLANE_PREFIX = 'design-datum-plane-';

export interface DatumPlaneColors {
  fill: string;     // 평면 채색 (반투명)
  outline: string;  // 외곽선
  label: string;    // 라벨 텍스트 색
}

export const DEFAULT_DATUM_COLORS: DatumPlaneColors = {
  fill: '#facc15',     // 노랑 (datum 표고)
  outline: '#eab308',  // 진노랑
  label: '#fde047',    // 라벨 노랑
};

/**
 * Cesium viewer에 §119 datum 평면 + 라벨 렌더링.
 *
 * @param viewer Cesium viewer 인스턴스
 * @param Cesium global Cesium namespace
 * @param datum_m §119 H=0 절대 표고 (m, EGM2008). 0/null이면 렌더 X.
 * @param parcelRing parcel 외곽 polygon ring [[lng, lat], ...]
 * @param colors 색상 (선택)
 * @returns 추가된 entity id 배열 (정리용)
 */
export function renderDatumPlane(
  viewer: any,
  Cesium: any,
  datum_m: number | null | undefined,
  parcelRing: number[][] | null | undefined,
  colors: DatumPlaneColors = DEFAULT_DATUM_COLORS,
): string[] {
  if (!viewer || !Cesium) return [];
  if (datum_m == null || !isFinite(datum_m) || datum_m === 0) return [];
  if (!parcelRing || parcelRing.length < 3) return [];

  const fillC = Cesium.Color.fromCssColorString(colors.fill);
  const outlineC = Cesium.Color.fromCssColorString(colors.outline);
  const labelC = Cesium.Color.fromCssColorString(colors.label);
  const addedIds: string[] = [];

  // (1) datum 평면 — parcel ring을 terrain 표면에 클램프 (지형과 시각 일관성).
  // 정확한 §119 datum_m 값은 라벨에 표시. Cesium globe terrain DEM과 Open-Meteo 90m DEM이
  // 다른 출처라 두 값 수 m 차이 있음 (메모리 박제 known issue) — 평면은 시각용, 라벨이 정답.
  const flat: number[] = [];
  for (const [lng, lat] of parcelRing) flat.push(lng, lat);

  const planeId = `${DATUM_PLANE_PREFIX}plane`;
  viewer.entities.add({
    id: planeId,
    polygon: {
      hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
      // Cesium 요구: heightReference 사용 시 height도 정의 필수 (warning 회피)
      height: 0,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      material: fillC.withAlpha(0.45),
      outline: false,   // CLAMP_TO_GROUND는 outline 미지원 → polyline 별도
    },
  });
  addedIds.push(planeId);

  // outline polyline (clampToGround로 terrain 따라감)
  const outlineId = `${DATUM_PLANE_PREFIX}outline`;
  viewer.entities.add({
    id: outlineId,
    polyline: {
      positions: Cesium.Cartesian3.fromDegreesArray(flat),
      width: 4,
      material: outlineC,
      clampToGround: true,
    },
  });
  addedIds.push(outlineId);

  // (2) parcel centroid 위 라벨 "H₀ = 38.42m" — datum_m + 약간 위 띄움
  let cx = 0;
  let cy = 0;
  for (const [lng, lat] of parcelRing) {
    cx += lng;
    cy += lat;
  }
  cx /= parcelRing.length;
  cy /= parcelRing.length;

  const labelId = `${DATUM_PLANE_PREFIX}label`;
  viewer.entities.add({
    id: labelId,
    // 라벨은 terrain 표면 위로 클램프 (parcel 평면 위에 떠 있음)
    position: Cesium.Cartesian3.fromDegrees(cx, cy),
    label: {
      text: `§119 H₀ = ${datum_m.toFixed(2)}m`,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      font: '700 18px ui-monospace, SFMono-Regular, Menlo, monospace',
      fillColor: labelC,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 4,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
      pixelOffset: new Cesium.Cartesian2(0, -12),
      backgroundColor: Cesium.Color.BLACK.withAlpha(0.6),
      backgroundPadding: new Cesium.Cartesian2(8, 4),
      showBackground: true,
      // 멀리서도 보이게 거리 기반 스케일
      scaleByDistance: new Cesium.NearFarScalar(50, 1.2, 5000, 0.7),
      // disableDepthTestDistance — 평면 뒤에 가려지지 않도록
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  });
  addedIds.push(labelId);

  return addedIds;
}

/** Viewer에서 기존 datum entity 제거 (re-render 전 정리용). */
export function clearDatumPlane(viewer: any): void {
  if (!viewer) return;
  const toRemove: any[] = [];
  for (const e of viewer.entities.values) {
    if (typeof e.id === 'string' && e.id.startsWith(DATUM_PLANE_PREFIX)) {
      toRemove.push(e);
    }
  }
  for (const e of toRemove) viewer.entities.remove(e);
}
