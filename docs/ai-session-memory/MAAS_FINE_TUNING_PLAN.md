# MAAS Fine-Tuning Plan

Updated: 2026-06-10

## Decision

Do not fine-tune a model to emit raw mesh coordinates.

Fine-tune a model to translate architectural language into strict MAAS grammar
JSON. ARR/MAAS code remains the geometry source of truth, and validators remain
the legal source of truth.

```text
architectural intent
-> fine-tuned intent-to-sequence model
-> MAAS grammar JSON
-> deterministic geometry execution
-> legal repair/check
-> evidence bundle
-> agent review
```

## External Signals Checked

- `architext/gptj-162M`: LLM-style residential layout generation from natural
  language. Useful signal: text can map to geometric representation. Important
  caveat: conceptual design only, not construction/legal documentation.
- `zimhe/pseudo-floor-plan-12k`: synthetic Grasshopper/PlanFinder floor-plan
  dataset. Useful for controlled plan language; quality caveat is explicit.
- `Nithins03/us-architectural-floorplan-llm`: Qwen2.5-3B LoRA example using
  floor-plan JSON, adjacency, style, and design Q&A.
- ResPlan / vector-graph floor-plan research: directionally supports graph and
  vector representations for spatial AI, not image-only generation.
- Unified Vector Floorplan Generation via Markup Representation: supports the
  idea that structured markup/grammar can be trained as next-token prediction.
- Hugging Face Text-to-3D task: useful for general 3D assets, but not a legal
  architecture geometry source of truth.

## Model Task

Input:

```text
북측 일조 때문에 상부를 계단식으로 후퇴시키고,
저층은 포디움으로 잡고, 중앙에는 작은 중정을 넣어줘.
```

Output:

```json
{
  "intent": {
    "typology": "podium_stepback_courtyard",
    "priority": ["legal_capacity", "sunlight", "open_space"]
  },
  "maas_sequence": [
    {"verb": "base", "params": {"source": "legal_buildable"}},
    {"verb": "courtyard", "params": {"ratio": 0.18}},
    {"verb": "lift", "params": {"upper_ratio": 0.62}},
    {"verb": "step_envelope", "params": {"side": "north", "bands": 4}}
  ],
  "constraints": {
    "must_validate": ["bcr", "far", "height", "setback", "sunlight", "daylight"]
  }
}
```

## Data Sources

1. Current data-backed MAAS sequence library:
   - `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
2. Term ontology:
   - `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
3. Existing MAAS generated candidates:
   - candidate properties, `maas_verb_sequence`, `mass_volumes`,
     `floor_plates`, score, rejected sibling audit.
4. Evidence bundle:
   - `docs/ai-session-memory/schema/arr.maas.evidence.v0.schema.json`
   - live/generated evidence JSON.
5. Negative examples:
   - claims of legal pass without evidence.
   - raw coordinate/mesh outputs.
   - daylight reference surface treated as final compliance.
   - image/aesthetic generation mutating legal mass.

## Training Phases

### Phase 0 - Contract

- Freeze `maas_sequence.v0.schema.json`.
- Keep geometry execution in ARR deterministic code.
- Require JSON-only output for the translator task.

### Phase 1 - SFT Seed

- Export current sequence and term ontology into JSONL:

```bash
cd ARR/backend
.venv/bin/python -m design.maas.training.export_sft_seed
```

- Initial target: 500-2,000 examples.
- Include Korean/English aliases.
- Include negative examples for no-raw-mesh and no-unverified-pass behavior.

### Phase 2 - Generated Candidate Data

- Convert MAAS jobs/results/evidence to supervised examples:
  - prompt: site summary + intent.
  - answer: valid `maas_sequence` + required validators.
  - rationale fields can be stored for eval but not necessarily trained into
    final output.

### Phase 3 - Preference Tuning

- Pair good/bad sequences:
  - good: legal repair passes, meaningful plan/section diversity.
  - bad: invalid verb, envelope escape, tiny unusable floor, unsupported legal
    claim.
- Use DPO/ORPO only after SFT produces valid JSON consistently.

### Phase 4 - Tool Calling

Translator should request tools instead of inventing geometry:

- `generate_maas_variants`
- `validate_mass_candidate`
- `render_mass_evidence`
- `vworld_visual_check`
- `maas_review`

## Evaluation

- JSON schema validity.
- Supported verb rate.
- Legal repair pass rate.
- Candidate diversity class distribution.
- Missing-evidence honesty: must not mark unknown as pass.
- Human architect review of design intent fit.

## Immediate Implementation Tasks

- Move hardcoded grammar to JSON data. Done in first pass.
- Add seed SFT exporter. Done in first pass.
- Add job/evidence dataset exporter. Done in second pass.
- Add MAAS translator API surface. Baseline deterministic resolver done in second pass.
- Add eval script for schema validity and repair pass rate.

## 2026-06-10 Implementation Update

Implemented files:

- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
- `ARR/backend/design/maas/grammar/schema/maas_sequence.v0.schema.json`
- `ARR/backend/design/maas/grammar/sequence_library.py`
- `ARR/backend/design/maas/grammar/intent.py`
- `ARR/backend/design/maas/training/export_sft_seed.py`
- `ARR/backend/design/maas/training/export_job_sft.py`
- `ARR/backend/design/management/commands/export_maas_training_data.py`

Current command:

```bash
cd ARR/backend
.venv/bin/python manage.py export_maas_training_data --limit 2
```

Current outputs:

- `docs/ai-session-memory/datasets/maas_intent_sft_seed.jsonl`
  - 41 examples after adding sunlight aliases and one negative no-pass example.
- `docs/ai-session-memory/datasets/maas_evidence_review_sft.jsonl`
  - 2 examples with `--limit 2` from local DB evidence.

Baseline resolver check:

```python
from design.maas.grammar import resolve_intent_to_sequence
resolve_intent_to_sequence("북측 일조 때문에 상부를 계단식으로 후퇴")
```

Expected first proposal:

```text
grammar_sunlight_multi_step
```

The resolver is not the final AI model. It is a deterministic contract and
fallback layer so the future fine-tuned model has a concrete output target.

Management command behavior:

- By default, DB/evidence export disables Neo4j graph lookup to avoid noisy
  connection failures in offline/local training export.
- Use `--include-graph` only when Neo4j law provenance should be included.

Verification:

```bash
python -m json.tool ARR/backend/design/maas/grammar/data/maas_sequences.v0.json
python -m json.tool ARR/backend/design/maas/grammar/data/maas_terms.v0.json
python -m json.tool ARR/backend/design/maas/grammar/schema/maas_sequence.v0.schema.json
cd ARR/backend
env -u NEO4J_URI .venv/bin/python manage.py test design.test_maas_export --verbosity 1
```

Observed result:

```text
design.test_maas_export: 23 tests OK
```
