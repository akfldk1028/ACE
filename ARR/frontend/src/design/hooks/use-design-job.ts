import { useState, useCallback } from 'react';
import type { DesignJob, Constraint, SetbackGeometriesMap, LawSearchResult } from '../lib/types';
import { createJob, getAutoConstraints, getSiteBoundary } from '../lib/api-client';

interface DesignJobState {
  job: DesignJob | null;
  constraints: Constraint[];
  sitePolygon: object | null;
  siteArea: number | null;
  zones: string[];
  setbackGeometries: SetbackGeometriesMap;
  lawArticles: LawSearchResult | null;
  loading: boolean;
  error: string | null;
}

export function useDesignJob() {
  const [state, setState] = useState<DesignJobState>({
    job: null,
    constraints: [],
    sitePolygon: null,
    siteArea: null,
    zones: [],
    setbackGeometries: {},
    lawArticles: null,
    loading: false,
    error: null,
  });

  const loadSiteBoundary = useCallback(async (pnu: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const result = await getSiteBoundary(pnu);
      setState(prev => ({
        ...prev,
        sitePolygon: result.geometry,
        siteArea: result.area_m2,
        loading: false,
      }));
      return result;
    } catch (e) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: e instanceof Error ? e.message : 'Failed to load boundary',
      }));
      return null;
    }
  }, []);

  const loadConstraints = useCallback(async (params: {
    pnu?: string; zones?: string[]; site_polygon?: object; building_type?: string;
  }) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const result = await getAutoConstraints(params);
      setState(prev => ({
        ...prev,
        constraints: result.constraints,
        zones: result.zones || [],
        setbackGeometries: result.setback_geometries || {},
        lawArticles: result.law_articles || null,
        loading: false,
      }));
      return result;
    } catch (e) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: e instanceof Error ? e.message : 'Failed to load constraints',
      }));
      return null;
    }
  }, []);

  const startJob = useCallback(async (params?: { job_spec?: object }) => {
    if (!state.sitePolygon) {
      setState(prev => ({ ...prev, error: 'No site polygon selected' }));
      return null;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const job = await createJob({
        site_polygon: state.sitePolygon,
        constraints: state.constraints,
        ...params,
      });
      setState(prev => ({ ...prev, job, loading: false }));
      return job;
    } catch (e) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: e instanceof Error ? e.message : 'Failed to create job',
      }));
      return null;
    }
  }, [state.sitePolygon, state.constraints]);

  const reset = useCallback(() => {
    setState({
      job: null,
      constraints: [],
      sitePolygon: null,
      siteArea: null,
      zones: [],
      setbackGeometries: {},
      lawArticles: null,
      loading: false,
      error: null,
    });
  }, []);

  return { ...state, loadSiteBoundary, loadConstraints, startJob, reset };
}
