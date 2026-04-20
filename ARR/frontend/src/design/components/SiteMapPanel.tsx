import React, { useRef, useCallback, useState } from 'react';
import { useVworld3D } from '../../land/hooks/use-vworld-3d';
import { reverse } from '../../land/lib/land-api-client';
import type { GeoJSONFeature, SetbackGeometry } from '../lib/types';
import type { SunlightEnvelope } from '../../land/lib/types';

/* eslint-disable @typescript-eslint/no-explicit-any */
const getCesium = (): any => (window as any).Cesium;

const MASS_PREFIX = 'design-mass-';
const SETBACK_PREFIX = 'design-setback-';

interface Props {
  sitePolygon: object | null;
  massFeatures?: GeoJSONFeature[];
  selectedDesignId?: number;
  onParcelClick?: (pnu: string, address: string) => void;
  setbackGeometries?: Record<string, SetbackGeometry>;
}

/** Extract outer ring from Polygon or MultiPolygon geometry */
function extractRing(geometry: { type: string; coordinates: any }): number[][] | null {
  if (geometry.type === 'Polygon') return geometry.coordinates[0];
  if (geometry.type === 'MultiPolygon') return geometry.coordinates[0]?.[0];
  return null;
}

/** Clear all 3D mass entities from viewer */
function clearMassEntities(viewer: any) {
  const toRemove: any[] = [];
  for (const e of viewer.entities.values) {
    if (typeof e.id === 'string' && e.id.startsWith(MASS_PREFIX)) {
      toRemove.push(e);
    }
  }
  for (const e of toRemove) viewer.entities.remove(e);
}

/** Flatten a coordinate ring to [lng, lat, lng, lat, ...] */
function flattenRing(ring: number[][]): number[] {
  const flat: number[] = [];
  for (const [lng, lat] of ring) flat.push(lng, lat);
  return flat;
}

/** Get ground height at centroid */
function getGroundHeight(Cesium: any, viewer: any, ring: number[][]): number {
  let cx = 0, cy = 0;
  for (const [lng, lat] of ring) { cx += lng; cy += lat; }
  cx /= ring.length; cy /= ring.length;
  try {
    const carto = Cesium.Cartographic.fromDegrees(cx, cy);
    const h = viewer.scene?.globe?.getHeight?.(carto);
    if (typeof h === 'number' && isFinite(h)) return h;
  } catch { /* fallback */ }
  return 0;
}

/** Mass shape display labels */
const SHAPE_LABELS: Record<string, string> = {
  additive: '자유형', subtractive: '감산형', grid: '격자형',
  lshape: 'ㄱ자형', ushape: 'ㄷ자형', cross: '십자형',
  courtyard: '중정형', tower_podium: '타워+기단', hshape: 'H자형',
  radial: '방사형',
  freeform: '자유형', rectangle: '직사각형', L: 'L형', U: 'U형',
};

/** Mass shape color palette — 10 distinct colors for 10 algorithms */
const SHAPE_COLORS: Record<string, string> = {
  additive: '#60a5fa',       // blue
  subtractive: '#a78bfa',    // purple
  grid: '#34d399',           // emerald
  lshape: '#f97316',         // orange
  ushape: '#06b6d4',         // cyan
  cross: '#ef4444',          // red
  courtyard: '#f472b6',      // pink
  tower_podium: '#eab308',   // yellow
  hshape: '#8b5cf6',         // violet
  radial: '#14b8a6',         // teal
  freeform: '#60a5fa',
  rectangle: '#60a5fa',
  L: '#f97316',
  U: '#06b6d4',
};

/** Render 3D building mass on Cesium viewer */
function renderMassEntities(
  viewer: any,
  Cesium: any,
  features: GeoJSONFeature[],
  selectedId?: number,
) {
  clearMassEntities(viewer);

  for (const feature of features) {
    const ring = extractRing(feature.geometry);
    if (!ring || ring.length < 3) continue;

    const p = feature.properties;
    const height = p.height || 15;
    const numFloors = p.num_floors || 1;
    const floorH = p.floor_height || (height / numFloors);
    const designId = p.design_id ?? 0;
    const isSelected = selectedId != null && designId === selectedId;
    const shapeColor = SHAPE_COLORS[p.mass_shape || 'rectangle'] || '#60a5fa';

    const groundH = getGroundHeight(Cesium, viewer, ring);
    const flat = flattenRing(ring);

    const hasStepback = p.step_floor && p.upper_geometry && p.lower_height;

    if (hasStepback) {
      // Two-tier mass: lower (base polygon) + upper (smaller polygon)
      const lowerTop = groundH + p.lower_height!;

      // Lower tier
      viewer.entities.add({
        id: `${MASS_PREFIX}lower-${designId}`,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
          height: groundH,
          extrudedHeight: lowerTop,
          material: isSelected
            ? Cesium.Color.fromCssColorString('#f59e0b').withAlpha(0.3)
            : Cesium.Color.fromCssColorString(shapeColor).withAlpha(0.2),
          outline: true,
          outlineColor: isSelected
            ? Cesium.Color.fromCssColorString('#fbbf24')
            : Cesium.Color.fromCssColorString(shapeColor),
        },
      });

      // Upper tier
      const upperRing = extractRing(p.upper_geometry!);
      if (upperRing && upperRing.length >= 3) {
        const upperFlat = flattenRing(upperRing);
        viewer.entities.add({
          id: `${MASS_PREFIX}upper-${designId}`,
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArray(upperFlat),
            height: lowerTop,
            extrudedHeight: groundH + height,
            material: isSelected
              ? Cesium.Color.fromCssColorString('#f59e0b').withAlpha(0.25)
              : Cesium.Color.fromCssColorString(shapeColor).withAlpha(0.15),
            outline: true,
            outlineColor: isSelected
              ? Cesium.Color.fromCssColorString('#fbbf24')
              : Cesium.Color.fromCssColorString(shapeColor).withAlpha(0.8),
          },
        });
      }
    } else {
      // Single-tier mass
      viewer.entities.add({
        id: `${MASS_PREFIX}body-${designId}`,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
          height: groundH,
          extrudedHeight: groundH + height,
          material: isSelected
            ? Cesium.Color.fromCssColorString('#f59e0b').withAlpha(0.3)
            : Cesium.Color.fromCssColorString(shapeColor).withAlpha(0.2),
          outline: true,
          outlineColor: isSelected
            ? Cesium.Color.fromCssColorString('#fbbf24')
            : Cesium.Color.fromCssColorString(shapeColor),
        },
      });
    }

    // Floor plate lines
    for (let i = 1; i < numFloors; i++) {
      const plateH = groundH + floorH * i;
      // Use upper geometry for floors above step
      const useUpper = hasStepback && p.step_floor && i >= p.step_floor;
      let plateFlat = flat;
      if (useUpper && p.upper_geometry) {
        const uRing = extractRing(p.upper_geometry);
        if (uRing && uRing.length >= 3) plateFlat = flattenRing(uRing);
      }
      viewer.entities.add({
        id: `${MASS_PREFIX}floor-${designId}-${i}`,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(plateFlat),
          height: plateH,
          material: Cesium.Color.fromCssColorString('#93c5fd').withAlpha(0.06),
          outline: true,
          outlineColor: isSelected
            ? Cesium.Color.fromCssColorString('#fbbf24').withAlpha(0.3)
            : Cesium.Color.fromCssColorString(shapeColor).withAlpha(0.15),
        },
      });
    }

    // Ground footprint outline (orange)
    viewer.entities.add({
      id: `${MASS_PREFIX}footprint-${designId}`,
      polygon: {
        hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
        height: groundH + 0.3,
        material: Cesium.Color.fromCssColorString('#f97316').withAlpha(0.15),
        outline: true,
        outlineColor: Cesium.Color.fromCssColorString('#f97316'),
      },
    });
  }
}

/** Clear and render setback geometry lines + 3D envelopes */
function renderSetbackEntities(
  viewer: any,
  Cesium: any,
  setbacks: Record<string, SetbackGeometry> & {
    sunlight_envelope?: SunlightEnvelope | null;
    daylight_diagonal_envelope?: SunlightEnvelope | null;
  },
) {
  // Clear old
  const toRemove: any[] = [];
  for (const e of viewer.entities.values) {
    if (typeof e.id === 'string' && e.id.startsWith(SETBACK_PREFIX)) toRemove.push(e);
  }
  for (const e of toRemove) viewer.entities.remove(e);

  // 규제별 고유 색상 — 프런트/CLI 공통 레퍼런스.
  // 변경시 land/services/regulations/colors.py 와 동기화 필요.
  const colors: Record<string, string> = {
    buildable_area: '#22c55e',                 // 초록 — 건축가능영역
    north_setback: '#dc2626',                  // 진홍 — 정북 일조사선 (2D 선)
    sunlight_envelope_wall: '#dc2626',         // 진홍 — 정북 수직 직각벽 (3D)
    sunlight_envelope_plateau: '#f472b6',      // 분홍 — 정북 평탄 지붕 (3D)
    sunlight_envelope_slope: '#ec4899',        // 핑크 — 정북 경사 지붕 (3D)
    adjacent_setback: '#3b82f6',               // 파랑 — 인접대지 이격
    road_setback: '#f97316',                   // 주황 — 건축선 후퇴
    corner_cutoff: '#eab308',                  // 노랑 — 가각전제
    daylight_diagonal_envelope: '#a855f7',     // 보라 — 채광사선 경사면
    building_designation_line: '#14b8a6',      // 청록 — 건축지정선 (지구단위)
    building_limit_line: '#06b6d4',            // 시안 — 건축한계선
    wall_designation_line: '#84cc16',          // 라임 — 벽면지정선
    wall_limit_line: '#f43f5e',                // 산호 — 벽면한계선
  };

  for (const [key, sb] of Object.entries(setbacks)) {
    // sunlight_envelope has different structure — handled separately below
    if (key === 'sunlight_envelope' || !sb || !('geometry' in sb)) continue;
    const geom = (sb as SetbackGeometry).geometry;
    const color = colors[key] || '#f97316';

    if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
      const ring = extractRing(geom);
      if (!ring || ring.length < 3) continue;
      const flat = flattenRing(ring);
      viewer.entities.add({
        id: `${SETBACK_PREFIX}${key}`,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
          height: 0.5,
          material: Cesium.Color.fromCssColorString(color).withAlpha(0.25),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString(color),
          outlineWidth: 3,
        },
      });
    } else if (geom.type === 'LineString') {
      const coords = geom.coordinates as number[][];
      if (!coords || coords.length < 2) continue;
      const flat = flattenRing(coords);
      viewer.entities.add({
        id: `${SETBACK_PREFIX}${key}`,
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray(flat),
          width: 12,
          material: new Cesium.PolylineDashMaterialProperty({
            color: Cesium.Color.fromCssColorString(color),
            dashLength: 16,
          }),
          clampToGround: true,
        },
      });
    } else if (geom.type === 'MultiLineString') {
      const lines = geom.coordinates as number[][][];
      for (let i = 0; i < lines.length; i++) {
        const coords = lines[i];
        if (!coords || coords.length < 2) continue;
        const flat = flattenRing(coords);
        viewer.entities.add({
          id: `${SETBACK_PREFIX}${key}-${i}`,
          polyline: {
            positions: Cesium.Cartesian3.fromDegreesArray(flat),
            width: 12,
            material: new Cesium.PolylineDashMaterialProperty({
              color: Cesium.Color.fromCssColorString(color),
              dashLength: 16,
            }),
            clampToGround: true,
          },
        });
      }
    }
  }

  // 3D 일조사선 envelope — 수직 직각벽 (진홍) + 평탄 지붕 (분홍) + 경사 지붕 (핑크)
  const envelope = setbacks.sunlight_envelope as any;
  if (envelope) {
    const wallC = Cesium.Color.fromCssColorString(colors.sunlight_envelope_wall);
    const plateauC = Cesium.Color.fromCssColorString(colors.sunlight_envelope_plateau);
    const slopeC = Cesium.Color.fromCssColorString(colors.sunlight_envelope_slope);

    // 수직 직각벽 (진홍) — 얇고 투명하게
    if (envelope.walls) {
      for (let wi = 0; wi < envelope.walls.length; wi++) {
        const wall = envelope.walls[wi];
        const positions = wall.positions;
        const maxH = wall.max_heights;
        const minH = wall.min_heights;
        if (!positions || positions.length < 2 || positions.length !== maxH.length) continue;
        const flat: number[] = [];
        for (const [lng, lat] of positions) flat.push(lng, lat);
        viewer.entities.add({
          id: `${SETBACK_PREFIX}sunlight-wall-${wi}`,
          wall: {
            positions: Cesium.Cartesian3.fromDegreesArray(flat),
            minimumHeights: minH,
            maximumHeights: maxH,
            material: wallC.withAlpha(0.18),
            outline: true,
            outlineColor: wallC.withAlpha(0.85),
            outlineWidth: 2,
          },
        });
      }
    }

    // 평탄/경사 지붕 (kind별 색상 분리, 낮은 alpha로 투명)
    if (envelope.slanted_polygons) {
      for (let pi = 0; pi < envelope.slanted_polygons.length; pi++) {
        const poly = envelope.slanted_polygons[pi];
        const corners = poly.corners as number[][];
        if (!corners || corners.length < 3) continue;
        const kind = poly.kind || '';
        const color = kind === 'plateau' ? plateauC : slopeC;
        const flat: number[] = [];
        for (const c of corners) flat.push(c[0], c[1], c[2]);
        viewer.entities.add({
          id: `${SETBACK_PREFIX}sunlight-${kind}-${pi}`,
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArrayHeights(flat),
            perPositionHeight: true,
            material: color.withAlpha(0.15),
            outline: true,
            outlineColor: color.withAlpha(0.85),
            outlineWidth: 2,
          },
        });
      }
    }
  }

  // 채광사선제한 경사면 (daylight_diagonal_envelope — 공동주택 인접경계, 보라)
  const daylightEnvelope = setbacks.daylight_diagonal_envelope;
  if (daylightEnvelope?.walls) {
    const dlColor = Cesium.Color.fromCssColorString(colors.daylight_diagonal_envelope);
    for (let wi = 0; wi < daylightEnvelope.walls.length; wi++) {
      const wall = daylightEnvelope.walls[wi];
      if (!wall.positions || wall.positions.length < 2) continue;

      const flat: number[] = [];
      for (const [lng, lat] of wall.positions) flat.push(lng, lat);

      viewer.entities.add({
        id: `${SETBACK_PREFIX}daylight-diag-wall-${wi}`,
        wall: {
          positions: Cesium.Cartesian3.fromDegreesArray(flat),
          minimumHeights: wall.min_heights,
          maximumHeights: wall.max_heights,
          material: dlColor.withAlpha(0.15),
          outline: true,
          outlineColor: dlColor.withAlpha(0.75),
          outlineWidth: 2,
        },
      });
    }
  }
}

/** Fly camera to fit a GeoJSON geometry bounding box */
function flyToGeometryBbox(viewerRef: React.RefObject<any>, geometry: any) {
  const Cesium = getCesium();
  const viewer = viewerRef.current;
  if (!Cesium || !viewer) return;

  // Extract ring from geometry
  let ring: number[][] | null = null;
  if (geometry.type === 'Polygon') ring = geometry.coordinates?.[0];
  else if (geometry.type === 'MultiPolygon') ring = geometry.coordinates?.[0]?.[0];
  else if (geometry.type === 'Feature') {
    const g = geometry.geometry;
    if (g?.type === 'Polygon') ring = g.coordinates?.[0];
    else if (g?.type === 'MultiPolygon') ring = g.coordinates?.[0]?.[0];
  }
  if (!ring || ring.length < 3) return;

  // Calculate bounding box
  let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity;
  for (const [lng, lat] of ring) {
    if (lng < west) west = lng;
    if (lng > east) east = lng;
    if (lat < south) south = lat;
    if (lat > north) north = lat;
  }

  // Add 20% padding
  const dLng = (east - west) * 0.2 || 0.0005;
  const dLat = (north - south) * 0.2 || 0.0005;
  west -= dLng; east += dLng;
  south -= dLat; north += dLat;

  viewer.camera.flyTo({
    destination: Cesium.Rectangle.fromDegrees(west, south, east, north),
    orientation: {
      heading: Cesium.Math.toRadians(0),
      pitch: Cesium.Math.toRadians(-60),
      roll: 0,
    },
    duration: 1.5,
  });
}

const SiteMapPanel: React.FC<Props> = React.memo(({
  sitePolygon, massFeatures, selectedDesignId, onParcelClick, setbackGeometries,
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState('');
  const [reversing, setReversing] = useState(false);

  // Ref to break circular dependency: handleMapClick needs highlightParcel/flyTo/viewerRef,
  // but useVworld3D needs onClick (which is handleMapClick).
  const actionsRef = useRef<{
    highlightParcel: (g: object) => void;
    flyTo: (lng: number, lat: number) => void;
    viewerRef: React.RefObject<any>;
  } | null>(null);

  const handleMapClick = useCallback(async (lng: number, lat: number) => {
    setReversing(true);
    setStatus('필지 조회 중...');
    try {
      const result = await reverse(lng, lat);
      if (result.success && result.pnu) {
        if (result.geometry) {
          actionsRef.current?.highlightParcel(result.geometry);
          if (actionsRef.current?.viewerRef) flyToGeometryBbox(actionsRef.current.viewerRef, result.geometry);
        } else {
          actionsRef.current?.flyTo(lng, lat);
        }
        onParcelClick?.(result.pnu, result.address || '');
        setStatus(result.address || result.pnu);
      } else {
        setStatus(result.error || '필지 정보 없음');
      }
    } catch {
      setStatus('필지 조회 실패');
    } finally {
      setReversing(false);
    }
  }, [onParcelClick]);

  const { ready, loading, error, highlightParcel, flyTo, setBuildingsVisible, viewerRef } = useVworld3D({
    target: mapRef,
    onClick: handleMapClick,
  });

  actionsRef.current = { highlightParcel, flyTo, viewerRef };

  // Highlight + flyTo when sitePolygon changes
  React.useEffect(() => {
    if (!sitePolygon || !ready) return;
    highlightParcel(sitePolygon);
    flyToGeometryBbox(viewerRef, sitePolygon);
  }, [sitePolygon, ready, highlightParcel, viewerRef]);

  // Render 3D building mass when features change + hide existing Vworld buildings
  React.useEffect(() => {
    if (!ready) return;
    const viewer = viewerRef.current;
    const Cesium = getCesium();
    if (!viewer || !Cesium) return;

    const hasSetbacks = setbackGeometries && Object.keys(setbackGeometries).length > 0;
    if (massFeatures && massFeatures.length > 0) {
      setBuildingsVisible(false);
      renderMassEntities(viewer, Cesium, massFeatures, selectedDesignId);
    } else if (hasSetbacks) {
      // 규제선만 있어도 기존 건물 숨기기 (Wall이 건물에 가려지지 않도록)
      setBuildingsVisible(false);
      clearMassEntities(viewer);
    } else {
      clearMassEntities(viewer);
      setBuildingsVisible(true);
    }
  }, [massFeatures, selectedDesignId, setbackGeometries, ready, viewerRef, setBuildingsVisible]);

  // Render setback geometry lines (regulation boundaries)
  React.useEffect(() => {
    if (!ready) return;
    const viewer = viewerRef.current;
    const Cesium = getCesium();
    if (!viewer || !Cesium) return;

    if (setbackGeometries && Object.keys(setbackGeometries).length > 0) {
      renderSetbackEntities(viewer, Cesium, setbackGeometries);
    }
  }, [setbackGeometries, ready, viewerRef]);

  return (
    <div style={{
      width: '100%', height: '100%',
      position: 'relative', borderRadius: 12, overflow: 'hidden',
      boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
    }}>
      <div
        ref={mapRef}
        id="vworld-3d-design"
        style={{ width: '100%', height: '100%', background: '#0f172a' }}
      />

      {/* Loading overlay */}
      {loading && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(15,23,42,0.85)', zIndex: 10,
          backdropFilter: 'blur(8px)',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              width: 36, height: 36, margin: '0 auto 12px',
              border: '3px solid #334155', borderTopColor: '#3b82f6',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <div style={{ color: '#94a3b8', fontSize: 13 }}>3D 지도 로딩 중...</div>
          </div>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: '#0f172a', zIndex: 10,
        }}>
          <div style={{ color: '#f87171', fontSize: 13 }}>{error}</div>
        </div>
      )}

      {/* Mass info overlay — shows building stats */}
      {massFeatures && massFeatures.length > 0 && (
        <div style={{
          position: 'absolute', top: 12, right: 12,
          padding: '10px 14px',
          background: 'rgba(15,23,42,0.88)', borderRadius: 8,
          border: '1px solid rgba(96,165,250,0.2)',
          backdropFilter: 'blur(8px)',
          fontSize: 12, color: '#e2e8f0',
          zIndex: 10, minWidth: 140,
        }}>
          <div style={{ color: '#60a5fa', fontWeight: 600, marginBottom: 6, fontSize: 11, letterSpacing: '0.05em' }}>
            BUILDING MASS
          </div>
          {massFeatures.map((f, i) => {
            const p = f.properties;
            const algoKey = p.algorithm || p.mass_shape || 'rectangle';
            const algoColor = SHAPE_COLORS[algoKey] || '#60a5fa';
            return (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: '#94a3b8' }}>형태</span>
                  <span style={{ fontFamily: 'monospace', color: algoColor, fontWeight: 600 }}>
                    {SHAPE_LABELS[algoKey] || algoKey}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>높이</span>
                  <span style={{ fontFamily: 'monospace' }}>{p.height?.toFixed(1)}m</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>층수</span>
                  <span style={{ fontFamily: 'monospace' }}>
                    {p.num_floors}F
                    {p.step_floor ? ` (${p.step_floor}F+${p.num_floors - p.step_floor}F)` : ''}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>건폐율</span>
                  <span style={{ fontFamily: 'monospace', color: '#22c55e' }}>{p.bcr?.toFixed(1)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: '#94a3b8' }}>용적률</span>
                  <span style={{ fontFamily: 'monospace', color: '#f59e0b' }}>{p.far?.toFixed(1)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: '#94a3b8' }}>연면적</span>
                  <span style={{ fontFamily: 'monospace', color: '#60c8ff' }}>
                    {p.floor_area >= 1000 ? (p.floor_area / 1000).toFixed(1) + 'k' : p.floor_area?.toFixed(0)}m²
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Status bar — shows parcel info after click */}
      {(status || reversing) && (
        <div style={{
          position: 'absolute', bottom: 12, left: 12, right: 12,
          padding: '8px 14px',
          background: 'rgba(15,23,42,0.88)', borderRadius: 8,
          border: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(8px)',
          fontSize: 12, color: reversing ? '#94a3b8' : '#e2e8f0',
          zIndex: 10,
        }}>
          {reversing ? '필지 조회 중...' : status}
        </div>
      )}

      {/* Hint — shown when map is ready but no parcel selected */}
      {ready && !status && !massFeatures?.length && (
        <div style={{
          position: 'absolute', top: 12, left: 12,
          padding: '6px 12px',
          background: 'rgba(15,23,42,0.85)', borderRadius: 8,
          border: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(8px)',
          fontSize: 11, color: '#64748b',
          zIndex: 10,
        }}>
          지적도 필지를 클릭하여 대지를 선택하세요
        </div>
      )}
    </div>
  );
});

SiteMapPanel.displayName = 'SiteMapPanel';
export default SiteMapPanel;
