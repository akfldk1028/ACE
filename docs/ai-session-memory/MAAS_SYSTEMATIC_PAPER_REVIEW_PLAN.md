# MAAS Systematic Paper Review Plan

Created: 2026-07-07

## Why This Exists

The current MAAS loop can pass legal/parking/diversity counters while still
looking architecturally weak: some candidates read as irregular fragments, and
some do not show a clear mixture of architectural languages.

Therefore the next loop must pause implementation-first hacking and review the
papers systematically.

## Review Question

How should ARR generate legal massing alternatives that are:

- inside deterministic Korean legal envelopes,
- diverse without becoming random,
- composed from legible architectural languages,
- traceable from language -> grammar -> geometry -> legal repair -> PNG,
- suitable as a research method, not just a product demo.

## Paper Buckets

### 1. Solver-Aided LLM CAD / Hierarchical DSL

Core papers:

- AIDL 2025, "A Solver-Aided Hierarchical Language for LLM-Driven CAD Design"
- LLM-for-CAD survey 2025
- CAD-HLLM / CAD-Assistant style tool-augmented CAD generation

What ARR should extract:

- LLM should produce hierarchical DSL and design intent.
- Solver should handle geometric/legal feasibility.
- The DSL should separate high-level composition from low-level coordinates.

ARR check:

- `llm_proposals.py` must emit `primary_language`, `secondary_language`,
  hierarchy/composition intent, and authored parameters.
- `source_geometry/compiler.py` must compile this into explicit source volumes.
- `legal_mesh_optimizer.py` must validate/clip/reject, not invent design intent.

### 2. Shape Grammar / Graph Grammar / Optimizable Grammar

Core papers:

- Procedural Modeling of Buildings, SIGGRAPH 2006
- Example-Based Procedural Modeling Using Graph Grammars, SIGGRAPH 2023
- Design for Descent, SIGGRAPH Asia 2025

What ARR should extract:

- Massing needs rule hierarchy and topology, not only family labels.
- A good grammar is easy to optimize and produces legible derivation traces.
- Mixed language should be represented as `primary rule + modifier rule`.

ARR check:

- Add `composition_rule`, `composition_layer_roles`, and topology tags.
- Reject random fragment helpers that exist only to increase volume count.
- PNG/JSON verifier should measure compositional evidence, not just count.

### 3. Evolutionary / Typological Massing Optimization

Core papers:

- EvoMass FOAR 2024
- SSIEA / island-based evolutionary architectural design
- Parallel typological optimization in architectural design, 2026
- CAADRIA 2025 performance-based urban massing optimization

What ARR should extract:

- Diversity comes from population search and typology-aware selection.
- Candidate groups should be selected as representatives/medoids, not random
  high-score leftovers.
- Performance and diversity must be optimized together.

ARR check:

- Add population log: generated candidates, rejects, repairs, objective vectors.
- Add cluster/medoid selection over primary/secondary language, topology, height,
  footprint, and legal metrics.
- Keep island quotas, but do not confuse island labels with architectural language.

### 4. Constraint-Aware Generation / Projection

Core papers:

- Constraint-aware generative surveys in local research folder
- Projected Diffusion / constrained discrete diffusion as future references
- Whiting et al. structurally sound procedural modeling as classic constraint
  integration reference

What ARR should extract:

- Hard constraints belong inside generation/projection, not only post-hoc text.
- Severe repair should be penalized because it means the design intent did not
  survive the legal envelope.

ARR check:

- Preserve deterministic legal checks.
- Add `repair_delta` and severe-repair rejection/penalty.
- Do not let image/PNG overlay hide illegal or heavily repaired geometry.

### 5. Generative Pre-Design / Problem Framing

Core papers:

- CAADRIA 2026 generative pre-design framework
- Human-in-the-loop generative design workflow references

What ARR should extract:

- Early optimization is also information collection and problem framing.
- The system should record rejected hypotheses and revised exploration direction.

ARR check:

- Add session artifact:
  `goal -> hypothesis -> generated population -> critic -> revised goal`.
- Store why a mass family was reduced, merged, rejected, or promoted.

## Immediate Reading Order

1. AIDL 2025 and LLM-for-CAD survey:
   define the LLM/DSL/solver contract.
2. Shape grammar / Design for Descent:
   define compositional mass language.
3. EvoMass / SSIEA / parallel typological optimization:
   define diversity-preserving selection.
4. CAADRIA 2025/2026 massing and pre-design:
   define architectural workflow and problem-framing artifacts.
5. Constraint-aware generation:
   define projection/repair and hard-constraint evidence.

## Required Output Of The Review

For every paper:

- citation/link,
- actual method claim,
- what not to overclaim,
- corresponding ARR module,
- missing code,
- verifier gate,
- PNG/JSON evidence needed.

## Next Code Rule

Do not add more mass families or numeric presets until the review matrix states
which paper requirement they satisfy and which verifier proves it.
