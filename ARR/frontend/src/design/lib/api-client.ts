import type { DesignJob, AutoConstraintsResult, SiteBoundaryResult, FloorPlanRoom, FloorPlanResult } from './types';

const BASE = '/design';

export async function createJob(params: {
  site_polygon: object;
  pnu?: string;
  address?: string;
  constraints?: object[];
  job_spec?: object;
}): Promise<DesignJob> {
  const res = await fetch(`${BASE}/jobs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || res.statusText);
  return res.json();
}

export async function getJob(jobId: string): Promise<DesignJob> {
  const res = await fetch(`${BASE}/jobs/${jobId}/`);
  if (!res.ok) throw new Error('Job not found');
  return res.json();
}

export async function cancelJob(jobId: string): Promise<void> {
  await fetch(`${BASE}/jobs/${jobId}/cancel/`, { method: 'POST' });
}

export async function getJobResults(jobId: string) {
  const res = await fetch(`${BASE}/jobs/${jobId}/results/`);
  if (!res.ok) throw new Error('Results not found');
  return res.json();
}

export async function getSiteBoundary(pnu: string): Promise<SiteBoundaryResult> {
  const res = await fetch(`${BASE}/site-boundary/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pnu }),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Boundary fetch failed');
  return res.json();
}

export async function getAutoConstraints(params: {
  pnu?: string;
  zones?: string[];
  address?: string;
  site_polygon?: object;
  building_type?: string;
  include_law_articles?: boolean;
}): Promise<AutoConstraintsResult> {
  const res = await fetch(`${BASE}/auto-constraints/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Constraint generation failed');
  return res.json();
}

export async function generateFloorPlan(params: {
  footprint_geojson: object;
  rooms: FloorPlanRoom[];
  cell_size?: number;
  algorithm?: string;
  options?: { num_generations?: number; population_size?: number };
}): Promise<FloorPlanResult> {
  const res = await fetch(`${BASE}/floor-plan/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Floor plan generation failed');
  return res.json();
}

export interface ConstraintsParams {
  site_polygon: object;
  bcr_limit_pct?: number;
  far_limit_pct?: number;
  height_limit_m?: number;
  adjacent_setback_m?: number;
  north_setback_m?: number;
  road_setback_m?: number;
  sunlight_slope?: number;
  sunlight_base_height_m?: number;
}

export interface ConstraintsResult {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: { type: string; coordinates: unknown };
    properties: {
      kind: string;
      label?: string;
      color?: string;
      stroke_width?: number;
      stroke_dasharray?: number[];
      fill_opacity?: number;
      metadata?: Record<string, unknown>;
    };
  }>;
  metadata?: { generator?: string; version?: string };
}

export async function visualizeConstraints(params: ConstraintsParams): Promise<ConstraintsResult> {
  const res = await fetch(`${BASE}/constraints/visualize/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Constraints visualize failed');
  return res.json();
}
