# Parking Layout Algorithm Review

Updated: 2026-06-11

## Why This Matters For MAAS

Parking is not a scalar requirement. Required count comes from law/ordinance and
candidate use areas, but feasibility comes from layout: stall modules, aisles,
entrance/exit, turning, ramps, columns, core, accessible stalls, and pedestrian
routes. MAAS must therefore treat parking as a generation constraint and repair
signal, not as a final checklist item.

## Sources Reviewed

Primary/relevant sources:

- Thomas, Rambha, 2025, "A Branch-and-Cut Algorithm for the Optimal Design of
  Parking Lots with One-way and Two-way Lanes".
  - URL: https://arxiv.org/abs/2506.09961
  - Code: https://github.com/transnetlab/parking-lot-design
  - Local clone:
    `docs/ai-session-memory/parking-layout-clones/transnetlab-parking-lot-design`
  - Method: grid MIP with driveway connectivity, one-way/two-way lanes, valid
    inequalities, and branch-and-cut feasibility cuts.
  - Use as the primary exact-solver reference.
- Jamaludin, Zhou, Yeoh, 2024, "Automated Basement Car Park Design: Impact of
  Design Factors on Static Capacity", Journal of Architectural Engineering.
  - URL: https://ascelibrary.org/doi/10.1061/JAEIED.AEENG-1609
  - Method: basement car park placement algorithm with GA; focuses on aisle
    network, building footprint, and column positions.
  - Use for basement/piloti column/core impact modeling.
- Cudzik, Nessel, 2024, "Computational Approach towards Repetitive Design Tasks:
  The Case Study of Parking Lot Automated Design", Sustainability.
  - URL: https://www.mdpi.com/2071-1050/16/2/592
  - Method: automated variant generation inside predefined outlines.
  - Use for interactive design/variant workflow framing.
- Lan, Chen, Xu, 2023, "Underground Parking Layout Generation Based on the
  WaveFunctionCollapse Algorithm", Buildings.
  - URL: https://www.mdpi.com/2075-5309/13/11/2898
  - Method: extract underground parking modules, turn design constraints into
    adjacency rules, generate with WFC and optimize with MOO.
  - Use for future basement layout grammar, not for initial legal validation.
- Zhang, Li, Yu, 2023, "Research on Plan Generation Design of Parking Lot Based
  on Integer Programming", CAADRIA 2023.
  - URL: https://scholar.hit.edu.cn/en/publications/research-on-plan-generation-design-of-parking-lot-based-on-intege/
  - PDF: https://papers.cumincad.org/data/works/att/caadria2023_121.pdf
  - Method: ILP for automated surface-parking plan generation; classifies 27
    plan modes using inner-ring organization, traffic organization, and parking
    angle.
  - Use for architectural plan-pattern taxonomy.
- Stephan, Weidinger, Boysen, 2021, "Layout Design of Parking Lots with
  Mathematical Programming", Transportation Science.
  - URL: https://pubsonline.informs.org/doi/abs/10.1287/trsc.2021.1049
  - Method: rasterize the parking plot into a grid; formulate mixed-integer
    programs for orthogonal parking; maximize reachable stalls through driving
    lanes.
  - Use as foundational baseline only, not the newest implementation target.
- Yildirim, Yildirim, Satir, 2019, "Design of a Rectangular Parking Lot Using a
  Cutting-Stock Formulation".
  - URL: https://dergipark.org.tr/tr/download/article-file/729720
  - Method: parking modules/patterns for rectangular lots; supports different
    parking angles, stall dimensions, and access widths. Useful for fast
    module-based precheck.
- Korean statutory dimensions:
  - Parking Lot Act Enforcement Rule Article 3 for stall sizes.
  - Parking Lot Act Enforcement Rule Article 11 for attached parking structure
    and aisle criteria.
  - Official source:
    https://www.law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsId=008238&lsJoLnkSeq=1000128079&print=print

## Algorithm Takeaways

0. 2021 is not the implementation target.
   - It remains useful because the 2025 branch-and-cut paper explicitly builds
     on the grid/MIP line of work.
   - For our implementation, prioritize the 2025 `transnetlab` solver structure,
     2024 basement capacity paper, and 2023/2024 architectural generation papers.

1. Fast deterministic precheck should use parking modules.
   - A module combines stalls and access aisle.
   - For Korea, the initial 90-degree module uses:
     - standard stall: 2.5m x 5.0m;
     - accessible stall: 3.3m x 5.0m;
     - 90-degree adjacent aisle: 6.0m;
     - single-loaded module depth: 11.0m;
     - double-loaded module depth: 16.0m.
   - This is enough to detect impossible mass strategies early.

2. Real layout generation should be grid-based.
   - Rasterize usable parking envelope by a cell size tied to statutory stall
     and aisle dimensions.
   - Decision variables classify cells as stall, drive aisle, blocked/core,
     ramp, pedestrian/access route, or empty.
   - Constraints must enforce connectivity from stalls to entrance/exit.

3. Exact optimization is an MIP/ILP problem.
   - Objective: maximize legal/usable stalls or minimize unmet required stalls.
   - Constraints:
     - no overlap between stalls, aisles, ramps, cores, columns, and egress;
     - each stall has driveway access;
     - driveway graph connects to entrance/exit;
     - accessible stall is close to barrier-free route;
     - ramp and turning constraints for basement/semi-basement;
     - local law dimensions and project-specific BF/design standards.

4. One-way and angled parking are later optimization variants.
   - Literature suggests one-way can increase capacity, but legal/local
     acceptance, circulation clarity, and ramp/turning must be checked.
   - Initial MAAS should start with 90-degree two-way modules because they align
     with simple statutory checks and are easier to verify.

## MAAS Implementation Roadmap

## `transnetlab/parking-lot-design` Code Review

Local clone:

```text
docs/ai-session-memory/parking-layout-clones/transnetlab-parking-lot-design
```

Key files:

- `main.py`
  - procedural runner;
  - reads config, populates valid drive/parking fields, builds grid graph, sets
    CPLEX problem, then calls one-way or two-way optimizer.
- `config.py`
  - global mutable config;
  - defaults to one-way lane mode, cutting-plane solve, valid inequalities on;
  - uses CPLEX, NetworkX, NYC parking lot CSV data.
- `variables.py`
  - binary parking variables:
    - `x0(i,j)` for one orientation;
    - `x90(i,j)` for perpendicular orientation;
  - binary driving variable:
    - `y(i,j)`;
  - continuous flow variables:
    - `f(i,j,k,l)` entry flow;
    - `g(i,j,k,l)` exit flow for one-way;
  - binary one-way direction variable:
    - `z(i,j,k,l)`.
- `grid_utils.py`
  - derives valid parking anchors and valid drive anchors;
  - removes anchors overlapping blocked cells;
  - creates neighbor relationships and adjacency graph.
- `constraints.py`
  - forces entry/exit drive cells;
  - disaggregated single-purpose constraints prevent parking/drive overlap;
  - parking accessibility constraints require each selected stall field to have
    adjacent drive fields;
  - flow conservation connects active drive cells to entry/exit;
  - one-way direction constraints bind `z` to active drive cells.
- `valid_inequalities.py`
  - lazy callbacks reject disconnected driveway solutions;
  - uses NetworkX min node/edge cut;
  - adds hop/reverse-hop inequalities and dead-end constraints.
- `mip.py`
  - assembles all variables and constraints;
  - supports two-way with flow or cut approach;
  - supports one-way with direction variables and cut approach.

Direct import decision:

- Do not import this repo directly into ARR.
- Reasons:
  - CPLEX dependency is commercial/heavy;
  - global config makes web/API use brittle;
  - code is research-script style, not service contract style;
  - dimensions and legal standards must be converted to Korean law/project
    inputs.

Porting decision:

- Reuse the model architecture, not the code shape.
- ARR solver contract should expose:

```text
ParkingGridInput:
  envelope_polygon
  blocked_polygons: core, columns, stairs, ramp, setbacks
  entrance_edges / driveway candidates
  stall_dimensions
  aisle_dimensions
  required_spaces
  accessible_required_spaces
  one_way_allowed

ParkingGridSolution:
  status: pass/fail/needs_solver
  standard_stalls
  accessible_stalls
  drive_cells
  direction_edges
  unmet_required_spaces
  repair_requests
```

Recommended implementation path:

1. Keep current module precheck for fast candidate filtering.
2. Add a lightweight pure-Python grid feasibility check using NetworkX:
   - no optimization yet;
   - verify candidate stall/aisle components if generated by heuristics.
3. Add OR-Tools CP-SAT or python-mip backend for exact solver.
   - Prefer OR-Tools first because it is easier to ship than CPLEX.
4. Port `x0/x90/y/z` variable concepts and connectivity constraints.
5. Add lazy-cut/branch-and-cut only if CP-SAT/MIP is too slow for real cases.

### Stage 0: Implemented Hook

- `ARR/backend/design/maas/parking_strategy.py`
  - chooses a mass-level strategy:
    `ground_surface`, `piloti_ground`, `basement`, `semi_basement`,
    `mechanical`, `mixed`.
- `ARR/backend/design/maas/parking_layout.py`
  - estimates module capacity using envelope geometry and statutory dimensions.
  - now uses actual candidate footprint/site geometry when available:
    - `ground_surface`: `site - footprint`;
    - `piloti_ground`, `basement`, `semi_basement`, `mechanical`, `mixed`:
      candidate footprint envelope.
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - attaches `parking_strategy` and `parking_precheck` to every candidate and
    `maas_model`.
- `ARR/backend/design/maas/evidence.py`
  - exposes parking strategy in evidence but keeps final status as
    `needs_evidence`.

### Stage 0.5: Implemented Deterministic Coordinate Candidate

Implemented after reviewing the 2025 branch-and-cut code and Korean small
attached-parking exceptions:

- `ARR/backend/design/maas/parking_layout.py`
  - `generate_parking_layout_candidate(...)`
    - returns `arr.maas.parking_layout_candidate.v0`;
    - places actual stall polygons in metric coordinates;
    - supports a deterministic first candidate, not a global optimum.
  - Current placement modes:
    - `internal_double_loaded_90`;
    - `internal_single_loaded_90`;
    - `road_as_aisle_single_row`;
    - `road_as_aisle_tandem`.
  - Small-site logic:
    - uses `evaluate_small_attached_parking_relief(...)`;
    - if road-as-aisle conditions are available, tries that first;
    - if 5 or fewer stalls and depth allows, places tandem/serial stalls up to
      two deep from the aisle;
    - otherwise falls back to internal 90-degree module placement.
  - Output includes:
    - `provided_spaces`;
    - `provided_accessible_spaces`;
    - per-stall `polygon` coordinates;
    - `unmet_spaces`;
    - deterministic `repair_requests`.
- `ARR/backend/design/maas/parking_strategy.py`
  - if candidate properties include any of:
    - `required_parking_spaces`;
    - `parking_required_spaces`;
    - `parking_count_required`;
  - then `parking_precheck.layout_candidate` is generated immediately from the
    current MAAS parking envelope.
  - Until Graph DB required-count integration is complete, most generated MAAS
    candidates still report `needs_parking_requirements`.

Reference mapping from reviewed code:

- `transnetlab/parking-lot-design/grid_utils.py`
  - ARR equivalent now starts with metric polygon envelope and deterministic
    valid stall anchors rather than a full grid.
- `transnetlab/parking-lot-design/variables.py`
  - future ARR exact solver should still use `x0/x90/y/z`-style variables;
  - current deterministic candidate only emits placed stall polygons.
- `transnetlab/parking-lot-design/constraints.py`
  - future ARR exact solver must enforce driveway connectivity and
    stall-drive adjacency;
  - current candidate encodes layout mode but does not prove connectivity beyond
    the simple module assumption.
- `transnetlab/parking-lot-design/valid_inequalities.py`
  - future ARR branch-and-cut/lazy-cut pass should reject disconnected driveway
    graphs;
  - current candidate explicitly says it is not a global optimum and does not
    replace the grid/MIP solver.

Why code was not directly imported:

- CPLEX dependency;
- research-script global config;
- NYC dataset assumptions;
- Korean statutory dimensions and small attached-parking exceptions require a
  project-local contract.

### Stage 1: Graph DB Required Count Integration

Input:

```text
PNU + building_type/use schedule + candidate floor/use areas
```

Output:

```text
required_spaces
accessible_spaces_min/max or exact local ratio
law_refs
ordinance_refs
status
```

Connect this to `parking_precheck.required_count` and compare against estimated
capacity.

### Stage 2: Repair Request Generation

If estimated capacity is below required count, emit deterministic repairs:

- `reserve_piloti_void`
- `move_core`
- `reduce_or_split_footprint`
- `add_basement_parking`
- `switch_to_mechanical_parking`
- `change_program_area_or_use_mix`

These become `RequestedRepair` graph/evidence objects, not raw chat.

### Stage 3: Grid Solver

Use a grid/ILP or CP-SAT solver:

- Cell states: empty, standard stall, accessible stall, aisle, ramp, core,
  pedestrian route, column obstruction.
- Connectivity graph: stalls connect to driveway, driveway connects to
  entrance/exit.
- Objective: satisfy required spaces first, then maximize usability/compactness
  and minimize mass damage.

### Stage 4: Advanced Optimization

Branch-and-cut / valid-inequality solver can be added later for difficult
medium-size envelopes. This should be an optional slow solver, not the default
interactive path.

## Design Decision For This Project

Use a tiered solver:

```text
law graph required count
-> module capacity precheck
-> repair request if clearly infeasible
-> grid/ILP solver for reviewable layouts
-> optional branch-and-cut for hard cases
```

Do not claim compliance from the module precheck. It is only an early feasibility
gate for MAAS generation.
