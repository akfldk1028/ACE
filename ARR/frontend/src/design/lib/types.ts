export interface DesignJob {
  id: string;
  pnu: string;
  address: string;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'cancelled';
  generation_count: number;
  max_generations: number;
  population_size: number;
  site_area_m2: number | null;
  constraints: Constraint[];
  created_at: string | null;
  completed_at: string | null;
  error: string;
}

export interface Constraint {
  name: string;
  type: 'Constraint';
  Requirement: string;
  val: number;
  unit: string;
  label: string;
}

export interface DesignData {
  id: number;
  generation: number;
  parents: [number | null, number | null];
  feasible: boolean;
  inputs: number[][];
  objectives: number[];
  penalty: number;
  rank: number;
  elite: number;
  /** Algorithm name — set in "all" mode (multi-algorithm) */
  algorithm?: string;
}

export interface DesignResult {
  design_id: number;
  generation: number;
  inputs: number[][];
  outputs: Record<string, unknown>;
  ranking: number | null;
  crowding_distance: number | null;
  is_feasible: boolean;
  is_pareto_optimal: boolean;
  mass_geojson: GeoJSONFeature | null;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: number[][][];
  };
  properties: {
    height: number;
    num_floors: number;
    floor_height?: number;
    building_type?: string;
    mass_shape?: string;
    footprint_area: number;
    floor_area: number;
    bcr: number;
    far: number;
    design_id?: number;
    generation?: number;
    objectives?: number[];
    algorithm?: string;
    // Step-back (two-tier) massing
    step_floor?: number;
    upper_scale?: number;
    lower_height?: number;
    upper_geometry?: { type: string; coordinates: number[][][] };
  };
}

export interface SSEEvent {
  type: 'started' | 'generation' | 'complete' | 'error' | 'cancelled';
  generation?: number;
  max_generations?: number;
  population_size?: number;
  pareto_count?: number;
  pareto_front?: DesignData[];
  best?: DesignData | null;
  best_geojson?: GeoJSONFeature | null;
  pareto_geojson?: GeoJSONFeature[];
  feasible_count?: number;
  total_designs?: number;
  total_evaluated?: number;
  generations?: number;
  message?: string;
  objectives?: { name: string; goal: string }[];
  scatter?: [number, number, boolean, number][]; // [obj0, obj1, feasible, generation]
}

export interface SetbackGeometry {
  geometry: { type: string; coordinates: number[][][] };
  distance_m: number;
  label: string;
}

/**
 * setback_geometries 응답 dict — heterogeneous values:
 *   - 일반 키 (buildable_area, north_setback, ...) → SetbackGeometry
 *   - sunlight_envelope, daylight_diagonal_envelope → SunlightEnvelope (from land/lib/types)
 *   - datum_result → DatumResultDict (envelope 없는 zone에서도 datum 표시용)
 *
 * `as unknown as` 캐스팅 회피용. Phase 2C+ datum metadata 4 필드 포함.
 */
import type { SunlightEnvelope } from '../../land/lib/types';

/** Phase 2D — envelope과 독립적인 datum 정보 (정북일조 미적용 zone 표시용). */
export interface DatumResultDict {
  elevation_m: number;
  case: string | null;
  basis: string | null;
  elevation_source: 'open_meteo' | 'copernicus_glo30' | 'ngii_lidar_1m' | 'ngii_5m' | 'ngii_local_dem' | 'failed' | null;
  parcel_datum_m?: number | null;
  road_datum_m?: number | null;
  neighbor_datum_m?: number | null;
  neighbor_avg_datum_m?: number | null;
  parcel_segments?: DatumBoundarySegment[] | null;
  road_samples?: DatumPointSample[] | null;
  neighbor_segments?: DatumBoundarySegment[] | null;
  split_bands?: Array<{
    band_index: number;
    min_elevation_m: number;
    max_elevation_m: number;
    datum_m: number;
    length_m: number;
    sample_count: number;
    basis: string;
  }> | null;
  split_polygons?: DatumResultDict['split_bands'];
  notes?: string[] | null;
}

export interface DatumBoundarySegment {
  midpoint_lng?: number | null;
  midpoint_lat?: number | null;
  length_m?: number | null;
  elevation_m?: number | null;
}

export interface DatumPointSample {
  lng?: number | null;
  lat?: number | null;
  elevation_m?: number | null;
  weight?: number | null;
}

export type SetbackGeometriesMap =
  Record<string, SetbackGeometry | SunlightEnvelope | DatumResultDict | null | undefined> & {
    sunlight_envelope?: SunlightEnvelope | null;
    daylight_diagonal_envelope?: SunlightEnvelope | null;
    datum_result?: DatumResultDict | null;
  };

export interface LawArticle {
  full_id: string;
  content: string;
  law_name: string;
  law_type: string;
  similarity: number;
}

export interface LawSearchResult {
  articles: { query: string; results: LawArticle[] }[];
  total_count: number;
  errors: string[];
}

export interface AutoConstraintsResult {
  zones: string[];
  regulations: {
    bcr_pct: number | null;
    far_pct: number | null;
    height_limit_m: number | null;
    adjacent_setback_m: number | null;
  };
  constraints: Constraint[];
  setback_geometries?: SetbackGeometriesMap;
  law_articles?: LawSearchResult;
  building_type?: string;
}

export interface SiteBoundaryResult {
  pnu: string;
  geometry: {
    type: string;
    coordinates: number[][][];
  };
  area_m2: number;
  valid: boolean;
  errors: string[];
}

// ── Floor Plan Types ──

export interface FloorPlanRoom {
  name: string;
  area: number;
  adjacency: string[];
}

export interface FloorPlanMetrics {
  adjacency_score: number;
  area_error: number;
  compactness: number;
}

export interface FloorPlanDesign {
  design_id: number;
  metrics: FloorPlanMetrics;
  floor_plan: {
    type: 'FeatureCollection';
    features: {
      type: 'Feature';
      properties: {
        room_code: number;
        room_name: string;
        color: string;
        area_m2: number;
      };
      geometry: {
        type: string;
        coordinates: number[][][];
      };
    }[];
  };
}

export interface FloorPlanResult {
  algorithm?: string;
  grid_info: {
    rows: number;
    cols: number;
    cell_size: number;
    active_cells: number;
  };
  rooms: FloorPlanRoom[];
  num_results: number;
  results: FloorPlanDesign[];
}
