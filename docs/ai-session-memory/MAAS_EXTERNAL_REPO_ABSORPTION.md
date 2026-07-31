# MAAS External Repo Absorption Review

Date: 2026-06-23

Purpose: record which cloned research repositories can be absorbed into ARR
MAAS without confusing the legal-design goal. The project target remains legal
Korean PNU massing first, then design grammar/operator exploration inside the
validated envelope.

## Current Clone Inventory

Existing or newly cloned references under `/mnt/d/Data/25_ACE/clone`:

- `clone/MAAS`
  - Remote: `https://github.com/akfldk1028/MAAS.git`
  - Status: highest-value internal reference.
  - Relevant content: Operative Design verb vocabulary, `VerbSequence`,
    OpenSCAD compiler, case-study labels, zero-shot verb evaluation.
  - Absorption rule: do not replace ARR geometry. Port vocabulary, sequence
    ideas, intent mapping, and evaluation metrics into ARR deterministic
    Shapely/legal pipeline.
- `clone/d4descent`
  - Remote: `https://github.com/milmillin/d4descent.git`
  - Paper: "Design for Descent: What Makes a Shape Grammar Easy to Optimize?",
    SIGGRAPH Asia 2025.
  - License: CC BY-NC 4.0. Do not copy into production/commercial code.
  - Relevant content: grammar object model, optimizer/task/loss separation,
    raster/SDS/topology objective structure.
  - Absorption rule: use only as conceptual reference. Reimplement our own
    grammar optimizer interface if needed.
- `clone/archcomplete`
  - Remote: `https://gitlab.cg.tuwien.ac.at/srasoulzadeh/archcomplete.git`
  - Paper: ArchComplete, Computers & Graphics 2025.
  - License: MIT.
  - Relevant content: 3D voxel generation, interpolation, variation, and
    upsampling. Heavy A100-oriented model pipeline.
  - Absorption rule: not suitable as ARR legal geometry truth. Use as a future
    design-style/variation reference only after legal mass is locked.
- `clone/daylight-optimization`
  - Remote: `https://github.com/Pi-Star-Lab/daylight-optimization.git`
  - License: MIT.
  - Relevant content: Grasshopper CMA-ES/Galapagos daylight optimization files.
  - Absorption rule: no direct Python code. Useful as objective-function
    precedent for daylight/solar score, not as runtime dependency.
- `clone/evolutionary-optimization`
  - Remote: `https://github.com/strongio/evolutionary-optimization.git`
  - License: MIT.
  - Relevant content: GA, PSO, DEA style black-box optimizer examples.
  - Absorption rule: only small algorithmic ideas are useful. ARR should prefer
    a compact in-house optimizer or scipy/DEAP/Optuna rather than vendoring this
    old package wholesale.
- `clone/Graph2Plan`
  - Remote: `https://github.com/HanHan55/Graph2plan.git`
  - Paper: SIGGRAPH 2020.
  - Relevant content: layout graph to floorplan pipeline.
  - Absorption rule: not for current mass generation. Later useful for
    floor-plan viability, room/core adjacency, and plan refinement checks.
- `clone/DRL-UrbanPlanning`
  - Remote: `https://github.com/tsinghua-fib-lab/DRL-urban-planning.git`
  - Paper: Nature Computational Science 2023.
  - License: MIT.
  - Relevant content: spatial planning objectives, baselines, human-AI
    collaborative planning workflow.
  - Absorption rule: useful for benchmark framing and objective reporting, not
    for parcel-scale mass geometry.
- `clone/ArchiGAN`
  - Remote: `https://github.com/archiGAN/SmartCity.git`
  - Relevant content: GAN-era architecture generation references/PDFs.
  - Absorption rule: background only. Do not use as ARR geometry algorithm.

## What Is Already Absorbed In ARR

ARR already has the correct architectural direction in code:

- `ARR/backend/design/maas/morphology_operators.py`
  - deterministic Shapely operators for inset, BCR fill, notch, open court,
    bar, split-bridge, branch, pinch, interlock, overlap, courtyard, terrace,
    tower/stepback families.
- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
  - term ontology mapping Korean/English design words to MAAS verbs.
- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
  - data-backed grammar sequences such as sunlight stepback, courtyard+taper,
    split+bridge+stepback, bar+notch+terrace, overlap+shift+terrace.
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - attaches operator family, concept labels, 3D diversity signatures, legal
    repair/evaluation, parking requirements, and ranking.

Therefore the next step is not a fresh rewrite. It is to strengthen design
quality and benchmark evidence around the existing ARR modules.

## Absorption Priority

1. Expand ARR sequence library from `clone/MAAS` vocabulary.
   - Add design operators that make legal stepped envelopes feel intentional:
     `diagonal_connect`, `terrace_link`, `sloped_roof_mass`,
     `street_wall_cut`, `podium_carve`, `view_corridor_notch`.
   - Keep each as JSON sequence + deterministic Shapely/volume operation.
2. Add a design-quality scorer.
   - Inputs: volume profile, floor plate area profile, operator family,
     compactness, usable plate depth, terrace continuity, envelope utilization,
     diversity distance.
   - Output: evidence field, not a hidden aesthetic claim.
3. Add benchmark harness.
   - Run baseline legal box, current ARR morphology, and grammar variants across
     20-50 PNU cases.
   - Metrics: legal pass rate, FAR/BCR utilization, parking feasibility,
     sunlight/datum pass, diversity, runtime, failure taxonomy.
4. Keep ML/generative models outside the legal truth path.
   - ArchComplete/diffusion/VLM ideas may suggest variations or styles.
   - ARR deterministic validators must rebuild and recheck all geometry.

## License Guardrails

- MIT repositories may be copied with notices, but copying is still not the
  preferred first step.
- CC BY-NC repositories such as `d4descent` must not be copied into product or
  commercial code. Use paper-level ideas and implement our own clean version.
- PDFs and datasets from third parties are research references only unless
  their licenses explicitly allow redistribution or derivative use.

## Next AI Session Instruction

If continuing this work:

1. Do not create a new MAAS engine.
2. Read this memo, then inspect:
   - `ARR/backend/design/maas/morphology_operators.py`
   - `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
   - `ARR/backend/design/maas/legal_mesh_optimizer.py`
   - `clone/MAAS/src/maas/grammar/vocab.py`
3. Add missing design-oriented operators only as small, testable modules.
4. Every new geometry operation must pass legal repair/evaluation before UI.
5. Use Playwright and PNG evidence after changes to `/design`.

## 2026-06-23 Implementation Update

ARR absorbed the first design-oriented massing operators inspired by the
`clone/MAAS` verb grammar and recent shape-grammar/massing research direction.
This is not a wholesale clone import; the operators are ARR-native and still
run through deterministic legal repair/evaluation.

Implemented files:

- `ARR/backend/design/maas/grammar/vocab.py`
  - Added supported design-section verbs:
    `diagonal_connect`, `terrace_link`, `sloped_roof_mass`.
- `ARR/backend/design/maas/grammar/legal_interpreter.py`
  - Interprets those verbs into upper-footprint/section hints.
- `ARR/backend/design/maas/morphology_operators.py`
  - Added direct seed variants:
    `diagonal_connect_step_x`, `diagonal_connect_step_y`,
    `terrace_link_north`, `sloped_roof_mass`.
- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
  - Added ontology terms for diagonal connection, terrace linking, and sloped
    roof massing.
- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
  - Added grammar sequences:
    `grammar_diagonal_step_connector`,
    `grammar_terrace_ribbon_stepback`,
    `grammar_sloped_roof_envelope`.
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - Added concept labels/families and preferred-operator handling so an agent
    or user-selected design operator survives final selection and is placed
    first.
- `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`
  - Updated `maas_geometry_agent` responsibility: it owns MAAS repair/design
    operators. Law/parking agents still own legal evidence.
- `ARR/backend/design/test_maas_export.py`
  - Added tests for new sequence generation, morphology upper-mass hints,
    ontology entries, and preferred design operator selection.

Verification:

```bash
python3 -m json.tool ARR/backend/design/maas/grammar/data/maas_sequences.v0.json
python3 -m json.tool ARR/backend/design/maas/grammar/data/maas_terms.v0.json
python3 -m json.tool JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json
cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export
```

Result:

- JSON validation: OK.
- `design.test_maas_export`: 53 tests OK.
- Sample generation produced 12 grammar variants and 37 morphology variants.
- Preferred operator loop confirmed these can be returned first:
  `grammar_terrace_ribbon_stepback`,
  `grammar_sloped_roof_envelope`,
  `diagonal_connect_step_x`,
  `terrace_link_north`,
  `sloped_roof_mass`.

Responsibility model:

- `law_graph_agent`: legal envelope/source/provenance.
- `parking_agent`: parking count/layout evidence.
- `maas_geometry_agent`: repair/design operators, including the new
  `diagonal_connect`, `terrace_link`, `sloped_roof_mass`.
- `review_agent`: final evidence and remaining-risk summary.
