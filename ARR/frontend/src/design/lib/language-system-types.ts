export interface LanguageAxisItem {
  id: string;
  label: string;
  [key: string]: unknown;
}

export type ExplorationAuthority = 'book' | 'engineered' | 'experimental' | 'observed';

export interface ExplorationGraphNode {
  id: string;
  kind: string;
  stage: string;
  label: string;
  authority: ExplorationAuthority;
  evidence_ids: string[];
  visible: boolean;
  attributes: Record<string, unknown>;
}

export interface ExplorationGraphEdge {
  id: string;
  source: string;
  target: string;
  kind: string;
  scope: 'execution' | 'evidence' | 'detail' | 'feedback';
  authority: ExplorationAuthority;
}

export interface BookExplorationGraph {
  schema_version: string;
  graph_id: string;
  root_node_ids: string[];
  stage_order: string[];
  catalog_stage_order: string[];
  authority_order: ExplorationAuthority[];
  source_documents: Array<{ id: string; label: string; path: string; sha256: string }>;
  nodes: ExplorationGraphNode[];
  edges: ExplorationGraphEdge[];
  counts: Record<string, number>;
  contracts: Record<string, boolean>;
}

export interface OutcomeGraphNode {
  id: string;
  kind: string;
  label: string;
  attributes: Record<string, unknown>;
}

export interface OutcomeGraphEdge {
  id: string;
  source: string;
  target: string;
  kind: string;
}

export interface OutcomeGraphSlice {
  schema_version: string;
  status: 'ready' | 'not_found';
  pnu: string;
  root_node_ids: string[];
  nodes: OutcomeGraphNode[];
  edges: OutcomeGraphEdge[];
  counts?: Record<string, number>;
  contracts?: Record<string, boolean>;
}

export interface MassExecutionStage {
  id: string;
  label: string;
  status: 'passed' | 'failed' | 'evaluated' | 'not_evaluated' | 'cache_hit' | 'live_scored';
  required_for_final: boolean;
  node_ids: string[];
  evidence: Record<string, unknown>;
}

export interface MassActivationNode {
  id: string;
  source_id?: string;
  column: string;
  label: string;
  kind: string;
  operator?: string;
  status: string;
  activation: number;
  evidence: Record<string, unknown>;
}

export interface MassExecutionPassport {
  schema_version: string;
  mass_id: string;
  program_name: string;
  program_hash: string;
  structural_hash: string;
  geometry_hash: string;
  status: string;
  full_flow_complete: boolean;
  truth_policy: {
    unevaluated_is_never_pass: boolean;
    internal_neuron_claim: boolean;
    causal_program_trace: boolean;
    visual_activation_uses_materialized_evidence_only: boolean;
  };
  stages: MassExecutionStage[];
  activation_graph: {
    schema_version: string;
    internal_neuron_claim: boolean;
    causal_program_trace: boolean;
    nodes: MassActivationNode[];
    edges: Array<{
      id: string;
      source: string;
      target: string;
      relation: string;
      activation: number;
    }>;
  };
  retrieved_references?: Array<{
    id: string;
    source_id: string;
    title: string;
    source: string;
    source_url: string;
    preview_url: string;
    selection_role: string;
    matched_tags: string[];
    program_match_tier: string;
    reference_collection: string;
    score: number | null;
    retrieval_order: number;
    used_by_vlm: boolean;
  }>;
  reference_truth_policy?: {
    retrieved_is_not_vlm_input: boolean;
    active_visual_reference_edge_requires_recorded_vlm_submission: boolean;
    retrieval_launches_paid_vlm: boolean;
  };
  reference_retrieval?: {
    source: string;
    collection_count: number;
    image_count: number;
    project_count: number;
    program_id: string;
    building_type: string;
    geometry_family: string;
    intent_tags: string[];
    query_role: string;
    current_mass_causality: string;
  };
}

export interface ExecutedMassRecord {
  archive_key: string;
  index: number;
  variant_id: string;
  label: string;
  operation_label: string;
  source_sequence: string;
  run_id: string;
  program_type: string;
  program_label: string;
  program_hash: string;
  geometry_hash: string;
  dsl: string;
  node_count: number;
  operator_path: string[];
  book_principle_id: string;
  book_scope: string;
  book_orientation: string;
  capacity_alternative_id: string;
  capacity_target_utilization: number | null;
  capacity_achieved_utilization: number | null;
  far_pct: number | null;
  score: number | null;
  hard_pass: boolean;
  geometry_ready?: boolean;
  vlm_evaluated: boolean;
  preview_url: string;
  passport_url: string;
  image_role: 'actual_run_candidate_render' | 'single_mass_execution_render';
}

export interface ExecutedMassRun {
  run_id: string;
  created_at: string;
  pnu: string;
  selected_mass_count: number;
  status: 'selected_mass_ready' | 'single_mass_ready' | 'completed_without_selected_mass' | 'running' | 'failed' | 'aborted_memory_pressure' | 'unknown';
  replayable: boolean;
  run_type?: 'portfolio' | 'single_execution';
}

export interface SingleMassExecutionResponse {
  execution_id: string;
  archive_run_id: string;
  status: string;
  geometry_ready: boolean;
  full_flow_status: string;
  geometry_hash: string;
  timings_ms: Record<string, number>;
  preview_url: string;
  passport_url: string;
  manifest_url: string;
}

export interface ExecutedMassManifest {
  schema_version: string;
  run_id: string;
  pnu: string;
  run_status: string;
  numeric_status: string;
  source_archive: string;
  mass_count: number;
  selected_run_id: string;
  run_count: number;
  archive_revision: string;
  runs: ExecutedMassRun[];
  book_images_included: false;
  image_authority: string;
  portfolio_vlm_audit: {
    status?: string;
    hard_pass?: boolean;
    candidate_count?: number;
    visible_family_count?: number;
    dominant_family_share?: number;
    failure_reasons?: string[];
    model?: string;
    response_id?: string;
    cache_hit?: boolean;
  };
  masses: ExecutedMassRecord[];
}

export interface MaasLanguageSystemManifest {
  schema_version: string;
  system_id: string;
  source: {
    page_count: number;
    principle_count: number;
    authority: string;
    bundle: {
      schema_version: string;
      document_count: number;
      documents: Array<{
        role: string;
        filename: string;
        path: string;
        purpose: string;
        line_count: number;
        sha256: string;
      }>;
    };
  };
  geometry_language_contract: {
    schema_version: string;
    definition: string;
    type_invariant: string;
    recursive_grammar: string[];
    shape_count: number;
    shapes: Array<{
      index: number;
      family: string;
      name: string;
      feature: string;
      recommended: string;
      risk: string;
      primitive_operators: string[];
      operators: string[];
      minimum_program: string;
      compile_status: string;
      gate_pass: boolean;
      geometry_hash: string;
      program_cost: Record<string, number>;
    }>;
    graph: {
      stage_order: string[];
      nodes: Array<{
        id: string;
        kind: string;
        stage: string;
        label: string;
        attributes: Record<string, unknown>;
      }>;
      edges: Array<{ source: string; target: string; kind: string }>;
    };
  };
  semantic_order: string[];
  exploration_graph: BookExplorationGraph;
  form_bank_contract: {
    schema_version: string;
    stage_order: string[];
    program_conditioned: boolean;
    program_count: number;
    dominant_solid_authority: string;
    program_role: string;
    vlm_role: string;
  };
  base_volume_contract: {
    rule: string;
    examples: Array<{
      base_volume: string;
      base_seed: string;
      reads_as: string;
    }>;
  };
  reference_context: {
    source: string;
    available: boolean;
    collection_count: number;
    image_count: number;
    transfer_contract: string;
    pipeline_order: string[];
    live_vlm_policy: {
      reference_images_per_request: number;
      process_request_cap: number;
      retry_count: number;
      launch_mode: string;
    };
  };
  axes: {
    base_volumes: LanguageAxisItem[];
    orientations: LanguageAxisItem[];
    base_seeds: LanguageAxisItem[];
    chassis: LanguageAxisItem[];
    principles: LanguageAxisItem[];
    variations: LanguageAxisItem[];
    programs: LanguageAxisItem[];
    capacity_alternatives: LanguageAxisItem[];
    hard_gates: LanguageAxisItem[];
    live_vlm: LanguageAxisItem[];
  };
  counts: {
    base_volumes: number;
    orientations: number;
    base_seeds: number;
    chassis: number;
    principles: number;
    variations: number;
    programs: number;
    capacity_alternatives: number;
    base_seed_scope_instances: number;
    book_variant_paths: number;
    program_conditioned_paths: number;
    capacity_conditioned_paths: number;
    theoretical_language_paths: number;
    universal_form_programs: number;
    declared_search_units: number;
    declared_execution_edges: number;
  };
  count_formula: string;
  compatibility_contract: Record<string, boolean>;
}
