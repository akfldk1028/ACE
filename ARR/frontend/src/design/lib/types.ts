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
  setback_geometries?: Record<string, SetbackGeometry>;
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
