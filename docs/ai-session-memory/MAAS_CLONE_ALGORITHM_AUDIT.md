# MAAS Clone Algorithm Audit

Date: 2026-06-23

Update 2026-06-25:

- `ARR/backend/design/maas/research_backends/maas_clone_bridge.py` now imports
  `clone/MAAS/src` directly and compiles both the original simple grammar
  sanity sequence and the recovered 10 book case-study gold verb sequences.
- The exact `clone/MAAS/data/case_studies/labels.json` file is still missing
  and remains recorded as `missing_artifact`.
- The 10-case baseline is recovered from the original output artifact
  `clone/MAAS/outputs/sprint15_coma/book_case_eval.json::per_case.gold`.
  Latest verified benchmark:
  `docs/ai-session-memory/maas-benchmarks/maas_algorithm_benchmark_20260625T051624Z.json`.
- Result: original MAAS case baseline `compiled`, `10/10` cases compiled.
  Recovered original verbs:
  `bend`, `branch`, `cave`, `embed`, `expand`, `extrude`, `lift`, `nest`,
  `overlap`, `rotate_part`, `shift`, `stack`, `taper`.
- ARR currently shares `cave`, `lift`, `overlap`, `rotate_part`, `shift`,
  `taper`; the remaining absorption gap is `bend`, `branch`, `embed`,
  `expand`, `extrude`, `nest`, `stack`.

Purpose: record the detailed review of cloned algorithm repositories before
absorbing them into ARR MAAS. This project is a legal massing/design
collaboration system. Cloned code must not turn ARR into a generic ML geometry
demo or bypass deterministic Korean law checks.

## Verdict

The cloned algorithms must be reviewed repo by repo before use. The correct
near-term path is:

1. Use `clone/MAAS` as the main grammar/sequence reference.
2. Keep ARR Shapely/legal repair/evaluation as the geometry source of truth.
3. Use d4descent as an explicit external research backend when available.
   Graph2Plan, DRL-UrbanPlanning, ArchComplete, daylight, and evolutionary
   optimization remain scoped references for later layers.
4. Use the existing `clone/d4descent` checkout through a bridge. Do not create
   a second duplicated/vendor copy inside ARR. Do not let stochastic or
   optimizer output become legal geometry without ARR repair/evaluation.

The 2026-06-23 ARR operator work follows this rule: `diagonal_connect`,
`terrace_link`, and `sloped_roof_mass` were implemented as ARR-native
deterministic operators, not copied external geometry code.

## Repo Audit

| Repo | Algorithm core | License/status | Use now? | ARR action |
| --- | --- | --- | --- | --- |
| `clone/MAAS` | VerbSequence grammar, vocabulary, OpenSCAD-style compiler, sequence metrics | Internal repo, no external license file found in clone | Yes | Use direct clone bridge as reference baseline and absorb vocabulary, sequence schema, intent mapping, and sequence metrics into ARR-native Shapely/legal pipeline. Do not replace ARR geometry. |
| `clone/d4descent` | Shape grammar optimization with task/loss/object separation, rewrite proposals, differentiable objectives | README says CC BY-NC 4.0 | Yes, as external research backend | ARR now connects to `clone/d4descent/src` through a bridge that records optimizer/task interfaces and import status. Do not silently turn it into legal geometry truth. |
| `clone/archcomplete` | VQGAN + Transformer + DDPM voxel completion/variation/upsampling | MIT | Not in legal path | Future optional design inspiration/preview. Heavy GPU/stochastic output cannot be a legal massing source. |
| `clone/evolutionary-optimization` | GA, PSO, differential evolution black-box optimizer examples | MIT | Later | Use as a pattern for small in-house population search, not as vendored dependency. |
| `clone/Graph2Plan` | Boundary + layout graph to raster floorplan and refined room boxes; Matlab postprocess alignment | Mixed files; some Apache-noted borrowed code, no top-level license found | Later | Floor/core/program viability agent only. Not mass envelope generation. |
| `clone/DRL-UrbanPlanning` | PPO/SGNN spatial planning for land-use and roads; rule/GA baselines | MIT | Later | Benchmark/objective framing and human-AI planning workflow reference. Scale is community planning, not parcel legal massing. |
| `clone/daylight-optimization` | Grasshopper CMA-ES/Galapagos daylight optimization files | MIT | Not directly | Daylight objective precedent only. No direct Python runtime code. |
| `clone/ArchiGAN` | GAN-era architecture/city generation references | Unclear/background | No | Background reference only. |

## What Each Repo Actually Contributes

### `clone/MAAS`

Observed files:

- `src/maas/grammar/verb_sequence.py`
- `src/maas/grammar/vocab.py`
- `src/maas/eval/metrics.py`
- `docs/maas_overview/10_최종아키텍처.md`
- `docs/MASS_연구노트.md`

Useful concept:

- Text/site intent becomes a constrained verb sequence.
- A compiler turns that sequence into deterministic geometry.
- Metrics compare predicted/gold verb sequences by parsimony, verb-set
  Jaccard, token F1, and LCS.

ARR mapping:

- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
- `ARR/backend/design/maas/grammar/legal_interpreter.py`
- `ARR/backend/design/maas/morphology_operators.py`
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
- `ARR/backend/design/maas/research_backends/maas_clone_bridge.py`

This is the main valid absorption path.

### `clone/d4descent`

Observed files:

- `src/d4descent/optimizer.py`
- `src/d4descent/tasks/*`
- `src/d4descent/losses/*`
- `src/d4descent/objects/*`

Useful concept:

- Separate object representation, grammar rewrite proposals, objective/loss,
  optimizer, and metrics.
- Run continuous optimization while periodically trying discrete rewrites.

ARR mapping:

- `ARR/backend/design/maas/research_backends/d4descent_bridge.py` connects the
  cloned source path and attempts import by default.
- `ARR/backend/design/maas/design_quality.py` uses the d4descent task/loss/
  optimizer separation as candidate-quality evidence.
- The generated GeoJSON properties now include
  `design_quality.optimizer_backend.name=d4descent`.
- Future search loop can evaluate candidate sequences/operators using legal
  score plus design-quality score.

Current backend dependency status:

- On 2026-06-23, `ARR/backend/.venv` has `torch` but lacks `yaml`,
  `confify`, `diffusers`, and `kornia`.
- Therefore the bridge reports `status=import_failed` with the concrete Python
  import error until those research dependencies are installed.

Guardrail:

- CC BY-NC 4.0 remains recorded in evidence. The bridge uses the cloned code
  from `clone/d4descent/src`; do not duplicate/vendor another copy into ARR.
  ARR repair/evaluation remains the legal truth.

### `clone/Graph2Plan`

Observed files:

- `Network/model/model.py`
- `PostProcess/g2p/align.py`
- `Interface/model/*`

Useful concept:

- User-editable layout graph plus boundary can generate room boxes.
- GNN/CNN predicts room boxes and raster floorplan, then alignment fixes boxes.

ARR mapping:

- Later `plan_viability_agent`: given a legal mass/floor plate, check whether a
  rough core/program/room layout could exist.
- Not a current MAAS mass generator.

Guardrail:

- Matlab postprocess dependency and floorplan dataset assumptions make this
  unsuitable for ARR `/design` legal massing runtime.

### `clone/DRL-UrbanPlanning`

Observed files:

- `urban_planning/agents/urban_planning_agent.py`
- `urban_planning/envs/*`
- `urban_planning/models/baseline.py`
- `urban_planning/cfg/test_data/*/objectives_*.yaml`

Useful concept:

- Explicit objectives, constraints, baselines, reward logging, and
  human-AI planning workflow.

ARR mapping:

- Future benchmark harness can report pass rate, utilization, diversity,
  parking feasibility, datum/sunlight pass, and failure taxonomy.
- Not parcel-scale mass geometry.

### `clone/archcomplete`

Useful concept:

- 3D variation/interpolation/upsampling as design inspiration after the legal
  mass is fixed.

ARR mapping:

- Optional later aesthetic/proposal layer only.

Guardrail:

- Do not use voxel/ML output as legal geometry. All outputs must be rebuilt or
  rejected by ARR deterministic validators.

### `clone/evolutionary-optimization`

Useful concept:

- Basic GA/PSO/DE optimizer structure for black-box objective search.

ARR mapping:

- Later use for population search over ARR-native grammar/operator parameters.

Guardrail:

- Prefer compact in-house code or a maintained optimizer library. Do not vendor
  an old generic package wholesale.

### `clone/daylight-optimization`

Useful concept:

- Daylight objective precedent using Grasshopper CMA-ES/Galapagos workflows.

ARR mapping:

- Future daylight/solar score only, not runtime code.

## Current ARR Mapping Status

Already implemented on 2026-06-23:

- MAAS vocabulary support for `diagonal_connect`, `terrace_link`,
  `sloped_roof_mass`.
- Grammar sequences:
  `grammar_diagonal_step_connector`,
  `grammar_terrace_ribbon_stepback`,
  `grammar_sloped_roof_envelope`.
- Direct morphology variants:
  `diagonal_connect_step_x`, `diagonal_connect_step_y`,
  `terrace_link_north`, `sloped_roof_mass`.
- Preferred-operator selection so an agent-selected operator is not filtered
  out before final ranking.
- Tests in `ARR/backend/design/test_maas_export.py`.

Additional implementation on 2026-06-23:

- `ARR/backend/design/maas/design_quality.py`
  - Added MAAS sequence metrics adapted from `clone/MAAS`:
    parsimony, verb-set Jaccard, token F1, ordered LCS, plan/section verb
    coverage, and sequence richness.
  - Adds explainable `design_quality` evidence to generated legal candidates.
- `ARR/backend/design/maas/research_backends/d4descent_bridge.py`
  - Connects to `clone/d4descent/src`.
  - Attempts to import `d4descent.optimizer.optimize`,
    `OptimizeArgs`, `Task`, and `ObjectCollection` by default.
  - Captures dependency failures in candidate evidence instead of breaking the
    `/design` legal massing endpoint.
- `ARR/backend/design/maas/research_backends/maas_clone_bridge.py`
  - Directly imports `clone/MAAS/src` as an external reference baseline.
  - Runs original MAAS `VerbSequence -> compile_sequence` for a fixed reference
    sequence from the clone tests and records SCAD hash/metrics in the
    benchmark evidence.
  - Does not make original MAAS the legal geometry source.
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - Attaches `design_quality` and `design_quality_score` to selected variants
    and parking-repair variants after legal utilization metrics are computed.

Verified:

```bash
python3 -m json.tool ARR/backend/design/maas/grammar/data/maas_sequences.v0.json
python3 -m json.tool ARR/backend/design/maas/grammar/data/maas_terms.v0.json
python3 -m json.tool JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json
cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export
```

Result: JSON OK, `design.test_maas_export` 53 tests OK.

Latest result after design-quality/d4descent integration:

- JSON validation: OK.
- `design.test_maas_export`: 56 tests OK.
- Current d4descent bridge status in `ARR/backend/.venv`:
  `imported`. `ARR/backend/requirements.txt` now includes the minimal imports
  needed by the bridge, `PyYAML>=6.0.2` and `scikit-video>=1.1.11`. The bridge
  path exists and records the real optimizer/task interfaces.

Additional benchmark harness update on 2026-06-24:

- Added `ARR/backend/design/management/commands/benchmark_maas_algorithms.py`.
  This is the first deterministic benchmark harness for the paper/clone
  absorption path. It compares baseline legal-envelope output and preferred
  MAAS grammar/design operators over fixed geometry fixtures.
- Default benchmark mode is parking-disabled so mass/design algorithm checks do
  not block on Neo4j or local parking evidence. Use `--with-parking` when
  explicitly testing parking count/layout evidence.
- Latest command:
  `cd ARR/backend && .venv/bin/python manage.py benchmark_maas_algorithms --max-variants 6`.
- Latest output:
  `docs/ai-session-memory/maas-benchmarks/latest.json` and timestamped
  `maas_algorithm_benchmark_20260624T130531Z.json`.
- Latest aggregate:
  `scenario_count=14`, `successful_scenarios=14`, `feature_count=84`,
  `unique_mass_shape_count=19`, `unique_concept_count=16`,
  `unique_verb_count=16`, `average_unique_shapes_per_scenario=6.0`,
  `legal_pass_rate=1.0`, `preferred_survival_rate=1.0`,
  `preferred_top_rate=1.0`, `average_design_quality=0.6424`,
  `original_maas_baseline_status=compiled`,
  `section_connector_feature_count=14`,
  `section_connector_scenario_count=14`,
  `section_connector_shape_count=7`, `parking_evidence_feature_count=0`,
  `parking_pass_rate=null`.
- The command now prints CLI-visible diversity evidence after the aggregate,
  one line per scenario, e.g.
  `6 variants, 6 shapes, 7-9 verbs, connectors=1, top=...`.
  This is intended to catch regressions where the algorithm returns many
  candidates but they collapse to the same mass family or lose the stepped-mass
  connector alternatives.
- Baseline scenarios now preserve at least one section connector candidate in
  the visible top `max_variants` list. This matters because stepped massing
  must be compared against diagonal/terrace/sloped linking alternatives, not
  only against unrelated plan-shape variants or forced preferred operators.
- Follow-up code review added a parking-gate guard for this preservation step:
  if legal parking required count is resolved, the connector candidate may not
  replace the visible tail unless its parking priority is at least as good.
  Benchmark mode without `--with-parking` still preserves connector diversity
  because it is measuring mass algorithm coverage, not parking evidence.
- Original MAAS baseline status:
  `maas_clone_bridge` imports `clone/MAAS/src`, compiles the original
  `VerbSequence` fixture to SCAD, records a SCAD hash, and compares reference
  verbs `cave,taper` against ARR benchmark verbs. The expected
  `clone/MAAS/data/case_studies/labels.json` is missing in this checkout, so
  book case-study baseline is recorded as `missing_artifact` until restored.
- Parking field semantics were tightened after review: in parking-disabled
  mode each feature now has `parking_evidence_enabled=false` and
  `parking_status=null`. `parking_layout_status` may still record the local
  layout candidate status, but it is not counted as legal parking evidence
  unless `--with-parking` provides a required-space count.
- Latest full regression:
  `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export -v 1`
  passed `58` tests.

## Current Module Boundaries

- `design.maas.grammar.*`
  - Owns ARR-local MAAS vocabulary, sequence JSON loading, intent matching, and
    interpretation into deterministic Shapely seed variants.
- `design.maas.morphology_operators`
  - Owns deterministic footprint/upper-footprint operators.
- `design.maas.legal_mesh_optimizer`
  - Owns legal envelope generation, repair, FAR/BCR/height checks, parking
    attachment, final variant ranking, and candidate properties.
- `design.maas.design_quality`
  - Owns non-legal design-quality evidence:
    MAAS sequence metrics, compactness, plate profile, sequence richness, and
    `design_quality_score`.
- `design.maas.research_backends.d4descent_bridge`
  - Owns the external `clone/d4descent/src` bridge and import status evidence.
  - It must not become the legal validator. It is a research optimizer/backend
    integration point.

## Next Implementation Order

1. Extend the benchmark harness beyond fixed geometry fixtures to live PNU
   cases only after keeping deterministic fixture output stable.
   - baseline legal box: implemented in `benchmark_maas_algorithms`
   - current morphology variants: implemented in `benchmark_maas_algorithms`
   - grammar sequence variants: implemented in `benchmark_maas_algorithms`
   - preferred operator variants: implemented in `benchmark_maas_algorithms`
2. Keep d4descent as an external research backend, not as the legal geometry
   source.
   - Current bridge import status: `imported`.
   - Minimal bridge dependencies installed/recorded: `PyYAML`,
     `scikit-video`.
   - Heavier d4descent research dependencies such as `diffusers`, `kornia`,
     and `transformers` are still not required unless ARR adds diffusion/SDS
     experiments.
   - Keep any future import failures visible in
     `design_quality.optimizer_backend`.
3. Only after benchmark evidence, add an optimizer loop.
   - Search over ARR-native sequences/operators.
   - Keep law, datum, parking, coverage, FAR, and sunlight checks as hard gates.
4. Later add plan/core viability and daylight/aesthetic agents.

## Do Not Do

- Do not make a new MAAS engine beside ARR.
- Do not duplicate/vendor d4descent code into ARR; use `clone/d4descent/src`
  through `d4descent_bridge.py`.
- Do not use ArchComplete, Graph2Plan, DRL, or GAN output as legal geometry.
- Do not optimize for visual novelty before datum, legal envelope, parking, and
  provenance pass.
- Do not claim the mass is "paper-perfect" until benchmark cases and visual
  Playwright PNG checks pass.

## Next Session Read List

Read these before editing MAAS again:

1. `docs/ai-session-memory/README.md`
2. `docs/ai-session-memory/MAAS_EXTERNAL_REPO_ABSORPTION.md`
3. `docs/ai-session-memory/MAAS_CLONE_ALGORITHM_AUDIT.md`
4. `ARR/backend/design/maas/morphology_operators.py`
5. `ARR/backend/design/maas/legal_mesh_optimizer.py`
6. `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
7. `clone/MAAS/src/maas/grammar/verb_sequence.py`
8. `clone/MAAS/src/maas/eval/metrics.py`
