/**
 * Bridge between land regulation results and GA constraints.
 *
 * Converts regulation calculator output into GA constraint/objective
 * definitions that the optimization engine understands.
 *
 * Ported from: ARR/backend/design/services/constraint_bridge.py
 *
 * 10 algorithm gene layouts:
 *   additive(29), subtractive(23), grid(22), lshape(11), ushape(13),
 *   cross(10), courtyard(12), tower_podium(13), hshape(13), radial(16)
 */

// --- Floor height by building type (from mass_evaluator.py) ---

const BUILDING_TYPES: Record<string, { label: string; floorHeight: number }> = {
  "공동주택":     { label: "공동주택 (아파트)",    floorHeight: 2.8 },
  "근린생활시설": { label: "근린생활시설",          floorHeight: 3.5 },
  "업무시설":     { label: "업무시설 (오피스)",     floorHeight: 3.8 },
  "판매시설":     { label: "판매시설 (상가)",       floorHeight: 4.0 },
  "숙박시설":     { label: "숙박시설 (호텔)",       floorHeight: 3.0 },
  "문화집회시설": { label: "문화 및 집회시설",      floorHeight: 4.5 },
  "의료시설":     { label: "의료시설",              floorHeight: 3.6 },
  "교육연구시설": { label: "교육연구시설",          floorHeight: 3.5 },
  "공장":         { label: "공장",                  floorHeight: 5.0 },
  "창고시설":     { label: "창고시설",              floorHeight: 6.0 },
};

const DEFAULT_FLOOR_HEIGHT = 3.0;

function getFloorHeight(buildingType: string): number {
  return BUILDING_TYPES[buildingType]?.floorHeight ?? DEFAULT_FLOOR_HEIGHT;
}

// --- Types ---

export interface GAParam {
  name: string;
  type: string;
  Min?: number;
  Max?: number;
  "Set length"?: number;
  Requirement?: string;
  val?: number;
  unit?: string;
  label?: string;
  Goal?: string;
}

export interface JobSpec {
  inputs: GAParam[];
  outputs: GAParam[];
  options: Record<string, unknown>;
}

// --- Constraints from regulation result ---

export function regulationsToConstraints(reg: Record<string, unknown>): GAParam[] {
  const constraints: GAParam[] = [];

  const bcr = (reg.bcr_pct ?? reg.bcr_limit) as number | undefined;
  if (bcr != null) {
    constraints.push({
      name: "bcr", type: "Constraint", Requirement: "Less than",
      val: bcr, unit: "%", label: `건폐율 ≤ ${bcr}%`,
    });
  }

  const far = (reg.far_pct ?? reg.far_limit) as number | undefined;
  if (far != null) {
    constraints.push({
      name: "far", type: "Constraint", Requirement: "Less than",
      val: far, unit: "%", label: `용적률 ≤ ${far}%`,
    });
  }

  const height = reg.height_limit_m as number | undefined;
  if (height != null) {
    constraints.push({
      name: "height", type: "Constraint", Requirement: "Less than",
      val: height, unit: "m", label: `높이 ≤ ${height}m`,
    });
  }

  const setback = reg.adjacent_setback_m as number | undefined;
  if (setback != null) {
    constraints.push({
      name: "setback", type: "Constraint", Requirement: "Greater than",
      val: setback, unit: "m", label: `인접대지 이격 ≥ ${setback}m`,
    });
  }

  const bline = reg.building_line_setback_m as number | undefined;
  if (bline != null) {
    constraints.push({
      name: "building_line_setback", type: "Constraint", Requirement: "Greater than",
      val: bline, unit: "m", label: `건축선 후퇴 ≥ ${bline}m`,
    });
  }

  const landscape = reg.landscaping_min_pct as number | undefined;
  if (landscape != null) {
    constraints.push({
      name: "landscaping_pct", type: "Constraint", Requirement: "Greater than",
      val: landscape, unit: "%", label: `조경면적 ≥ ${landscape}%`,
    });
  }

  return constraints;
}

// --- Objectives by building type ---

const TYPE_OBJECTIVES: Record<string, GAParam[]> = {
  "공동주택":     [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "daylight_score", type: "Objective", Goal: "Maximize" }],
  "근린생활시설": [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "landscaping_pct", type: "Objective", Goal: "Maximize" }],
  "업무시설":     [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "landscaping_pct", type: "Objective", Goal: "Maximize" }],
  "판매시설":     [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "landscaping_pct", type: "Objective", Goal: "Maximize" }],
  "숙박시설":     [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "daylight_score", type: "Objective", Goal: "Maximize" }],
  "문화집회시설": [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "setback", type: "Objective", Goal: "Maximize" }],
  "의료시설":     [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "daylight_score", type: "Objective", Goal: "Maximize" }],
  "교육연구시설": [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "daylight_score", type: "Objective", Goal: "Maximize" }],
  "공장":         [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "landscaping_pct", type: "Objective", Goal: "Maximize" }],
  "창고시설":     [{ name: "floor_area", type: "Objective", Goal: "Maximize" },
                   { name: "landscaping_pct", type: "Objective", Goal: "Maximize" }],
};

const DEFAULT_OBJECTIVES: GAParam[] = [
  { name: "floor_area", type: "Objective", Goal: "Maximize" },
  { name: "daylight_score", type: "Objective", Goal: "Maximize" },
];

// --- Gene input builders (10 algorithms) ---

function cont(name: string, min: number, max: number): GAParam {
  return { name, type: "Continuous", Min: min, Max: max, "Set length": 1 };
}

function globalInputs(maxFloors: number): GAParam[] {
  return [
    cont("num_floors", 1, maxFloors),
    cont("rotation", 0, 180),
    cont("upper_scale", 0.5, 1.0),
    cont("step_fraction", 0.3, 0.8),
  ];
}

function buildAdditiveInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  const inputs: GAParam[] = [];
  for (let i = 0; i < 5; i++) {
    inputs.push(
      cont(`b${i}_x`, -maxDim * 0.5, maxDim * 0.5),
      cont(`b${i}_y`, -maxDim * 0.5, maxDim * 0.5),
      cont(`b${i}_w`, minDim, maxDim * 0.6),
      cont(`b${i}_d`, minDim, maxDim * 0.6),
      cont(`b${i}_rot`, 0, 180),
    );
  }
  return [...inputs, ...globalInputs(maxFloors)];
}

function buildSubtractiveInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  const inputs: GAParam[] = [
    cont("scale_x", 0.4, 1.0),
    cont("scale_y", 0.4, 1.0),
    cont("block_rot", 0, 180),
    cont("block_inset", 0, maxDim * 0.2),
  ];
  for (let i = 0; i < 3; i++) {
    inputs.push(
      cont(`v${i}_x`, -maxDim * 0.4, maxDim * 0.4),
      cont(`v${i}_y`, -maxDim * 0.4, maxDim * 0.4),
      cont(`v${i}_w`, minDim, maxDim * 0.5),
      cont(`v${i}_d`, minDim, maxDim * 0.5),
      cont(`v${i}_rot`, 0, 180),
    );
  }
  return [...inputs, ...globalInputs(maxFloors)];
}

function buildGridInputs(maxDim: number, _minDim: number, maxFloors: number): GAParam[] {
  const inputs: GAParam[] = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      inputs.push(
        cont(`cell_${i}_${j}_on`, 0, 1),
        cont(`cell_${i}_${j}_h`, 0.3, 1.0),
      );
    }
  }
  return [...inputs, ...globalInputs(maxFloors)];
}

function buildLshapeInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  return [
    cont("wing1_w", minDim, maxDim * 0.7),
    cont("wing1_d", minDim, maxDim * 0.4),
    cont("wing2_w", minDim, maxDim * 0.4),
    cont("wing2_d", minDim, maxDim * 0.7),
    cont("junction", 0, 1),
    cont("side", 0, 1),
    cont("local_rot", 0, 180),
    ...globalInputs(maxFloors),
  ];
}

function buildUshapeInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  return [
    cont("base_w", minDim * 2, maxDim * 0.8),
    cont("base_d", minDim, maxDim * 0.3),
    cont("left_w", minDim, maxDim * 0.3),
    cont("left_d", minDim, maxDim * 0.6),
    cont("right_w", minDim, maxDim * 0.3),
    cont("right_d", minDim, maxDim * 0.6),
    cont("gap", minDim, maxDim * 0.5),
    cont("opening_side", 0, 1),
    cont("local_rot", 0, 180),
    ...globalInputs(maxFloors),
  ];
}

function buildCrossInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  return [
    cont("bar1_w", minDim * 2, maxDim * 0.8),
    cont("bar1_d", minDim, maxDim * 0.35),
    cont("bar2_w", minDim * 2, maxDim * 0.8),
    cont("bar2_d", minDim, maxDim * 0.35),
    cont("offset_x", -maxDim * 0.2, maxDim * 0.2),
    cont("offset_y", -maxDim * 0.2, maxDim * 0.2),
    ...globalInputs(maxFloors),
  ];
}

function buildCourtyardInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  return [
    cont("outer_w", minDim * 3, maxDim * 0.9),
    cont("outer_d", minDim * 3, maxDim * 0.9),
    cont("wall_t", minDim, maxDim * 0.25),
    cont("court_x", -maxDim * 0.1, maxDim * 0.1),
    cont("court_y", -maxDim * 0.1, maxDim * 0.1),
    cont("court_w", minDim, maxDim * 0.5),
    cont("court_d", minDim, maxDim * 0.5),
    cont("opening", 0, 1),
    ...globalInputs(maxFloors),
  ];
}

function buildTowerPodiumInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  return [
    cont("podium_w", minDim * 3, maxDim * 0.9),
    cont("podium_d", minDim * 3, maxDim * 0.9),
    cont("podium_h_ratio", 0.1, 0.5),
    cont("tower_x", -maxDim * 0.2, maxDim * 0.2),
    cont("tower_y", -maxDim * 0.2, maxDim * 0.2),
    cont("tower_w", minDim * 2, maxDim * 0.5),
    cont("tower_d", minDim * 2, maxDim * 0.5),
    cont("tower_rot", 0, 90),
    cont("setback", 0, maxDim * 0.15),
    ...globalInputs(maxFloors),
  ];
}

function buildHshapeInputs(maxDim: number, minDim: number, maxFloors: number): GAParam[] {
  return [
    cont("bar1_w", minDim, maxDim * 0.35),
    cont("bar1_d", minDim * 2, maxDim * 0.8),
    cont("bar2_w", minDim, maxDim * 0.35),
    cont("bar2_d", minDim * 2, maxDim * 0.8),
    cont("gap", minDim, maxDim * 0.4),
    cont("bridge_w", minDim, maxDim * 0.4),
    cont("bridge_d", minDim, maxDim * 0.25),
    cont("bridge_offset", 0, 1),
    cont("local_rot", 0, 180),
    ...globalInputs(maxFloors),
  ];
}

function buildRadialInputs(maxDim: number, _minDim: number, maxFloors: number): GAParam[] {
  const inputs: GAParam[] = [];
  for (let i = 0; i < 6; i++) {
    inputs.push(
      cont(`sec${i}_on`, 0, 1),
      cont(`sec${i}_radius`, 0.2, 1.0),
    );
  }
  return [...inputs, ...globalInputs(maxFloors)];
}

// --- Algorithm registry ---

export const ALL_ALGORITHMS = [
  "additive", "subtractive", "grid",
  "lshape", "ushape", "cross", "courtyard",
  "tower_podium", "hshape", "radial",
] as const;

export type Algorithm = (typeof ALL_ALGORITHMS)[number];

const INPUT_BUILDERS: Record<string, (md: number, mn: number, mf: number) => GAParam[]> = {
  additive: buildAdditiveInputs,
  subtractive: buildSubtractiveInputs,
  grid: buildGridInputs,
  lshape: buildLshapeInputs,
  ushape: buildUshapeInputs,
  cross: buildCrossInputs,
  courtyard: buildCourtyardInputs,
  tower_podium: buildTowerPodiumInputs,
  hshape: buildHshapeInputs,
  radial: buildRadialInputs,
};

// --- Build default job spec ---

export function buildDefaultJobSpec(
  siteAreaM2: number,
  constraints: GAParam[],
  buildingType = "공동주택",
  algorithm = "additive",
): JobSpec {
  const maxDim = Math.sqrt(siteAreaM2) * 0.9;
  const minDim = Math.max(3.0, maxDim * 0.1);

  let maxHeight = 100.0;
  for (const c of constraints) {
    if (c.name === "height" && c.Requirement === "Less than" && c.val != null) {
      maxHeight = c.val;
      break;
    }
  }

  const floorHeight = getFloorHeight(buildingType);
  const maxFloors = Math.max(1, Math.floor(maxHeight / floorHeight));

  const builder = INPUT_BUILDERS[algorithm] ?? buildAdditiveInputs;
  const inputs = builder(maxDim, minDim, maxFloors);

  const objectives = TYPE_OBJECTIVES[buildingType] ?? DEFAULT_OBJECTIVES;
  const outputs = [...objectives, ...constraints];

  const options: Record<string, unknown> = {
    "Number of generations": 120,
    num_islands: 7,
    pop_per_island: 30,
    migration_interval: 8,
    migrants_count: 3,
    tournament_size: 8,
    initial_mutation_rate: 0.35,
    final_mutation_rate: 0.10,
    algorithm,
  };

  return { inputs, outputs, options };
}
