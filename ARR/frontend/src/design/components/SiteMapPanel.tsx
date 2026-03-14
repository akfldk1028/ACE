import React, { useRef, useCallback, useState } from 'react';
import { useVworld3D } from '../../land/hooks/use-vworld-3d';
import { reverse } from '../../land/lib/land-api-client';
import type { GeoJSONFeature, SetbackGeometry } from '../lib/types';

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
  additive: '자유형', subtractive: '중정형', grid: '격자형',
  freeform: '자유형', rectangle: '직사각형', L: 'L형', U: 'U형', courtyard: 'ㅁ형 중정',
};

/** Mass shape color palette */
const SHAPE_COLORS: Record<string, string> = {
  additive: '#60a5fa',
  subtractive: '#a78bfa',
  grid: '#34d399',
  freeform: '#60a5fa',
  rectangle: '#60a5fa',
  L: '#a78bfa',
  U: '#34d399',
  courtyard: '#f472b6',
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

/** Clear and render setback geometry lines */
function renderSetbackEntities(
  viewer: any,
  Cesium: any,
  setbacks: Record<string, SetbackGeometry>,
) {
  // Clear old
  const toRemove: any[] = [];
  for (const e of viewer.entities.values) {
    if (typeof e.id === 'string' && e.id.startsWith(SETBACK_PREFIX)) toRemove.push(e);
  }
  for (const e of toRemove) viewer.entities.remove(e);

  const colors: Record<string, string> = {
    adjacent_setback: '#ef4444',
    building_line: '#f59e0b',
  };

  for (const [key, sb] of Object.entries(setbacks)) {
    const ring = extractRing(sb.geometry);
    if (!ring || ring.length < 3) continue;
    const flat = flattenRing(ring);
    const color = colors[key] || '#f97316';

    viewer.entities.add({
      id: `${SETBACK_PREFIX}${key}`,
      polygon: {
        hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
        height: 0.5,
        material: Cesium.Color.fromCssColorString(color).withAlpha(0.08),
        outline: true,
        outlineColor: Cesium.Color.fromCssColorString(color).withAlpha(0.7),
        outlineWidth: 2,
      },
    });
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

    if (massFeatures && massFeatures.length > 0) {
      setBuildingsVisible(false);
      renderMassEntities(viewer, Cesium, massFeatures, selectedDesignId);
    } else {
      clearMassEntities(viewer);
      setBuildingsVisible(true);
    }
  }, [massFeatures, selectedDesignId, ready, viewerRef, setBuildingsVisible]);

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
            return (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>형태</span>
                  <span style={{
                    fontFamily: 'monospace',
                    color: SHAPE_COLORS[p.mass_shape || 'rectangle'] || '#60a5fa',
                  }}>
                    {SHAPE_LABELS[p.mass_shape || 'rectangle'] || p.mass_shape}
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
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>용적률</span>
                  <span style={{ fontFamily: 'monospace', color: '#f59e0b' }}>{p.far?.toFixed(1)}%</span>
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
