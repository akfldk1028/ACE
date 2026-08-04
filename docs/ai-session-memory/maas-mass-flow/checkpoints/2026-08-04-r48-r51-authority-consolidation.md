# MAAS MASS Flow Checkpoint: r48-r51 Authority Consolidation

Date: 2026-08-04

Status: authoritative checkpoint for r48-r51. Focused refactor tests are
verified. No full benchmark has been run after commit `7b093e1`.

## Authority invariants

- The LLM authors the full typed BOOK graph.
- Matrix4 owns principal placement in physical space.
- Typed CSG owns nonlinear geometry construction.
- Certified metric geometry is the sole visual, artifact, law, capacity,
  witness, persistence, and archive authority.
- XY and Z must use one declared physical metric coordinate contract. A visual
  payload may not mix XY meters with normalized Z.
- Canonical surface payload, payload hash, geometry hash, and persisted artifact
  identity must describe the same immutable geometry.
- Statutory law and parking remain hard authorities.
- Final VLM remains hard for genuine provider program-fit and provider blocking
  verdicts. Competition score floors and locally derived diagnostics remain
  ranking and repair evidence.
- Facade development happens later and is not MASS geometry authority.
- No convex hull, synthetic capacity plate, largest-component substitution,
  loft, prism, or other fallback may replace certified geometry.
- Fail-closed compatibility checks must not be weakened to admit stale or
  noncanonical archive fixtures.

## Commit chronology

- `58fe0d4`: metric projection authority.
- `7c13423`: canonical metric artifact binding.
- `7b093e1`: refactor to immutable `CertifiedMassArtifact` and typed
  `StageOutcome`.

## r48

Verified result:

- Selected: 1/5.
- Selected BOOK language: `shift+shift`.

Exact verified funnel:

- Attempts: 62.
- Materialized: 16.
- Clean: 12.
- Program hard passes: 8.
- BASE reviewed/approved supply: 4 approved.
- Released parents: 3.
- Downstream candidates: 4.
- Final VLM: 4 reviewed -> 1 hard pass.
- Selected: 1.

Root cause discovered from the selected artifact:

- The visual payload mixed coordinate systems.
- XY values were physical meters.
- Z remained normalized.
- The candidate could pass the funnel and persist a selection, but the visual
  artifact was not one coherent physical metric surface payload.

PNG:

- `D:/Data/25_ACE/docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r48/maas-book-neighborhood-5.png`

## r49

Verified result:

- Physical metric payload v2 corrected the visual appearance.
- Selected: 0.

Root cause:

- The corrected visual geometry and the bound artifact identity disagreed at
  the artifact hash boundary.
- The metric payload was visually correct, but its canonical artifact hash did
  not match the hash expected by the downstream authority chain.
- The system correctly failed closed rather than accepting a visually plausible
  but identity-mismatched artifact.

PNG:

- `D:/Data/25_ACE/docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r49/maas-book-neighborhood-5.png`

## r50

Verified result:

- Canonical artifact hash binding was corrected.
- Selection still did not complete.

Root cause:

- The v2 payload crossed a consumer boundary using field names that did not
  match the field names expected by the receiving contract.
- Geometry and hash authority were aligned, but schema transport remained
  incompatible.

## r51

Verified result:

- The run reached persistence.
- Persistence then crashed.

Root cause:

- A stale source object was reserialized after canonical metric artifact
  binding.
- That reserialization reintroduced an obsolete mutable representation instead
  of persisting the already certified immutable artifact.
- The crash showed that geometry authority was still duplicated between the
  certified artifact and stale source serialization.

## Authority consolidation refactor

Commit `7b093e1` consolidated the pipeline around two typed values.

### Immutable CertifiedMassArtifact

- The certified MASS artifact is immutable after certification.
- Canonical metric surface payload and its hashes travel together.
- Persistence consumes the certified artifact rather than rebuilding it from a
  stale source object.
- Visual, witness, archive, and persistence consumers share one artifact
  identity.
- Source objects may retain lineage and authoring evidence, but cannot
  reserialize or replace certified geometry.

### Typed StageOutcome

- Stage transport uses a typed outcome rather than loosely related dictionaries
  and mutable side channels.
- A stage outcome carries explicit success/failure state and the artifact or
  diagnostic evidence produced by that stage.
- Downstream stages cannot silently combine a current hash with an obsolete
  payload or stale source.
- Failures remain explicit and fail closed.

### Removed or retired authority paths

- Removed the stale source reserialization path from persistence authority.
- Removed parallel mutable geometry payload authority after certification.
- Removed implicit reconstruction of canonical metric geometry from legacy
  source fields.
- Removed untyped stage handoffs that allowed payload, hash, and field-name
  versions to drift independently.
- Retained legacy data only as lineage/diagnostic evidence where it cannot
  replace the certified artifact.

These deletions consolidate authority; they do not introduce fallback geometry
or relax law, parking, VLM, hash, or schema checks.

## Focused verification

Verified focused tests after the consolidation:

- Visual authority suite: 7 tests plus its subtests passed.
- Typed stage/outcome suite: 7 tests passed.

The focused tests cover the metric visual payload, canonical artifact binding,
immutable artifact transport, and typed stage outcomes. They are not evidence
of a successful post-refactor full benchmark.

## Known compatibility gap

- Two existing legal archive fixtures fail closed at
  `canonical_metric_surface_payload`.
- Those fixtures do not satisfy the new canonical metric artifact contract.
- Their failure was not hidden, bypassed, or weakened.
- No compatibility fallback was added.
- The fixtures require explicit migration or replacement with canonical metric
  payload evidence if they are intended to remain valid.

## Current verified status

- `CertifiedMassArtifact` and `StageOutcome` focused tests are green.
- The r48 mixed-coordinate visual defect has a metric projection correction.
- The r49 artifact hash mismatch has canonical metric binding.
- The r50 v2 field-name transport mismatch is included in the consolidated
  typed contract.
- The r51 stale source persistence path has been removed from authority.
- Two legacy archive fixtures remain intentionally fail-closed.
- No full benchmark has been run after `7b093e1`.

## Next action

Run one r52 target-5 full benchmark before writing more code.

Required comparison:

1. Capture the complete fixed funnel using the r48 axes: attempts,
   materialized, clean, program hard pass, BASE approved, released parent,
   downstream, final VLM reviewed/pass, and selected.
2. Compare r52 counts directly with r48's
   `62/16/12/8 -> BASE 4 -> parent 3 -> downstream 4 -> final 4/1 -> selected 1`.
3. Inspect the r52 PNG against both the r48 mixed-coordinate PNG and the r49
   corrected-appearance PNG.
4. Confirm persistence completes from the immutable certified artifact without
   stale source reserialization.
5. Confirm canonical metric payload, payload hash, geometry hash, witness,
   archive, and persisted artifact remain identical through the terminal path.
6. Record any failure at its exact typed stage before proposing another code
   change.

The next step is evidence collection through one full r52 run, not additional
code first.
