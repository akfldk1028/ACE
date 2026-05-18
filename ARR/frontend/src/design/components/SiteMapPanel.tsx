import React, { useRef, useCallback, useState } from 'react';
import { useVworld3D } from '../../land/hooks/use-vworld-3d';
import { reverse } from '../../land/lib/land-api-client';
import type { DatumBoundarySegment, DatumPointSample, GeoJSONFeature, SetbackGeometry, SetbackGeometriesMap } from '../lib/types';
import type { SunlightEnvelope } from '../../land/lib/types';
import { renderSunlightEnvelope } from '../lib/envelopes/sunlight';
import { clearDatumPlane, renderDatumMarkers, type DatumMarker } from '../lib/envelopes/datum-plane';
import { clearElevationGrid } from '../lib/envelopes/elevation-grid';
import { visualizeConstraints, type ConstraintsResult } from '../lib/api-client';

/* eslint-disable @typescript-eslint/no-explicit-any */
const getCesium = (): any => (window as any).Cesium;

const MASS_PREFIX = 'design-mass-';
const SETBACK_PREFIX = 'design-setback-';
const CONSTRAINTS_PREFIX = 'design-constraints-';

interface Props {
  sitePolygon: object | null;
  massFeatures?: GeoJSONFeature[];
  selectedDesignId?: number;
  onParcelClick?: (pnu: string, address: string) => void;
  setbackGeometries?: SetbackGeometriesMap;
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

function numberOrNull(value: unknown): number | null {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

function weightedPoint<T>(
  items: T[] | null | undefined,
  lngKey: keyof T,
  latKey: keyof T,
  weightKey?: keyof T,
): { lng: number; lat: number } | null {
  if (!items?.length) return null;
  let sumLng = 0;
  let sumLat = 0;
  let sumWeight = 0;
  for (const item of items) {
    const lng = numberOrNull(item[lngKey]);
    const lat = numberOrNull(item[latKey]);
    if (lng == null || lat == null) continue;
    const weight = weightKey ? (numberOrNull(item[weightKey]) ?? 1) : 1;
    if (weight <= 0) continue;
    sumLng += lng * weight;
    sumLat += lat * weight;
    sumWeight += weight;
  }
  if (sumWeight <= 0) return null;
  return { lng: sumLng / sumWeight, lat: sumLat / sumWeight };
}

function ringCentroid(ring: number[][] | null | undefined): { lng: number; lat: number } | null {
  if (!ring?.length) return null;
  let lng = 0;
  let lat = 0;
  for (const [x, y] of ring) {
    lng += x;
    lat += y;
  }
  return { lng: lng / ring.length, lat: lat / ring.length };
}

function midpoint(a: { lng: number; lat: number }, b: { lng: number; lat: number }): { lng: number; lat: number } {
  return { lng: (a.lng + b.lng) / 2, lat: (a.lat + b.lat) / 2 };
}

function lineCoords(geom: unknown): number[][] | null {
  const g = geom as { type?: string; coordinates?: unknown } | undefined;
  if (!g?.coordinates) return null;
  if (g.type === 'LineString' && Array.isArray(g.coordinates)) return g.coordinates as number[][];
  if (g.type === 'MultiLineString' && Array.isArray(g.coordinates)) return (g.coordinates as number[][][])[0] ?? null;
  return null;
}

function lineMidpoint(coords: number[][]): { lng: number; lat: number } | null {
  if (!coords.length) return null;
  const mid = coords[Math.floor(coords.length / 2)];
  if (!mid || mid.length < 2) return null;
  return { lng: mid[0], lat: mid[1] };
}

function lineKey(coords: number[][]): string {
  return coords.map((p) => `${p[0]?.toFixed(7)},${p[1]?.toFixed(7)}`).join('|');
}

function metersPerDegreeLng(lat: number): number {
  return Math.max(1, 111_320 * Math.cos((lat * Math.PI) / 180));
}

function lngLatToLocalMeters(point: { lng: number; lat: number }, origin: { lng: number; lat: number }) {
  return {
    x: (point.lng - origin.lng) * metersPerDegreeLng(origin.lat),
    y: (point.lat - origin.lat) * 110_540,
  };
}

function localMetersToLngLat(point: { x: number; y: number }, origin: { lng: number; lat: number }) {
  return {
    lng: origin.lng + point.x / metersPerDegreeLng(origin.lat),
    lat: origin.lat + point.y / 110_540,
  };
}

function offsetPointMeters(
  point: { lng: number; lat: number },
  origin: { lng: number; lat: number },
  unit: { x: number; y: number },
  meters: number,
): { lng: number; lat: number } {
  const local = lngLatToLocalMeters(point, origin);
  return localMetersToLngLat({ x: local.x + unit.x * meters, y: local.y + unit.y * meters }, origin);
}

function clippedLineSegment(
  a: { lng: number; lat: number },
  b: { lng: number; lat: number },
  origin: { lng: number; lat: number },
  maxLengthM: number,
): [{ lng: number; lat: number }, { lng: number; lat: number }] {
  const al = lngLatToLocalMeters(a, origin);
  const bl = lngLatToLocalMeters(b, origin);
  const dx = bl.x - al.x;
  const dy = bl.y - al.y;
  const len = Math.hypot(dx, dy);
  if (len <= maxLengthM || len < 0.01) return [a, b];
  const ux = dx / len;
  const uy = dy / len;
  const half = maxLengthM / 2;
  return [
    localMetersToLngLat({ x: -ux * half, y: -uy * half }, origin),
    localMetersToLngLat({ x: ux * half, y: uy * half }, origin),
  ];
}

function buildDatumMarkers(setbacks: SetbackGeometriesMap, parcelRing: number[][] | null): DatumMarker[] {
  const datum = setbacks.datum_result;
  if (!datum) return [];

  const parcelDatumM = datum.parcel_datum_m ?? datum.elevation_m ?? null;
  const roadDatumM = datum.road_datum_m ?? null;
  const neighborDatumM = datum.neighbor_datum_m ?? null;
  const neighborAvgM = datum.neighbor_avg_datum_m ?? null;

  const parcelBasis = weightedPoint<DatumBoundarySegment>(
    datum.parcel_segments,
    'midpoint_lng',
    'midpoint_lat',
    'length_m',
  ) ?? ringCentroid(parcelRing);
  const roadBasis = weightedPoint<DatumPointSample>(
    datum.road_samples,
    'lng',
    'lat',
    'weight',
  );
  const neighborBasis = weightedPoint<DatumBoundarySegment>(
    datum.neighbor_segments,
    'midpoint_lng',
    'midpoint_lat',
    'length_m',
  );

  const markers: DatumMarker[] = [];
  if (parcelBasis && parcelDatumM != null) {
    markers.push({
      id: 'parcel-119',
      label: '대지',
      lng: parcelBasis.lng,
      lat: parcelBasis.lat,
      elevationM: parcelDatumM,
      color: '#facc15',
      labelOffset: [0, 28],
    });
  }
  if (roadBasis && roadDatumM != null) {
    markers.push({
      id: 'road',
      label: '도로',
      lng: roadBasis.lng,
      lat: roadBasis.lat,
      elevationM: roadDatumM,
      color: '#38bdf8',
      labelOffset: [-78, 18],
    });
  }
  if (neighborBasis && neighborDatumM != null) {
    markers.push({
      id: 'neighbor',
      label: '인접',
      lng: neighborBasis.lng,
      lat: neighborBasis.lat,
      elevationM: neighborDatumM,
      color: '#f472b6',
      labelOffset: [-90, -28],
    });
  }
  if (parcelBasis && neighborBasis && neighborAvgM != null) {
    const basis = midpoint(parcelBasis, neighborBasis);
    markers.push({
      id: 'neighbor-avg-86',
      label: '§86 평균',
      lng: basis.lng,
      lat: basis.lat,
      elevationM: neighborAvgM,
      color: '#22c55e',
      labelOffset: [42, -70],
    });
  }
  return markers;
}

function renderRoadAndNeighborContext(viewer: any, Cesium: any, setbacks: SetbackGeometriesMap): string[] {
  const addedIds: string[] = [];
  const datum = setbacks.datum_result;
  const roadFrontages = (setbacks as Record<string, unknown>).road_frontages as Array<Record<string, unknown>> | undefined;
  const neighborParcels = (setbacks as Record<string, unknown>).neighbor_parcels as Array<Record<string, unknown>> | undefined;
  const params = new URLSearchParams(window.location.search);
  const showAllLabels = params.get('roadLabels') === 'all' || params.get('layers') === 'all';
  const roadC = Cesium.Color.fromCssColorString('#0ea5e9');
  const roadEdgeC = Cesium.Color.fromCssColorString('#f97316');
  const neighborC = Cesium.Color.fromCssColorString('#f472b6');

  const seenRoads = new Set<string>();
  const roads = (roadFrontages ?? [])
    .map((r, index) => {
      const shared = lineCoords(r.sharedEdge ?? r.shared_edge);
      const center = lineCoords(r.roadCenterline ?? r.road_centerline);
      const width = numberOrNull(r.roadWidthM ?? r.road_width_m) ?? 0;
      return { index, shared, center, width };
    })
    .filter((r) => r.shared && r.shared.length >= 2 && r.width > 0)
    .filter((r) => {
      const key = lineKey(r.shared!);
      if (seenRoads.has(key)) return false;
      seenRoads.add(key);
      return true;
    })
    .sort((a, b) => b.width - a.width);

  roads.forEach((road, order) => {
    const shared = road.shared!;
    const id = `${SETBACK_PREFIX}road-context-${road.index}`;
    viewer.entities.add({
      id: `${id}-edge`,
      polyline: {
        positions: Cesium.Cartesian3.fromDegreesArray(flattenRing(shared)),
        width: 4,
        material: roadEdgeC.withAlpha(0.92),
        clampToGround: true,
      },
    });
    addedIds.push(`${id}-edge`);

    if (road.center && road.center.length >= 2) {
      viewer.entities.add({
        id: `${id}-centerline`,
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray(flattenRing(road.center)),
          width: 2,
          material: new Cesium.PolylineDashMaterialProperty({
            color: roadC.withAlpha(0.85),
            dashLength: 12,
          }),
          clampToGround: true,
        },
      });
      addedIds.push(`${id}-centerline`);
    }

    if (showAllLabels || order < 2) {
      const basis = lineMidpoint(road.center ?? shared);
      if (basis) {
        viewer.entities.add({
          id: `${id}-label`,
          position: Cesium.Cartesian3.fromDegrees(basis.lng, basis.lat, (datum?.road_datum_m ?? datum?.elevation_m ?? 0) + 6),
          label: {
            text: `도로 ${road.width.toFixed(1)}m\n레벨 ${(datum?.road_datum_m ?? datum?.elevation_m ?? 0).toFixed(2)}m`,
            font: '700 12px ui-monospace, SFMono-Regular, Menlo, monospace',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            backgroundColor: Cesium.Color.BLACK.withAlpha(0.50),
            backgroundPadding: new Cesium.Cartesian2(7, 4),
            showBackground: true,
            pixelOffset: new Cesium.Cartesian2(-86, order === 0 ? 18 : -28),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });
        addedIds.push(`${id}-label`);
      }
    }
  });

  const seenNeighbors = new Set<string>();
  (neighborParcels ?? []).forEach((neighbor, index) => {
    const shared = lineCoords(neighbor.sharedEdge ?? neighbor.shared_edge);
    if (!shared || shared.length < 2) return;
    const key = lineKey(shared);
    if (seenNeighbors.has(key)) return;
    seenNeighbors.add(key);
    const id = `${SETBACK_PREFIX}neighbor-context-${index}`;
    viewer.entities.add({
      id: `${id}-edge`,
      polyline: {
        positions: Cesium.Cartesian3.fromDegreesArray(flattenRing(shared)),
        width: 3,
        material: neighborC.withAlpha(0.82),
        clampToGround: true,
      },
    });
    addedIds.push(`${id}-edge`);
  });

  return addedIds;
}

function renderFrontRoadDiagonalReference(
  viewer: any,
  Cesium: any,
  setbacks: SetbackGeometriesMap,
  parcelRing: number[][] | null,
  colors: { surface: string; line: string },
): string[] {
  const params = new URLSearchParams(window.location.search);
  const showReference = params.get('roadDiag') === '1' || params.get('layers') === 'all';
  if (!showReference) return [];

  const profile = (setbacks as Record<string, unknown>).front_road_diagonal_profile as Record<string, unknown> | undefined;
  const datum = setbacks.datum_result;
  const roadFrontages = (setbacks as Record<string, unknown>).road_frontages as Array<Record<string, unknown>> | undefined;
  const parcelBasis = parcelRing ? ringCentroid(parcelRing) : null;
  if (!profile || !datum || !roadFrontages?.length || !parcelBasis) return [];

  const slope = numberOrNull(profile.slope) ?? 1.5;
  const profileWidth = numberOrNull(profile.road_width_m) ?? 0;
  const roadDatum = numberOrNull(profile.road_datum_m) ?? datum.road_datum_m ?? datum.elevation_m ?? 0;
  const applies = Boolean(profile.applies);
  const alpha = applies ? 0.14 : 0.09;

  const roads = roadFrontages
    .map((r, index) => {
      const shared = lineCoords(r.sharedEdge ?? r.shared_edge);
      const width = numberOrNull(r.roadWidthM ?? r.road_width_m) ?? profileWidth;
      return { index, shared, width };
    })
    .filter((r) => r.shared && r.shared.length >= 2 && r.width > 0)
    .sort((a, b) => b.width - a.width);
  const road = roads[0];
  if (!road?.shared) return [];

  const shared = road.shared;
  const rawA = { lng: shared[0][0], lat: shared[0][1] };
  const rawB = { lng: shared[shared.length - 1][0], lat: shared[shared.length - 1][1] };
  const edgeMid = midpoint(rawA, rawB);
  const origin = edgeMid;
  const [a, b] = clippedLineSegment(rawA, rawB, origin, 32);
  const midLocal = lngLatToLocalMeters(edgeMid, origin);
  const parcelLocal = lngLatToLocalMeters(parcelBasis, origin);
  const inwardRaw = { x: parcelLocal.x - midLocal.x, y: parcelLocal.y - midLocal.y };
  const inwardLen = Math.hypot(inwardRaw.x, inwardRaw.y);
  if (inwardLen < 0.01) return [];
  const inward = { x: inwardRaw.x / inwardLen, y: inwardRaw.y / inwardLen };
  const roadWidth = road.width || profileWidth;
  const displayDepth = Math.min(18, Math.max(10, roadWidth * 1.2));

  // Clean reference ribbon: show the section plane only near the selected road
  // frontage. The legal section starts at the opposite road boundary, so the
  // shared-edge height includes roadWidth * slope; the ribbon then rises inward.
  const edgeH = slope * roadWidth;
  const innerB = offsetPointMeters(b, origin, inward, displayDepth);
  const innerA = offsetPointMeters(a, origin, inward, displayDepth);
  const innerH = edgeH + slope * displayDepth;
  const positions = [
    [a.lng, a.lat, roadDatum + edgeH],
    [b.lng, b.lat, roadDatum + edgeH],
    [innerB.lng, innerB.lat, roadDatum + innerH],
    [innerA.lng, innerA.lat, roadDatum + innerH],
  ];

  const surfaceC = Cesium.Color.fromCssColorString(colors.surface);
  const lineC = Cesium.Color.fromCssColorString(colors.line);
  const addedIds: string[] = [];
  const flatHeights: number[] = [];
  positions.forEach((p) => flatHeights.push(p[0], p[1], p[2]));
  viewer.entities.add({
    id: `${SETBACK_PREFIX}front-road-diagonal-reference-surface`,
    polygon: {
      hierarchy: Cesium.Cartesian3.fromDegreesArrayHeights(flatHeights),
      perPositionHeight: true,
      material: surfaceC.withAlpha(alpha),
      outline: false,
    },
  });
  addedIds.push(`${SETBACK_PREFIX}front-road-diagonal-reference-surface`);

  const outline = positions.map((p) => Cesium.Cartesian3.fromDegrees(p[0], p[1], p[2]));
  outline.push(outline[0]);
  viewer.entities.add({
    id: `${SETBACK_PREFIX}front-road-diagonal-reference-outline`,
    polyline: {
      positions: outline,
      width: applies ? 4 : 3,
      material: applies
        ? lineC.withAlpha(0.86)
        : new Cesium.PolylineDashMaterialProperty({
            color: lineC.withAlpha(0.72),
            dashLength: 14,
          }),
    },
  });
  addedIds.push(`${SETBACK_PREFIX}front-road-diagonal-reference-outline`);

  viewer.entities.add({
    id: `${SETBACK_PREFIX}front-road-diagonal-reference-label`,
    position: Cesium.Cartesian3.fromDegrees(edgeMid.lng, edgeMid.lat, roadDatum + Math.max(8, innerH * 0.35)),
    label: {
      text: applies
        ? `전면도로 사선\n도로 ${roadWidth.toFixed(1)}m / ${slope}:1`
        : `전면도로 참고\n${slope}:1`,
      font: '700 12px ui-monospace, SFMono-Regular, Menlo, monospace',
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 3,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      backgroundColor: Cesium.Color.BLACK.withAlpha(0.46),
      backgroundPadding: new Cesium.Cartesian2(7, 4),
      showBackground: true,
      pixelOffset: new Cesium.Cartesian2(46, -34),
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  });
  addedIds.push(`${SETBACK_PREFIX}front-road-diagonal-reference-label`);

  return addedIds;
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
  datumZ?: number,  // 2026-05-11 Step 5: NGII §119 datum 절대 z (envelope과 통일)
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

    // Step 5: datumZ(NGII §119) 우선 → envelope/매스/datum 평면 단일 평면.
    // 없으면 Cesium globe terrain fallback (LOCKED SPEC 이전 동작).
    const groundH = (datumZ != null && isFinite(datumZ) && datumZ !== 0)
      ? datumZ
      : getGroundHeight(Cesium, viewer, ring);
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
  setbacks: SetbackGeometriesMap,
  parcelRing: number[][] | null,
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
    buildable_area: '#86efac',                 // 연녹 — 건축가능영역
    north_setback: '#dc2626',                  // 진홍 — 정북 일조사선 (2D 선)
    sunlight_envelope_wall: '#22c55e',         // 초록 — 정북 수직 직각벽 (3D)
    sunlight_envelope_plateau: '#86efac',      // 연녹 — 정북 평탄부 (3D)
    sunlight_envelope_slope: '#22c55e',        // 초록 — 정북 경사 메쉬 (3D)
    adjacent_setback: '#3b82f6',               // 파랑 — 인접대지 이격
    road_setback: '#f97316',                   // 주황 — 건축선 후퇴
    corner_cutoff: '#eab308',                  // 노랑 — 가각전제
    daylight_diagonal_envelope: '#a855f7',     // 보라 — 채광 검토 참고면 (정확 판정은 매스/채광창 벽면 필요)
    front_road_diagonal_reference: '#16a34a',  // 녹색 — 전면도로 사선/가로구역 높이 참고면
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

    if (geom.type === 'FeatureCollection') {
      const features = (geom as unknown as { features?: Array<{ geometry?: { type: string; coordinates: any } }> }).features ?? [];
      for (let i = 0; i < features.length; i++) {
        const featureGeom = features[i]?.geometry;
        if (!featureGeom) continue;
        if (featureGeom.type === 'LineString') {
          const coords = featureGeom.coordinates as number[][];
          if (!coords || coords.length < 2) continue;
          viewer.entities.add({
            id: `${SETBACK_PREFIX}${key}-feature-${i}`,
            polyline: {
              positions: Cesium.Cartesian3.fromDegreesArray(flattenRing(coords)),
              width: key === 'north_setback' ? 5 : 4,
              material: new Cesium.PolylineDashMaterialProperty({
                color: Cesium.Color.fromCssColorString(color),
                dashLength: key === 'north_setback' ? 10 : 16,
              }),
              clampToGround: true,
            },
          });
        } else if (featureGeom.type === 'Polygon' || featureGeom.type === 'MultiPolygon') {
          const ring = extractRing(featureGeom);
          if (!ring || ring.length < 3) continue;
          viewer.entities.add({
            id: `${SETBACK_PREFIX}${key}-feature-${i}-outline`,
            polyline: {
              positions: Cesium.Cartesian3.fromDegreesArray(flattenRing(ring)),
              width: 3,
              material: Cesium.Color.fromCssColorString(color),
              clampToGround: true,
            },
          });
        }
      }
    } else if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
      const ring = extractRing(geom);
      if (!ring || ring.length < 3) continue;
      const flat = flattenRing(ring);
      const params = new URLSearchParams(window.location.search);
      const showFill = key !== 'buildable_area' || params.get('fill') === '1' || params.get('layers') === 'all';
      if (showFill) {
        viewer.entities.add({
          id: `${SETBACK_PREFIX}${key}`,
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
            // height: 0.5 (sea level) → terrain 표면 따라가도록 클램프.
            // 강남 지표면 ~38m, sunlight envelope wall도 terrainH(~38m)에서 시작 → z축 일치.
            // (이전 height:0.5 시 envelope만 38m 위에 떠 보임 z축 불일치 발생)
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
            material: Cesium.Color.fromCssColorString(color).withAlpha(key === 'buildable_area' ? 0.06 : 0.22),
            // outline은 CLAMP_TO_GROUND 모드에서 미지원 → outline 끄고 별도 polyline 추가
            outline: false,
          },
        });
      }
      // Polygon outline 별도 polyline (clampToGround로 terrain 따라감)
      viewer.entities.add({
        id: `${SETBACK_PREFIX}${key}-outline`,
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray(flat),
          width: key === 'buildable_area' ? 3 : 3,
          material: Cesium.Color.fromCssColorString(key === 'buildable_area' ? '#10b981' : color),
          clampToGround: true,
        },
      });
    } else if (geom.type === 'LineString') {
      const coords = geom.coordinates as unknown as number[][];
      if (!coords || coords.length < 2) continue;
      const flat = flattenRing(coords);
      viewer.entities.add({
        id: `${SETBACK_PREFIX}${key}`,
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray(flat),
          width: 5,
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
            width: 5,
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

  renderRoadAndNeighborContext(viewer, Cesium, setbacks);

  // 정북일조 envelope — design/lib/envelopes/sunlight.ts 전담 모듈로 위임.
  // 북쪽 수직벽 + 경사 지붕만 렌더 (사용자 img_18 피드백 반영 LOCKED SPEC).
  renderSunlightEnvelope(viewer, Cesium, setbacks.sunlight_envelope, {
    wall: colors.sunlight_envelope_wall,
    slope: colors.sunlight_envelope_slope,
  });

  const params = new URLSearchParams(window.location.search);
  const showDaylight = params.get('daylight') !== '0';
  if (showDaylight) {
    renderDaylightDiagonalEnvelope(viewer, Cesium, setbacks.daylight_diagonal_envelope, {
      wall: colors.daylight_diagonal_envelope,
    }, setbacks.datum_result?.parcel_datum_m ?? setbacks.datum_result?.elevation_m ?? 0);
  }

  renderFrontRoadDiagonalReference(viewer, Cesium, setbacks, parcelRing, {
    surface: colors.front_road_diagonal_reference,
    line: colors.front_road_diagonal_reference,
  });
}

function renderDaylightDiagonalEnvelope(
  viewer: any,
  Cesium: any,
  envelope: {
    walls?: Array<{ positions?: number[][]; min_heights?: number[]; max_heights?: number[] }>;
    multiplier?: number;
  } | null | undefined,
  colors: { wall: string },
  datumElevationM: number,
) {
  if (!envelope?.walls?.length) return;
  const color = Cesium.Color.fromCssColorString(colors.wall);
  const params = new URLSearchParams(window.location.search);
  const detailed = params.get('daylight') === 'detail' || params.get('layers') === 'all';
  for (let i = 0; i < envelope.walls.length; i++) {
    const wall = envelope.walls[i];
    if (!wall.positions || wall.positions.length < 2) continue;
    const heights = wall.max_heights ?? wall.positions.map(() => 0);
    const flatHeights: number[] = [];
    for (let j = 0; j < wall.positions.length; j++) {
      const p = wall.positions[j];
      flatHeights.push(p[0], p[1], datumElevationM + (heights[j] ?? 0));
    }

    // Backend gives this daylight envelope as a sloped quadrilateral:
    // boundary edge at H=0 and inward edge at H=d*multiplier.
    // Rendering it as Cesium `wall` folds the 4-point polygon into vertical
    // fence pieces, which is visually and legally misleading. Use an actual
    // per-vertex-height polygon instead.
    viewer.entities.add({
      id: `${SETBACK_PREFIX}daylight_diagonal_envelope-${i}`,
      polygon: {
        hierarchy: Cesium.Cartesian3.fromDegreesArrayHeights(flatHeights),
        perPositionHeight: true,
        material: color.withAlpha(detailed ? 0.20 : 0.11),
        outline: false,
      },
    });
    const outlinePositions = wall.positions.map((p, j) =>
      Cesium.Cartesian3.fromDegrees(p[0], p[1], datumElevationM + (heights[j] ?? 0)),
    );
    outlinePositions.push(outlinePositions[0]);
    viewer.entities.add({
      id: `${SETBACK_PREFIX}daylight_diagonal_envelope-outline-${i}`,
      polyline: {
        positions: outlinePositions,
        width: detailed ? 4 : 3,
        material: color.withAlpha(detailed ? 0.90 : 0.68),
      },
    });

    if (wall.positions.length >= 4) {
      const edgeMid = midpoint(
        { lng: wall.positions[0][0], lat: wall.positions[0][1] },
        { lng: wall.positions[1][0], lat: wall.positions[1][1] },
      );
      const innerMid = midpoint(
        { lng: wall.positions[wall.positions.length - 1][0], lat: wall.positions[wall.positions.length - 1][1] },
        { lng: wall.positions[2][0], lat: wall.positions[2][1] },
      );
      const maxHeight = Math.max(...heights);
      viewer.entities.add({
        id: `${SETBACK_PREFIX}daylight_diagonal_profile-${i}`,
        polyline: {
          positions: [
            Cesium.Cartesian3.fromDegrees(edgeMid.lng, edgeMid.lat, datumElevationM),
            Cesium.Cartesian3.fromDegrees(innerMid.lng, innerMid.lat, datumElevationM + maxHeight),
          ],
          width: detailed ? 6 : 4,
          material: color.withAlpha(0.92),
        },
      });
    }

    const labelPoint = wall.positions[Math.floor(wall.positions.length / 2)];
    const maxHeight = Math.max(...heights);
    if (i === 0 && labelPoint) {
      viewer.entities.add({
        id: `${SETBACK_PREFIX}daylight_diagonal_envelope-label`,
        position: Cesium.Cartesian3.fromDegrees(labelPoint[0], labelPoint[1], datumElevationM + Math.max(8, maxHeight * 0.45)),
        label: {
          text: `채광사선\nH ≤ 거리 × ${((envelope as { multiplier?: number }).multiplier ?? 2).toFixed(0)}`,
          font: '700 12px ui-monospace, SFMono-Regular, Menlo, monospace',
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 3,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          backgroundColor: Cesium.Color.BLACK.withAlpha(0.44),
          backgroundPadding: new Cesium.Cartesian2(7, 4),
          showBackground: true,
          pixelOffset: new Cesium.Cartesian2(-36, -28),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
      });
    }
  }
}

/** Clear all constraint visualization entities */
function clearConstraintEntities(viewer: any) {
  const toRemove: any[] = [];
  for (const e of viewer.entities.values) {
    if (typeof e.id === 'string' && e.id.startsWith(CONSTRAINTS_PREFIX)) toRemove.push(e);
  }
  for (const e of toRemove) viewer.entities.remove(e);
}

/**
 * Render constraint envelope features from /design/constraints/visualize/.
 * setbackGeometries fallback path — PNU 검색 없이 임의 polygon에 envelope 시각.
 *
 * features per kind:
 *   - site: 검정 outline (대지경계선)
 *   - adjacent_setback: 빨간 점선 (대지 안의 공지) — Flexity 광고 매칭
 *   - north_sunlight_base: 녹색 점선 + 반투명 fill (정북 일조 base 1.5m)
 *   - sunlight_slope_info: 라벨용 (3D는 sunlight 모듈 별도)
 *   - regulation_summary: metadata only (시각 X)
 */
function renderConstraintEntities(viewer: any, Cesium: any, result: ConstraintsResult) {
  clearConstraintEntities(viewer);

  for (const feature of result.features) {
    const kind = feature.properties.kind;
    const color = feature.properties.color || '#888888';
    const dashArray = feature.properties.stroke_dasharray;
    const fillOpacity = feature.properties.fill_opacity ?? 0.0;
    const strokeWidth = feature.properties.stroke_width ?? 2;

    // Skip metadata-only features
    if (kind === 'regulation_summary' || kind === 'sunlight_slope_info') {
      continue;
    }

    const geom = feature.geometry as { type: string; coordinates: any };
    const ring = extractRing(geom);
    if (!ring || ring.length < 3) {
      continue;
    }
    const flat = flattenRing(ring);

    // Polygon fill (when fill_opacity > 0)
    if (fillOpacity > 0) {
      viewer.entities.add({
        id: `${CONSTRAINTS_PREFIX}${kind}-fill`,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
          // Cesium: heightReference + CLAMP_TO_GROUND 사용 시 height 명시 필요.
          // 0 = sea level, terrain 기반 자동 클램프 (renderSetbackEntities와 동일 패턴).
          height: 0,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          material: Cesium.Color.fromCssColorString(color).withAlpha(fillOpacity),
          outline: false,
        },
      });
    }

    // Outline polyline (dashed if stroke_dasharray present)
    const cesiumColor = Cesium.Color.fromCssColorString(color);
    const material = dashArray
      ? new Cesium.PolylineDashMaterialProperty({
          color: cesiumColor,
          dashLength: (dashArray[0] + (dashArray[1] || 0)) * 4,
        })
      : cesiumColor;

    viewer.entities.add({
      id: `${CONSTRAINTS_PREFIX}${kind}-outline`,
      polyline: {
        positions: Cesium.Cartesian3.fromDegreesArray(flat),
        width: strokeWidth * 2,
        material,
        clampToGround: true,
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

  // 2026-05-11 v4 — Cesium 공식 권장: flyToBoundingSphere + HeadingPitchRange.
  // BoundingSphere가 parcel bbox 자동 fit + range는 sphere.radius 비율로 결정.
  // 우주/검정 방지 — Cesium이 자동으로 적절한 거리 계산.
  // https://cesium.com/learn/cesiumjs/ref-doc/Camera.html#flyToBoundingSphere
  const rect = Cesium.Rectangle.fromDegrees(west, south, east, north);
  const sphere = Cesium.BoundingSphere.fromRectangle3D(rect, Cesium.Ellipsoid.WGS84);

  viewer.camera.flyToBoundingSphere(sphere, {
    offset: new Cesium.HeadingPitchRange(
      0,                                  // heading 0 = 정북 보기
      Cesium.Math.toRadians(-45),         // pitch -45° = 측면 + 윗면 균형
      sphere.radius * 3,                  // range = 3× radius (적정 zoom)
    ),
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
    clearHighlight: () => void;
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

  const { ready, loading, error, highlightParcel, clearHighlight, flyTo, setBuildingsVisible, viewerRef } = useVworld3D({
    target: mapRef,
    onClick: handleMapClick,
  });

  actionsRef.current = { highlightParcel, clearHighlight, flyTo, viewerRef };

  // Highlight + flyTo when sitePolygon changes
  React.useEffect(() => {
    if (!sitePolygon || !ready) return;
    const hasSetbacks = setbackGeometries && Object.keys(setbackGeometries).length > 0;
    if (hasSetbacks) {
      clearHighlight();
    } else {
      highlightParcel(sitePolygon);
    }
    flyToGeometryBbox(viewerRef, sitePolygon);
  }, [sitePolygon, setbackGeometries, ready, highlightParcel, clearHighlight, viewerRef]);

  // Render 3D building mass when features change + hide existing Vworld buildings
  React.useEffect(() => {
    if (!ready) return;
    const viewer = viewerRef.current;
    const Cesium = getCesium();
    if (!viewer || !Cesium) return;

    const hasSetbacks = setbackGeometries && Object.keys(setbackGeometries).length > 0;
    // 매스는 정북일조 평균수평면이 아니라 대지 자체 §119 datum 위에 배치한다.
    const datumZ = setbackGeometries?.datum_result?.parcel_datum_m
      ?? setbackGeometries?.datum_result?.elevation_m;
    if (massFeatures && massFeatures.length > 0) {
      setBuildingsVisible(false);
      renderMassEntities(viewer, Cesium, massFeatures, selectedDesignId, datumZ);
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
      clearHighlight();
      clearConstraintEntities(viewer);
      // Terrain이 envelope polygon (H=10~50m)을 가리는 것 방지 — depth test 끔.
      // Vworld terrain이 parcel 위치에서 10.18m 고도라 H=10m envelope가 묻힘.
      try {
        if (viewer.scene?.globe) viewer.scene.globe.depthTestAgainstTerrain = false;
      } catch { /* ignore */ }
      const ring = sitePolygon ? extractRing(sitePolygon as { type: string; coordinates: any }) : null;
      renderSetbackEntities(viewer, Cesium, setbackGeometries, ring);
      // NOTE: 카메라 이동은 sitePolygon useEffect의 flyToGeometryBbox(line 407)이
      // 이미 parcel 위치로 이동시킴. zoomTo(entities)는 vworld map 자체 카메라 모션과
      // race condition 발생해 기존 위치 잃어버림 → entities 위치 이동 호출 제거.
      // 사용자가 carcel에 줌인 되어 있으면 envelope wall(H=10m)/slope(H=50m) 자동 보임.

      // Plan PNG와 동일한 희소 법규 기준점만 표시한다.
      // 전체 표고 격자/넓은 datum 면은 법규 기준점과 혼동되므로 기본 표시하지 않는다.
      clearDatumPlane(viewer);
      renderDatumMarkers(viewer, Cesium, buildDatumMarkers(setbackGeometries, ring));

      // 자동 표고 격자는 법규 기준면과 혼동되므로 /design에서는 기본 표시하지 않는다.
      clearElevationGrid(viewer);
    } else {
      clearDatumPlane(viewer);
      clearElevationGrid(viewer);
    }
  }, [setbackGeometries, sitePolygon, ready, viewerRef, clearHighlight]);

  // visualizeConstraints fallback — setbackGeometries 비어있을 때 임의 polygon에
  // envelope/setback 시각 자동 생성 (Flexity 광고의 빨간 공지 + 녹색 사선 base 매칭).
  // PNU 검색 성공 시 setbackGeometries가 채워지므로 이 fallback은 트리거 X.
  React.useEffect(() => {
    if (!ready) return;
    const viewer = viewerRef.current;
    const Cesium = getCesium();
    if (!viewer || !Cesium) return;

    const hasSetbacks = setbackGeometries && Object.keys(setbackGeometries).length > 0;
    if (sitePolygon && !hasSetbacks) {
      visualizeConstraints({ site_polygon: sitePolygon })
        .then(result => renderConstraintEntities(viewer, Cesium, result))
        .catch(err => console.warn('[visualizeConstraints] fallback failed:', err));
    } else {
      clearConstraintEntities(viewer);
    }
  }, [sitePolygon, setbackGeometries, ready, viewerRef]);

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
